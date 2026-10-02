"""Small local Widgets API used only by the Phase 5 reference pilot."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar
from urllib.parse import unquote, urlsplit

PILOT_TOKEN = "pilot-token"


class WidgetsHandler(BaseHTTPRequestHandler):
    widgets: ClassVar[dict[str, str]] = {}

    def _send(self, status: int, value: dict) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        if self.headers.get("Authorization") == f"Bearer {PILOT_TOKEN}":
            return True
        self._send(401, {"code": "unauthorized"})
        return False

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/widgets":
            self._send(404, {"code": "not_found"})
            return
        if not self._authorized():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 4096 or length <= 0:
                raise ValueError("invalid length")
            value = json.loads(self.rfile.read(length))
            name = value["name"]
            if not isinstance(name, str) or not name.strip() or set(value) != {"name"}:
                raise ValueError("invalid widget")
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            self._send(400, {"code": "invalid_widget"})
            return
        widget_id = str(len(self.widgets) + 1)
        self.widgets[widget_id] = name
        self._send(201, {"id": widget_id, "name": name})

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if not path.startswith("/widgets/"):
            self._send(404, {"code": "not_found"})
            return
        if not self._authorized():
            return
        widget_id = unquote(path.removeprefix("/widgets/"))
        if widget_id not in self.widgets:
            self._send(404, {"code": "not_found"})
            return
        self._send(200, {"id": widget_id, "name": self.widgets[widget_id]})

    def log_message(self, _format: str, *args: object) -> None:
        return


def new_server() -> ThreadingHTTPServer:
    handler = type("PilotWidgetsHandler", (WidgetsHandler,), {"widgets": {}})
    return ThreadingHTTPServer(("127.0.0.1", 0), handler)
