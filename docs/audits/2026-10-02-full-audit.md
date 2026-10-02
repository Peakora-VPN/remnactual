# remnactual — предварительный полный аудит, 2026-10-02

**?????????? ??????????? ? Git.** ?? ??????? ???????????? ???????????, ????????????? ????? ? ?????? ???????? ? ????????? ??????? ????? `audit/full-2026-10-02`. ?????? ??????, ????? JSON-??????????, ????????? runners ? ???? ????????? ???????? ? ????????? ?? ????????; ?? ???? ???? ??????? ???????. ?????????? ?????????? staging/???????? ? ?????????? ????????? ? ?????? ?? ????? ???????. Push ? ?????????? ??????? ?? ???????????.

Статус: **аудит завершён, REM-01 исправлен локально**. Ветка `audit/full-2026-10-02`, исходный HEAD `dcb0e8ac6f92cdd9997d16ca0b65cc715c9cfce9`. Разделы до «Исправление и проверка» сохраняют первоначальный отчёт до изменения production/tests. Коммиты, push, публикация пакета и вызовы живой панели не выполнялись.

## Инвентаризация и реальная полнота

`git ls-files`: **139 tracked files**, из них **130 Python files**. Production: **94 Python modules / 12 776 строк**, tests: **36 Python files**. В библиотеке 32 файла controllers, 36 models, 15 enums, 3 exceptions, 4 rapid, 3 utils и package entrypoint. В AST найдено 222 декорированных HTTP-метода / 220 уникальных HTTP routes: два inbounds route доступны через совместимые controllers; это не коллизия FastAPI, библиотека не регистрирует серверные роуты.

| Область | Что проверено |
| --- | --- |
| README / project / release | README, pyproject.toml, pytest.ini, .gitignore, LICENSE, release workflow, run_tests.sh, fixture setup; AGENTS.md не обнаружен |
| Все исходники | AST всех 130 tracked Python files; Ruff всего production/tests; импорт всех 94 production modules; каталог всех controller методов и DTO signatures/aliases |
| Транспорт | Создание/передача AsyncClient, URL/headers, build_request, decorators, error mapping, raw/typed/RootModel responses, query/body serialization, explicit null/default fields |
| Domain boundaries | users/nodes/subscriptions/hosts/bulk, auth/passkeys/SSH, metadata, billing, squads/configs/templates, node plugins/snippets, webhook DTO/utility; ручное чтение ключевых controllers/DTO и структурная проверка остальных деклараций |
| Контракт | Существующие автономные compliance suites 3.0–3.4.4; выборочное сопоставление с первичным backend contract, зафиксированным на tag 3.4.4 |
| Downstream | Read-only проверен фактический потребитель peakora-api, включая dependency `remnactual` и управление lifetime клиента |

Не утверждается, что каждое из сотен DTO fields было независимо сверено с каждой строкой upstream schema. Полная live suite намеренно исключена: fixture читает REMNAWAVE_* и создаёт реальный SDK (`tests/conftest.py:8–29`), а domain tests могут изменять панель. Файл `tests/.env.test` и любые реальные `.env` не читались. Отсутствие других подтверждённых дефектов не означает гарантии безопасности всех внешних endpoint contracts.

Применены Ponytail (минимальный fix/reuse существующих DTO) и systematic-debugging (прослеживание причин, локальная проверка, refutation альтернатив).

## Baseline

Среда: CPython **3.14.7**, установленное локальное `.venv`; `uv run --no-sync` использован, чтобы не менять library dependency resolution/ignored lock. `PYTHON_DOTENV_DISABLED=1`, REMNAWAVE_BASE_URL/TOKEN очищены для запуска. Все HTTP-воспроизведения используют `httpx.MockTransport` и фиктивный адрес `panel.invalid`.

