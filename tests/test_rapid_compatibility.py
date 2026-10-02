"""Exercise request serialization with the supported dependency versions."""
import base64
import json
from typing import Annotated

import httpx
import pytest
from pydantic import Field, ValidationError
from rapid_api_client import Path, Query

from remnawave import RemnawaveSDK
from remnawave.models import UpdateHostBodyDto, UpdateManyHostsBodyDto
from remnawave.rapid import AttributeBody, BaseController, get, post
from remnawave.utils.happ_crypt import create_happ_crypto_link
from tests.test_3_3_compliance import HOST_PAYLOAD


async def test_patch_keeps_explicit_null_and_omits_unset_fields():
    def respond(request):
        assert request.method == "PATCH"
        assert json.loads(request.content) == {
            "uuid": HOST_PAYLOAD["uuid"], "serverDescription": None
        }
        return httpx.Response(200, json={"response": HOST_PAYLOAD})

    async with httpx.AsyncClient(
        base_url="https://panel.example/api", transport=httpx.MockTransport(respond)
    ) as client:
        await RemnawaveSDK(client=client).hosts.update_host(
            UpdateHostBodyDto(uuid=HOST_PAYLOAD["uuid"], server_description=None)
        )


async def test_bulk_host_update_preserves_mapper_operations():
    mapper = {"xrayJson": [
        {"op": "copy", "from": "$host.address", "to": "server"},
        {"op": "set", "to": "tls.enabled", "value": False},
        {"op": "unset", "to": "mux"},
    ]}

    def respond(request):
        assert request.method == "PATCH"
        assert request.url.path == "/api/hosts/bulk/update"
        assert json.loads(request.content) == {
            "uuids": [HOST_PAYLOAD["uuid"]], "mapper": mapper,
        }
        return httpx.Response(204)

    async with httpx.AsyncClient(
        base_url="https://panel.invalid/api", transport=httpx.MockTransport(respond)
    ) as client:
        assert await RemnawaveSDK(client=client).hosts_bulk_actions.update_hosts(
            UpdateManyHostsBodyDto(uuids=[HOST_PAYLOAD["uuid"]], mapper=mapper)
        ) is None


async def test_bulk_host_update_omits_unset_mapper():
    def respond(request):
        assert json.loads(request.content) == {"uuids": [HOST_PAYLOAD["uuid"]]}
        return httpx.Response(204)

    async with httpx.AsyncClient(
        base_url="https://panel.invalid/api", transport=httpx.MockTransport(respond)
    ) as client:
        await RemnawaveSDK(client=client).hosts_bulk_actions.update_hosts(
            UpdateManyHostsBodyDto(uuids=[HOST_PAYLOAD["uuid"]])
        )


async def test_parameter_defaults_validation_and_attribute_body():
    class Controller(BaseController):
        @get("/users/{userId}")
        async def fetch(
            self,
            user_id: Annotated[int, Path(alias="userId")],
            size: Annotated[int, Query(), Field(default=25, ge=1, le=500)],
            enabled: Annotated[bool, Query()] = False,
        ): ...

        @post("/actions", response_class=None)
        async def action(
            self,
            user_id: Annotated[int, AttributeBody(alias="userId")],
            enabled: Annotated[bool, AttributeBody()] = False,
        ): ...

    def respond(request):
        if request.method == "GET":
            assert request.url.path == "/api/users/7"
            assert dict(request.url.params) == {"size": "25", "enabled": "false"}
            return httpx.Response(200, json={})
        assert json.loads(request.content) == {"userId": 7, "enabled": False}
        return httpx.Response(204)

    async with httpx.AsyncClient(
        base_url="https://panel.example/api", transport=httpx.MockTransport(respond)
    ) as client:
        controller = Controller(client)
        assert (await controller.fetch(7)).status_code == 200
        assert await controller.action(7) is None
        with pytest.raises(ValidationError):
            await controller.fetch(7, size=501)


@pytest.mark.parametrize("method", ["v3", "v4"])
def test_happ_encryption_with_current_cryptography(method):
    link = create_happ_crypto_link("https://example.com/subscription", method=method)
    prefix = f"happ://crypt{method[1:]}/"
    assert link.startswith(prefix)
    assert len(base64.b64decode(link[len(prefix):], validate=True)) == 512
