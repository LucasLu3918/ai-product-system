"""Product-owned consumer of the generated transport boundary."""
from __future__ import annotations

from client.generated.client import WidgetClient


def create_and_fetch(base_url: str, token: str, name: str) -> dict:
    client = WidgetClient(base_url, token)
    created = client.create_widget(name)
    return client.get_widget(created["id"])
