"""Exercise the generated client against a real loopback Widgets API."""
from __future__ import annotations

import os
import threading
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path

from client.generated.client import WidgetApiError, WidgetClient
from consumer import create_and_fetch
from service import PILOT_TOKEN, new_server


def main() -> int:
    server = new_server()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    failures: list[str] = []

    def check(name: str, callback: Callable[[], None]) -> None:
        try:
            callback()
        except Exception as exc:  # noqa: BLE001 - write JUnit for unexpected test failures
            failures.append(f"{name}: {type(exc).__name__}")

    try:
        client = WidgetClient(base_url, PILOT_TOKEN)

        def create_widget() -> None:
            widget = client.create_widget("中文 Widget")
            assert widget == {"id": "1", "name": "中文 Widget"}

        def get_widget() -> None:
            assert create_and_fetch(base_url, PILOT_TOKEN, "second") == {"id": "2", "name": "second"}

        def error_paths() -> None:
            for action, status, code in ((lambda: client.create_widget(""), 400, "invalid_widget"),
                                         (lambda: client.get_widget("missing"), 404, "not_found"),
                                         (lambda: WidgetClient(base_url, "wrong").get_widget("1"), 401, "unauthorized")):
                try:
                    action()
                except WidgetApiError as exc:
                    assert (exc.status, exc.code) == (status, code)
                else:
                    raise AssertionError(f"expected HTTP {status}")

        check("createWidget", create_widget)
        check("getWidget", get_widget)
        check("errorPaths", error_paths)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)

    junit = os.environ.get("AIPS_JUNIT_XML")
    if junit:
        suite = ET.Element("testsuite", tests="3", failures=str(len(failures)))
        for name in ("createWidget", "getWidget", "errorPaths"):
            case = ET.SubElement(suite, "testcase", classname="pilot", name=name)
            for failure in failures:
                if failure.startswith(name + ":"):
                    ET.SubElement(case, "failure", message=failure)
        Path(junit).write_bytes(ET.tostring(suite, encoding="utf-8", xml_declaration=True))
    print("pilot PASS" if not failures else "pilot FAIL: " + ", ".join(failures))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
