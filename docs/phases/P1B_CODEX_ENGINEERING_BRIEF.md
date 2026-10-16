# MODEL PROFILE

**ChatGPT Phase Lead**
- Perfil indicado por el contrato del Orchestrator: **GPT-6.1 Sol / High** en Work si realmente figura en el selector; en Chat normal, **GPT-5.6 Sol / High** si está disponible. Para este intercambio no se ha verificado el selector del usuario: no atribuir un modelo de backend no observado.
- Motivo: autorización de datos reales, identidad canónica, transición de esquema, captura inmutable y revisión entre fases.

**Codex Engineering Lead**
- Recomendación contractual: **GPT-6.1 Sol / Medium** para planificación, inspección, integración y trabajo rutinario; escalar a **High** para migraciones, integridad y debugging difícil, siempre que figure disponible.
- ARQ/DB-OWNER, INTEGRATIONS/DATA y SEC/SRE: **GPT-6.1 Sol / High** solo para responsabilidades justificadas.
- QA y REVIEWER: **GPT-6.1 Sol / High**; agentes distintos entre sí y distintos de todos los autores; revisar SHA y árbol finales exactos.
- Escalado: primero High; **GPT-6 Astra / High** solo si hay bloqueo difícil reproducible, persiste tras el análisis y el selector lo ofrece. No elegir un nombre de modelo inexistente ni Max/Ultra por defecto.
- Registrar por rol modelo/reasoning solicitados, aceptados y efectivamente observables. Si no figura un modelo, utilizar una alternativa realmente disponible y registrar la desviación. No afirmar acceso a modelos no observados.

---

# ENGINEERING BRIEF — P1b Pinned Metadata Ingestion & Capture Scope

**Emisor:** P1b Phase Lead, 2026-10-14 UTC.
**Destinatario:** Codex Engineering Lead.
**Autoridad superior:** 00 — ORCHESTRATOR.
**Repositorio:** `KastaTM/card-market-tracker` (`https://github.com/KastaTM/card-market-tracker`).
**Checkout local de referencia:** `C:\Projects\card-market-tracker` (verificar su existencia; no asumirlo).
**Rama autorizada:** `feat/p1b-pinned-metadata-ingestion`.
**Documento vinculante:** `P1B_PINNED_METADATA_INGESTION_CONTRACT.md` adjunto; archivar copia íntegra en `docs/phases/P1B_PINNED_METADATA_INGESTION_CONTRACT.md` antes de desarrollar.
**Permisos:** crear rama, implementar, probar y abrir PR. **NO MERGE**. No aceptar/cerrar fase ni abrir otra fase; el Orchestrator lo decide.

## A. Objetivo, dependencias y límites

Implementar un flujo **offline y reproducible** de mínimos metadatos reales procedentes de dos artefactos concretos de `tcgdex/cards-database` fijados a un commit, que produzca **cuatro observaciones contextualizadas** (set y carta, ES y EN), pase por validación, resolución conservadora y **persistencia SQLite v2** con captura/scope y procedencia inmutables. Debe demostrar migración segura de v1, atomicidad, replay/conflicto, verificación/copia/recuperación y que las vías existentes synthetic-only nunca se abren por accidente.

P0, P0.5, P1a, P3a, P4a y P0.5b constan como cerradas **por decisión del Orchestrator**. Esta fase no cualifica TCGdex REST ni el catálogo completo. No realizar seguimiento de nuevas revisiones, crawl, compilación de TS, REST/SDK, mercado EUR, retail, sealed, stock, precios, preorders, scheduler, Telegram, frontend/API, señales, Discovery real, promoción de candidatos ni nuevos productores independientes.

P2, P6a y Discovery retail siguen BLOCKED. No ampliar permisos para eBay, GAME, Awin o Scrydex. Discovery P4a conserva selección exclusively synthetic; lo observado o mixto **debe fallar explícitamente**, nunca filtrarse.

## B. Preflight obligatorio antes de editar

El Phase Lead verificó remotamente por GitHub el 2026-10-14:

- `main = acca10e406dac8809edc289c3077a6ec8785a622`.
- `tree(main) = 26011d0375f3716a7fffb31956665eb97567a0df`.
- Padres del merge, **en orden**: `6385c952a9f2024c8b7bdb33d37fa21017029bd5`, `302e8d3f3155c14091d26841b8a230791109f220`.
- PR #8 fusionado; CI histórico main `https://github.com/KastaTM/card-market-tracker/actions/runs/38595222923`.
- Rama remota `feat/p1b-pinned-metadata-ingestion` no encontrada en búsqueda exacta a esa hora.
- GitHub reportó permisos de lectura/escritura del conector.

