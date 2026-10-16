# MODEL PROFILE

**ChatGPT Phase Lead.** El contrato del Orchestrator recomienda GPT-6.1 Sol / High en ChatGPT Work si aparece en el selector; en Chat normal GPT-5.6 Sol / High si figura. Motivo: supervisar las fronteras de evidencia, comparabilidad, temporalidad, integración y aceptación. No atribuir disponibilidad ni configuración efectiva no observadas; si el selector difiere, usar una opción realmente disponible y registrar la diferencia.

**Codex Engineering Lead.** Recomendación del contrato: GPT-6.1 Sol / Medium **solo si está disponible**. Elevar a High para diseño de la transacción de lectura, integridad y validación de bundles, identidad semántica, fallos difíciles y cierre de hallazgos. ARQ/DB-OWNER y BE/DISCOVERY: High cuando la decisión lo justifique; SEC/SRE para revisión de fronteras. **QA y REVIEWER: agentes distintos entre sí y de todos los autores**, con High si se ofrece, sobre SHA/árbol finales inmutables. Para un bloqueo complejo reproducido, valorar la opción superior efectivamente presente, sin inventar nombres o afirmar un backend no verificable. Registrar modelo y reasoning solicitados, seleccionados y comprobables para cada rol. No usar Max/Ultra por defecto.

---

# ENGINEERING BRIEF — P4b Scoped Capture Discovery

**Emisor:** P4b Phase Lead — 2026-10-16 (Europe/Madrid).  
**Destinatario:** Codex Engineering Lead.  
**Autoridad:** 00 — ORCHESTRATOR (único que acepta/cierra la fase).  
**Repositorio:** `KastaTM/card-market-tracker` — https://github.com/KastaTM/card-market-tracker  
**Rama autorizada:** `feat/p4b-scoped-capture-discovery`.  
**Contrato vinculante íntegro:** `P4B_SCOPED_CAPTURE_DISCOVERY_CONTRACT.md`, aportado por el Orchestrator; archivarlo en `docs/phases/P4B_SCOPED_CAPTURE_DISCOVERY_CONTRACT.md` sin modificar sus restricciones. Este brief desarrolla su ejecución y **no lo sustituye**.  
**Permisos:** inspeccionar, planificar, crear rama/worktree, implementar, hacer commits, ejecutar tests, abrir PR y publicar evidencias. **No merge.** El merge exige posterior autorización del Orchestrator sobre el candidato exacto. No declarar `ACCEPTED`, `PHASE CLOSED` ni abrir otra fase.

## A. Estado remoto comprobado por el Phase Lead

Verificado mediante GitHub en 2026-10-16:

