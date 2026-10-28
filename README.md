# Remnawave Python SDK — fork

[![PyPI](https://img.shields.io/pypi/v/remnactual?logo=pypi&logoColor=white&label=pypi)](https://pypi.org/project/remnactual/)
[![Python](https://img.shields.io/pypi/pyversions/remnactual?logo=python&logoColor=white)](https://pypi.org/project/remnactual/)
[![License](https://img.shields.io/github/license/IceOne-i/remnactual?color=44cc11)](https://github.com/IceOne-i/remnactual/blob/production/LICENSE)
[![Publish](https://img.shields.io/github/actions/workflow/status/IceOne-i/remnactual/upload.yml?logo=githubactions&logoColor=white&label=publish)](https://github.com/IceOne-i/remnactual/actions/workflows/upload.yml)
[![Fork of remnawave/python-sdk](https://img.shields.io/badge/fork%20of-remnawave%2Fpython--sdk-24292f?logo=github)](https://github.com/remnawave/python-sdk)

[![Remnawave panel](https://img.shields.io/badge/Remnawave%20panel-%E2%89%A5%203.0.0-1f6feb)](https://remna.st)
[![Backend contract](https://img.shields.io/badge/backend--contract-3.4.7-1f6feb)](https://github.com/remnawave/backend/tree/3.4.7/libs/contract)
[![Endpoints](https://img.shields.io/badge/endpoints-222-1f6feb)](https://github.com/IceOne-i/remnactual#controllers)
[![Models](https://img.shields.io/badge/models-695-1f6feb)](https://github.com/IceOne-i/remnactual#controllers)
[![API docs](https://img.shields.io/badge/API%20docs-docs.rw-1f6feb)](https://docs.rw/api)

[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-e92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![httpx](https://img.shields.io/badge/httpx-async-0e7c86)](https://www.python-httpx.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

Asynchronous Python client for the **[Remnawave](https://remna.st)** panel API, built on
`httpx` + `pydantic` v2, with `orjson` for fast serialization.

> [!IMPORTANT]
> **This is a fork of [`remnawave/python-sdk`](https://github.com/remnawave/python-sdk).**
> It is published to PyPI as **`remnactual`** (the upstream `remnawave` project belongs to the
> Remnawave community). The import name is unchanged — `import remnawave`.
> The fork exists to track the Remnawave 3.x API closely and to fix the divergences that
> the migration from 2.7.x left behind — see [What this fork changes](#what-this-fork-changes).
> Attribution for the original work is at the [bottom of this file](#credits).

---

## Compatibility

| SDK version | Remnawave panel | Backend contract |
| ----------- | --------------- | ---------------- |
| Next release | >= 3.0.0       | `remnawave/backend` at tag 3.4.7 |
| 3.4.3       | >= 3.0.0        | `remnawave/backend` at tag 3.4.3 |
| 3.3.2       | >= 3.0.0        | `remnawave/backend` at tag 3.3.2 |
| 3.2.3       | >= 3.0.0        | `@remnawave/backend-contract` 3.2.3 |
| 3.2.0       | >= 3.0.0        | `@remnawave/backend-contract` 3.2.0 |
| 3.0.0       | >= 3.0.0        | `@remnawave/backend-contract` 3.0.0 |
| 2.8.1       | >= 2.8.0, < 3.0 | `@remnawave/backend-contract` 2.8.35 |

Every endpoint, request body and response model in this fork is verified against
`libs/contract` of [`remnawave/backend`](https://github.com/remnawave/backend) through tag `3.4.7`.

> The npm package `@remnawave/backend-contract` has its **own** version series and does not
> track the panel: tag `3.3.2` of the backend ships contract `3.4.2`, tag `3.4.3` ships
> `3.4.13`, and tags `3.4.4`–`3.4.7` ship `3.4.15`. Always compare tag to tag — comparing npm versions
> silently mixes up releases.

Panel **3.4.4** adds `sdk.hosts.clone_host(CloneHostBodyDto(clone_from_uuid=host_uuid))`.
It returns `HostResponseDto` (HTTP 201) and requires the `hosts:clone` scope (or a broader
hosts write scope). The SDK exposes `Scope.HOSTS_CLONE` and `ErrorCode.CLONE_HOST_ERROR`
(`A258`). Existing methods retain their panel requirements.

Dependencies now use `rapid-api-client` 0.10.0, HTTPX 0.28.1, Pydantic 2.13.5,
orjson 3.12.0 and cryptography 50.0.1 as their minimum versions. Custom controller
annotations should put validation and descriptions in a separate Pydantic `Field`,
e.g. `Annotated[int, Query(), Field(default=25, ge=1)]`. PATCH serialization still
preserves explicit `None` as JSON `null` and omits fields that were not set.

> 3.1, 3.2, 3.2.3 and 3.3 are purely additive, so the panel floor stays at 3.0.0: the fields
> they added are optional here and simply stay `None` (or empty) against an older panel.
> The endpoints they introduced of course need a panel that has them:
> `GET /system/configuration` a panel on 3.2.0, `POST /snippets/actions/sync` on 3.2.3, and
> node integrations, shared lists, plugin sync and node geocheck a panel on 3.3.0.

> **3.4 is not additive** — it replaced a host field and moved two shared-list endpoints.
> The floor still stays at 3.0.0 because the replaced field is kept alongside the new one
> (see [Migration to 3.4](#migration-to-34)), but `get_shared_list` / `delete_shared_list`,
> the twelve tag endpoints and `sdk.node_ssh` need a panel on **3.4.0**.

> Remnawave 3.0 is **not** backwards compatible with 2.8 — users are identified by a numeric
> `id` instead of a `uuid`, `/api/ip-control` became `/api/connections`, and many endpoints
> answer with an empty body. Pin `2.8.1` if your panel is still on the 2.8 line.

**Requirements:** Python >= 3.11, < 3.15.

## Installation

```bash
pip install remnactual
```

The import name stays `remnawave`:

```python
from remnawave import RemnawaveSDK
```

Straight from git:

```bash
pip install "git+https://github.com/IceOne-i/remnactual.git@production"
```

## Quick start

```python
import asyncio
import os

from remnawave import RemnawaveSDK
from remnawave.models import GetAllUsersResponseDto


async def main() -> None:
    sdk = RemnawaveSDK(
        # https://panel.example.com  or  http://127.0.0.1:3000
        base_url=os.environ["REMNAWAVE_BASE_URL"],
        # Bearer token from the panel: Settings -> API Tokens
        token=os.environ["REMNAWAVE_TOKEN"],
    )

    page: GetAllUsersResponseDto = await sdk.users.get_all_users(start=0, size=50)
    print(f"total: {page.total}")
    for user in page.users:
        # 3.0: users are identified by a numeric id; there is no `uuid` field any more
        print(user.id, user.username, user.status, user.expire_at)


asyncio.run(main())
```

The transport unwraps the API's `{"response": ...}` envelope for you, so responses are the
payload itself.

### Client options

```python
sdk = RemnawaveSDK(
    base_url="https://panel.example.com",
    token="...",
    caddy_token="...",                      # X-Api-Key when the panel sits behind Caddy
    ssl_ignore=False,                       # skip TLS verification (self-signed certs)
    custom_headers={"X-Real-IP": "1.2.3.4"},
    cookies={"session": "..."},             # reverse-proxy auth
)
```

You can also pass a pre-configured client and manage its lifetime yourself:

```python
import httpx

async with httpx.AsyncClient(
    base_url="https://panel.example.com/api",
    headers={"Authorization": "Bearer ..."},
) as client:
    sdk = RemnawaveSDK(client=client)
```

`base_url` is normalised automatically: a trailing slash is stripped and `/api` is appended
when missing.

## Controllers

| Attribute | Covers |
| --- | --- |
| `sdk.users` | CRUD, lookups by id / short-uuid / username, actions (incl. `extend`), tags, `stream` (cursor pagination + filters), accessible nodes |
| `sdk.users_bulk_actions` | `bulk/*` and `bulk/all/*` operations |
| `sdk.nodes` | CRUD, enable/disable/restart, reorder, reset traffic, bulk actions, tags |
| `sdk.hosts` / `sdk.hosts_bulk_actions` | CRUD, reorder, tags, bulk enable/disable/delete/update |
| `sdk.config_profiles` | Config profiles, inbounds, computed config, reorder |
| `sdk.inbounds` | Inbounds under `/config-profiles/inbounds` |
| `sdk.internal_squads` / `sdk.external_squads` | Squads, membership bulk actions, accessible nodes, reorder |
| `sdk.subscription` | Public `/sub/{shortUuid}` endpoints |
| `sdk.subscriptions` | Admin subscription lookups, raw subscription, connection keys |
| `sdk.subscriptions_settings` / `sdk.subscriptions_template` / `sdk.subscription_page_config` | Subscription settings, templates, subscription page configs |
| `sdk.subscription_request_history` | Request history and its stats |
| `sdk.hwid` | HWID devices, stats, top users |
| `sdk.connections` | Per-user / per-node connection jobs, node geocheck, drop connections (was `sdk.ip_control`) |
| `sdk.node_plugins` | Node plugins, executor, torrent-blocker reports, shared lists, `sync` |
| `sdk.node_integrations` | Node integrations CRUD — the `integrationUuids` of a node |
| `sdk.node_ssh` | SSH ticket and key-vault evaluation (3.4.0+, **admin JWT only**) |
| `sdk.infra_billing` | Providers, billing nodes, billing history |
| `sdk.bandwidthstats` | Per-node and per-user bandwidth stats (incl. legacy endpoints) |
| `sdk.system` | Stats, digest, HTTP counters, health, metrics, recap, configuration, x25519, SRR matcher |
| `sdk.auth` / `sdk.passkeys` / `sdk.api_tokens_management` | Login, OAuth2, passkeys, scoped API tokens |
| `sdk.remnawave_settings` / `sdk.snippets` / `sdk.keygen` / `sdk.metadata` | Panel settings, snippets (incl. `sync`), node secret key, user/node metadata |
| `sdk.webhook_utility` | Webhook signature validation and payload parsing |

## Request bodies and `null`

Request models are serialized with `model_dump(exclude_unset=True)`, i.e. **exactly the fields
you set are sent**. Several fields can only be cleared by sending an explicit `null`:

```python
from remnawave.models import UpdateUserBodyDto

# `telegram_id` is cleared, `email` is left untouched
await sdk.users.update_user(
    UpdateUserBodyDto(id=user_id, telegram_id=None)
)
```

Fields you do not pass are omitted from the payload, so the server's own defaults apply.

## Endpoints without a response body

In 3.0, 43 endpoints answer `204 No Content` or `202 Accepted` with an empty body: every
`DELETE`, the asynchronous bulk operations, node restarts, squad membership changes and the
plugin executor. Their SDK methods return `None` — success is "no exception raised", and
affected-row counts are no longer reported by the API.

```python
await sdk.users.delete_user(user_id)          # -> None (204)
await sdk.users_bulk_actions.bulk_delete_users(
    BulkDeleteUsersBodyDto(user_ids=[1, 2, 3])
)                                             # -> None (204)
await sdk.nodes.restart_node(node_uuid, RestartNodeBodyDto(force_restart=True))  # -> None (202)
```

## Error handling

Every non-2xx response raises a subclass of `ApiError`. The exception class is derived from
the `httpCode` declared for that error code in the backend contract.

```python
from remnawave.exceptions import ApiError, NotFoundError, ConflictError

try:
    user = await sdk.users.get_user_by_id(user_id)
except NotFoundError as e:
    print(e.code, e.message)      # A025 User not found
except ConflictError:
    ...
except ApiError as e:
    print(e.status_code, e.error)
```

`remnawave.enums.ErrorCode` contains every error code of the contract; `ERROR_HTTP_CODES` and
`ERROR_MESSAGES` in `remnawave.enums.error_code` expose the declared status and default message.

## Webhooks

```python
from remnawave import RemnawaveSDK

sdk = RemnawaveSDK(base_url=..., token=...)

# `raw_body` must be the RAW request body (bytes or str) — re-serializing a parsed dict
# can change the byte string and break the signature check.
payload = sdk.webhook_utility.parse_webhook(raw_body, request_headers, webhook_secret)
if payload is None:
    ...  # invalid signature

if sdk.webhook_utility.is_user_event(payload.event):
    user = payload.data
    if payload.event == "user.expiration":
        # single event replacing user.expires_in_*; hours are in meta
        print(payload.meta.expiration)
```

## What this fork changes

This fork tracks the Remnawave API closely and fixes the divergences each upstream migration
left behind.

### Compatibility with 3.4.5–3.4.7

The [changes since 3.4.4](https://github.com/remnawave/backend/compare/3.4.4...3.4.7)
leave `libs/contract` identical (contract package `3.4.15`): no endpoints, DTO fields,
scopes or error codes changed. Existing SDK methods remain compatible.

| Panel | Changes relevant to SDK users |
| --- | --- |
| [3.4.5](https://github.com/remnawave/backend/releases/tag/3.4.5) | Adds the `postStart` node plugin. Fixes gRPC `multiMode` in generated Xray JSON and ID filters in users/Torrent Blocker reports. Adds the server-side `SERVICE_SNI_VERIFICATION` setting for panel-to-node connections. |
| [3.4.6](https://github.com/remnawave/backend/releases/tag/3.4.6) | Updates the Docker image to the Node.js security release and changes the server's bulk deletion query. |
| [3.4.7](https://github.com/remnawave/backend/releases/tag/3.4.7) | Fixes Reality/X25519 public key derivation on the server. |

ID filters now use exact equality for users' `id` and reports' `id`, `userId` and
`nodeId`; invalid IDs return no matches. The query format is unchanged. These fixes
and the SNI setting require updating/configuring the panel, with no SDK option needed.

`postStart` (panel 3.4.5+, with a supporting node version) sends an optional webhook
after Xray starts or restarts. It uses the existing untyped `plugin_config` mapping;
the panel validates its contents. Preserve other plugin sections when updating it:

```python
from remnawave.models import SyncNodePluginBodyDto, UpdateNodePluginBodyDto

plugin = await sdk.node_plugins.get_node_plugin_by_uuid(uuid=str(plugin_uuid))
config = dict(plugin.plugin_config or {})
config["postStart"] = {
    "enabled": True,
    "webhook": {"enabled": True, "url": "https://hooks.example.com/core-started"},
}
await sdk.node_plugins.update_node_plugin(
    UpdateNodePluginBodyDto(uuid=plugin.uuid, plugin_config=config)
)
await sdk.node_plugins.sync_node_plugin(SyncNodePluginBodyDto(uuid=plugin.uuid))
```

`postStart.enabled` defaults to `false` on the panel; `webhook` is optional. When
provided, it requires `enabled` and an HTTP(S) `url`. Offline compatibility tests
cover request serialization and response parsing, including disabled and omitted fields.

### Migration to 3.4

The first **non-additive** step since 3.0: one field was replaced and two endpoints moved.

- **Hosts: `excludedInternalSquads` -> `internalSquads`.** The old field was a bare list of
  squads to hide the host from; the new one is `{ mode, squads }`, where `mode` is `EXCLUDE`
  (the old behaviour) or `ALLOW_ONLY` (show the host **only** to those squads, and then the
  list may not be empty). Both fields are kept here so the SDK still reads and writes a 3.3
  panel, and `HostResponseDto.effective_internal_squads` folds the two into one shape — on a
  pre-3.4 panel it returns the old list under `mode=EXCLUDE`, which is exactly what it meant.
  Setting **both** in a request body raises before the call: panel schemas are not strict, so
  an `excludedInternalSquads` sent to a 3.4 panel would be dropped in silence and you would
  believe the host was configured. The same replacement reached `PATCH /hosts/bulk/update`
  transitively — its body is derived from the single-host one in the contract.
- **`isDisabled` of `PATCH /hosts` became optional.** It used to default to `false`, so an
  update that did not mention it silently **enabled** a disabled host. It now stays untouched.
- **Shared lists: the name left the path.** `GET /node-plugins/shared-lists/{name}` is now
  `GET /node-plugins/shared-lists/by-name?name=`, and `DELETE .../{name}` takes the name in the
  body. Not cosmetic: 3.4 allows a slash inside the name, and such a name cannot be a path
  segment. Snippet names gained the same slash.
- **Tags** on six kinds of entity — config profiles, internal and external squads, node
  plugins, subscription page configs and subscription templates. Each gained a `tags` field
  plus `GET`/`PATCH <entity>/tags` (`sdk.<controller>.get_tags()` / `.set_tags()`); `PATCH`
  **replaces** the set. A tag matches `^[A-Z0-9_:]+$`, at most 36 characters, at most ten per
  entity. Scopes `<resource>:list-tags` / `:set-tags`, errors `A256`-`A257`.
- **`sdk.node_ssh`** — `POST /node-ssh/{uuid}/ticket` and `POST /node-ssh/vault/evaluate`.
  Guarded by the **admin role**, not by a scope: the panel controller carries no
  `@ApiScopeResource`, so `node-ssh` does not appear in `GET /tokens/scopes` at all and no API
  token can reach it. The terminal itself is a WebSocket and is out of scope for an `httpx`
  client — only the two HTTP steps that precede it are here. Errors `A254`-`A255`.
- **Host Mapper `$link.`** — a target may now rewrite the share link itself rather than its
  query string (`$link.address`, `$link.port`, `$link.password`, `$link.remark`, and
  `$link.method` for Shadowsocks). No SDK change: the contract types the target as a plain
  1..512 string, and narrowing it here would forbid what the panel accepts.

### Migration to 3.3

Additive as well — nothing was renamed or removed, and the shape of every existing response is
unchanged.

- **Node integrations** — a new controller, `sdk.node_integrations`: a named piece of
  configuration the panel merges into the config of every node it is enabled on. Nodes carry
  `integrationUuids` (up to 20) on `NodeResponseDto`, on the webhook node model and as an
  optional field of `POST` / `PATCH /nodes` and of the bulk update. Scopes are
  `node-integrations:*`, errors `A238`-`A244`.
- **Shared lists** — `sdk.node_plugins.get_shared_lists()` and friends under
  `/node-plugins/shared-lists`. A list is either `ipList` (IPs and CIDR ranges) or `asList`
  (ASNs); an unknown type stays a plain dict, because the contract types `config` as an
  arbitrary object and validates it on the panel (`A252`). The `ext:` prefix is added by the
  panel, so the name you send must match `^[A-Za-z0-9_-]+$`. `GET /node-plugins/shared-lists`
  returns previews only — name, type and item count. Errors `A245`-`A252`.
- **Added** — `POST /node-plugins/actions/sync` (`sdk.node_plugins.sync_node_plugin()`) and
  `POST /node-plugins/shared-lists/actions/sync`, both `202 Accepted` with no body.
- **Node geocheck** — `sdk.connections.geocheck_by_node()` queues the check and returns a job
  ID, `geocheck_by_node_result()` polls it (the node may take up to a minute). The result
  carries a base64 SVG ready for a `data:` URL and the raw node report. The source of the
  check is either `ip` or `interface`, never both — the body model rejects that combination
  locally.
- **Host Mapper** — `mapper` on hosts (response and both bodies) and on `clientOverrides` of
  the raw subscription. It rewrites the generated config per client type (`xrayJson`,
  `mihomo`, `base64`, `singbox`) with `copy` / `set` / `unset` operations. `from` is a Python
  keyword, so the field is `from_` and serializes back to `from`.
- **`respondWithRemarks`** in SRR response modifications — replaces the response body with the
  given remarks.
- `rulePlacement` of the Torrent Blocker plugin (3.3.1, its default dropped in 3.3.2) needs no
  SDK change — the contract types `pluginConfig` as `unknown`, so it stays an untyped mapping
  here.

### Migration to 3.2.3

Additive as well — nothing was renamed or removed.

- **Added** — `POST /snippets/actions/sync` (`sdk.snippets.sync_snippet()`), with the
  `snippets:sync` token scope and the new `A237` error code. It rolls a snippet out to every
  config profile referencing it and restarts the nodes of those profiles; the panel answers
  `202 Accepted` with no body, so the method returns `None`.
- **Nodes carry `ips`** — a list of up to 64 `{ip, status}` entries on `NodeResponseDto` and on
  the webhook node model, and an optional field of `POST` / `PATCH /nodes`. Statuses live in
  `remnawave.enums.NodeIpStatus`. Panels below 3.2.3 do not send it, so the list stays empty.
- **`cipherSuites`** of the inbound's `tlsSettings` reaches the raw subscription —
  `TlsSecurityOptions.cipher_suites`.
- `vlessUuid` validation was loosened upstream (`z.uuid()` → `z.guid()`) and needs no SDK
  change: Python's `uuid.UUID` already accepts non-RFC-4122 values.

### Migration to 3.1 / 3.2

Both releases are additive — no endpoint, path or field was renamed or removed.

- **Nodes carry a numeric `id`** next to the `uuid`, on `NodeResponseDto` and on the webhook
  node model (`data.id` of node events, `data.node.id` of torrent-blocker events). Node routes
  still take `{uuid}`.
- **Subscription request history reports the matched SRR rule** — `srrResponseType` and
  `srrRuleName` on both `GET /subscription-request-history` and
  `GET /users/{userId}/subscription-request-history`.
- **Added** — `GET /system/configuration` (`sdk.system.get_configuration()`), with the
  `system:configuration` token scope.
- **Renamed** — the contract's constant for error `A084` became
  `BULK_DELETE_USERS_BY_USER_IDS_ERROR` (the code and its HTTP status are unchanged); the old
  `BULK_DELETE_USERS_BY_UUID_ERROR` name stays as an alias of the same member.
- The `preStart` node plugin needs no SDK change — the contract types `pluginConfig` as
  `unknown`, so it stays an untyped mapping here.

### Migration to 3.0

- **Users are identified by a numeric `id`.** The `uuid` field is gone from the user model, all
  `{uuid}` path params became `{userId}` (integers), and bulk bodies take `userIds`.
- **`/api/ip-control` became `/api/connections`** — `sdk.ip_control` is now `sdk.connections`,
  with `by-user` / `by-node` jobs and `drop`.
- **43 endpoints answer with an empty body** (204/202) and their methods return `None`;
  the `Delete*ResponseDto` / `Bulk*ResponseDto` models were removed.
- **Removed upstream, removed here** — `GET /users/by-email`, `/by-tag`, `/by-telegram-id`,
  `/by-id`, both legacy bandwidth-stats endpoints, the `docs` object of `GET /tokens`, and the
  `profileTitle` / `profileUpdateInterval` / `supportLink` / `isProfileWebpageUrlEnabled` /
  `happAnnounce` / `happRouting` subscription settings (they moved to response headers).
- **Added** — `POST /users/{userId}/actions/extend`, `POST /tokens/ott`,
  `GET /system/stats/digest`, `GET /system/stats/http`, `POST /bandwidth-stats/nodes/usage`,
  internal-squad usage stats and targeted squad membership bulk actions,
  `GET /subscriptions/by-id/{userId}`.
- **Renamed** — `keygen` returns `secretKey` instead of `pubKey`; external squads split
  `responseHeaders` into `responseHeadersAdd` / `responseHeadersRemove`; request models follow
  the contract's `*BodyDto` naming, with the old `*RequestDto` names kept as aliases.

### Earlier: 2.8 compliance

- Removed the endpoints 2.8 dropped (`/xray`, `/inbounds/bulk/*`, `/sub/outline/...`,
  `POST /nodes/actions/reset-traffic`, `POST /auth/oauth2/tg/callback`,
  `GET /bandwidth-stats/nodes/realtime`).
- `userUuid` → `userId` in HWID devices and subscription request history; `hwidCheckup`
  replaced `isHwidLimited`; `resolvedProxyConfigs` replaced `rawHosts`.
- Error codes regenerated from the contract, exceptions mapped from the declared `httpCode`.
- Name collisions in `remnawave.models` resolved (webhook models are prefixed `Webhook*`).
- Serialization switched from `exclude_none` to `exclude_unset`, so an explicit `null` reaches
  the API; keys the contract requires unconditionally are always emitted.

## Development

The project is managed with [uv](https://docs.astral.sh/uv/) — there is no lock file, because
a library should resolve against whatever its consumers already have.

```bash
uv sync --group dev

# offline tests (contract regressions, models, enums, controller surface)
uv run pytest tests/test_3_0_compliance.py tests/test_3_2_compliance.py \
              tests/test_3_2_3_compliance.py tests/test_3_3_compliance.py \
              tests/test_3_4_compliance.py tests/test_3_4_4_compliance.py \
              tests/test_3_4_7_compliance.py tests/test_rapid_compatibility.py \
              tests/test_models_validation.py tests/test_enums.py \
              tests/test_controllers_completeness.py

# full suite — requires a live panel
#   REMNAWAVE_BASE_URL, REMNAWAVE_TOKEN and the REMNAWAVE_* fixtures in tests/conftest.py
uv run pytest

# build locally — the version comes from the git tag
uv build
```

## Releasing

The version lives in exactly one place: **the git tag**. `pyproject.toml` carries no version
number — `hatch-vcs` derives it from `git describe` at build time, so a release
is a single action:

```bash
git tag v3.0.1
git push origin v3.0.1
```

Pushing to a branch never publishes anything. The `Publish Python Package` workflow then builds
the wheel and sdist (their version comes straight from the tag), runs the offline test suite,
asserts that the built version equals the tag, publishes to PyPI via Trusted Publishing
(OIDC — no tokens), and finally creates the GitHub Release with the artifacts attached.

Between tags the version is a PEP 440 development version derived from the last tag, e.g.
`3.0.1.post7.dev0+g1a2b3c4`, and `remnawave.__version__` reports whatever was installed:

```python
import remnawave
print(remnawave.__version__)
```

To rehearse without touching PyPI: Actions → *Publish Python Package* → *Run workflow* →
target `testpypi`.

## Credits

This SDK is a fork of the official
**[`remnawave/python-sdk`](https://github.com/remnawave/python-sdk)**, maintained by the
Remnawave community.

Upstream history:

- originally written by [@kesevone](https://github.com/kesevone);
- previously maintained by [@sm1ky](https://github.com/sm1ky) at
  [`sm1ky/remnawave-api`](https://github.com/sm1ky/remnawave-api);
- now maintained by the Remnawave community at
  [`remnawave/python-sdk`](https://github.com/remnawave/python-sdk).

The Remnawave panel itself lives at [`remnawave/backend`](https://github.com/remnawave/backend);
API documentation is at [docs.rw](https://docs.rw).

## License

MIT — see [LICENSE](LICENSE). The original license and copyright of the upstream project are
preserved.
