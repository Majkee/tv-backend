"""MCP servers in ``mcp_server/``: the stdlib shim and the ready-made Lumio Ops server.

The end-to-end tests start the servers the way an agent does, as a subprocess
talking JSON-RPC over stdio. They pass with the official SDK installed and
without it (then the servers use ``mcp_lite``).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from typing import Annotated, Literal, Optional
from unittest import mock

from backend.storage import REPO_ROOT

MCP_DIR = REPO_ROOT / "mcp_server"
sys.path.insert(0, str(MCP_DIR))

import mcp_lite  # noqa: E402
from smoke import Client  # noqa: E402


def _server():
    server = mcp_lite.MCPServer("test")

    @server.tool(annotations=mcp_lite.ToolAnnotations(readOnlyHint=True))
    def lookup(
        device_id: Annotated[str, mcp_lite.Field(description="Identyfikator, np. TV-001.")],
        limit: int = 5,
        region: Optional[str] = None,
        mode: Literal["short", "long"] = "short",
    ):
        """Szuka urządzenia."""
        if device_id == "boom":
            raise RuntimeError("internal detail")
        if device_id == "missing":
            raise mcp_lite.ToolError("Nie ma urządzenia missing.")
        return {"device_id": device_id, "limit": limit}

    @server.resource("lumio://hello", mime_type="text/plain")
    def hello():
        """Powitanie."""
        return "cześć"

    @server.prompt()
    def ask(device_id: str):
        """Pytanie o urządzenie."""
        return "Sprawdź %s." % device_id

    return server


def _request(server, method, params=None, request_id=1):
    return server.handle_message({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}})


class McpLiteTest(unittest.TestCase):
    def setUp(self):
        self.server = _server()

    def test_initialize_echoes_known_protocol_version(self):
        result = _request(self.server, "initialize", {"protocolVersion": "2025-06-18"})["result"]
        self.assertEqual(result["protocolVersion"], "2025-06-18")
        self.assertEqual(result["serverInfo"]["name"], "test")
        self.assertIn("tools", result["capabilities"])

    def test_initialize_offers_newest_version_for_unknown_one(self):
        result = _request(self.server, "initialize", {"protocolVersion": "1999-01-01"})["result"]
        self.assertEqual(result["protocolVersion"], mcp_lite.PROTOCOL_VERSIONS[0])

    def test_notification_gets_no_response(self):
        self.assertIsNone(self.server.handle_message({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_tool_schema_comes_from_signature_and_docstring(self):
        (tool,) = _request(self.server, "tools/list")["result"]["tools"]
        self.assertEqual(tool["name"], "lookup")
        self.assertEqual(tool["description"], "Szuka urządzenia.")
        self.assertEqual(tool["annotations"], {"readOnlyHint": True})
        schema = tool["inputSchema"]
        self.assertEqual(schema["required"], ["device_id"])
        self.assertEqual(schema["properties"]["device_id"], {"type": "string", "description": "Identyfikator, np. TV-001."})
        self.assertEqual(schema["properties"]["limit"], {"type": "integer", "default": 5})
        self.assertEqual(schema["properties"]["region"], {"type": "string"})
        self.assertEqual(schema["properties"]["mode"], {"enum": ["short", "long"], "type": "string", "default": "short"})

    def test_tool_call_returns_json_text(self):
        result = _request(self.server, "tools/call", {"name": "lookup", "arguments": {"device_id": "TV-001"}})["result"]
        self.assertFalse(result["isError"])
        self.assertEqual(json.loads(result["content"][0]["text"]), {"device_id": "TV-001", "limit": 5})

    def test_tool_error_message_reaches_the_agent(self):
        result = _request(self.server, "tools/call", {"name": "lookup", "arguments": {"device_id": "missing"}})["result"]
        self.assertTrue(result["isError"])
        self.assertIn("Nie ma urządzenia missing.", result["content"][0]["text"])

    def test_unexpected_exception_details_stay_in_the_server(self):
        with mock.patch("sys.stderr"):
            result = _request(self.server, "tools/call", {"name": "lookup", "arguments": {"device_id": "boom"}})["result"]
        self.assertTrue(result["isError"])
        self.assertNotIn("internal detail", result["content"][0]["text"])

    def test_missing_and_unknown_arguments_are_tool_errors(self):
        result = _request(self.server, "tools/call", {"name": "lookup", "arguments": {"limit": 1, "colour": "red"}})["result"]
        self.assertTrue(result["isError"])
        self.assertIn("device_id", result["content"][0]["text"])
        self.assertIn("colour", result["content"][0]["text"])

    def test_unknown_tool_and_method_are_protocol_errors(self):
        self.assertEqual(_request(self.server, "tools/call", {"name": "nope"})["error"]["code"], mcp_lite.INVALID_PARAMS)
        self.assertEqual(_request(self.server, "nope/nope")["error"]["code"], mcp_lite.METHOD_NOT_FOUND)

    def test_resources(self):
        (res,) = _request(self.server, "resources/list")["result"]["resources"]
        self.assertEqual((res["uri"], res["description"]), ("lumio://hello", "Powitanie."))
        (content,) = _request(self.server, "resources/read", {"uri": "lumio://hello"})["result"]["contents"]
        self.assertEqual(content["text"], "cześć")

    def test_prompts(self):
        (prompt,) = _request(self.server, "prompts/list")["result"]["prompts"]
        self.assertEqual(prompt["arguments"], [{"name": "device_id", "required": True}])
        result = _request(self.server, "prompts/get", {"name": "ask", "arguments": {"device_id": "TV-003"}})["result"]
        self.assertEqual(result["messages"][0]["content"]["text"], "Sprawdź TV-003.")


class LumioOpsServerTest(unittest.TestCase):
    """Starts mcp_server/lumio_ops.py as a subprocess, with its own data directory."""

    def start(self, **env):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        env.setdefault("LUMIO_DATA_DIR", tmp.name)
        client = Client([sys.executable, str(MCP_DIR / "lumio_ops.py")], env=env, stderr=subprocess.DEVNULL)
        self.addCleanup(client.close)
        client.initialize()
        return client

    def call(self, client, name, **arguments):
        result = client.request("tools/call", {"name": name, "arguments": arguments})
        text = "".join(item.get("text", "") for item in result["content"])
        return result.get("isError", False), text

    def tool_names(self, client):
        return {tool["name"] for tool in client.request("tools/list")["tools"]}

    def test_lists_tools_resources_and_prompts(self):
        client = self.start()
        self.assertEqual(
            self.tool_names(client),
            {"list_devices", "get_device", "pending_update", "set_device_firmware", "reset_devices"},
        )
        uris = {res["uri"] for res in client.request("resources/list")["resources"]}
        self.assertEqual(uris, {"lumio://releases", "lumio://models"})
        prompts = {prompt["name"] for prompt in client.request("prompts/list")["prompts"]}
        self.assertEqual(prompts, {"diagnose_device"})

    def test_readonly_mode_does_not_register_write_tools(self):
        client = self.start(LUMIO_MCP_READONLY="1")
        self.assertEqual(self.tool_names(client), {"list_devices", "get_device", "pending_update"})

    def test_get_device(self):
        client = self.start()
        is_error, text = self.call(client, "get_device", device_id="TV-003")
        self.assertFalse(is_error)
        payload = json.loads(text)
        self.assertEqual(payload["device"]["id"], "TV-003")
        self.assertEqual(payload["model"]["model"], "LM-65X25")

    def test_unknown_device_is_a_readable_error(self):
        client = self.start()
        is_error, text = self.call(client, "get_device", device_id="TV-999")
        self.assertTrue(is_error)
        self.assertIn("TV-999", text)
        self.assertIn("list_devices", text)

    def test_list_devices_filters_by_region(self):
        client = self.start()
        _, text = self.call(client, "list_devices", region="eu")
        regions = {d["region"] for d in json.loads(text)["devices"]}
        self.assertEqual(regions, {"EU"})

    def test_pending_update_does_not_touch_the_registry(self):
        client = self.start()
        _, before = self.call(client, "get_device", device_id="TV-002")
        is_error, _ = self.call(client, "pending_update", device_id="TV-002")
        _, after = self.call(client, "get_device", device_id="TV-002")
        self.assertFalse(is_error)
        self.assertEqual(json.loads(before), json.loads(after))

    def test_set_device_firmware_validates_and_saves(self):
        client = self.start()
        is_error, _ = self.call(client, "set_device_firmware", device_id="TV-001", firmware="abc")
        self.assertTrue(is_error)
        is_error, _ = self.call(client, "set_device_firmware", device_id="TV-001", firmware="2.9.0")
        self.assertFalse(is_error)
        _, text = self.call(client, "get_device", device_id="TV-001")
        self.assertEqual(json.loads(text)["device"]["firmware"], "2.9.0")

    def test_releases_resource(self):
        client = self.start()
        (content,) = client.request("resources/read", {"uri": "lumio://releases"})["contents"]
        versions = [release["version"] for release in json.loads(content["text"])]
        self.assertIn("2.9.0", versions)