**Lo anterior NO verifica el checkout Windows, worktrees o cambios locales.** Ingeniería debe ejecutar y adjuntar resultados de:

```sh
git remote -v
git status --porcelain=v1
git branch -vv
git worktree list
git fetch origin
git rev-parse origin/main
git rev-parse origin/main^{tree}
git show -s --format='%P' origin/main
git branch -r
```

Inspeccionar el delta si `main` avanzó; no mover base autorizada silenciosamente, resetear, sobrescribir, forzar push ni rebasear trabajo ajeno. Separar la nueva rama/worktree de los worktrees anteriores. El Phase Lead no ha creado la rama ni tocado el repositorio. Si la rama ya existe al ejecutar, **inspeccionarla** antes de reutilizarla. Leer antes de editar `context.md`, `AGENTS.md`, modelo operativo, arquitectura, roadmap, ADR-0003/0004/0005, contratos vigentes, quality gates, testing, threat model, deuda, política de fuente e informes P0.5b. Registrar P0.5b cerrada y P1b abierta en roadmap con atribución correcta; conservar los informes antiguos como snapshots.

## C. Fuente autorizada, presupuesto y derechos

Ruta y commit inmutables:

```
repository: tcgdex/cards-database
revision:   4199850a6af49665db0080fa2bb9ef751750a406
source namespace: tcgdex_repository
```

| Artefacto exacto | Git blob SHA-1 esperado |
| --- | --- |
| `data/Sword & Shield/Darkness Ablaze.ts` | `db48bc4a054b3b1c5bd2b6956257f20ba251c79c` |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | `6db89c69b56552fa4e09f26e0e90d14e97466411` |
| `LICENSE` | `c67ded0d5f0abc77b4fbdbfd37312f2a88de1b55` |
| `README.md` | `77bc8108c2cdb54c663e1fdf8c4502ac65f88734` |

**Máximo ocho solicitudes de contenido nuevas para toda P1b**, no por agente: hasta cuatro para extracción y cuatro para QA independiente. Cada intento, redirect y retry que genere petición consume una unidad. Ejecutar lecturas secuencialmente, contabilidad única antes de cada llamada y stop ante denegación. El Phase Lead ha consumido **0/8** solicitudes P1b a estos cuatro artefactos en este intercambio: solo inspeccionó el repositorio CMT. No reutilizar el presupuesto histórico P0.5b. Obtener fuentes exclusivamente de GitHub/raw GitHub en el commit fijado; no ejecutar TS ni seguir URLs del payload, no clonar/crawlear el upstream entero, no usar TCGdex API. Registrar resultados, HTTP/bytes/tiempo **solo si efectivamente observables**, fallos, caché y digest. QA debe comparar de manera independiente contra los originales fijados, no aprobar solo por el extractor autor.

El Orchestrator autorizó consulta, extracción, retención local de **proyección mínima**, fixture pública mínima con atribución y conservación histórica de dicha proyección. Copiar el aviso MIT **íntegro**, con su copyright y permiso, dentro de los entregables publicados; conservar referencia al README de licencia. No asumir que MIT concede derechos adicionales sobre marcas, arte o información de terceros.

**Allowlist estricta:** `set.id`, `set.name.es`, `set.name.en`, `set.releaseDate`; `card.name.es`, `card.name.en`; número textual procedente del filename stem `136`; relación carta→set validada por import declarado al archivo autorizado; ID externo contextual de carta construido explícitamente `swsh3-136`; fuente, commit, path, SHA-1 blob y SHA-256 contenido, política/extractor versionados, selector, idioma y tiempos de captura. Exclusión por defecto de TODO campo no enumerado: imágenes/URLs, ilustrador, efectos, ataques, descripciones, variantes/finish, precios, stock, sealed, conteos, `updated`, marketplace IDs, etc. Fuente original solo transitoria, nunca fixture/log/DB íntegro. No converter número de carta a int; conservar ceros/prefijos en pruebas sintéticas. `releaseDate` es fecha declarada, no instante ni garantía de estreno España.

La carta tiene `variant=unknown`; no derivar normal/reverse/holo de disponibilidad; con manifest actual puede quedar candidata `unknown_variant`. Sets se aceptan solo con binding curado explícito consistente; ningún hash, nombre ni ID proveedor origina UUID CMT.

## D. Diseño y workstreams con ownership

