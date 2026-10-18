# MODEL PROFILE

- **ChatGPT / Phase Lead recomendado por el contrato:** GPT-6.1 Sol / High en ChatGPT Work **si figura realmente en el selector**; en Chat normal, GPT-5.6 Sol / High si está disponible. Motivo: revisión de autorización, procedencia, identidad, comparabilidad y compatibilidad entre fases. El Phase Lead de este chat opera con GPT-6; no puede cambiar ni verificar el selector de otro cliente.
- **Codex / Engineering Lead:** GPT-6.1 Sol / Medium **si está disponible**. Medium para coordinación y tareas mecánicas; **High** para contrato, admisión, identidad, integridad, read transactions y debugging difícil.
- **Especialistas Codex:** INTEGRATIONS/DATA, ARQ/DB-OWNER y BE/DISCOVERY en High cuando lo justifique la decisión. SEC/SRE revisa confianza, logs y recuperabilidad; DOCS mantiene las decisiones. **QA y REVIEWER deben ser distintos entre sí y de los autores**, preferiblemente High, y revisar el SHA/tree final exacto.
- **Escalado:** primero High; una opción superior (GPT-6 Astra / High, solo si existe en el selector) ante un bloqueo complejo reproducido. No inventar modelos disponibles, ni usar Max/Ultra por defecto. Registrar modelo/reasoning solicitados, seleccionados y realmente observables por rol.

# ENGINEERING BRIEF — P1c Multi-Revision Metadata Capture

**Fecha y autoridad:** 2026-10-17, Europe/Madrid. Emite P1c Phase Lead bajo el contrato de **00 — ORCHESTRATOR**.  
**Repositorio:** `KastaTM/card-market-tracker` — https://github.com/KastaTM/card-market-tracker  
**Baseline autorizado:** `112916382ce02486ca38eb14487220dbb24196e7`, árbol `c79edde3f13c5983d11505f5917f91559265b506`.  
**Padres del merge previo:** base `430e2049c9ffdffb68508329df6556bfed62baa2`, head `ab5e0fa7d4225c2ce137ce2261cd9686ef765a32`.  
**P4b:** PR #10 fusionado, CI histórico push/main https://github.com/KastaTM/card-market-tracker/actions/runs/39040138813. Histórico no equivale a gates P1c.  
**Rama P1c:** `feat/p1c-multi-revision-metadata-capture` (no encontrada en búsqueda remota durante el preflight del Phase Lead).  
**Contrato vinculante:** `P1C_MULTI_REVISION_METADATA_CAPTURE_CONTRACT.md` suministrado por el Orchestrator. Archivar su contenido íntegro en `docs/phases/P1C_MULTI_REVISION_METADATA_CAPTURE_CONTRACT.md`, sin modificar alcance. Este brief **no sustituye** el contrato.

## 0. Mandato y condiciones de parada

Implementar dos capturas reales, estrictamente revisadas, de los mismos dos artefactos TCGdex en revisiones Git diferentes, persistirlas en SQLite schema2 y añadir una ruta **DISCOVERY_V3** para compararlas bajo un perfil semántico aprobado. R0 y R1 deben producir cuatro unidades iguales en proyección y, comparadas R0→R1, `no_discoveries` y cero eventos. **No generar novedad ficticia**; positivos solo con fixtures sintéticas. 

Autorizado: investigación de ingeniería delimitada, solicitudes R1 permitidas, implementación, branch, tests, PR y evidencias. **Prohibido merge** sin autorización exacta del Orchestrator; no declarar `ACCEPTED`, `PHASE CLOSED`, ni abrir fase sucesora.

Fuera de alcance: tercera revisión, ampliar corpus/paths, REST/SDK, proveedor nuevo, crawlers/scheduler de producción, schema3/migración, event store, API/UI, retail, precios, stock, preorders, alertas, nuevas identidades canónicas/printings, promoción de candidatos y nuevas fuentes. P2, P6a y retail Discovery continúan BLOCKED; Scrydex no autorizado para la ruta EUR.

Si surge un cambio de alcance, **parar y elevar al Orchestrator**. Si un gate no es verificable, registrarlo FAIL/BLOCKED, nunca PASS inferido.

## 1. Preflight reproducible antes de editar

