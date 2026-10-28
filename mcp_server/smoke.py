"""Talk to an MCP server without an agent: what does it expose, and does it work?

    python mcp_server/smoke.py mcp_server/lumio_ops.py
    python mcp_server/smoke.py mcp_server/lumio_ops.py --call get_device device_id=TV-003
    python mcp_server/smoke.py mcp_server/lumio_ops.py --read lumio://releases
    python mcp_server/smoke.py mcp_server/lumio_ops.py --prompt diagnose_device device_id=TV-003
    python mcp_server/smoke.py mcp_server/lumio_ops.py --env LUMIO_MCP_READONLY=1

Arguments are ``name=value`` pairs; a value that parses as JSON (numbers,
true/false, lists) is sent as JSON, anything else as a string. Standard
library only, so it works with the SDK and with ``mcp_lite`` alike.
"""

import argparse
import json
import os
import queue
import subprocess
import sys
import threading

PROTOCOL_VERSION = "2025-06-18"


class Client:
    """A minimal MCP client over stdio: start a server, send requests, read responses."""

    def __init__(self, command, env=None, stderr=None, timeout=20):
        full_env = dict(os.environ)
        full_env.update(env or {})
        full_env.setdefault("PYTHONIOENCODING", "utf-8")
        self.timeout = timeout
        self._next_id = 0
        self._proc = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, env=full_env
        )
        self._lines = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for raw in self._proc.stdout:
            self._lines.put(raw)
        self._lines.put(None)

    def notify(self, method, params=None):
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def request(self, method, params=None):
        """Send a request and return its ``result``. Raises RuntimeError on a JSON-RPC error."""
        self._next_id += 1
        request_id = self._next_id
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}})
        while True:
            try:
                raw = self._lines.get(timeout=self.timeout)
            except queue.Empty:
                raise RuntimeError("Serwer nie odpowiedział na %s w ciągu %d s." % (method, self.timeout))
            if raw is None:
                raise RuntimeError("Serwer zakończył działanie. Sprawdź komunikat błędu powyżej.")
            try:
                message = json.loads(raw.decode("utf-8"))
            except ValueError:
                raise RuntimeError("Serwer wypisał na stdout coś, co nie jest JSON-em: %r" % raw[:200])
            if message.get("id") != request_id:
                continue  # notifications and logs from the server
            if "error" in message:
                raise RuntimeError("%s: %s" % (method, message["error"].get("message")))
            return message["result"]

    def initialize(self):
        result = self.request(
            "initialize",
            {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "lumio-smoke", "version": "1.0"}},
        )
        self.notify("notifications/initialized")
        return result

    def _send(self, message):
        self._proc.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
        self._proc.stdin.flush()

    def close(self):
        if self._proc.stdin:
            self._proc.stdin.close()
        try:
            self._proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait()
        self._proc.stdout.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def server_command(path):
    return [sys.executable, path] if path.endswith(".py") else [path]


def parse_pairs(pairs):
    values = {}
    for pair in pairs:
        name, sep, value = pair.partition("=")
        if not sep:
            raise SystemExit("Argument %r musi mieć postać nazwa=wartość." % pair)
        try:
            values[name] = json.loads(value)
        except ValueError:
            values[name] = value
    return values


def estimate_tokens(text):
    return (len(text) + 3) // 4


def show_text_content(result):
    for item in result.get("content") or result.get("contents") or []:
        if "text" in item:
            print(item["text"])
        else:
            print(json.dumps(item, ensure_ascii=False, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sprawdź serwer MCP bez agenta.")
    parser.add_argument("server", help="ścieżka do pliku .py z serwerem")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--call", metavar="NARZĘDZIE", help="wywołaj narzędzie z argumentami nazwa=wartość")
    group.add_argument("--read", metavar="URI", help="odczytaj zasób")
    group.add_argument("--prompt", metavar="PROMPT", help="pobierz prompt z argumentami nazwa=wartość")
    parser.add_argument("args", nargs="*", help="argumenty nazwa=wartość")
    parser.add_argument("--env", action="append", default=[], metavar="NAZWA=WARTOŚĆ", help="zmienna środowiskowa dla serwera")
    opts = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # pipes on Windows default to the ANSI code page

    env = {str(k): str(v) for k, v in parse_pairs(opts.env).items()}
    try:
        with Client(server_command(opts.server), env=env) as client:
            info = client.initialize()
            if opts.call:
                result = client.request("tools/call", {"name": opts.call, "arguments": parse_pairs(opts.args)})
                print("BŁĄD NARZĘDZIA:" if result.get("isError") else "Wynik:")
                show_text_content(result)
            elif opts.read:
                show_text_content(client.request("resources/read", {"uri": opts.read}))
            elif opts.prompt:
                result = client.request("prompts/get", {"name": opts.prompt, "arguments": parse_pairs(opts.args)})
                for message in result["messages"]:
                    print("[%s] %s" % (message["role"], message["content"].get("text", message["content"])))
            else:
                describe(client, info)
    except RuntimeError as exc:
        print("Błąd: %s" % exc, file=sys.stderr)
        return 1
    return 0


def describe(client, info):
    capabilities = info.get("capabilities", {})
    server = info.get("serverInfo", {})
    print("Serwer: %s (%s), protokół %s" % (server.get("name"), server.get("version"), info.get("protocolVersion")))
    if info.get("instructions"):
        print("Instrukcje serwera: %s" % info["instructions"])

    tools = client.request("tools/list")["tools"] if "tools" in capabilities else []
    print("\nNarzędzia (tools): %d" % len(tools))
    for tool in tools:
        schema = tool.get("inputSchema", {})
        required = set(schema.get("required", []))
        params = ", ".join(
            name + ("" if name in required else "?") for name in schema.get("properties", {})
        )
        print("\n  %s(%s)" % (tool["name"], params))
        for line in (tool.get("description") or "(brak opisu)").splitlines():
            print("    " + line)
        for name, prop in schema.get("properties", {}).items():
            if prop.get("description"):
                print("    - %s: %s" % (name, prop["description"]))

    if "resources" in capabilities:
        resources = client.request("resources/list")["resources"]
        print("\nZasoby (resources): %d" % len(resources))
        for res in resources:
            print("  %s  %s" % (res["uri"], res.get("description") or res.get("name", "")))

    if "prompts" in capabilities:
        prompts = client.request("prompts/list")["prompts"]
        print("\nPrompty (prompts): %d" % len(prompts))
        for prompt in prompts:
            args = ", ".join(a["name"] for a in prompt.get("arguments") or [])
            print("  %s(%s)  %s" % (prompt["name"], args, prompt.get("description") or ""))

    listing = json.dumps(tools, ensure_ascii=False)
    print("\nKoszt kontekstu: definicje narzędzi to %d znaków, około %d tokenów (szacunek: znaki / 4)." % (len(listing), estimate_tokens(listing)))
    print("Klient, który ładuje wszystkie narzędzia z góry (np. Cline), wysyła to modelowi przy każdym zapytaniu.")


if __name__ == "__main__":
    sys.exit(main())