Engineering Lead coordina Git y PR, contratos compartidos, integración, versionado, CI y revisión de evidencias. Antes de paralelizar, publicar `docs/phases/P1B_OWNERSHIP.md` con dueño de cada ruta, agentes concretos y límites de independencia. **Author ≠ QA ≠ REVIEWER**. QA y REVIEWER no editan código autor. Permitida concurrencia para investigación read-only o módulos con ownership de archivos disjunto; serializar modificaciones a `sqlite_repository.py`, `schema.py`, `cli.py`, contratos comunes, workflow, lock y Git.

- **ARQ/DB-OWNER (autor de diseño/migración):** ADR de admisión real estrecha, SQLite schema v2, preservación byte/lógico de historia v1, preflight, backup, transacciones, replay, constraints, consultas consistentes y reversión. Owner único del storage tras acordar interfaces.
- **INTEGRATIONS/DATA (autor del source bundle/adapter):** ledger de adquisiciones, extractor TS no ejecutable, política fija y digests, adapter offline a `Observation`, evidencia de campos, aviso MIT. Sin acceso simultáneo de edición a storage.
- **SEC/SRE (análisis/revisión específica y, si se justifica, rutas propias):** threat model, trusted paths, límites y denegaciones, logs redacted, migración interrumpida, offline builds y UID10001; no suplantar revisión QA final.
- **Engineering Lead/BE integrador:** frontera de admisión, CLI, contratos versionados, harness, wiring e integración de pruebas, resolviendo posibles cambios de ownership mediante coordinación explícita.
- **QA (independiente):** contraste independiente de artefactos/adversariales, migración/recuperación/fixtures no autoradas por QA, ejecución y resultados sobre SHA exacto.
- **REVIEWER (independiente de QA y autores):** auditoría final de cambios, ACs, exposición de datos, seguridad, contratos, coherencia del árbol y CI exactos.

No es obligatorio multiplicar agentes por número de módulos; combinación de especialidades de autor permitida, nunca combinar autores con QA/REVIEWER. Registrar límites reales de delegación y selección de modelos sin inventar ejecuciones.

## E. Invariantes de implementación

Flujo: `Pinned GitHub artifacts (engineering only) -> non-executing deterministic extractor -> approved minimal bundle + reviewed policy/lock -> validated source model -> normalized Observation -> curated manifest resolver -> narrow real-admission boundary -> SQLite schema v2`. El runtime/CI trabaja **sin red**. La ausencia de llamadas externas en CI debe quedar probada por harness/entorno.

1. **Extractor:** gramática restringida que identifique inequívocamente propiedades en su posición estructural aprobada; rechazar expresiones ambiguas, duplicados, imports distintos, sintaxis incompatible, TS ejecutable o incompleto. Sin `eval`, `exec`, compilador, Node ni imports dinámicos. Hash Git blob SHA-1 calculado a partir de `blob <n>\0<bytes>` separado de SHA-256 de contenido; verificar ambos. Ledger por campo con posición, transformación y versión; QA valida contra original.
2. **Paquete/política:** declarar versión y formato estricto, listado exacto de archivos y digests, proyección normalizada mínima + digest, aviso MIT y timestamps verificables. Nunca aceptar autoridad porque un JSON del usuario diga `observed`, tenga hashes calculados por él o cambie el path. El paquete/política autorizados deben quedar anclados a artefactos **revisados dentro de la distribución/codebase** (por ejemplo constantes/digests protegidos por revisión), verificarse en la API pública y en almacenamiento. Un objeto Python manufacturado tampoco debe eludirlo. Hash = equivalencia/integridad, **no** autenticación de productor externo ni verdad del producto.
3. **Identidad:** namespace separado `tcgdex_repository`, referencia exacta con idioma y variant; commit es procedencia de la captura, no parte de identidad estable. Preservar UUIDs curados, nombre nunca matching, sin fallback ES/EN y sin promoción. Sets ES y EN requieren bindings explícitos; si no existen, quedan candidatos y deben registrarse honestamente; no crear bindings automáticamente.
4. **Compatibilidad:** mantener exactamente `PERSISTENCE_V1` y sus entrypoints synthetic-only; no aflojar enum/provenance ni reinterpretar documentación `documented` como permiso. Preferir nueva API/contrato dedicado a real autorizado. No recalcular fingerprints históricos v1, ni re-resolver contra manifest posterior. Conservar literal los contratos v1 como historia.
5. **Captura:** identidad estable de lote; política/extractor; fuente/método `pinned_repository_bundle`; commit/paths/blobs/digests; namespace, kind, ES/EN y selector por unidad disjunta; paths selected/completed, resultados/contadores y verificación; adquisición vs captura declarada en UTC vs primera persistencia local; estados `verified_local_pinned_bundle`/`legacy_unverified`/producer attested claramente distintos. Scope válido también con cero observaciones en casos **genéricos sintéticos de prueba**, jamás con falta de una traducción/artefacto real. Vacío legítimo ≠ error/partial/rejected; selección incompleta no prueba ausencia.
6. **SQLite v1→v2:** migración explícita y versionada, nunca auto-migrar en `read`, `verify` o `init` sobre DB v1 existente. DB futura/no soportada y schema manipulado fallan. Preflight fuerte, copia de seguridad anterior validada y destino exclusivo, migración transaccional, rollback de fallos inyectados y recuperación reproducible. Preservar entidades/UUIDs/timestamps/registros/fingerprints y tokens v1; no inventar scope legacy y mantener `request_attested_empty` como límite histórico. Nuevas capturas v2 inmutables y vinculadas a registros en FK/constraints. Reimport con mismo token/contexto devuelve `replay` 0 mutaciones, diferencia en política, bytes, selector, timestamps, manifest, resolución o proyección implica conflicto sin sobrescritura. Consultas scope + observaciones usan una sola transacción snapshot; verify/backup/restore protegen relaciones y corrupción sin lectura ilimitada. No reconstruir v1 desde un export ruidoso.
7. **Discovery:** P4a debe fallar si algún lote solicitado tiene `observed` o mezcla, aunque existan filas synthetic; no devolver subconjunto filtrado que aparente comparabilidad completa.
8. **Seguridad/observabilidad:** validaciones de bytes, nodos, profundidad, cadenas, count, timeout/lock y paths; source never follows input-provided URL/path. Logs estructurados con run ID, duración, contadores, categorías fijas, **sin** payload, nombres, rutas arbitrarias, URL, SQL, lotes, secretos ni excepciones crudas. Stdout de consulta puede contener campos contratados, limitado. Riesgos: spoofing de provenance, tampering policy/lock, migración interrumpida, scope falsamente completo, corrupción, disco lleno, lock, trusted dirs y ARM64.

