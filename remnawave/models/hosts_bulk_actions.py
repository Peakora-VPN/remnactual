"""Bulk host operations.

Все четыре эндпоинта `/hosts/bulk/*` в 3.0 отвечают `204 No Content` с пустым телом,
поэтому моделей ответа у них больше нет — контроллеры объявлены с
``response_class=None`` и возвращают ``None``.
"""
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from remnawave.enums import ALPN, MihomoIpVersion, SecurityLayer, SubscriptionType
from remnawave.models.host_mapper import HostMapperDto
from remnawave.models.hosts import (
    CreateHostInboundData,
    HostInternalSquadsDto,
    HostRemark,
    HostTag,
    _reject_both_squad_fields,
)


class UpdateManyHostsBodyDto(BaseModel):
    """Request to update many hosts at once (PATCH /hosts/bulk/update → 204)."""
    uuids: List[UUID] = Field(min_length=1)
    inbound: Optional[CreateHostInboundData] = None
    remark: Optional[HostRemark] = None
    address: Optional[str] = None
    port: Optional[int] = None
    path: Optional[str] = None
    sni: Optional[str] = None
    host: Optional[str] = None
    alpn: Optional[ALPN] = None
    fingerprint: Optional[str] = None
    is_disabled: Optional[bool] = Field(None, serialization_alias="isDisabled")
    security_layer: Optional[SecurityLayer] = Field(None, serialization_alias="securityLayer")
    server_description: Optional[str] = Field(None, serialization_alias="serverDescription", max_length=30)
    tags: Optional[List[HostTag]] = Field(None, serialization_alias="tags", max_length=10)
    is_hidden: Optional[bool] = Field(None, serialization_alias="isHidden")
    override_sni_from_address: Optional[bool] = Field(None, serialization_alias="overrideSniFromAddress")
    keep_blank_sni: Optional[bool] = Field(None, serialization_alias="keepSniBlank")
    vless_route_id: Optional[int] = Field(None, serialization_alias="vlessRouteId", ge=0, le=65535)
    pinned_peer_cert_sha256: Optional[str] = Field(None, serialization_alias="pinnedPeerCertSha256")
    verify_peer_cert_by_name: Optional[str] = Field(None, serialization_alias="verifyPeerCertByName")
    shuffle_host: Optional[bool] = Field(None, serialization_alias="shuffleHost")
    mihomo_x25519: Optional[bool] = Field(None, serialization_alias="mihomoX25519")
    mihomo_ip_version: Optional[MihomoIpVersion] = Field(None, serialization_alias="mihomoIpVersion")
    xhttp_extra_params: Optional[Any] = Field(None, serialization_alias="xhttpExtraParams")
    mux_params: Optional[Any] = Field(None, serialization_alias="muxParams")
    sockopt_params: Optional[Any] = Field(None, serialization_alias="sockoptParams")
    final_mask: Optional[Any] = Field(None, serialization_alias="finalMask")
    nodes: Optional[List[UUID]] = None
    xray_json_template_uuid: Optional[UUID] = Field(None, serialization_alias="xrayJsonTemplateUuid")
    #: Панель < 3.4. Снято в 3.4.0 в пользу :attr:`internal_squads`.
    #:
    #: Тело массового обновления контракт выводит из тела одиночного
    #: (``UpdateHostCommand.RequestBodySchema.omit({uuid}).partial()``), поэтому
    #: замена поля пришла сюда транзитивно — сам файл команды в 3.4.0 не менялся.
    excluded_internal_squads: Optional[List[UUID]] = Field(
        None,
        serialization_alias="excludedInternalSquads",
        deprecated="Panel < 3.4 only. Panel 3.4 replaced it with internal_squads "
        "and IGNORES this key silently.",
    )
    #: Панель 3.4.0+.
    internal_squads: Optional[HostInternalSquadsDto] = Field(
        None, serialization_alias="internalSquads"
    )
    mapper: Optional[HostMapperDto] = None
    exclude_from_subscription_types: Optional[List[SubscriptionType]] = Field(
        None,
        serialization_alias="excludeFromSubscriptionTypes",
        description="Subscription types from which the hosts will be excluded.",
    )

    @model_validator(mode="after")
    def _one_squad_form(self) -> "UpdateManyHostsBodyDto":
        _reject_both_squad_fields(self)
        return self


# ─────────────────────────────────────────────────────────────────────────────
# Legacy alias (имя до 3.0)
# ─────────────────────────────────────────────────────────────────────────────
UpdateManyHostsRequestDto = UpdateManyHostsBodyDto

__all__ = [
    "UpdateManyHostsBodyDto",
    "UpdateManyHostsRequestDto",
]
