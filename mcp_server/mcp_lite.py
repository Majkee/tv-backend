"""A stdlib-only stand-in for the official MCP Python SDK (``mcp`` on PyPI).

Use it only where ``pip install mcp`` is not possible (no pip, Python 3.9,
locked-down laptop). It implements the part of ``MCPServer`` (SDK 2.x; ``FastMCP`` in 1.x)
used in this repository: tools, static resources and prompts over the stdio
transport. Server code stays the same, only the imports change:

    from mcp.server.mcpserver import MCPServer                # official SDK
    from mcp.server.mcpserver.exceptions import ToolError
    from mcp.types import ToolAnnotations
    from pydantic import Field

    from mcp_lite import MCPServer, ToolError, ToolAnnotations, Field   # this file

As in the SDK, only a ``ToolError`` message reaches the agent; any other
exception becomes a generic "Error executing tool ..." and its traceback goes
to stderr.

Under the hood MCP over stdio is JSON-RPC 2.0, one JSON message per line:
the client writes requests to the server's stdin and reads responses from
its stdout. Anything else printed to stdout breaks the connection, so this
module sends ``print`` output to stderr while the server runs.
"""

import inspect
import json
import sys
import traceback
import typing

# Newest first. The server answers with the client's version when it knows it.
PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

_JSON_TYPES = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}


class Field:
    """Parameter description, used like ``pydantic.Field``:

    ``device_id: Annotated[str, Field(description="Identyfikator, np. TV-003.")]``
    """

    def __init__(self, default=None, description=None, **_ignored):
        self.description = description


class ToolAnnotations:
    """Hints for the client, like ``mcp.types.ToolAnnotations``: ``ToolAnnotations(readOnlyHint=True)``."""

    def __init__(self, **hints):
        self.hints = hints


class ToolError(Exception):
    """Raise from a tool to send the agent a readable error message."""