## F. API/CLI y compatibilidad

Primero formular en ADR y data contract `PINNED_REPOSITORY_BUNDLE_V1` + `CAPTURE_SCOPE_V1`/`STORAGE_V2` (nombres sugeridos, no renombrar contratos históricos), con schema exacto, estados, enum, límites, códigos de error y semántica de consulta. Definir CLI clara y mínima (por ejemplo `cmt bundle verify`, `cmt bundle import`, `cmt captures`, `cmt db migrate`), pero **elegir comandos conforme al parser existente** y documentarlos; el contrato no impone nombres. Los comandos existentes `cmt persist`, `cmt catalog`, `cmt observations`, `cmt discover`, `cmt db init|verify|backup|restore`, `version`, `diagnose` conservan códigos y resultados synthetic soportados. Leer DB v1 y v2, con comportamiento explícito, sin auto-upgrade. Evitar complejidad nueva, PostgreSQL/ORM/event store y runtime HTTP.

El código existente a inspeccionar primero: `catalog/ingestion.py`, `catalog/manifest.py`, `catalog/resolver.py`, `catalog/adapters/tcgdex.py` (**ruta REST diagnóstica, NO adaptador productivo de este paquete**), `persistence/input.py`, `persistence/application.py`, `persistence/schema.py` (SCHEMA_VERSION=1), `persistence/sqlite_repository.py`, `discovery/comparison.py`, `discovery/input.py`, `cli.py`, `scripts/*smoke*`, `compose.yaml`, `.github/workflows/ci.yml`. No copiar/ejecutar upstream ni reusar sin acreditación el parser diagnóstico P0.5b.

## G. Orden de ejecución recomendado

1. Preflight remoto y local; registrar Git ownership, baseline y desvíos; archivar contrato íntegro, brief y decisiones del Orchestrator en roadmap.
2. Elaborar contratos/ADR detallados **antes** de fijar esquema/CLI; ARQ/DB-OWNER y SEC revisan invariantes, compatibilidad y recuperación.
3. Reservar ledger de ocho solicitudes y ejecutar cuatro lecturas fuente fijadas secuencialmente (o caché de bytes verificables). Extraer proyección; QA reserva sus lecturas de contraste y verifica independientemente los cuatro artefactos. Publicar proyección mínima y MIT íntegra.
4. Implementar adaptador offline y tests de shape, números, idioma, relación, metadatos y falsificación; medir variación de manifest curado sin inventar aceptación.
5. Implementar frontera autorizada separada de synthetic-only; tests direct-object/repository/storage bypass y de adulteración de lock/artifact/proyección.
6. Implementar migración v1→v2 y nuevos scope/storage operations; exigir backup anterior y fault-injection; tests con SQLite real antes de integración CLI.
7. Integrar CLI + harness offline de procesos independientes, incluir en wheel, Compose y ambos contenedores. Preservar todos los harnesses anteriores.
8. Completar threat model, runbooks, documentación de fuente/política, technical debt, arquitectura, ADR, contratos y gates. No declarar TD-005 cerrada por nuevas capturas: la historia legacy y productores independientes siguen limitados.
9. Construir candidato congelado SHA/árbol; ejecutar gates locales y PR CI. Separar QA y REVIEWER exact-SHA; resolver hallazgos y repetir revisión/CI en SHA final.
10. Abrir PR **sin merge**; publicar ledger externo que enlace base/head/tree, logs completos de jobs/steps, AC-I01..I16, revisiones, derechos, permisos y limitaciones. Entregar Completion Report para el Phase Lead, nunca autodeclarar cierre.

