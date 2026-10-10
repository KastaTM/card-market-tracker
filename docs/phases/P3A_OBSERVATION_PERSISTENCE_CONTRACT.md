# P3a — Observation Persistence: contrato y prompt de apertura

## MODEL PROFILE

- **ChatGPT Phase Lead recomendado:** **GPT-5.6 Sol / High** si se abre un chat normal. Si se abre en ChatGPT Work y está disponible, **GPT-6.1 Sol / High**. Motivo: delimitar histórico, replay, identidad, recuperación y evidencias de aceptación.
- **Codex Engineering Lead recomendado:** **GPT-6.1 Sol / Medium** para inspección, trabajo mecánico, CLI, fixtures y documentación; **High** para diseño transaccional, migraciones, integridad, errores de almacenamiento y revisión de integración.
- **ARQ, DB-OWNER, SEC y SRE:** **GPT-6.1 Sol / High** para las decisiones y revisiones de su competencia. Un mismo autor puede cubrir ARQ/DB-OWNER cuando convenga; registrar esa coincidencia.
- **QA y REVIEWER:** **GPT-6.1 Sol / High**, en dos agentes distintos, independientes de los autores y entre sí. No sustituir su revisión por la autoevaluación del Engineering Lead.
- **Escalación:** **GPT-6 Astra / High** únicamente ante un bloqueo complejo persistente, después de reproducirlo y analizarlo con Sol, y si el cliente lo ofrece. Registrar motivo, alcance y resultado.
- Confirmar los modelos seleccionables al empezar. La recomendación no acredita el modelo realmente usado. Registrar por separado selección/configuración observada, delegaciones y backend o reasoning no verificables. No inferirlos a partir del nombre de un rol ni afirmar que este prompt cambia la configuración del cliente.