| Проверка | Результат |
| --- | --- |
| AST parse | 130 / 130 Python files успешно |
| Import production | 94 / 94 modules успешно, без конструирования live SDK |
| Offline suite, список ровно как в CI | **295 passed in 0.32s** |
| `uv run --no-sync ruff check remnawave tests` | exit 1, 1 382 замечания |
| Ruff без внешней конфигурации: `ruff check --isolated remnawave tests --output-format json` | exit 1, **1 375 замечаний** |
| Type check | В repo нет настроенного type checker / команды; не подменяется заявлением «types passed» |
| Build/twine/release/Docker/live integration | Не запускались; Dockerfile/compose у библиотеки нет |

Команда автономных тестов:

```text
uv run --no-sync pytest -q tests/test_3_0_compliance.py tests/test_3_2_compliance.py tests/test_3_2_3_compliance.py tests/test_3_3_compliance.py tests/test_3_4_compliance.py tests/test_3_4_4_compliance.py tests/test_rapid_compatibility.py tests/test_models_validation.py tests/test_enums.py tests/test_controllers_completeness.py
```

Из 1 375 isolated Ruff diagnostics 595 — UP045, 285 — UP006, 270 — PIE790; прочие в основном import/typing/style. 48 F401 и 2 F841 не превращены автоматически в production incidents; F821/F811 в этом запуске отсутствуют. Ruff baseline не зелёный, но массовая style migration не является минимальным исправлением обнаруженного бага. CI сейчас запускает offline tests, build, twine metadata/version checks (`.github/workflows/upload.yml:49–68`), Ruff gate в нём отсутствует.

Dependency версии в локальной среде: rapid-api-client 0.10.0, httpx 0.28.1, pydantic 2.13.5, orjson 3.12.0, cryptography 50.0.1. Editable distribution metadata содержит прежнюю dev version; baseline относится к импортированному текущему source tree, не к проверенному релизному wheel.

## Подтверждённые дефекты

P2 — воспроизводимый неправильный результат при допустимом вызове. P0/P1 в проверенных локальных сценариях не подтверждены.

| ID | Severity | Результат | Root cause |
| --- | --- | --- | --- |
| REM-01 | P2 | Массовый PATCH mapper проходит без ошибки, но обновление не передаётся панели | `remnawave/models/hosts_bulk_actions.py:22–77` |

### REM-01 — mapper потерян в bulk host update DTO

Одиночный `UpdateHostBodyDto` уже содержит `mapper: Optional[HostMapperDto]` (`remnawave/models/hosts.py:130–131`), а `UpdateManyHostsBodyDto` не содержит это поле. Pydantic default `extra="ignore"` молча удаляет переданный mapper; контроллер отправляет сериализацию этого DTO (`remnawave/controllers/hosts_bulk_actions.py:37–42`, `remnawave/rapid/client.py:186–262`). Вызов возвращает `None` при ожидаемом 204: вызывающий видит нормальное завершение, хотя нужной операции в HTTP body вообще нет.