El Phase Lead confirmó por GitHub que `main` remoto = baseline y PR #10 merged, tree y padres como arriba. También inspeccionó el árbol remoto, `AGENTS.md`, roadmap, ledger P1b, bundle v1, archivos de persistencia/discovery, CLI y contratos de almacenamiento/Discovery v2. **No se ha verificado el checkout local ni ningún worktree; hacerlo primero.** No asumir que el directorio local siga en la ruta de fases previas.

```bash
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

Verificar remote correcto, worktrees, cambios no propios, refs y acceso. No reset, force-push, borrado de ramas o modificación de trabajo ajeno. Si `main` difiere, inspeccionar y comunicar delta; nunca rebasar silenciosamente el contrato. Abrir rama propia desde baseline verificado y registrar HEAD inicial/tree; no compartir edición de archivos entre agentes paralelos.

Antes de planificar cambios, leer `context.md`, `AGENTS.md`, `docs/ENGINEERING_OPERATING_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/QUALITY_GATES.md`, `docs/TESTING_STRATEGY.md`, `docs/CODING_STANDARDS.md`, `docs/TECHNICAL_DEBT.md`, `docs/threat-model/THREAT_MODEL.md`, ADR-0003–0007, contratos bundle v1, CAPTURE_SCOPE_V1, STORAGE_V1/V2, DISCOVERY_V1/V2, docs/sources/P1B_FIELD_LEDGER.md, los runbooks y suites/CI existentes.

Archivar el contrato. Actualizar roadmap con **P4b cerrado/P1c abierta por decisión del Orchestrator en chat**, enlazando PR #10, CI, commit/árbol y reporte de integración. No inventar cierre publicado en comentario GitHub. `AGENTS.md` sigue siendo mapa conciso.

## 2. Fuente exacta, autoridad de datos y presupuesto

Única fuente `tcgdex/cards-database`. **R0** `4199850a6af49665db0080fa2bb9ef751750a406` se reutiliza sin recaptura ni cambio de fechas. Su package SHA-256 es `3b43e1a78c117ef1ecb5cf200a4b2fc7e57af8fd29e3fcf29b06f4291ae58085` y su proyección SHA-256 `53100248a987378fb3ca2273b7ec219747b876b515f57087faf6becdd0caa479`.

**R1** `af57972e8f784c2507ab9e573c99bf02ae2e5e42`: exactamente los siguientes cuatro paths, con Git blob SHA-1 exigidos:

| Orden | Path | Blob SHA-1 |
| --- | --- | --- |
| 1 | `data/Sword & Shield/Darkness Ablaze.ts` | `db48bc4a054b3b1c5bd2b6956257f20ba251c79c` |
| 2 | `data/Sword & Shield/Darkness Ablaze/136.ts` | `6db89c69b56552fa4e09f26e0e90d14e97466411` |
| 3 | `LICENSE` | `c67ded0d5f0abc77b4fbdbfd37312f2a88de1b55` |
| 4 | `README.md` | `77bc8108c2cdb54c663e1fdf8c4502ac65f88734` |

R0/R1 tienen **blobs iguales para estos cuatro paths** según contrato. R1 nueva revisión ≠ nuevo contenido seleccionado. Verificar bytes, UTF-8, tamaños, `sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw)` y SHA-256 original. Contrastar de manera independiente campos, relación, spans UTF-8 y MIT; no tratar las afirmaciones previas del Orchestrator como ejecución de ingeniería. No perseguir otra revisión ni enumerar corpus. No Node/eval/exec/compilador ni parser diagnóstico como autoridad de admisión; reutilizar extractor P1b no ejecutable.

**Presupuesto de fuente nuevo total = 12 solicitudes secuenciales** con ledger único para ingeniería+QA, incluyendo retries/redirects como corresponda: hasta 8 lecturas de contenido R1 (4 ingeniería + 4 QA si necesita readquisición) y hasta 4 consultas Git metadata/recovery. La consulta previa del Orchestrator no cuenta como ejecución de fase. No gastar presupuesto sobrante de fases anteriores. Las lecturas del Phase Lead a *CMT repo* no fueron adquisiciones de la fuente TCGdex; contador R1 hasta este handoff: **0**.

Solo GitHub/raw GitHub a esas revisiones/paths. No clonar el repo upstream, no seguir links del payload. Registrar cada solicitud, propósito, ruta, revisión, timestamp UTC inicio/fin real, tamaño/digests/resultado y cuenta de presupuesto. Definir captura R1 a partir del final efectivo de adquisición completa (no fecha de commit). Importación tiene tiempo distinto y no cambia captura. Si se reutiliza caché, declarar caché/procedencia/tiempo original, no simular fetch. Los tiempos son declaraciones locales verificables por ledger, no sellos del proveedor.

Allowlist exacta: set `id`, `name.es/en`, `releaseDate`; card `name.es/en`, número textual `136` desde filename, `set` explícito y su parent import, external ID `${set.id}-${stem}`. Cuatro proyecciones: set ES/EN y card ES/EN. Namespace `tcgdex_repository`, `unknown_variant`, UUIDs curados existentes. Set necesita binding coherente; card puede permanecer candidate. Prohibido conservar imágenes, logos, descripciones, ataques, otras lenguas, terceros, precios, stock, `updated`, variantes o datos fuera de allowlist. Originales TS/README temporales: al finalizar contraste, borrarlos y dejar constancia sin incluir sus cuerpos en Git, logs, DB, fixtures ni PR. Mantener el aviso MIT completo; no extrapolar licencia a imágenes/marcas.

## 3. Ownership y estrategia de ejecución

**Engineering Lead** hace preflight, mapa de archivos, dependencias, orden, integración y validación final. Agentes se asignan archivos exclusivos; análisis read-only en paralelo sí, edición concurrente del mismo estado no.

| Rol | Ownership principal | Secuencia / condición |
| --- | --- | --- |
| INTEGRATIONS/DATA (autor A) | Adquisición R1, hashes, parser P1b, mínima proyección, notice y ledger | Primero; coordinar lock final con QA antes de aprobar |
| ARQ/DB-OWNER (autor B) | Contrato bundle v2, registro de paquetes code-controlled, admisión, envelopes, persist/verify/query/replay/backup | Tras fijar lock R1; integra interfaces compartidas secuencialmente |
| BE/DISCOVERY (autor C) | Perfil comparabilidad y `DISCOVERY_V3`, validación/snapshot/query-only/transacción, cmp3/evt3 | Contrato/perfil estables antes de editar las interfaces compartidas |
| SEC/SRE | Amenazas, bounds, permisos, logs, recuperación, container/ARM64 | Revisión read-only y hallazgos dirigidos al Lead |
| DOCS | ADR y contratos versionados, runbooks/roadmap/gates/technical debt | Archivos propios, tras estabilizar decisiones |
| QA (no autor) | Extracción independiente, pruebas adversariales, integración, ejecución de gates candidato | Debe contrastar R1 por método independiente antes de freeze |
| REVIEWER (no autor ni QA) | Auditoría final de arquitectura, tests, datos, scope y SHA/tree final | Después del freeze, cualquier cambio obliga a revalidar |

Evitar trabajos paralelos sobre `capture.py`, `sqlite_repository.py`, `cli.py`, registry/locks y contratos compartidos. Declarar ownership final por paths en `docs/phases/P1C_OWNERSHIP.md`.

### Paquete y admisión

1. Mantener **exactamente** bundle v1, fixture, digest y API P1b. Introducir `PINNED_REPOSITORY_BUNDLE_V2` (o versión inequívoca equivalente), paquete R1 mínimo y registry de confianza **en código/configuración revisada**, con entradas exactas para R0/R1: revisión, política, extractor, paths, digests, projection, licencia, timestamps. Registry externo pasado como request NO admite paquetes. Alteraciones, un tercer commit, autodeclaración `observed` y `VerifiedBundle` forjado deben fallar antes de escribir.
2. Preservar API synthetic-only `PERSISTENCE_V1`, namespace, unknown_variant y UUIDs. Publicar entrypoint/CLI versionados, sin abrir v1/v2 por fallback ni cambiar hashes anteriores.
3. Schema SQLite sigue siendo **2, mismas cinco tablas**. Extender/adaptar envelope y decodificación de forma versionada si realmente necesario: `capture._bundle_batch`, `_check_capture`, `persist_bundle`, reader, verify, backup/restore deben reconstruir la variante aprobada; revisar `persistence.application`, `input`, `capture_decode`, `sqlite_repository`. No duplicar validador permisivo. Verificar íntegramente manifest/parent closure/resolution/rows/snapshot de **todos** los batches incluso fuera de la selección. Rechazo antes de retención y transacción atómica.
4. Replay: mismo token+contexto+bundle/evidencia → sin writes, aunque instante de nueva importación difiera. Token igual + contexto diferente → conflicto. Revisiones, artefactos, captura, manifest, snapshot siguen en fingerprint; perfil de comparabilidad **no** los elimina. Históricos no se reetiquetan ni re-resuelven con manifest actual.

### Comparabilidad v3

5. Perfil revisado, p.ej. `tcgdex_swsh3_136_r0_r1_v1`, asociado a registry exacto; pertenencia verificada desde paquete almacenado, nunca por request o hashes autodeclarados. Exige mismo repositorio/evidence family/namespace/kind/idioma exacto, selector y paths autorizados, allowlist y transformación, complete/no rejects y memberships R0/R1. Revisión, blobs, hashes y tiempos pueden diferir **solo** entre los miembros autorizados; nunca desaparecen de la evidencia de comparación/replay.
6. Nuevo contrato `DISCOVERY_V3` y entrypoint explícito (p.ej. `discover-multi-revision` con `version:3` + `profile`), sin cambiar `discover-scoped` v2. Mantener exactitud de límites: una unidad por batch, ≤32 history/33 batches/33000 filas/1000 eventos, límites JSON/lexical previos, 2s default/5s max.
7. Lectura SQLite: **una sola conexión** de solo lectura `query_only`, **una transacción explícita** y snapshot coherente de ventana completa (todas las unidades/envelopes verificadas). No escrituras/migración/reparación en comparación. Validación bytes/tokens antes de materializar; integridad del conjunto, no solo de la unidad seleccionada. Un error produce FAIL categorizado, nunca `no_discoveries`.
8. Comparador puro, sin SQLite ni lógica de proveedor, reutilizando algoritmo v2 cuando es seguro. Unión histórica accepted/candidate; duplicados idénticos colapsados con índices originales, contradicciones rechazadas; novedad de set aceptado o candidato en ausencia de historia. No eventos para eliminación, metadatos modificados, stock, launches o precios.
9. Cronología por **captured_at original**: R0 antes de R1; R1→R0 inválido; igualdad temporal entre history y current inválida; history-history empates permitidos. Reimport no cambia timestamp. Identidades `cmp3:`/`evt3:` canonicalizadas y versionadas con perfil + evidencia relevante. Excluir run ID/path DB/insert time, pero incluir revisiones y capturas. Mantener cmp1/evt1/cmp2/evt2 estables.

## 4. Pruebas mínimas (AC-M01…M16)

**Fuente/contratos:** validar SHA-1 Git, SHA-256, tamaños, UTF-8, spans y MIT por segunda vía; negar campos extra, hashes alterados, timestamp/revision/policy falsos, paquetes desconocidos, payload registry fake y objetos Python forjados. Reutilizar límites parser no ejecutable. R0 permanece byte/semánticamente igual.

**SQLite:** DB nueva y migrada previamente por ruta aceptada, ambas capturas; replay vs conflicto; fallo atómico, captura reimportada sin redatación, verificación de todas las filas/envelopes/manifest/parent closure; corruption in non-selected unit; query/read/backup/restore; concurrencia y read snapshot; límites deadline/lock; no writes en v3.

**Real E2E offline:** conservar el R0 original y almacenar R1 revisado; cuatro comparaciones separadas R0→R1 (set es, set en, card es, card en), resultado `no_discoveries` y cero eventos. Dos variantes de manifest: sin bindings y con set curado/bindings coherentes. Card `unknown_variant` candidate. Prueba invertida R1→R0 debe fallar, igual timestamp no crea temporalidad, selección/perfil extraño falla. V2 no admite R1 por accidente.

**Synthetic adversarial:** nuevos sets/cards, alias, candidate→accepted, cambios de metadatos sin novedad, reaparición, empty `producer_declared` complete, partial/failed/rejected, scope mezclado, duplicados contradictorios/idénticos, tercer paquete, batch forgery, identidades deterministas e invariancia ante orden histórico/replay/restauración. No publicar synthetic como observed real.

**Compatibilidad:** resultados/hash golden v1/v2, PERSISTENCE_V1 synthetic-only, bundle v1, migrations y history intactos. Mantener cinco harnesses y añadir sexto en wheel, Compose, AMD64, ARM64/QEMU (sin afirmar hardware Pi): procesos separados import/read/compare/replay/copy/reopen; usuario UID10001, fixtures read-only, runtime sin red y datos privados. Wheel instalado fuera de checkout.

**Calidad y seguridad:** `uv sync --frozen` o equivalente del repo; `ruff format --check`, `ruff check`, `mypy --strict`, suite completa pytest (unit/integration/contract/regression/security/concurrency), cobertura propia ≥85% líneas/≥80% ramas, sdist/wheel externo, dependency audit, secret scan granular sin supresión general, revisión de arquitectura/DB/SEC/SRE/docs, CI `Quality`, `Compose`, `container linux/amd64`, `container linux/arm64` con logs completos para SHA final. No borrar tests, bajar thresholds ni añadir skips de conveniencia.

## 5. Documentación y observabilidad

Entregar `docs/adr/0008-...md` si es el siguiente libre, con Context/Decision/Alternatives/Consequences/Status/Revisit conditions; bundle v2, registry y perfil, contrato `DISCOVERY_V3`, ledger R1, derechos por campo/disposición, actualizaciones en arquitectura, testing/gates, roadmap, source matrix, runbook multi-revision, threat model, deuda y CLI. No alterar TD-001–TD-005 salvo evidencia y decisión documentada.

Logging estructurado: run ID, fase/operación, duración, categorías fijas, contadores adquisición/admisión/comparación; no datos TS/README, nombres, nombres de rutas/URLs, tokens, input crudo, SQL o exceptions crudas. Errores con counts null/events [] y exit codes versionados. Aclarar que source health ≠ cero descubrimientos, timestamp productor ≠ autenticación externa.

Amenazas a revisar: registry spoofing, third revision, poisoned package, forged evidence_state, falsa marca de tiempo, compatibilidad que borra provenance, lectura de mezcla temporal, corrupción fuera de selección, replay-false-novelty, agotamiento de recursos, permisos FS, caída de DB/disco, recuperación y serialización incompatible.

## 6. Gates de aceptación y freeze

Exigir PASS/FAIL explícito por AC-M01…M16 y por cada quality gate, enlazando pruebas, comandos, tiempo y artefactos. Para AC-M02/M03 QA debe contrastar R1 independientemente **antes del freeze de lock**. Al estabilizar branch, fijar commit SHA + Git tree. Ejecutar QA y REVIEWER independientes sobre ese candidato; cualquier cambio obliga a revisión/gates afectados otra vez. Comprobar PR head/base, CI exact-SHA y logs completos; no confundir CI previo de P4b con P1c.

**Punto de parada:** abrir PR, publicar Phase Completion Report con branch/PR/commit/tree/base; MODEL PROFILE USED y backend realmente observable, especialistas, arquitectura/ADRs/contratos/DB, source requests, hashes atribuidos a quien los calculó, threat model/deuda, pruebas, gates, AC-M01…M16, issues, limitaciones y recomendación. Cierre textual únicamente:

`READY_FOR_ORCHESTRATOR_REVIEW`

Si un AC obligatorio no tiene evidencia, notificar FAIL/BLOCKED con acción específica; no declarar listo ni fusionar.

## 7. Evidencia de Phase Lead (preparación, no implementación)

El 2026-10-17 el Phase Lead verificó por conector GitHub: `main` en `1129163...`, PR #10 merged, árbol `c79edde...`, padres base→head tal como arriba; rama P1c ausente en búsqueda remota. Se revisó estructura de repo (231 entradas), files anteriores y rutas de implementación. **No existe revisión del worktree local, no se ha creado rama/PR/commit, no se ha leído R1 durante esta preparación, no se han ejecutado tests P1c ni QA independiente.** Ledger de R1 para fase: cero solicitudes hasta este handoff. Los hashes fuente y la igualdad R0/R1 indicados arriba provienen del contrato del Orchestrator y P1b; Codex/QA deben verificarlos.