Referencias oficiales consultadas el 2026-10-10: [https://learn.chatgpt.com/docs/models](https://learn.chatgpt.com/docs/models) y [https://developers.openai.com/api/docs/guides/latest-model](https://developers.openai.com/api/docs/guides/latest-model). La disponibilidad depende del cliente, plan y configuración. Conservar GPT-5.6 Sol si ese es el modelo expresamente seleccionado en el chat normal.

## Rol, autoridad y apertura

Actúa como **Phase Lead de P3a — Observation Persistence** para **Card Market Tracker**. Convierte este contrato en un Engineering Brief para Codex local, coordina su ejecución, contrasta sus evidencias y entrega el Phase Completion Report al chat **00 — ORCHESTRATOR**.

El Orchestrator **abre P3a el 2026-10-10, Europe/Madrid**, mediante este contrato. Puedes proponer `READY_FOR_ORCHESTRATOR_REVIEW`; solo el Orchestrator puede decidir `ACCEPTED`, `REWORK_REQUIRED`, `BLOCKED` y declarar `PHASE CLOSED`.

Repositorio: [https://github.com/KastaTM/card-market-tracker](https://github.com/KastaTM/card-market-tracker)

Checkout local previsto: `C:\Projects\card-market-tracker`. Comprobar existencia y estado. La falta de acceso desde ChatGPT no demuestra que Codex local esté bloqueado. No presentar los comandos locales aportados por Codex como ejecuciones de este chat.

## Baseline y decisiones vigentes

**P0, P0.5 y P1a están ACCEPTED y PHASE CLOSED por decisión del Orchestrator.** P1a se aceptó y cerró el **2026-10-10**, después de revisar el candidato, su integración y los logs de CI posteriores al merge.

| Evidencia de P1a aceptada                                 | Valor                                                                                                                                              |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| PR integrado                                              | [https://github.com/KastaTM/card-market-tracker/pull/5](https://github.com/KastaTM/card-market-tracker/pull/5)                                     |
| Baseline aceptado y punta de main comprobada al abrir P3a | `c6e66a2aba469d02f0ca63fde3b81ecc5eea41bc`                                                                                                         |
| Árbol integrado                                           | `a9717922736a6220d3ff05293bec4cb222644269`                                                                                                         |
| Primer padre del merge                                    | `af573f04586024e7666a8999526e0aaab238c0dc`                                                                                                         |
| Segundo padre: head revisado                              | `93a17711cb75f91816e41279fe76069055391e50`                                                                                                         |
| CI push de main, SHA exacto                               | [https://github.com/KastaTM/card-market-tracker/actions/runs/37965128340](https://github.com/KastaTM/card-market-tracker/actions/runs/37965128340) |

El árbol del merge coincide con el candidato; la comparación de archivos es vacía. Quality, Compose, AMD64 y ARM64 QEMU pasaron. Los logs registran 218 pruebas, 99,04 % de líneas y 97,59 % de ramas, auditoría y secret scan, wheel y cinco escenarios offline. Es evidencia histórica de P1a; P3a debe generar sus propios resultados.

Antes de editar, verificar remote, objetos Git, main remoto, checkout y trabajo previo. Si main ha avanzado, inspeccionar delta y CI y comunicarlo; no reemplazar silenciosamente el baseline autorizado. Si altera las dependencias o el candidato de partida, elevarlo al Orchestrator antes de integrar sobre él. Preservar cambios ajenos; usar rama o worktree aislado si hace falta.

Registrar **dentro de la rama P3a** el cierre de P1a y la apertura de P3a en el roadmap y en el informe P1a, atribuidos al Orchestrator y con las evidencias anteriores. Conservar los registros históricos como tales; no convertir retrospectivamente el informe previo a publicación en una ejecución posterior. No abrir un PR adicional solo para citar el SHA de ese mismo documento.

Dependencias que continúan vigentes:

- TCGdex es provisional para metadatos de cartas/sets; no hay validación de cobertura real ni permiso general de retención comercial.
- AC-F05 de P0.5 acredita únicamente viabilidad exploratoria por ID y enumeración de sets ES. No acredita delta temporal, novedades reales, retail, sealed vendible, stock o preventas.
- **P2 permanece BLOCKED** por acceso, derechos de histórico/retención y semántica de una fuente EUR.
- **P6a y Discovery retail permanecen BLOCKED** por falta de una fuente compatible.
- ARM64 QEMU no acredita comportamiento de una Raspberry Pi física ni resistencia a cortes eléctricos.

Estas carencias no impiden aceptar P3a como infraestructura offline con datos sintéticos. Esta apertura no autoriza feeds reales ni abre otra fase.

## Objetivo

Implementar una primera persistencia **SQLite**, offline y recuperable, del histórico mínimo de observaciones de metadatos normalizadas y de sus resultados de resolución. Debe conservar la identidad curada de P1a, mantener candidatos sin promoverlos, distinguir replay de una nueva captura y demostrar integridad transaccional, lectura acotada y backup/restore.

La capacidad debe ejecutarse desde el paquete instalado y desde Docker con almacenamiento que sobreviva a una nueva invocación del contenedor. La demostración usa exclusivamente fixtures sintéticos.

## Dentro de alcance

1. ADR de persistencia: SQLite, acceso, límites, transacciones, concurrencia, journal/synchronous, esquema versionado, idempotencia y recuperación. Revisar su encaje con ADR-0003.
2. Contrato versionado de entrada persistible y de almacenamiento/lectura, refinando solo los metadatos de `INGESTION_V1`. Definir campos, nulls, validación, timestamps, compatibilidad, claves y errores.
3. Esquema mínimo para lotes confirmados, observaciones válidas aceptadas/candidatas y las identidades/relaciones necesarias para integridad. No exigir un número concreto de tablas: DB-OWNER justificará una representación pequeña y comprobable.
4. Inicialización/migración inicial versionada, apertura segura y detección de versiones o ficheros incompatibles. No se exige una migración ficticia entre dos esquemas de negocio que aún no existen.
5. Escritura atómica por lote; replay idempotente; conflicto explícito de token o identidad; persistencia durable de candidatos sin workflow de revisión.
6. Lectura mínima acotada por lote, por CMT ID y por referencia contextual candidata, orden determinista y reapertura desde otro proceso.
7. Backup consistente y restauración comprobada en un destino nuevo. Runbook de bloqueo, corrupción, permisos, recuperación y límites.
8. CLI nueva de persistencia/lectura y operaciones locales necesarias de DB. Mantener `cmt catalog` como operación de solo lectura; usar comandos separados para hacer explícita la escritura.
9. Logging, controles de entrada/SQL/rutas, fixtures, pruebas, integración wheel/Compose/AMD64/ARM64, documentación y revisión independiente.

## Fuera de alcance

Feeds o peticiones HTTP, nuevos GET a TCGdex, scraping, fuentes reales o datos comerciales retenidos; precios, stock, ofertas, vendedores, impuestos, shipping, conversión de moneda y referencias de mercado; scheduler, collector de producción y operación 24/7; motor Discovery, comparación para señales de novedad, promoción automática o manual de candidatos, cola de revisión con estados; watchlist, alertas/Telegram, oportunidades, API, servidor o UI; queries analíticas y métricas de P3b/P10a; migración a PostgreSQL o sincronización remota.

**P3a no es una implementación de P2 con fixtures.** No añadir columnas de precio/stock, tablas vacías o interfaces sin consumidor para anticipar esos contratos. P2 y P6a definirán y versionarán sus propias observaciones cuando se abran.

No crear cuentas, adquirir accesos, contactar proveedores ni cambiar protecciones/permisos de GitHub. No modificar o borrar bases de datos del usuario. Todo drill se realiza con DB temporales o destinos nuevos identificados.

## Límites de arquitectura

- Mantener Python 3.13, src layout, paquete/CLI, identidades y contratos de P1a. El dominio y el resolver no deben importar SQLite ni adaptadores. La orquestación compone validación, normalización, resolución y repositorio.
- Preferir `sqlite3` de la biblioteca estándar. SQLite es la elección autorizada para esta fase; un ORM o framework de migraciones solo se incorpora con necesidad implementada, ADR, lock/audit y evidencia ARM64. No añadir abstracciones genéricas para múltiples DB inexistentes.
- El manifiesto curado continúa siendo la autoridad de identidades y correspondencias. La DB conserva las proyecciones y relaciones necesarias para las observaciones aceptadas, con la clausura de padres. No reemplazar el manifiesto por una autoridad nueva ni generar IDs CMT al ingerir.
- Conservar UUIDv4 de set/card/printing/sealed; referencias externas siguen siendo evidencia contextual. No resolver por nombre, usar null como wildcard, colapsar ES/EN/variantes ni vincular candidatos a un UUID inventado.
- Un mismo CMT ID con identidad o relación incompatible con la ya almacenada falla; no usar `INSERT OR REPLACE` o upserts que borren padres o reescriban decisiones en silencio. Las variaciones de metadatos observados pertenecen al histórico y no reasignan identidades.
- Conservar snapshots mínimos inmutables de evidencia y resolución. Nuevas capturas agregan observaciones; no sustituyen las antiguas ni cambian automáticamente el target de un candidato previo al cambiar el manifiesto.
- La salida de `BatchResult.to_dict()` de P1a **omite timestamps y otros metadatos normalizados**. No usarla como única entrada de una persistencia que pretenda conservarlos. Consumir valores normalizados validados y el resultado de resolución, unidos por índice/contexto con correspondencia comprobada.
- El repositorio no debe asumir que cualquier dataclass construida manualmente está validada. Definir y probar su frontera pública; reusar los validadores existentes o aplicar validación equivalente antes de escribir.

## Contrato temporal, replay y resultados

Antes de implementar, ARQ/DB-OWNER deben fijar lo siguiente en contratos ejecutables y documentados:

### Tiempo y procedencia

- Toda observación persistible necesita **`captured_at` explícito**, un instante con zona normalizado a UTC. Si falta en la observación P1a, una envoltura local puede aportarlo explícitamente; no copiar release date/provider update ni inventar captura con el reloj de la ejecución.
- Mantener separados `release_date`, `provider_updated_at`, `captured_at` e instante local de primera persistencia. Las dos primeras fechas pueden seguir ausentes. `captured_at` describe la captura declarada; la persistencia tiene su propio tiempo.
- Esta obligatoriedad es propia de la nueva frontera persistible, **no cambia retroactivamente el contrato P1a**, donde captura era opcional. Resolver discrepancias entre captura de envoltura y registro con error explícito, sin prioridad silenciosa.
- Los fixtures usarán timestamps fijos y `provenance=synthetic`. El comando de escritura de esta fase admitirá solo esta procedencia. `documented` u `observed` no acreditan derechos y deben fallar antes de retener evidencia.
- Una etiqueta synthetic es una declaración del productor local, no prueba criptográfica de origen. Documentar esa confianza y revisar fixtures; no presentar el control como una autorización de datos reales.
- No publicar un `first_seen_at` global de producto. Si se conserva primera persistencia de un lote/observación, denominarla y acotarla así; no equivale a lanzamiento, primera aparición comercial ni detección de novedad.

### Idempotencia

- Introducir un **identificador estable de lote**, por ejemplo `batch_id` UUIDv4 proporcionado por el productor y reutilizado al reintentar. Es independiente del `run_id`, que identifica cada intento de ejecución.
- El primer lote confirmado fija evidencia y resolución. Repetir su token con la misma entrada normalizada y el mismo contexto relevante del manifiesto no agrega observaciones, identidades o candidatos ni cambia su primera persistencia.
- Reutilizar el token con contenido o contexto de resolución incompatible falla de forma explícita y deja la DB sin cambios. Documentar cómo se compara la equivalencia, incluida versión de contrato y contexto del manifiesto; una huella puede acreditar contenido, **nunca definir la identidad CMT de un producto**.
- Un nuevo lote con una captura posterior debe poder agregar histórico aunque los valores no cambien. No deduplicar globalmente por nombre o contenido y perder observaciones legítimas.
- Delimitar la garantía: el productor debe conservar el token durante un retry. Un token nuevo no puede atribuirse automáticamente al lote previo. No prometer deduplicación de capturas arbitrarias que carecen de la clave estable requerida.

### Parciales y errores

- Registros válidos aceptados y candidatos se retienen con su estado original. Un candidato conserva la referencia exacta, categoría y evidencia mínima permitida, sin CMT ID ni promoción.
- Registros inválidos se contabilizan/categorizan, sin retener su payload, nombre, referencia arbitraria o texto de excepción. Se puede guardar el resumen seguro de rechazos para reconstruir el resultado del lote; no es una cuarentena de datos crudos.
- La parte admitida de un lote mixto y su resumen se confirman **en una sola transacción**. Un error de DB revierte el lote completo, incluidas identidades nuevas y metadatos de lote. No informar éxito parcial de almacenamiento.
- Definir resultados distintos para: válido con datos; vacío válido; mixto/candidatos/rechazos; replay; error global de validación; conflicto de replay; fallo de almacenamiento. La cantidad de registros procesados y la de filas nuevas son métricas diferentes.
- Si falla el almacenamiento, no presentar los contadores calculados en memoria como filas confirmadas. Contadores desconocidos no se convierten en cero exitoso.
- Fijar códigos de salida y JSON stdout; mantener separación de error de datos y error local. Se recomienda conservar 0 para ejecución correcta, 3 para resultado de registros no plenamente aceptados, 2 para entrada/contrato inválido y 1 para almacenamiento/ejecución local, definiendo explícitamente conflictos y replay. Una alternativa coherente requiere justificación y pruebas, sin alterar los códigos existentes de P0/P1a.

## SQLite, migraciones y recuperación

- Claves, checks, unicidad e integridad referencial deben materializar las invariantes pertinentes. Activar y comprobar foreign keys en **cada conexión** que las necesite; no depender de un default.
- SQL parametrizado para valores. Identificadores/ordenaciones permitidos son fijos o allowlisted, nunca SQL procedente de input. No habilitar carga de extensiones ni ejecutar dumps/SQL aportados por fuentes.
- Configurar explícitamente transacciones y cierre de conexiones según Python 3.13. No mezclar commits implícitos con una garantía de atomicidad no probada; revisar el comportamiento de helpers de scripts/DDL.
- Registrar esquema mediante metadata/version y validarlo antes de operar. Base vacía -> esquema inicial; esquema actual -> no-op. Versión futura, estructura incompatible o SQLite ajena -> error sin reset/destrucción. Una inicialización o migración fallida no deja un esquema parcialmente aceptado.
- Elegir journal/synchronous conscientemente para almacenamiento local y documentar la garantía. WAL es una opción, no un gate impuesto: si se usa, incluir sidecars, checkpoints, backup y bloqueos en el diseño. No afirmar que pasar pruebas de proceso demuestra durabilidad física tras un corte eléctrico.
- Alcance operativo: un host, un escritor a la vez; lectores y escritores concurrentes deben tener comportamiento definido. Establecer timeout de bloqueo finito y probado, por defecto no superior a cinco segundos; retries solo con presupuesto global explícito. No introducir un scheduler o un pool.
- Lecturas acotadas, límite máximo definido y orden estable. Leer una DB inexistente no crea silenciosamente un fichero ni inicializa esquema. Las consultas no cambian datos de negocio ni versiones; distinguir sidecars operativos si corresponden.
- Backup consistente mediante la API SQLite/Python u otra técnica oficial justificada; no copiar únicamente el fichero principal mientras está abierto si ello ignora estado pendiente del journal.
- Comprobar integridad y foreign keys del backup/restore, reapertura y equivalencia de IDs, observaciones, candidatos y replay. Restaurar solo hacia un destino nuevo; no sobrescribir el origen o una DB existente. Ante error no presentar un archivo incompleto como backup válido.
- Delimitar tiempo/recursos de operaciones, incluyendo backup bajo contención. Registrar crecimiento del histórico como requisito operativo futuro; no inventar una retención de fuentes reales ni añadir limpieza destructiva automática en P3a.
- No versionar `.db`, journals, backups reales ni artefactos de pruebas. Incluir reglas pertinentes en ignores/scans.

Fuentes técnicas que DB-OWNER debe contrastar con el runtime efectivo: [https://docs.python.org/3.13/library/sqlite3.html](https://docs.python.org/3.13/library/sqlite3.html), [https://www.sqlite.org/backup.html](https://www.sqlite.org/backup.html) y [https://www.sqlite.org/wal.html](https://www.sqlite.org/wal.html). Registrar versión Python/SQLite realmente observada en local y contenedores.

## CLI, contenedores y observabilidad

Definir una interfaz pequeña y documentada para inicializar/ingerir, leer, verificar integridad y ejecutar backup/restauración segura. No se exige un framework de comandos ni un servicio. Las operaciones pueden combinarse si conservan claridad, trazabilidad y errores.

Una demostración reproducible debe poder:

1. Crear una DB nueva e ingerir un lote sintético aceptado/mixto con manifiesto P1a.
2. Terminar el proceso, reabrir la misma DB y comprobar lo persistido.
3. Repetir el lote y comprobar replay sin filas nuevas ni cambio de IDs.
4. Ingerir una captura posterior y leer ambas observaciones en orden.
5. Intentar token conflictivo y entrada global inválida, comprobando que nada cambia.
6. Conservar y leer candidatos sin identidad; distinguir vacío válido y error.
7. Crear backup, restaurarlo en otro destino y verificar integridad/contenido/replay.

En Docker/Compose usar una ubicación writable explícita para UID `10001`, con volumen o bind mount de datos; fixtures montados read-only y networking deshabilitado durante los smokes. Demostrar persistencia entre **invocaciones distintas** de contenedor. No resolver permisos ejecutando el producto como root, usando chmod 777 o haciendo escribible todo el proyecto. Documentar preparación local/Windows y volúmenes usados. No agregar puertos.

Extender `LOGGING_V1` conscientemente: evento de operación, UUID run_id, resultado, duración, contadores de entrada/estados y filas confirmadas/replay, más categorías estables de validación, conflicto, schema, bloqueo, IO/corrupción/backup. Los nombres exactos pertenecen al contrato implementado. Logs no contienen payloads, nombres arbitrarios, SQL/valores, rutas, referencias externas, tokens o excepción cruda. Probar redacción y handlers; preservar compatibilidad P0/P1a.

La verificación DB indica únicamente integridad/compatibilidad en su alcance. No etiquetar como healthy una fuente no consultada ni equiparar integridad SQLite con salud de toda la Pi.

## Seguridad y derechos

Reutilizar límites P1a de bytes, profundidad, nodos, strings y registros en entradas JSON. Definir límites de lectura y de operaciones de almacenamiento; no procesar rutas de datos como código ni seguir URLs incluidas en registros.

SEC revisará SQL injection, contaminación de identidad, falsos replays, entradas grandes, fugas, permisos de DB/backup y rutas/destinos: mismo archivo, archivos existentes, directorios, links u otras rutas que puedan causar una sobrescritura inesperada. No crear una funcionalidad de cifrado o autenticación remota sin necesidad dentro del alcance.

Retener solo el mínimo normalizado definido por contrato y únicamente synthetic. No guardar imágenes, precios, datos personales, textos extensos, payloads completos ni extras del proveedor. Las categorías de rechazo no autorizan guardar la entrada fallida. Todo dato real continúa bloqueado por acceso y retención sin acreditar, aunque exista SQLite.

Actualizar threat model, riesgos R-03/R-04/R-05/R-06/R-10 y deuda pertinente con controles realmente probados. Conservar TD-001/TD-002 salvo evidencia que cumpla su condición de salida; P3a no acredita source health ni Pi física. Documentar una limitación deliberada significativa con ID, responsable, impacto, condición de salida y horizonte; no registrar cada feature futura como deuda.

## Criterios de aceptación — AC-O01 a AC-O15

| ID     | Evidencia exigida                                                                                                                                                                               |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-O01 | Baseline/árbol de P1a verificados, cierre atribuido al Orchestrator y apertura P3a registrada; rama y trabajo previo preservados.                                                               |
| AC-O02 | ADR y contratos versionados definen fronteras, esquema, timestamps, procedencia, replay, resultados y evolución. Dominio/resolver independientes de SQLite.                                     |
| AC-O03 | DB conserva UUIDs y relaciones curadas con integridad comprobada; identidad contradictoria falla sin sobrescritura ni IDs fabricados.                                                           |
| AC-O04 | Escritura/lectura durable desde procesos distintos conserva evidencia normalizada, captura y estado; no depende solo del stdout incompleto de P1a.                                              |
| AC-O05 | Replay del mismo token/contexto no agrega filas ni cambia primera persistencia; token conflictivo no cambia DB; captura posterior agrega histórico incluso con valores iguales.                 |
| AC-O06 | Candidatos persisten sin CMT ID ni promoción; inválidos tienen solo resumen seguro. Mixto, vacío, rechazado y error global se distinguen.                                                       |
| AC-O07 | Transacción por lote y rollback verificados con fallos después de escrituras intermedias; reinicio antes/después del commit conserva únicamente estado coherente.                               |
| AC-O08 | Inicialización/migración inicial atómica, no-op actual y rechazo de DB/versión incompatible sin reset; claves y foreign keys probadas.                                                          |
| AC-O09 | Bloqueo tiene tiempo finito y error seguro; permisos, fallo IO y corrupción no se interpretan como vacío/éxito. Lecturas acotadas no crean DB faltante.                                         |
| AC-O10 | Backup consistente y restore en destino nuevo pasan integridad y equivalencia de contenido/identidad/replay; rechazo de destinos peligrosos/existentes probado.                                 |
| AC-O11 | CLI instalada, wheel fuera del source tree, Compose y AMD64/ARM64 demuestran nueva capacidad con datos durables entre invocaciones y UID no-root; networking deshabilitado para procesar datos. |
| AC-O12 | Logs compatibles, categorizados y correlacionados; filas confirmadas/replay distintas de procesamiento; redacción demostrada en éxitos y fallos.                                                |
| AC-O13 | Procedencia synthetic exigida en escritura; derechos reales no inferidos; fixtures mínimas/provenance y controles de SQL/entrada/rutas/permisos revisados por SEC.                              |
| AC-O14 | Todos los gates obligatorios y regresión P0/P1a pasan sobre candidato exacto, con cobertura de runtime propio >=85 % líneas / >=80 % ramas y cuatro jobs CI.                                    |
| AC-O15 | QA y REVIEWER independientes revisan el SHA exacto; informe/AC/evidencias, arquitectura, contratos, runbook, riesgos, deuda y roadmap reflejan implementación y límites reales.                 |

## Pruebas obligatorias y gates

**Unitarias y contratos:** versiones, nulls, timestamps con offset y captura ausente/contradictoria; validación de procedencia; IDs/relaciones/candidatos; dedupe vs nueva captura; token conflictivo; canonización/comparación de replay; SQL parametrizado con strings hostiles; límites y categorías/redacción.

**Integración SQLite real sobre ficheros temporales:** persistencia/reapertura, dos procesos/conexiones, integridad/foreign keys, historial ordenado, lecturas vacías; rollback con fallo inyectado tras escritura intermedia; interrupción de proceso antes del commit y reapertura; reinicio tras commit; inicialización fallida sin esquema parcial; versión futura y DB ajena; contención con plazo finito; corrupción mínima no destructiva fuera de las DB del usuario; backup/restore verificable. Simulaciones de disk-full/IO pueden usar inyección en una frontera real de escritura y comprobar rollback; distinguir simulación de fallo físico observado.

**CLI y packaging:** aceptado, mixto/candidatos, todos rechazados, vacío válido, global inválido, replay y conflicto; consulta/reinicio/backup/restore; salida/logs/exit codes; permisos no-root; no red; wheel instalado fuera del checkout. Mantener los cinco smokes P1a, version/diagnose/config P0 y su regresión. Añadir un harness pequeño para la nueva persistencia y ejecutarlo en wheel, Compose y ambos contenedores, con aserciones sobre contenido durable, no solo sobre exit 0.

**Gates:** frozen install/lock; Ruff format/check; mypy estricto; pytest; coverage >=85/80 sobre todo el runtime propio sin excluir persistencia/errores para subir porcentaje; build/sdist/wheel; auditoría de dependencias y secret scan; revisión ARQ/DB-OWNER/SEC/SRE/documentación; QA y REVIEWER independientes; Compose; linux/amd64; linux/arm64 QEMU; cuatro jobs CI. Usar las recetas actuales de `QUALITY_GATES.md`, adaptándolas sin rebajarlas.

Cada gate aplicable requiere PASS/FAIL, comando/entorno/resultado y SHA o árbol idéntico demostrable. Un obligatorio no ejecutado es FAIL con razón, nunca N/A. No declarar los 218 tests/porcentajes P1a como resultado de P3a. No imponer un número objetivo de tests ni perseguir coverage 100 % con pruebas que reflejan la implementación sin cubrir riesgos.

Las pruebas del producto funcionan offline; CI puede descargar/build dependencies como en Foundation. No hay gate de fuente live ni Pi física en P3a. Registrar versiones Python/SQLite y QEMU; el resultado no prueba 24/7, NFS ni tolerancia eléctrica del hardware.

## Equipo, ownership y autonomía

El Engineering Lead asignará archivos antes de editar y coordinará Git, lock, CLI, logging, contratos compartidos y CI secuencialmente.

- **ARQ + DB-OWNER:** decisiones de persistencia, contrato temporal/idempotente, schema/migración, restricciones, backup y revisión de integridad. Pueden compartir un autor; señalarlo.
- **BE/DATA:** implementación del repositorio, validación de entrada persistible, composición con P1a, CLI y pruebas de autor, en rutas asignadas.
- **SEC:** entrada, SQL, derechos, rutas, logs y permisos; revisión preferentemente de lectura con correcciones asignadas al autor.
- **SRE:** volumen/no-root, contenedores, deadlines, interrupción/backup/restore y runbook. No desplegar en la Pi ni añadir operación continua.
- **QA:** agente independiente, deriva pruebas de AC/riesgos y verifica en checkout aislado del SHA final.
- **REVIEWER:** otro agente independiente de los autores y QA; revisa Git blobs, contratos, integridad, seguridad, alcance, docs y evidencia CI del SHA final.

No lanzar especialistas sin tarea concreta ni exigir que todos editen. Roles de autor pueden combinarse. QA y REVIEWER sí deben conservar independencia y trazabilidad; no presentar sus comentarios como aprobaciones formales de GitHub si no lo son.

Quedan autorizados sin nueva confirmación: inspección, rama **`feat/p3a-observation-persistence`**, contrato/ADRs, implementación dentro del scope, DB temporales, pruebas/fallos controlados, correcciones, documentación y apertura de PR. No detenerse para confirmar decisiones rutinarias ya cubiertas. Si hay un bloqueo parcial, continuar el trabajo independiente autorizado.

**El merge no queda autorizado por este contrato.** Presentar candidato concreto al Orchestrator con head/base/árbol y checks. La integración requiere su decisión sobre ese candidato; no usar permisos locales ni un CI verde como sustituto. No ampliar alcance/reducir gates unilateralmente ni abrir P2.

## Entregables y protocolo final

- Contrato archivado, por ejemplo `docs/phases/P3A_OBSERVATION_PERSISTENCE_CONTRACT.md`, conservando esta autorización.
- Implementación y CLI pequeña, contratos de frontera/almacenamiento versionados, esquema/migración y ADR de persistencia.
- Fixtures synthetic y ledger de procedencia; pruebas/harness y CI con regresiones y nueva capacidad.
- README con comandos reproducibles, arquitectura, gates/testing, threat model/riesgos/deuda y runbook de almacenamiento/backup/restore. No afirmar controles pendientes como ya implementados.
- Informe `docs/phases/P3A_OBSERVATION_PERSISTENCE.md`; roadmap actualizado con P1a CLOSED/P3a OPEN y bloqueos de fuentes preservados.
- PR abierto con diff revisable, ledger de especialistas/revisiones, head/base/árbol exactos, run/checks y sus enlaces. Usar el ledger externo del PR para evidencia posterior a publicación; evitar commits circulares para incluir su propio hash.

El Phase Completion Report seguirá `context.md`: phase/status, branch/PR/head/tree/base, MODEL PROFILE USED verificable, especialistas/independencia, objetivos, implementación, ADRs/contratos, **DATABASE CHANGES** y migración, seguridad/deuda, observabilidad, tests/gates, tabla AC-O01–O15 con evidencia, limitaciones y pendientes. Separar pruebas de proceso, fallos simulados, QEMU y hardware real; sintético/documentado/observado; ejecución propia y evidencia de Codex.

Una corrección sustantiva cambia el candidato: volver a comprobar/revisar nuevo SHA y checks; no reutilizar el PASS de un head anterior sin demostrar igualdad de árbol y alcance pertinente.

Después de una futura autorización exacta de integración, Codex repetirá head/base/main/árbol/checks inmediatamente antes del merge y se detendrá si cambian. Tras integrar, comprobará merge real, padres ordenados, árbol y CI **push de main para ese SHA**, incluido contenido de los cuatro jobs. El CI de PR no sustituye esa evidencia. Solo después el Orchestrator decide la aceptación y cierre; no se exige un PR extra de autorreferencia para registrar el merge.

## Primera respuesta del nuevo chat de fase

Lee `AGENTS.md`, `context.md`, operating model, roadmap, arquitectura/ADRs, quality gates, testing/coding, riesgos, deuda, threat model, contratos y reporte P1a con su ledger/CI. Verifica repo/baseline antes de afirmar inspección realizada.

Confirma rol, MODEL PROFILE, alcance y bloqueos vigentes. Entrega un **Engineering Brief inicial para Codex** que ordene: verificación y ownership; decisiones/contratos DB; persistencia/transacciones/replay; CLI y recuperación; smokes/gates; QA/REVIEWER final y entrega. Si este chat no tiene checkout, prepara ese brief para Codex local sin confundirlo con un bloqueo local confirmado.

Trabaja hasta un candidato revisable con evidencia completa. Finaliza con **READY_FOR_ORCHESTRATOR_REVIEW** únicamente cuando corresponda. No aceptes/cierres P3a, no autorices su merge y no abras una fase posterior.