Это поддержанная панелью операция: [bulk contract 3.4.4](https://github.com/remnawave/backend/blob/3.4.4/libs/contract/commands/hosts/bulk/update-many-hosts.command.ts) выводит request из `UpdateHostCommand.RequestBodySchema.omit({uuid}).partial()`, а [single update contract 3.4.4](https://github.com/remnawave/backend/blob/3.4.4/libs/contract/commands/hosts/update.command.ts) объявляет `mapper: HostMapperSchema.optional()`.

**Воспроизведение без панели:** один и тот же валидный объект mapper успешно проходит одиночный DTO. При `sdk.hosts_bulk_actions.update_hosts(UpdateManyHostsBodyDto(uuids=[UUID], mapper=mapper))` MockTransport принимает PATCH и отвечает 204. Фактические ключи отправленного body — только `['uuids']`; `mapper` отсутствует; result `None`.

```python
mapper = {"xrayJson": [
    {"op": "set", "to": "streamSettings.tlsSettings.enableSessionResumption", "value": True}
]}
one = UpdateHostBodyDto(uuid=host_uuid, mapper=mapper)  # валидно, mapper сохранён
many = UpdateManyHostsBodyDto(uuids=[host_uuid], mapper=mapper)
assert "mapper" not in many.model_dump(by_alias=True, exclude_unset=True)  # текущий дефект
```

**Минимальный fix:** импортировать существующий `HostMapperDto` и добавить такое же optional поле в bulk DTO. Не нужен новый serializer или общий генератор DTO. Поднять локальный regression на фактический outgoing JSON через MockTransport: mapper с copy/set/unset сохраняется, `op` и alias `from` присутствуют, 204 остаётся `None`; отсутствующий mapper не добавляется. Contract optional не означает nullable: explicit null не объявляется успешным panel input без отдельной проверки.

**Дополнительная страховка:** узкий field parity check между single-update и bulk-update (`single - uuid == bulk - uuids`) обнаружит эту же ошибку при следующих миграциях. Проверять только эту явную contract derivation, не распространять предположение на все bulk DTO: bulk-all users и bulk nodes имеют самостоятельные наборы полей.

## Отдельные рекомендации и hardening

1. **Проверка wire contract:** существующая completeness suite считает методы/классы, что не обнаружило отсутствующий mapper. Для производственных DTO важнее небольшие MockTransport snapshots реально передаваемых keys/aliases, чем ещё один тест количества классов. Сохранить существующие transport helpers и AlwaysEmitModel, которые уже решают explicit null/default operation tags.
2. **Lint без большого переписывания:** явно задать небольшой согласованный Ruff rule set и green gate для будущих изменений. 1 375 замечаний в основном показывают отсутствие принятого style baseline, а не 1 375 runtime defects. Не добавлять type/framework layers только ради числа проверок.
3. **Client lifetime:** при собственном AsyncClient SDK не предоставляет публичного `aclose`/async context API (`remnawave/__init__.py:135–144`). README уже показывает caller-owned client context (`README.md:143–153`); peakora-api закрывает `_sdk._client` сам. Минимум — документировать ownership для обоих вариантов. При подтверждённой потребности публичный close helper удобнее private attribute; новая client factory не нужна. Утечка соединений в Peakora API не подтверждена.
4. **Packaging secrets:** sdist include охватывает tests (`pyproject.toml:63–64`); `tests/.env.test` tracked. Явно исключить env files из artifacts/разобрать назначение tracked fixture. Реальные значения не читались, build archive не исследовался: это рекомендация по границе публикации, а не утверждение об утёкшем credential.
5. **Testing config:** pytest.ini перекрывает `[tool.pytest.ini_options]`, поэтому указанные в pyproject strict config/markers/xdist settings не применяются как ожидается. Свести конфигурацию к одному файлу и отделить live tests marker/opt-in от безопасной команды; не запускать весь pytest с боевой dotenv.
6. **Webhook:** raw-body HMAC и constant-time сравнение остаются правильной точкой проверки; README прямо предупреждает о повторной сериализации dict (`README.md:244–245`). Utility проверяет подпись, но не предоставляет durable replay protection. Peakora API имеет собственный timestamp/dedup ingress; не дублировать новую replay framework в SDK без требования самостоятельных consumers.
7. **Happ crypto:** `create_happ_crypto_link` ловит любое исключение и возвращает пустую строку (`remnawave/utils/happ_crypt.py:43–57`). Для неподдерживаемого метода/превышения RSA plaintext limit caller не отличает неудачу от пустого результата. Если callers требуют диагностируемость, минимальная явная ошибка/описанный fallback лучше swallowing всех исключений; менять криптографический protocol не требуется.
8. **Большие exports:** `/users/stream` возвращает целую строку через обычный buffered httpx send. Нагрузка/память на большом наборе не измерялись; вводить streaming API стоит по фактическому downstream объёму, а не как обязательное усложнение текущего audit fix.
9. **Release reproducibility:** Python range 3.11–3.14 объявлен, текущий локальный прогон только 3.14; CI использует один runtime. Добавить небольшой compatibility matrix по поддерживаемым версиям при релизе. Trusted Publishing/tag-version checks уже есть; переписывание release процесса не обосновано этим багом.

## Проверенные альтернативы и границы результата

- Гипотеза «202 уничтожает job_id connections/geocheck» отклонена: [backend controller 3.4.4](https://github.com/remnawave/backend/blob/3.4.4/src/modules/connections/connections.controller.ts) возвращает для job creation **201**, а 202 используется у drop без response body. Универсальный response guard не объявляется здесь текущим подтверждённым нарушением.
- У bulk-all users отсутствие external squad field и у bulk nodes отсутствие остальных single-update fields соответствует самостоятельным upstream request schemas; не добавлять их механически.
- Числовые user IDs, явные 202/204 no-content methods, StrEnum wire values, query bool/list handling, explicit null patch semantics и default mapper operation tags покрыты существующими compliance/rapid tests; массовое восстановление legacy UUID API не нужно.
- Не выполнены live panel auth/ACL checks, реальные mutate/delete/restart operations, Docker/environment deployment, supported-Python matrix, package artifact inspection, publish, load tests или CVE scan. Такой результат не выдаётся за их прохождение.

Первым patch candidate являлся REM-01 с regression test на outgoing body. Остальное отделено от подтверждённых багов. Отчёт сохранён в `docs/audits/2026-10-02-full-audit.md`; до исправлений `docs/` был gitignored. Текущее исключение описано ниже.

## Исправление и проверка — 2026-10-02

После общего предварительного отчёта разрешён REM-01. Добавлен MockTransport regression на настоящий вызов `hosts_bulk_actions.update_hosts`: outgoing PATCH `/api/hosts/bulk/update` должен содержать mapper с copy/set/unset, alias `from`, false value и 204 response→None. RED подтверждён: mapper отсутствовал в request JSON. GREEN получен добавлением **одного existing DTO field** `mapper: Optional[HostMapperDto] = None` в `UpdateManyHostsBodyDto` и импорта существующей модели. Второй test подтверждает, что unset mapper не появляется в payload. Старый неиспользуемый `typing.Dict` удалён из изменённого модуля для чистого targeted F gate.

`.gitignore` получил узкие exceptions для `docs/audits/2026-10-02-full-audit.md`: generated docs и соседние docs/audits файлы остаются исключёнными, отчёт виден обычному Git status и может быть сохранён с исправлением. Force-add, staging и commits не применялись.

| Проверка | После исправления |
| --- | --- |
| Offline CI suite, те же10 автономных файлов | **297 passed in0.31s** (baseline295) |
| AST tracked `.py` | **130/130** успешно |
| `ruff check --isolated --select F remnawave/models/hosts_bulk_actions.py tests/test_rapid_compatibility.py` | **All checks passed** |
| `git diff --check` | успешно |
| Полный Ruff / types | Полный green не заявляется: исходный style debt1375 отдельно зафиксирован; type gate отсутствует |

Воспроизводимая команда: `PYTHON_DOTENV_DISABLED=1`, пустые `REMNAWAVE_BASE_URL`/`REMNAWAVE_TOKEN`, `uv run --no-sync pytest -p no:cacheprovider -q tests/test_3_0_compliance.py tests/test_3_2_compliance.py tests/test_3_2_3_compliance.py tests/test_3_3_compliance.py tests/test_3_4_compliance.py tests/test_3_4_4_compliance.py tests/test_rapid_compatibility.py tests/test_models_validation.py tests/test_enums.py tests/test_controllers_completeness.py`. External/live suites намеренно не запускались.

Исправлен **локальный fork source**, опубликованный PyPI artifact не менялся. `peakora-api` сейчас не вызывает bulk-host update; отсутствие этих вызовов проверено read-only поиском. Изменение само по себе не означает выката нового wheel: consumers установленного релиза получат его только после отдельного выпуска/обновления dependency. Packaging API ради неиспользуемого bulk endpoint не менялся.
