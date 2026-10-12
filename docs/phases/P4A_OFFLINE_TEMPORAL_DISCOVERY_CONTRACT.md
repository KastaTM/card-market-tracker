MODEL PROFILE

- ChatGPT Phase Lead: GPT-6.1 Sol / High en ChatGPT Work, si está disponible en el selector. Para un chat normal, GPT-5.6 Sol / High si ese modelo está disponible. Motivo: definir correctamente novedad relativa, contexto, identidad, evidencia temporal y aceptación.
- Codex Engineering Lead: GPT-6.1 Sol / Medium para inspección, CLI, fixtures, documentación e integración; High para contrato de comparación, límites de lectura, identidad de eventos y revisión final.
- ARQ/DB-OWNER, DATA/DISCOVERY, SEC y SRE: GPT-6.1 Sol / High cuando su tarea concreta requiera diseño o revisión de riesgos. Roles de autor pueden combinarse.
- QA y REVIEWER: GPT-6.1 Sol / High, en agentes distintos e independientes de autores y entre sí; registrar selección solicitada, aceptada y alcance real.
- Escalación: aumentar a High para problemas de semántica o integridad. GPT-6 Astra / High solo para un bloqueo complejo persistente tras reproducción con Sol y si está disponible; registrar razón y resultado. No utilizar Max/Ultra por defecto.
- Confirmar los modelos realmente seleccionables. Este contrato recomienda configuraciones; no cambia el modelo del cliente ni acredita un backend efectivo. Si falta la opción recomendada, comunicar las disponibles y acordar un perfil equivalente antes de atribuir su uso; continuar inspecciones independientes.
- Fuentes oficiales consultadas el 2026-10-12: [https://learn.chatgpt.com/docs/models?surface=web](https://learn.chatgpt.com/docs/models?surface=web) y [https://developers.openai.com/api/docs/models/gpt-6.1-sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol). GPT-6.1 Sol pertenece a Work/Codex; no ofrecerlo como modelo de Chat normal.

# P4a — Offline Temporal Discovery: contrato y prompt de apertura

## Rol, autoridad y apertura

Actúa como Phase Lead de **P4a — Discovery temporal offline de sets y candidatos** de Card Market Tracker.

El Orchestrator abre P4a mediante este contrato el **2026-10-12, Europe/Madrid**. Traduce el contrato a un Engineering Brief para Codex local, coordina implementación y evidencias y devuelve un candidato al Orchestrator. Un Phase Lead puede declarar READY_FOR_ORCHESTRATOR_REVIEW; no puede aceptar, cerrar su propia fase ni abrir otras.

Repositorio: [https://github.com/KastaTM/card-market-tracker](https://github.com/KastaTM/card-market-tracker)\
Checkout local previsto: C:\Projects\card-market-tracker\
Rama autorizada: feat/p4a-offline-temporal-discovery

La apertura autoriza trabajo dentro del alcance y PR. **No autoriza merge.** La integración requerirá decisión del Orchestrator vinculada al candidato exacto.

## Baseline y decisiones del Orchestrator

P0, P0.5, P1a y P3a están ACCEPTED / PHASE CLOSED. P3a se cerró el 2026-10-12 después de contrastar integración y CI push real.

| Objeto de P3a aceptado     | Valor                                                                                                                                                          |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PR fusionado               | [https://github.com/KastaTM/card-market-tracker/pull/6](https://github.com/KastaTM/card-market-tracker/pull/6)                                                 |
| Baseline y main comprobado | 734641a7ef920688677cdea6bc82f908a2856927                                                                                                                       |
| Árbol                      | ae61fe57e6f874b138c98ecdaaa8cbd830406354                                                                                                                       |
| Primer padre               | c6e66a2aba469d02f0ca63fde3b81ecc5eea41bc                                                                                                                       |
| Segundo padre              | e9c5f02e7f093dedff55b67f137c4446f22e8735                                                                                                                       |
| CI push del merge exacto   | [https://github.com/KastaTM/card-market-tracker/actions/runs/38302824438](https://github.com/KastaTM/card-market-tracker/actions/runs/38302824438)             |
| Ledger integración         | [https://github.com/KastaTM/card-market-tracker/pull/6#issuecomment-6131957615](https://github.com/KastaTM/card-market-tracker/pull/6#issuecomment-6131957615) |

Quality, Compose, AMD64 y ARM64 QEMU pasaron sobre ese merge. Los logs acreditan 411 pruebas, un skip de plataforma y cobertura 97,54% líneas / 94,14% ramas. Es evidencia histórica; no sustituye los gates P4a.

La publicación del cierre por el conector del Orchestrator falló con 403. **La decisión de cierre sí fue emitida en el chat**. Archiva este contrato y registra dentro de la rama P4a el cierre atribuido al Orchestrator, su evidencia y la apertura P4a en ROADMAP.md y mediante una nota histórica en el informe P3a. No reescribas sus resultados prepublicación ni inventes un comentario de cierre publicado. Si Codex tiene permisos de comentarios, puede registrar la decisión exacta en el ledger PR6; no es un gate que obligue a detener la fase si ese permiso falta.

Verifica remote, checkout, cambios previos y objetos Git antes de editar. Si main avanzó, compara el delta y los gates, comunica la diferencia y eleva un baseline que cambie dependencias; no sustituirlo silenciosamente. Preserva trabajo ajeno y ramas/worktrees; utiliza aislamiento cuando corresponda.

### Dependencias que permanecen bloqueadas

- TCGdex continúa provisional para metadatos. No hay permiso general de retención real ni cobertura comercial acreditada.
- P2 sigue BLOCKED por acceso, retención e interpretación de precios EUR.
- P6a y Discovery retail siguen BLOCKED por falta de fuentes compatibles.
- AC-F05 solo probó viabilidad exploratoria de catálogo por ID/enumeración ES, sin delta temporal real.
- P4a no consulta fuentes. Sus observaciones, fixtures y demostraciones son **exclusivamente synthetic**.
- QEMU, procesos terminados y fallos simulados no certifican Pi física ni durabilidad ante cortes eléctricos.
- TD-001–TD-004 siguen abiertas salvo evidencia que cumpla expresamente sus condiciones de salida.

Decisión de roadmap: P4a se adelanta a P2/P6a como núcleo offline que consume P1a/P3a. Se conserva el significado de los IDs de fase; no declarar implementado el P4 completo ni desbloquear las fases de fuentes.

## Objetivo

Construir una operación local reproducible que compare una captura sintética persistida con un conjunto explícito y acotado de capturas anteriores, y produzca evidencia de referencias de sets aceptados y de candidatos que no aparecen en esa ventana histórica.

La novedad es **relativa al historial suministrado y al contexto seleccionado**. No equivale a lanzamiento, producto recién creado, primera aparición mundial, oportunidad de compra ni primera aparición global en toda la DB.

## Dentro de alcance

1. Contrato versionado de solicitud, snapshots de lectura y resultado de Discovery temporal; ADR de semántica, identidad de eventos y fronteras.
2. Modelo de comparación independiente de SQLite, TCGdex y CLI. Reutiliza referencias contextuales/estados validados de P1a.
3. Lectura consistente, de solo lectura, de metadata de lotes y registros P3a necesarios para la comparación; incluye existencia de un lote vacío.
4. Comparación de una captura actual con una lista explícita de lotes previos y un único contexto declarado.
5. Señales para referencia de set aceptado nueva en la ventana y referencia candidata nueva en la ventana. Los candidatos pueden ser de los kinds existentes de P1a; no es Discovery retail ni validación de un sealed vendible.
6. Resultado con evidencia de lotes, captura, referencia, estado congelado y CMT ID únicamente cuando ya existe en la observación aceptada.
7. CLI instalada, JSON stdout, logging correlacionado, fixtures sintéticos y harness de escenarios positivos y negativos.
8. Regresión P0/P1a/P3a y nueva capacidad en wheel, Compose, AMD64 y ARM64 QEMU.
9. Documentación, roadmap, runbook, threat model, riesgos y deuda realmente pertinente.

## Fuera de alcance

HTTP, scraping, collectors, feeds reales, altas, compras, contactos, scheduler, monitorización continua, precio/stock, retail, anuncios de lanzamiento/preorder, Telegram u otra entrega, watchlist, ranking, analítica de mercado, API/UI, promoción/curación de candidatos y asignación de nuevos CMT IDs.

No escribir eventos, cursores, checkpoints, outbox ni tablas Discovery en SQLite. No cambiar el esquema STORAGE_V1 ni introducir migración en esta fase. No aplicar limpiezas, cuotas o retención destructiva. El almacenamiento durable de eventos/delivery pertenece a un contrato posterior.

No detectar desapariciones, retiradas o disponibilidad por ausencia; no emitir METADATA_CHANGED ni eventos de promoción. Cambios de nombres, fechas o binding no son por sí solos referencia nueva.

## Fronteras y contrato mínimo

Flujo: solicitud local estricta -> lectura P3a acotada/consistente -> snapshots genéricos verificados -> función pura de comparación -> resultado tipado -> JSON/logging.

Crear, por ejemplo, DISCOVERY_V1 y una ampliación compatible documentada del contrato de lectura STORAGE_V1. El nombre de archivos/API final puede decidirlo ARQ. No retrocambiar salida o códigos existentes.

### Solicitud

Una petición JSON local versionada contendrá exactamente los campos definidos por el contrato: versión, current_batch_id, history_batch_ids y context. No incluir rutas/SQL/URLs dentro del contexto; la ruta DB se proporciona por CLI.

- UUIDs con validadores canónicos existentes; version nunca bool.
- Máximo **32 lotes anteriores**, sin IDs duplicados; captura actual distinta de los anteriores.
- Cada lote tiene máximo 1.000 registros según P3a; máximo 33.000 registros leídos por operación. Eventos como máximo 1.000; strings/profundidad/nodos/bytes de JSON mantienen los límites P1a.
- Contexto exacto: namespace, kind y language, incluyendo null como valor exacto, nunca wildcard. Variants pertenecen a la clave de referencia, no se colapsan.
- Todos los registros admitidos de cada lote deben pertenecer al contexto declarado. Este núcleo no acepta un lote multicontexto para filtrarlo silenciosamente; requiere capturas homogéneas para que el cero sea interpretable.
- Orden de history_batch_ids irrelevante; canonizarlo para determinismo.
- Todos los previos deben tener captured_at estrictamente anterior al actual; timestamps UTC normalizados. Dos lotes distintos pueden compartir captura histórica; actual no puede tener el mismo instante que un previo.
- Lote inexistente es error; lote vacío existente es evidencia de captura vacía con contexto declarado por el productor, no evidencia de la salud de una fuente.
- Solicitud sin historia válida es bootstrap: resultado explícito baseline, sin eventos de novedad. Capturas históricas vacías existentes sí constituyen una ventana explícita.
- Ningún token, captura o fecha se infiere del reloj de ejecución.
- Aceptados/candidatos solo synthetic. Un lote con rejected_count > 0 no es elegible: error de evidencia incompleta, sin eventos parciales. Un lote con candidatos y cero rechazos sí es elegible. No convertir 'todos rechazados', error DB o captura inexistente en snapshot vacío.

Los límites son budgets, no objetivos de escala. La lectura mantiene timeout global finito y no crea DB ni inicializa/migra esquema. Si un uso legítimo exige más historia, elevarlo; no eliminar el límite.

### Snapshot seguro y consistente

La query P3a devuelve como máximo 1.000 filas y no distingue por sí sola un lote vacío de uno inexistente. **No tratar ese stdout como prueba completa de existencia o metadata.**

Se permite añadir una pequeña API pública de lectura de snapshots de lotes que consulte sus metadata y registros en una **misma transacción de lectura**, usando una conexión mode=ro/query_only. Debe validar ownership/schema, versiones, enums, captura, procedencia, índices y coherencia de contadores/filas. No tomar metadata y filas de conexiones independientes y afirmar coherencia transaccional.

La API devuelve valores genéricos; Discovery no conoce nombres de tablas ni SQL. Dominio P1a y resolver no importan SQLite. No introducir una interfaz abstracta vacía o backend múltiple para un único consumidor.

Conservar cierre/rollback, timeout/lock budgets globales, parámetros SQL, límites y rutas existentes. Propagar categorías seguras; corrupción o incoherencia de snapshots no es 'sin novedades'. Para una lectura nueva de varios lotes, verificar sus metadata y filas en el mismo snapshot transaccional; documentar lo que integrity_check acredita y lo que la validación de negocio añade.

### Claves, novedad y duplicados

La clave de comparación es la referencia contextual completa validada: namespace, kind, external_id, language y variant. No usar nombre, SKU, fecha, índice, posición o hashes de payload como identidad CMT.

- La ventana histórica es la unión de referencias admitidas, aceptadas **y candidatas**, de todos los lotes previos seleccionados.
- Una referencia actual ya vista como candidata no es nueva al aparecer aceptada. Mantener el estado histórico congelado; no promoverla ni re-resolverla con un manifiesto actual.
- Reaparición tras una captura intermedia vacía no es nueva si sigue en la ventana seleccionada.
- Una referencia actual ausente de la unión previa es una primera observación **en esa ventana**.
- Una referencia nueva con CMT ID ya visto por otro external_id sigue siendo evidencia de nueva referencia, **no de nuevo producto canónico**. No inventar event product_new=true.
- Set aceptado y nuevo -> evento de referencia de set. Cualquier candidato nuevo -> evento de referencia candidata, incluido un candidato de kind=set; **solo un evento**, sin doble conteo.
- Referencias aceptadas de otros kinds no originan eventos en P4a, pero cuentan como vistas en su contexto para impedir falsas novedades candidatas.
- Registros idénticos duplicados dentro de un lote se agrupan por referencia, sin doble evento. Si una misma referencia presenta observaciones/snapshots incompatibles dentro del mismo lote, falla explícitamente; no escoger arbitrariamente una.
- Nombre/fecha cambiados con la misma referencia no generan novedad. Diferencias legítimas entre capturas no reescriben historia ni implican contradicción del lote.
- Una referencia que sale de la ventana seleccionada puede reaparecer como nueva respecto a la nueva ventana; declarar el alcance para evitar una garantía global falsa.

No existe baseline implícito, selección automática del 'último lote', scan ilimitado ni deduplicación perpetua.

### Resultados y reproducibilidad

Nombres recomendados: SET_REFERENCE_FIRST_OBSERVED y CANDIDATE_REFERENCE_FIRST_OBSERVED. Pueden ajustarse en ADR/contrato manteniendo la semántica de referencia/ventana; no usar NEW_SET con significado de lanzamiento real.

Resultado versionado contiene result (baseline/no_discoveries/discoveries/error o equivalentes documentados), contexto exacto, current_batch_id/captured_at, historia canonizada y cobertura de la ventana, contadores y eventos con evidencia.

Cada evento incluye tipo, referencia exacta, estado congelado, CMT ID nullable, lote/captura actual y evidencia necesaria para reproducir la decisión. first_observed_at significa mínimo en los lotes explícitamente suministrados, nunca primera persistencia local ni lanzamiento; nombrarlo de forma que ese alcance sea inequívoco.

Determinismo: misma solicitud y contenido DB -> mismo resultado semántico/event IDs/order, aunque cambien run_id/duración. Versionar la identidad de comparación y evento en ADR/contrato:

- event_id puede ser una huella determinista de versión/tipo/contexto/referencia/current batch/captura. Nunca es un CMT ID.
- comparison_id puede incluir la lista canonizada de historia y fingerprints de snapshots pertinentes.
- Mismo hallazgo actual con diferente orden de historia no cambia event_id; distinto contexto o captura debe distinguirse. Decidir qué cambio de ventana requiere comparison_id nuevo.
- Orden de eventos estable por la clave contextual; no incluir timestamps de ejecución ni run_id en identidad o salida semántica.
- Reejecutar produce los mismos eventos. **No implica exactly-once, entrega ni dedupe durable de alertas.**

La decisión ADR concretará canonización y hashes usando campos seguros/validados; no exigir un bus de eventos.

## CLI y operación

Definir una interfaz pequeña como:

cmt discover --db PATH --request REQUEST_JSON

Comando de solo lectura; request JSON conserva validación de bytes/estructura. Mantener stdout JSON y stderr logging separados, códigos documentados y probados: éxito baseline/no_discoveries/discoveries -> 0; entrada/contexto/cronología/evidencia incompleta -> 2; fallo local/DB/lock/corrupción -> 1, salvo alternativa justificada que no rompa comandos existentes.

No exigir un exportador con sobrescritura de archivos. Redirección de stdout es suficiente. No presentar salida del comparador como notificación enviada.

En contenedores: UID10001, fixtures read-only, sin networking. El harness primero siembra una DB sintética con comandos P3a en el volumen y luego compara desde **otra invocación**; demuestra que comparación no cambia tablas/versiones/snapshots mediante contenido verificado. mode=ro/query_only no exige montar el directorio entero read-only si SQLite necesita manejo operativo normal; explicar permisos/journal y no prometer recuperación de un hot journal sin escritura autorizada.

## Observabilidad, seguridad y fallos

Extender LOGGING_V1 de modo compatible para una operación Discovery: run_id, duración, resultado, error_category y contadores limitados (lotes/observaciones/eventos). Una falla no reporta cero novedades exitosas. Distinguir baseline, comparación válida sin novedades y error.

Logs no incluyen payloads, nombres arbitrarios, referencias/tokens, IDs de lotes, paths, SQL o excepciones crudas. Stdout puede incluir la evidencia mínima expresamente contratada. Validar también la nueva frontera Python: constructores tipados no constituyen validación.

SEC revisa request/IDs, SQL, fuentes synthetic, bounds/deadlines, input poisoning y falsos positivos por pérdida de contexto, truncamiento o snapshots contradictorios; además redacción, permisos y lectura no creadora. Toda entrada es no confiable.

Fallos obligatorios: request ausente/malformada/duplicated keys/version incorrecta; DB ausente/ajena/futura/corrupta; lock/timeout/IO; lote faltante; counts inconsistentes; procedencia incompatible; historial invertido/igual a current; contexto incompatible; límite superado; duplicados contradictorios; empty/bootstrap/replay. Ensayos solo con DBs temporales, sin modificar datos del usuario.

Threat model, riesgo y deuda actualizados con controles probados. Evitar afirmar licencia por synthetic o source health por consulta SQLite. TD-001–TD-004 conservadas; nueva deuda deliberada significativa requiere ID/motivo/impacto/owner/condición de salida/horizonte.

## Arquitectura, ADRs y cambios DB

ADRs obligatorios para semántica temporal, identidad de comparación/eventos y fronteras de lectura; se puede combinar en un ADR coherente sin duplicar decisiones triviales. Incluir Context, Decision, Alternatives, Consequences, Status, Revisit conditions.

Contratos versionados, fixtures inventados/provenance y pruebas de contrato de request/snapshot/output. Extensiones compatibles de STORAGE_V1/LOGGING_V1 explícitas, preservando API y CLI existentes.

**DATABASE CHANGES esperados: ninguno de esquema/migración ni datos de negocio.** Solo nueva lectura acotada. Si el diseño requiere schema2, tablas/cursor/eventos o cambios incompatibles, elevar propuesta y detener esa parte dependiente, continuando trabajo independiente; no implementarlos unilateralmente.

## Acceptance Criteria — AC-D01–AC-D15

| ID     | Evidencia exigida                                                                                                                                                  |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AC-D01 | Baseline/árbol/padres preservados; cierre P3a y apertura P4a atribuidos al Orchestrator, scope/ownership registrados.                                              |
| AC-D02 | ADR/contratos definen ventana, contexto, claves, eventos, canonización, bootstrap y límites; dominio/comparador independientes de proveedor/SQLite.                |
| AC-D03 | Lectura metadata+filas consistente, acotada, no creadora y sin mutación; empty existente distinto de missing; incoherencias detectadas.                            |
| AC-D04 | Set aceptado ausente de historia genera evidencia de nueva referencia, con IDs/captura originales; referencia distinta con mismo CMT ID no afirma producto nuevo.  |
| AC-D05 | Candidato nuevo genera un evento targetless, incluido set candidato sin doble conteo; no asignación/promoción/re-resolución.                                       |
| AC-D06 | Unión previa incluye aceptados/candidatos; repetición, reaparición y candidate->accepted no generan nueva referencia.                                              |
| AC-D07 | Cambios de nombre/fecha no crean novedad; duplicados idénticos colapsan y contradicciones del lote fallan sin escoger un vencedor.                                 |
| AC-D08 | Contextos exactos namespace/kind/language/null/variant, cronología y IDs validados; sin mezcla silenciosa entre idiomas/fuentes/ventanas.                          |
| AC-D09 | Bootstrap sin eventos, empty válido/no novedades y evidencia rechazada/fallida se distinguen; no lanzamiento/retirada/source health inferidos.                     |
| AC-D10 | Resultado/event IDs/order reproducibles entre ejecuciones, orden de historia y backup/restored DB; alcance de primera observación explícito.                       |
| AC-D11 | Input limits, máximo 32 históricos/33.000 filas/1.000 eventos, lock/timeout/IO/corrupción y categorías seguras probados; sin resultados truncados exitosos.        |
| AC-D12 | CLI/wheel/Compose/AMD64/ARM64 ejecutan nueva comparación tras persistencia en procesos distintos, UID no-root y red deshabilitada; DB permanece intacta.           |
| AC-D13 | Logging compatible/correlacionado/redactado; resultados/contadores no confunden error o baseline con cero descubrimientos exitosos.                                |
| AC-D14 | Gates automatizados/regresión P0/P1a/P3a, coverage >=85% líneas/>=80% ramas y cuatro jobs sobre candidato exacto PASS; schema1/identidad/histórico preservados.    |
| AC-D15 | QA y REVIEWER independientes del autor y entre sí verifican SHA final; documentación/runbook/threat/deuda/roadmap y ledger describen capacidades y límites reales. |

Todos los criterios se evalúan individualmente con evidencia reproducible. Un gate obligatorio no ejecutado es FAIL con razón; no usar N/A para gates de esta fase ni transferir cifras históricas como ejecución propia.

## Testing y quality gates

- Unit/contract: todos los casos de claves/contexto/novedad/temporalidad/duplicates/hash/output, DTOs forjados, limits y redacción.
- SQLite real: empty/missing, metadata/rows snapshot, contención, versiones/ownership/corrupción, counters/rows alterados en fixtures temporales, lectura sin mutación de tablas y no creación de DB ausente. Probar concurrencia relevante para coherencia, no solo mocks.
- Integración P1a/P3a: sembrar varias capturas, comparar, repetir, verificar contenido, backup/restore y repetir comparación con mismo resultado. Demostrar candidato congelado tras capturas posteriores aceptadas, referencia nueva de entidad conocida y reaparición tras empty.
- CLI installed: baseline, no discoveries, set nuevo, candidato nuevo, error contextual, error global y almacenamiento; stdout/logs/códigos. Ejecutar fuera del checkout/PYTHONPATH.
- Añadir harness pequeño Discovery a wheel/Compose/AMD64/ARM64 sin quitar version/diagnose, cinco casos P1a y harness durable P3a. Fixtures mínimas synthetic con ledger de procedencia; smokes contienen assertions sobre eventos y contenido persistido.
- Frozen install/lock, Ruff format/check, strict mypy, pytest, coverage >=85/80 sobre todo runtime propio incluidas nuevas lecturas y errores; sdist/wheel; audit/secret scan; arquitectura/DB/SEC/SRE/docs; QA y REVIEWER independientes; Compose y linux/amd64/linux/arm64 QEMU; cuatro jobs CI PASS.
- CI puede descargar/build dependencias; tests del producto offline, sin GET nuevos TCGdex. No imponer número objetivo de tests ni excluir código para subir coverage.
- Registrar Python/SQLite/QEMU y diferencias local/CI. Pi física no es gate P4a.

## Equipo y ownership

Engineering Lead inspecciona/planifica/asigna ownership e integra. Git/refs/lock/CLI/logging/workflows/documentos compartidos se coordinan secuencialmente; paralelizar únicamente análisis read-only o trabajo con archivos disjuntos.

- ARQ + DB-OWNER: ADR/contratos, nueva lectura consistente y revisión de integridad; autor combinado permitido y registrado.
- DATA/DISCOVERY + BE: comparación pura/modelos/fixtures/tests de autor, con rutas separadas de almacenamiento.
- SEC + SRE: revisión concreta de límites, falsos positivos, redacción, permisos y wheel/container; pueden combinarse. Preferir read-only y correcciones asignadas a autores.
- QA: agente independiente, checkout aislado del SHA final; pruebas derivadas de AC/riesgos además de ejecución de suite.
- REVIEWER: otro agente independiente de autores/QA, checkout distinto; revisión de objetos, código, contratos, identidad/semántica, scope/docs y CI exacto.
- DOCS solo si el trabajo lo justifica; no lanzar agentes sin tarea concreta.

Este contrato pide multiagente para la ejecución Codex y autoriza las delegaciones pertinentes. Registrar ownership antes de editar; los autores no cambian archivos ajenos sin handoff. Las revisiones de agentes no son aprobaciones formales de GitHub.

Autonomía: inspección, rama/worktrees aislados, ADRs/contratos, código dentro del scope, fixtures, DBs temporales, pruebas/fallos controlados, correcciones, documentación y PR sin nueva confirmación. No merge, nuevos feeds, compras, altas/contactos, ampliación unilateral o reducción de gates. Escalar decisiones cross-phase importantes al Orchestrator.

## Entregables, cierre y primera respuesta

Archivar este contrato como docs/phases/P4A_OFFLINE_TEMPORAL_DISCOVERY_CONTRACT.md; Engineering Brief y ownership; implementación y CLI; ADR/contratos; fixtures/provenance/tests/harness; README/arquitectura/testing/gates; runbook/threat/risks/debt/roadmap; informe docs/phases/P4A_OFFLINE_TEMPORAL_DISCOVERY.md y ledger externo PR.

El informe contiene Phase/Proposed Status/Branch/PR/head/base/tree; MODEL PROFILE realmente utilizado y limitaciones de introspección; especialistas/independencia; objetivos/implementación/ADRs/contratos; **DATABASE CHANGES**; seguridad/deuda/observabilidad; tests/gates/tabla AC-D01–D15; limitaciones/issues/recomendación. Separar ejecución propia y evidencia ajena, CI de PR y push, sintético y fuente real, QEMU y hardware. No introducir commit circular para su propio SHA.

Presentar candidato concreto con revisión independiente y cuatro jobs finales. Merge solo tras autorización exacta Orchestrator; repetir refs/alcance/árbol/checks/mergeability antes y detenerse si cambian. Tras una futura integración: commit real, padres base->head, mismo árbol y CI push/main exacto con cuatro logs; solo el Orchestrator decide ACCEPTED / PHASE CLOSED.

Primera respuesta del Phase Lead:

1. Leer completo este contrato, context.md y las fuentes del repo: AGENTS, operating model, roadmap, arquitectura/ADRs, gates/testing/coding, P1a/P3a contratos/reportes/ledger, threat/risks/debt.
2. Confirmar rol/MODEL PROFILE/scope y verificar el baseline disponible sin afirmar acceso local no realizado.
3. Entregar Engineering Brief inicial para Codex local, repitiendo su perfil de modelo, orden de diseño/implementación, ownership, checks y handoff.
4. Avanzar hasta candidato verificable; elevar solo scope nuevo/bloqueos reales, sin pedir al usuario requisitos ya definidos.

Terminar la entrega de fase con:\
**READY_FOR_ORCHESTRATOR_REVIEW**

Nunca declarar PHASE CLOSED ni abrir otra fase desde el Phase Chat.