## H. Pruebas obligatorias y evidencia

- **Fuente/contrato**: paths/commit/blob/SHA256 incorrectos, campos prohibidos, instrucciones TS ejecutables, imports extra/alterados, dup keys/ambigüedad, UTF-8 incorrecto, budgets, reformat semántico no soportado, scopes sin ES o EN, objeto Python forged, JSON self-attested, prueba sin red, MIT notice intacto.
- **Normalización/resolución**: cuatro proyecciones exactas; release date nullable/calendario; no fallback; número textual con `001` sintético; finish unknown; set binding curado coherente vs sin binding; carta candidate `unknown_variant`; contradicciones, duplicados, no CMT ID generado.
- **SQLite real**: v1 existente + v1 vacía; v1→v2, no migración implícita; futuro/foreign schema; backup verificado, destino ya existente, sidecars/locks; write rollback; interrupción fault injection, cierre/reapertura; contenido v1 exacto y hashes conservados; scope legacy/vacío/rechazos; FK/constraints/manipulación; replay/context conflicts; snapshot consistente bajo escrituras concurrentes, restore v1/v2.
- **CLI**: DB nueva y migrada, import, consultas y nuevo proceso, repetición de token y conflicto sin mutación; persist synthetic aceptado, observado rejected en v1, Discovery observado/mixto rejected; errores no imprimen data sensible.
- **Producto instalable**: suite completa, wheel instalado fuera del checkout, Compose, AMD64, ARM64/QEMU UID10001, fixtures read-only y `network_mode: none`. Harness P1b entre **procesos** (no solo invocaciones dentro del mismo Python).

Gates, todos PASS/FAIL con SHA final y evidencia:

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

Conservar y extender scripts Compose/AMD64/ARM64 y los cuatro jobs CI (Quality, Compose, AMD64, ARM64/QEMU). Cobertura total de código propio **≥85% líneas y ≥80% ramas**. No bajar thresholds, quitar regresiones ni sumar skips estratégicos. Auditar dependencies/runtime, licencia, secreto, SEC/SRE/ARQ/DB. QEMU no prueba fallos de energía ni hardware Pi real. Un gate no ejecutado **es FAIL**, no N/A. 611 tests/1 skip/97.79%/94.43% corresponden al baseline histórico, NO a P1b.

## I. Acceptance Criteria y documentación exigida

Rastrear individualmente **AC-I01..AC-I16** contra tests, archivos, logs, revisiones y enlaces (usar el texto íntegro del contrato, no reformularlo para rebajar condiciones). Documentar en `docs/phases/` el contrato, brief, ownership y Phase Completion Report. Crear ADR significativa de ruta, frontera de autorización y migración; contracts versionados de paquete/scope/schema; documentación de fuentes, licencia, evidence+request ledger, amenaza, deuda, arquitectura, roadmap, pruebas, gates y runbooks. Mantener `AGENTS.md` como mapa corto. El rechazo de una fuente o una captura completa falsa debe quedar como un error, **nunca cero resultados**.

El reporte final deberá incluir Phase, Proposed Status, Branch/PR/Commit, **MODEL PROFILE USED**, especialistas y ownership, objetivos, implementado, arquitectura/ADRs/data contracts/DB, source rights, cambios threat-model/deuda, observabilidad, pruebas, gates PASS/FAIL, ACs, límites, issues, SHA/tree/CI/revisiones exactos y recomendación.

**Regla final:** no afirmar `READY_FOR_ORCHESTRATOR_REVIEW` hasta que todos los gates obligatorios estén PASS y QA/REVIEWER independientes hayan confirmado el mismo candidato SHA/árbol. En bloqueo, entregar estado **BLOCKED**, motivo y acciones concretas. Nunca `ACCEPTED`, `PHASE CLOSED` ni ejecutar merge sin autorización posterior expresa del Orchestrator.
