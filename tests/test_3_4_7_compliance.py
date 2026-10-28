"""Offline compatibility checks for backend tags 3.4.5 through 3.4.7.

The HTTP contract is unchanged from 3.4.4 (contract 3.4.15). The new
postStart plugin travels in the existing, untyped pluginConfig field.
"""

import json
from uuid import UUID

import httpx
import pytest

from remnawave import RemnawaveSDK
from remnawave.models import UpdateNodePluginBodyDto


@pytest.mark.parametrize(
    "post_start",
    [
        {"enabled": True, "webhook": {"enabled": True, "url": "https://hooks.example/core"}},
        {"enabled": False, "webhook": {"enabled": False, "url": "http://hooks.example/core"}},
        {"enabled": True},
        {},
    ],
    ids=["webhook-enabled", "webhook-disabled", "no-webhook", "server-defaults"],
)
async def test_post_start_config_survives_update_and_get(post_start):
    plugin_uuid = UUID("11111111-1111-4111-8111-111111111111")
    config = {"preStart": {"enabled": False}, "postStart": post_start}
    payload = {
        "uuid": str(plugin_uuid),
        "viewPosition": 0,
        "name": "core_events",
        "tags": [],
        "pluginConfig": config,
    }

    def respond(request):
        if request.method == "PATCH":
            assert request.url.path == "/api/node-plugins"
            assert json.loads(request.content) == {
                "uuid": str(plugin_uuid),
                "pluginConfig": config,
            }
        else:
            assert request.method == "GET"
            assert request.url.path == f"/api/node-plugins/{plugin_uuid}"
            assert not request.content
        return httpx.Response(200, json={"response": payload})

    async with httpx.AsyncClient(
        base_url="https://panel.example/api", transport=httpx.MockTransport(respond)
    ) as client:
        sdk = RemnawaveSDK(client=client)
        updated = await sdk.node_plugins.update_node_plugin(
            UpdateNodePluginBodyDto(uuid=plugin_uuid, plugin_config=config)
        )
        assert updated.plugin_config == config
        fetched = await sdk.node_plugins.get_node_plugin_by_uuid(uuid=str(plugin_uuid))
        assert fetched.plugin_config == config
