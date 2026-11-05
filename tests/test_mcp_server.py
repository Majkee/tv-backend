"""MCP in ``mcp_server/``: the stdlib shim and the Lumio DB server.

The end-to-end tests start the servers the way an agent does, as a subprocess
talking JSON-RPC over stdio. They pass with the official SDK installed and
without it (then the servers use ``mcp_lite``).
"""

import json
import subprocess
import sys
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


class LumioDbServerTest(unittest.TestCase):
    """Starts mcp_server/lumio_db.py as a subprocess, the way an agent does."""

    def setUp(self):
        self.client = Client([sys.executable, str(MCP_DIR / "lumio_db.py")], stderr=subprocess.DEVNULL)
        self.addCleanup(self.client.close)
        self.client.initialize()

    def call(self, name, **arguments):
        result = self.client.request("tools/call", {"name": name, "arguments": arguments})
        text = "".join(item.get("text", "") for item in result["content"])
        return result.get("isError", False), text

    def query(self, sql):
        is_error, text = self.call("run_query", sql=sql)
        self.assertFalse(is_error, text)
        return json.loads(text)

    def test_exposes_two_read_only_tools(self):
        tools = self.client.request("tools/list")["tools"]
        self.assertEqual({tool["name"] for tool in tools}, {"describe_database", "run_query"})
        for tool in tools:
            self.assertEqual(tool["annotations"]["readOnlyHint"], True)

    def test_describe_database_lists_tables_with_column_comments(self):
        is_error, text = self.call("describe_database")
        self.assertFalse(is_error)
        tables = {t["table"]: t for t in json.loads(text)["tables"]}
        self.assertEqual(set(tables), {"models", "devices", "firmware_releases", "support_tickets"})
        self.assertEqual(tables["devices"]["rows"], 60)
        self.assertIn("EU, NA albo APAC", tables["devices"]["definition"])

    def test_run_query_returns_columns_and_rows(self):
        result = self.query("SELECT region, COUNT(*) AS devices FROM devices GROUP BY region ORDER BY region")
        self.assertEqual(result["columns"], ["region", "devices"])
        self.assertEqual(sum(row[1] for row in result["rows"]), 60)
        self.assertFalse(result["truncated"])

    def test_devices_match_the_tv_simulator(self):
        result = self.query("SELECT model, region FROM devices WHERE id = 'TV-003'")
        self.assertEqual(result["rows"], [["LM-65X25", "EU"]])

    def test_writes_are_refused_and_change_nothing(self):
        for sql in (
            "DELETE FROM support_tickets",
            "WITH x AS (SELECT 1) DELETE FROM support_tickets",
            "SELECT 1; DELETE FROM support_tickets",
        ):
            with self.subTest(sql=sql):
                is_error, _ = self.call("run_query", sql=sql)
                self.assertTrue(is_error)
        self.assertEqual(self.query("SELECT COUNT(*) FROM support_tickets")["rows"], [[48]])

    def test_sql_error_points_to_describe_database(self):
        is_error, text = self.call("run_query", sql="SELECT price FROM models")
        self.assertTrue(is_error)
        self.assertIn("price", text)
        self.assertIn("describe_database", text)

    def test_large_results_are_truncated(self):
        result = self.query(
            "WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n WHERE i < 500) SELECT i FROM n"
        )
        self.assertEqual(len(result["rows"]), 200)
        self.assertTrue(result["truncated"])