class McpError(Exception):
    """A protocol-level error, sent back as a JSON-RPC error response."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class MCPServer:
    def __init__(self, name=None, instructions=None, **_ignored):
        self.name = name
        self.instructions = instructions
        self._tools = {}
        self._resources = {}
        self._prompts = {}

    # ---------- registration ----------

    def tool(self, name=None, description=None, annotations=None, **_ignored):
        def register(fn):
            params, required = _parameters(fn)
            self._tools[name or fn.__name__] = {
                "fn": fn,
                "description": description or _doc(fn),
                "inputSchema": {"type": "object", "properties": params, "required": required},
                "annotations": annotations.hints if annotations else None,
            }
            return fn

        return register

    def resource(self, uri, name=None, description=None, mime_type=None, **_ignored):
        def register(fn):
            self._resources[uri] = {
                "fn": fn,
                "name": name or fn.__name__,
                "description": description or _doc(fn),
                "mimeType": mime_type or "text/plain",
            }
            return fn

        return register

    def prompt(self, name=None, description=None, **_ignored):
        def register(fn):
            params, required = _parameters(fn)
            arguments = []
            for arg_name, schema in params.items():
                argument = {"name": arg_name, "required": arg_name in required}
                if "description" in schema:
                    argument["description"] = schema["description"]
                arguments.append(argument)
            self._prompts[name or fn.__name__] = {"fn": fn, "description": description or _doc(fn), "arguments": arguments}
            return fn

        return register

    # ---------- transport ----------

    def run(self, transport="stdio"):
        if transport != "stdio":
            raise ValueError("mcp_lite supports only the stdio transport")
        out = sys.stdout.buffer
        sys.stdout = sys.stderr  # a stray print() must not corrupt the protocol stream
        for raw in sys.stdin.buffer:
            line = raw.decode("utf-8").strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except ValueError:
                response = _error(None, PARSE_ERROR, "Parse error")
            else:
                response = self.handle_message(message)
            if response is not None:
                out.write((json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))
                out.flush()

    def handle_message(self, message):
        """Handle one JSON-RPC message. Returns the response, or None for notifications."""
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or "method" not in message:
            return _error(message.get("id") if isinstance(message, dict) else None, INVALID_REQUEST, "Invalid request")
        if "id" not in message:
            return None  # notifications such as notifications/initialized need no answer
        handler = {
            "initialize": self._initialize,
            "ping": lambda params: {},
            "tools/list": self._tools_list,
            "tools/call": self._tools_call,
            "resources/list": self._resources_list,
            "resources/templates/list": lambda params: {"resourceTemplates": []},
            "resources/read": self._resources_read,
            "prompts/list": self._prompts_list,
            "prompts/get": self._prompts_get,
        }.get(message["method"])
        if handler is None:
            return _error(message["id"], METHOD_NOT_FOUND, "Method not found: %s" % message["method"])
        try:
            result = handler(message.get("params") or {})
        except McpError as exc:
            return _error(message["id"], exc.code, str(exc))
        except Exception as exc:  # noqa: BLE001 - report, keep the server alive
            traceback.print_exc(file=sys.stderr)
            return _error(message["id"], INTERNAL_ERROR, str(exc))
        return {"jsonrpc": "2.0", "id": message["id"], "result": result}

    # ---------- methods ----------

    def _initialize(self, params):
        requested = params.get("protocolVersion")
        result = {
            "protocolVersion": requested if requested in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "serverInfo": {"name": self.name or "mcp_lite", "version": "mcp_lite"},
        }
        if self.instructions:
            result["instructions"] = self.instructions
        return result

    def _tools_list(self, params):
        tools = []
        for name, tool in self._tools.items():
            entry = {"name": name, "description": tool["description"], "inputSchema": tool["inputSchema"]}
            if tool["annotations"]:
                entry["annotations"] = tool["annotations"]
            tools.append(entry)
        return {"tools": tools}

    def _tools_call(self, params):
        name = params.get("name")
        tool = self._tools.get(name)
        if tool is None:
            raise McpError(INVALID_PARAMS, "Unknown tool: %s" % name)
        arguments = params.get("arguments") or {}
        schema = tool["inputSchema"]
        missing = [p for p in schema["required"] if p not in arguments]
        unknown = [p for p in arguments if p not in schema["properties"]]
        if missing or unknown:
            problems = []
            if missing:
                problems.append("brak wymaganych parametrów: " + ", ".join(missing))
            if unknown:
                problems.append("nieznane parametry: " + ", ".join(unknown))
            return _tool_error("Błędne wywołanie %s: %s." % (name, "; ".join(problems)))
        try:
            value = tool["fn"](**arguments)
        except ToolError as exc:
            return _tool_error("Error executing tool %s: %s" % (name, exc))
        except Exception:  # noqa: BLE001 - details stay in the server log, like in the SDK
            traceback.print_exc(file=sys.stderr)
            return _tool_error("Error executing tool %s" % name)
        return {"content": [{"type": "text", "text": _text(value)}], "isError": False}

    def _resources_list(self, params):
        resources = []
        for uri, res in self._resources.items():
            resources.append({"uri": uri, "name": res["name"], "description": res["description"], "mimeType": res["mimeType"]})
        return {"resources": resources}

    def _resources_read(self, params):
        uri = params.get("uri")
        res = self._resources.get(uri)
        if res is None:
            raise McpError(INVALID_PARAMS, "Unknown resource: %s" % uri)
        return {"contents": [{"uri": uri, "mimeType": res["mimeType"], "text": _text(res["fn"]())}]}

    def _prompts_list(self, params):
        prompts = []
        for name, prompt in self._prompts.items():
            prompts.append({"name": name, "description": prompt["description"], "arguments": prompt["arguments"]})
        return {"prompts": prompts}

    def _prompts_get(self, params):
        name = params.get("name")
        prompt = self._prompts.get(name)
        if prompt is None:
            raise McpError(INVALID_PARAMS, "Unknown prompt: %s" % name)
        missing = [a["name"] for a in prompt["arguments"] if a["required"] and a["name"] not in (params.get("arguments") or {})]
        if missing:
            raise McpError(INVALID_PARAMS, "Missing prompt arguments: %s" % ", ".join(missing))
        text = _text(prompt["fn"](**(params.get("arguments") or {})))
        return {
            "description": prompt["description"],
            "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
        }


FastMCP = MCPServer  # the SDK 1.x name


def _doc(fn):
    return inspect.cleandoc(fn.__doc__) if fn.__doc__ else ""


def _parameters(fn):
    """JSON Schema properties and required names from a function signature."""
    hints = typing.get_type_hints(fn, include_extras=True)
    properties = {}
    required = []
    for name, param in inspect.signature(fn).parameters.items():
        properties[name] = _schema(hints.get(name, inspect.Parameter.empty))
        if param.default is inspect.Parameter.empty:
            required.append(name)
        elif param.default is not None:
            properties[name]["default"] = param.default
    return properties, required


def _schema(annotation):
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin is typing.Annotated:
        schema = _schema(args[0])
        for meta in args[1:]:
            if isinstance(meta, Field) and meta.description:
                schema["description"] = meta.description
        return schema
    if origin is typing.Union:
        rest = [a for a in args if a is not type(None)]
        return _schema(rest[0]) if len(rest) == 1 else {}
    if origin is typing.Literal:
        schema = {"enum": list(args)}
        if args and type(args[0]) in _JSON_TYPES:
            schema["type"] = _JSON_TYPES[type(args[0])]
        return schema
    if origin in (list, tuple, set):
        schema = {"type": "array"}
        if args:
            schema["items"] = _schema(args[0])
        return schema
    if origin is dict:
        return {"type": "object"}
    if annotation in _JSON_TYPES:
        return {"type": _JSON_TYPES[annotation]}
    return {}


def _text(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _tool_error(text):
    return {"content": [{"type": "text", "text": text}], "isError": True}


def _error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