- `main` = `430e2049c9ffdffb68508329df6556bfed62baa2`.
- Árbol de ese merge: `c3988a86cedf525cce364bd9cc4709689c510053`.
- Padres, **en orden base → head**: `acca10e406dac8809edc289c3077a6ec8785a622`, `252c394141948e3ab77a54bcf628e4290ba69652`.
- P1b [PR #9](https://github.com/KastaTM/card-market-tracker/pull/9) está fusionado; [CI push/main 38877640587](https://github.com/KastaTM/card-market-tracker/actions/runs/38877640587) muestra `quality`, `compose`, `container (linux/amd64)` y `container (linux/arm64)` terminados con `success`.
- Búsqueda remota de `feat/p4b-scoped-capture-discovery` sin resultado en ese momento; conector GitHub tiene permisos push. **No es una verificación de que el checkout local esté limpio ni de que la rama siga ausente.**
- P1b había comunicado 777 tests PASS, un skip y 96,85 % líneas / 92,62 % ramas; son datos históricos de P1b, jamás gates P4b.

Preflight obligatorio **antes de escribir** desde el checkout local real (no asumir su ruta ni estado):

```sh
git remote -v
git status --porcelain=v1
git branch -vv
git worktree list
git fetch origin
git rev-parse origin/main
git rev-parse 'origin/main^{tree}'
git show -s --format='%P' origin/main
git branch -r
```

Registrar resultados en informe. Verificar `AGENTS.md`, `context.md`, `docs/ENGINEERING_OPERATING_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/QUALITY_GATES.md`, `docs/TESTING_STRATEGY.md`, `docs/CODING_STANDARDS.md`, `docs/RISK_REGISTER.md`, `docs/TECHNICAL_DEBT.md`, `docs/threat-model/THREAT_MODEL.md`, ADR-0003 a 0006, todos los contratos `CATALOG/INGESTION/MANIFEST/PERSISTENCE/STORAGE_V1/STORAGE_V2/CAPTURE_SCOPE_V1/DISCOVERY_V1`, bundle/fuentes P1b y tests/smokes/CI. Si `main` cambió, revisar delta respecto al baseline autorizado y **escalar incompatibilidad**; no cambiar base silenciosamente. Respetar worktrees y cambios de terceros, sin reset, force-push ni reemplazar trabajo. Si rama ya existe, inspeccionar antes de reutilizar.

## B. Problema y alcance exacto

Habilitar `DISCOVERY_V2`, offline y solo lectura, sobre una **unidad inequívoca dentro de cada captura SQLite v2** con su scope/evidence_state durables. Ejemplo de interfaz: `cmt discover-scoped --db PATH --request REQUEST_JSON`. Lectura de ventana explícita (current + hasta 32 history) mediante **una única transacción SQLite consistente**; comparar referencias en el contexto/selector/paths elegido. No hacer filtrado que convierta un lote corrupto o incompleto en vacío correcto.

La ruta antigua `cmt discover` / `DISCOVERY_V1` debe permanecer byte/semánticamente compatible y synthetic-only. P1b `persist_bundle`/`persist_capture`, PERSISTENCE_V1, schema1/schema2, migración, backup, replay y hashes `cmp1:`/`evt1:` permanecen intactos.

**No permitido:** nueva red o datos upstream, nuevos packages reales, TCGdex REST, APIs comerciales, otros proveedores/retail, precios, stock, sealed observado, preorders, launch, nuevo esquema/migración, cambios históricos, reescritura de fingerprints, asignación de identidad, promoción, event store, alertas, scheduler, servicio, frontend, claim de autenticidad de productores independientes o certificación Pi física. P2, P6a y Discovery retail continúan BLOCKED. Mantener licencia MIT del paquete aprobado.

**Hecho de evidencia clave:** el bundle P1b representa **dos artefactos, cuatro proyecciones set/card ES/EN, un solo `captured_at`**. Sus cuatro unidades deben producir baseline sin eventos al elegirse individualmente. Dos tokens de importación del mismo bundle **no crean dos instantes**: comparación current/history debe fallar `chronology`. Solo fixtures **synthetic** persistidas con `persist_capture` pueden demostrar novedades temporales positivas; no acreditan cambio real del proveedor.

Admisión observed solo desde bundle revisado: namespace `tcgdex_repository`, revisión `4199850a6af49665db0080fa2bb9ef751750a406`, SHA256 aprobado `3b43e1a78c117ef1ecb5cf200a4b2fc7e57af8fd29e3fcf29b06f4291ae58085`. Una procedencia autodeclarada o digest suministrado por usuario no es autorización.

## C. Diseño de fronteras (ownership antes de paralelizar)

Engineering Lead: plan, contrato de interfaces, control de Git, integración, CI y ledger; no delegar escrituras concurrentes a archivos/estado compartidos. Sugerencia de ownership con **aprobación explícita del Lead**:

| Rol | Ownership exclusivo primario | Entrega |
| --- | --- | --- |
| ARQ + DB-OWNER | `persistence/sqlite_repository.py`, extracción de helpers de `persistence/capture.py` solo si necesaria, contratos storage/read, pruebas de concurrencia/integridad | Reader P4b con una transacción, presupuesto y validación total |
| BE + DISCOVERY | Nuevos módulos `discovery/scoped_*.py` (parser, DTOs, comparación), interfaz v2 `cli.py` coordinada | Request v2, validador, cmp2/evt2, CLI y salida |
| SEC + SRE | Análisis read-only de inputs, clasificación de errores, autenticidad/scope, recursos, Docker/QEMU/logging; cambios documentales solo tras asignación | Threat/operational review y límites |
| QA | Nuevas pruebas independientes y fixtures synthetic en archivos exclusivos; lectura del candidato final sin editarlo | Negative/contract/integration/regression report |
| REVIEWER | Revisión final aislada del SHA/árbol exactos y sus cuatro CI jobs, distinto de QA/autores | Hallazgos y veredicto independiente |
| DOCS (opcional) | Documentación disjunta bajo lock de ownership | ADR, contratos, runbook, roadmap, gates |

No simular agentes: registrar agentes realmente usados, roles, modelos disponibles y evidencias. ARQ y BE acuerdan una API **independiente de SQLite** que entrega a Discovery unidades validadas/DTOs genéricos sin importar objetos del proveedor. La procedencia verificada pertenece al reader/storage tras validar el envelope, no a un constructor Python.

## D. Request v2 estricto

Forma contractual:

```json
{
  "version": 2,
  "context": {"namespace": "tcgdex_repository", "kind": "set", "language": "es"},
  "current": {"batch_id": "bd9cc4b8-eace-4567-8364-93cc4eccddc5", "selector": "swsh3"},
  "history": []
}
```

Keys exactas, versión integer 2 (bool inválido), UUIDv4 canónicos y únicos, una unidad por batch, `history` <=32 y orden canónico sin ocultar duplicados. Contexto namespace/token P1a <=128, kind `set|card|sealed`, idioma `es|en|null` **exacto**; selector no vacío <=256. Cualquier referencia extra, path/URL/SQL/índice suministrado, unknown key, duplicate key, Unicode inválido, nonfinite, estructura malformada = error. Reusar strict parser P1a con 1 MiB, depth16, <=20k nodos, strings/keys <=1024 y validación independiente de objetos construidos en Python. Nunca tratar `null` como wildcard.

En cada batch encontrar **exactamente una** unidad persistida por `(namespace,kind,language,selector)` o fallar; 0 o >1 no es ausencia. `record_indexes` solo del envelope verificado; no renumerar ni recuperar filas desde el request. Antes de seleccionar, **leer y validar todas las unidades/filas/conteos/partición** del batch y la ventana completa, incluidos registros de otras unidades. Rechazo en la unidad seleccionada => `incomplete_evidence`, incluso baseline. Otras unidades íntegras no se comparan ni inflan los conteos de selected.

Límites: <=33 batches, <=33.000 filas leídas/validadas globales, <=1.000 eventos. Nunca éxito truncado.

## E. Reader, scope y niveles de evidencia

Implementar nueva lectura explícita sobre una conexión SQLite `mode=ro`, `PRAGMA query_only=ON`, `BEGIN`, lectura schema2/captures/batches/records/evidencias en el mismo snapshot, `ROLLBACK` al finalizar. Presupuesto global 2 s por defecto, máximo 5 s, progress handler y lock/timeouts. No crear DB, migrar, reparar, cachear ni tocar journals. Schema1 y `legacy_unverified` fallan por no tener scope fiable. No llamar repetidamente a `query_capture` ni ensamblar snapshots inter-transacción.

Reutilizar **sin debilitar** `_capture_row` (longitud UTF-8 antes de materializar), `_decode_envelope` (límites léxicos), `_check_capture` (reconstrucción real/synthetic, manifest/scope, parent closure, row-counts, fingerprints) y `_snapshot_target`; si hay extracción de helpers, conservar firmas y regresiones. Validar coherence entre `captures.mode`, `evidence_state` y `Observation.provenance` de **todos** los registros. No crear bypass observed en `discovery.validation.validate_snapshot` v1 que actualmente exige synthetic; crear validación versionada para la nueva ruta.

Familias mutuamente excluyentes en la ventana:

1. **pinned observed** `verified_local_pinned_bundle`: solo contra el bundle P1b aprobado. Equivalencia local revisada, no autenticidad física, cobertura de proveedor ni actualización temporal.
2. **generic synthetic** `producer_declared`: scope persistido y revalidado; incluidos vacíos completos, como declaración local del productor, no autenticación externa.

`documented` y mezclas observed/synthetic se rechazan. Comparabilidad requiere contexto, selector, **conjunto exacto de paths seleccionados**, método/política/semántica y familia compatibles. El reordenamiento de paths no altera su conjunto; una ruta diferente no puede simular novedad dentro del mismo universo. `partial`/`failed`, selected!=completed o rechazos de unidad no se convierten en completos por filtrar. Para pinned comprobar `complete_nonempty` respecto a sus paths, para synthetic `outcome=complete` y selected==completed; synthetic empty solo si el scope lo certifica en el envelope.

Cronología exclusivamente por el **captured_at original UTC** persistido: todos los history estrictamente anteriores al current; empates entre histories son legales; igualdad actual-historia y futuro inválidos. No `first_persisted_at`, timestamp de consulta, run/token ID, acquisition_time ni fecha de lanzamiento.

## F. Comparador puro y salida semántica

Comparador fuera de SQLite/provider/manifest y sin I/O. Clave de referencia completa `(namespace,kind,external_id,language,variant)`. Unión histórica de aceptados + candidatos. Candidato histórico luego aceptado no es novedoso; alias distinto al mismo CMT UUID es otra referencia, no producto nuevo. Solo nuevos sets aceptados generan `SET_REFERENCE_FIRST_OBSERVED`; candidatos de cualquier kind generan `CANDIDATE_REFERENCE_FIRST_OBSERVED`; cards/sealed aceptados no generan evento. Edición de nombre/fecha/binding sin cambio de reference no genera novedad. Duplicados idénticos dentro de unidad se colapsan conservando todos los índices originales; contradicción de snapshot/status/category/target dentro de la misma unidad invalida todo. Cambios legítimos entre capturas permitidos. Un historial vacío produce **baseline sin eventos tras validar la captura actual**.

Salida JSON `version:2` con `result` baseline/no_discoveries/discoveries; `comparison_id`, contexto, unidad actual e históricas y capturas originales, scope/paths y evidence_state explícitos, conteos de **batches/rows globales validados** separados de **rows/references de unidades seleccionadas** y eventos. Eventos con tipo/reference/status/category/frozen CMT target/token/capture/índices originales/evidencia de ventana seleccionada. `first_observed_in_window_at` significa SOLO primera observación en historia explícitamente elegida. No `global first seen`, de-listing, release, stock, source health, nuevos productos o notificación.

Nuevos IDs deterministas con JSON canónico (`ensure_ascii`, sorted keys, separadores compactos; SHA256): prefijos `cmp2:` y `evt2:`, payload y versión documentados en `DISCOVERY_V2`. Comparison ID incluye request canónico, evidence_state/familia, scope y contenido pertinente; event ID identifica referencia/evento/captura/unidad current (no cambia con orden del history). No incluir reloj de ejecución, run ID, DB path, duración ni primer persistido. Comprobar sensibilidad a alteración relevante y estabilidad en backup/restore/replay/permutación histórica. Estos hashes NO prueban autenticidad ni exactly-once. No cambiar cmp1/evt1.

CLI `cmt discover-scoped --db --request`: success exit 0; errores de request/scope/chronology/incomplete exit 2; schema/storage/corruption/lock/deadline/IO exit 1. Error JSON v2 con counts `null`, events `[]`, safe `error_category`; ninguna salida parece éxito parcial. Logging JSON allowlisted con `run_id`, `operation` diferenciada, duración, resultado y conteos bounded; sin nombres, refs, selectors, paths, tokens, SQL, payload o excepciones crudas. Revisar `logging_json.py` y sus tests.

## G. Plan de trabajo por hitos

1. **Preflight y ownership**: commit/árbol/refs/worktrees; leer el contrato entero; registrar plan, interfaces y conflictos. Archivar contrato y actualizar roadmap con P1b `ACCEPTED / PHASE CLOSED` y P4b apertura **atribuidas al Orchestrator**; enlazar PR #9, CI/main y contrato. No inventar comentario de cierre publicado.
2. **Contratos primero**: ADR-0007 (si sigue libre), `DISCOVERY_V2.md`, extensión read-only de captura/storage, DTOs y categorías de error. ADR con Context/Decision/Alternatives/Consequences/Status/Revisit conditions.
3. **Storage/read snapshot**: nuevo entrypoint y tests de integridad/concurrencia, límites, familias, selección; sin schema write. Acordar forma de DTO con BE.
4. **Pure comparator y CLI**: request estricto, validation v2, cmp2/evt2, serialización, logs, codes. Mantener Discovery v1 intacto; regression IDs.
5. **Test matrix completa**: synthetic `persist_capture`, bundle real aprobado sin modificar, cases de no event/current/history chronology, datos corruptos y concurrencia. `tests/fixtures/PROVENANCE.md` y fixtures versionadas mínimas.
6. **Harness entre procesos**: `scripts/scoped_capture_discovery_smoke.py` o equivalente, instalado vía wheel fuera de checkout, Compose, amd64 y arm64/QEMU. Todos los smoke previos se mantienen; containers UID10001, `--network none`, fixtures readonly.
7. **Documentación+hardening**: arquitectura, ADR, contracts, runbook, threat model, testing, quality gates, technical debt (TD-001..005 abiertos), README/AGENTS map si procede, CI 4 jobs, security/reproducibility.
8. **Congelar y revisar candidato**: QA independiente y REVIEWER diferente, ambos sobre SHA/árbol final; cerrar findings; PR sin merge; publicar ledger externo PR con hashes/checks/logs y Phase Completion Report. Evitar commit circular que inserte su propio SHA.

## H. Obligaciones de prueba y matriz AC-S01–S15

**Request y selección:** versions/bools/keys/dups/Unicode/bounds/forgery; UUID canonical; zero/ambiguous unit; selector, namespace, language-null, variant; path sets; snapshot indexes/counts/partition; unidades ajenas contaminadas o corruptas. **Familias:** constructor falso, observed no aprobado, producer_declared no autenticado, documented, mixed, schema1, legacy_unverified; scope malformado; partial/failed/missing/rejected; no success vacío. **Tiempo:** mismo paquete reimportado en diferente token debe fallar historia por igualdad temporal; historiales empatados, futuros, offsets canónicos.

**Comparador sintético persistido:** baseline válido e inválido, accepted new set, candidate unknown, alias mismo CMT ID, seen candidate->accepted, observed changed metadata, reappears after empty, complete empty, rejected within selected, duplicate collapse/conflict, otra unidad del mismo batch, paths distintos, history order deterministic, 1000 event limit. Usar producer_declared en todos los test cases synthetic; no falsificar un paquete observed.

**Real mínimo:** `persist_bundle` con la copia licenciada P1b sin edición; comprobar baseline de cada una de sus cuatro unidades ES/EN set/card con manifiesto sin bindings y bindings de set curados coherentes; original record indexes; sin event positivos; reimportación temporal fallida; `cmt discover` v1 sigue rechazando observed.

**Storage/replay/read-only:** captura corrupta (incluso unidad no seleccionada), falsificación de counters/provenance/parent closure/envelope, byte-size guard, schema/DB missing/lock/timeout, lector vs escritura intercalada (snapshot estable, siguiente lectura ve cambio), comprobación de no mutation lógica/schema/hash, replay, backup/restore semantic equivalence, sin memoria global/manifest actual ni red. No probar sobre bases de usuario.

**AC ledger**: mapear cada AC-S01 a AC-S15 al test/comando/evidencia/revisión exacta; no declarar PASS sin evidencia. Distinguir gates `FAIL` no ejecutados frente a gates históricamente PASS P1b. No existe AC de cambio real del proveedor; reportar esa limitación expresamente.

## I. Quality gates innegociables

```sh
uv sync --frozen --no-install-project
uv sync --frozen --no-build-isolation
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen mypy src
uv run --frozen coverage run -m pytest
uv run --frozen coverage json -o coverage.json
uv run --frozen python scripts/check_coverage.py coverage.json
uv build --no-build-isolation
sh scripts/wheel_smoke.sh
uv export --frozen --all-groups --no-emit-project -o requirements-audit.txt
uv run --frozen pip-audit -r requirements-audit.txt
uv run --frozen python scripts/check_secret_scan.py
```

Cobertura mínima código propio **>=85% líneas, >=80% ramas**. Build sdist/wheel e instalación **fuera del checkout**; nueva smoke no reemplaza anteriores. Ejecutar Compose y containers linux/amd64 y linux/arm64 con QEMU, verificando ejecución separada entre procesos y UID10001. Mantener los cuatro CI jobs (`quality`, `compose`, `container linux/amd64`, `container linux/arm64`). Revisar logs completos de todos sobre SHA exacto. QA/REVIEWER independientes y revisiones ARQ/DB/SEC/SRE/docs vinculadas a ese árbol. No reducir thresholds, omitir regresiones, silenciar tests con skips ni introducir dependencias de runtime sin necesidad. Un gate obligatorio no ejecutado es **FAIL**, con motivo. QEMU no prueba Pi real ni cortes eléctricos físicos.

## J. Informe final al Phase Lead, sin merge

Entregar:

- Phase, Proposed Status, Branch/PR/Commit, base+head SHA/tree, ownership, preflight y modelo/reasoning usados y verificables por rol.
- Objetivos/implementación/archivos; cambios arquitectura; ADR/contratos/storage (sin migración)/threat model/deuda/observabilidad; distinción synthetic versus paquete real fijo.
- Inventario de tests (unit/contract/integration/regression/negative/concurrency) y matriz AC-S01–S15 con PASS/FAIL y evidencia exacta.
- Gates locales y cuatro CI jobs con logs íntegros/URLs, coverage líneas/ramas, build outside tree, audit/scan, AMD64/ARM64/Compose; revisiones independientes QA + REVIEWER en SHA/tree congelados, findings/fixes.
- Evidencia de que la ruta v1 sigue synthetic-only y la v2 no modifica DB; límites y errores, replay/restore/hashes; ausencias/limitations/issues.
- URL del PR y ledger externo. No hacer merge; dejar candidato revisable por Orchestrator.

**Estado solo si los AC y todos los gates aplicables tienen evidencia PASS:** `READY_FOR_ORCHESTRATOR_REVIEW`. En caso contrario, informar `FAIL/BLOCKED` con acciones concretas, sin declarar cierre. Solo el Orchestrator autoriza integración del candidato exacto y, después del merge + CI `push/main`, evalúa `PHASE CLOSED`.
