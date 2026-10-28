# P8c — Offline Watchlist Signal Outbox

**From:** 00 — ORCHESTRATOR\
**To:** nuevo chat P8c — Phase Lead\
**Fecha:** 2026-10-25\
**Estado:** OPEN / IMPLEMENTATION AUTHORIZED\
**Proyecto:** `KastaTM/card-market-tracker`

Actúa como Phase Lead de P8c. Coordina la implementación con Codex Engineering Lead, exige evidencia reproducible y devuelve un Phase Completion Report. Solo el Orchestrator acepta el candidato, autoriza su integración y declara PHASE CLOSED.

## 1. MODEL PROFILE

- **ChatGPT Phase Lead recomendado:** GPT-6.1 Sol / High, si está disponible en el selector. Si no aparece, usar GPT-6 con reasoning High o el perfil de mayor capacidad disponible y registrar el nombre real seleccionado. No inventar disponibilidad ni introspección del backend.
- **Motivo:** decisiones de admisión entre almacenes, identidad, deduplicación, recuperación y revisión de aceptación.
- **Codex Engineering Lead recomendado:** GPT-6.1 Sol / Medium para inspección, coordinación, CLI, documentación y tareas mecánicas; High para admisión, SQLite, consistencia, límites, concurrencia y diagnóstico ARM64.
- **Especialistas críticos, QA y REVIEWER:** GPT-6.1 Sol / High solicitado. Si no está disponible, registrar la sustitución observable.
- Escalar a GPT-6 Astra / High, si está disponible, solo ante un bloqueo de razonamiento que no resuelva el perfil anterior. No escalar automáticamente tareas rutinarias.
- En el informe final distinguir modelo/effort solicitados, selección observable y backend/reasoning efectivo no verificable.

## 2. Estado recibido y baseline

El Orchestrator ha declarado **ACCEPTED / PHASE CLOSED — P5b**, en este chat, el 2026-10-25, después de verificar PR #17 y su CI posterior al merge. P5 global permanece OPEN.

Baseline autorizado:

| Objeto                 | SHA                                        |
| ---------------------- | ------------------------------------------ |
| main / merge de PR #17 | `228d5c8d0d91edf03ddb86a489c8232eeb7c08bc` |
| Árbol                  | `dde865b6d215efc4075918088d6deddfe7cdeb1f` |
| Primer padre           | `62ecd7ab792a93a6071b83277d870f1d95f61f9f` |
| Segundo padre          | `f80bc8cdb877946f37d76b09212d68dd8da3e246` |

Evidencia histórica, no gates de P8c:

- Integración: [https://github.com/KastaTM/card-market-tracker/pull/17#issuecomment-6397243812](https://github.com/KastaTM/card-market-tracker/pull/17#issuecomment-6397243812)
- CI push/main: [https://github.com/KastaTM/card-market-tracker/actions/runs/40186860176](https://github.com/KastaTM/card-market-tracker/actions/runs/40186860176)
- RW-04: [https://github.com/KastaTM/card-market-tracker/pull/17#issuecomment-6396529714](https://github.com/KastaTM/card-market-tracker/pull/17#issuecomment-6396529714)
- Índice público: [https://github.com/KastaTM/card-market-tracker/pull/17#issuecomment-6396496254](https://github.com/KastaTM/card-market-tracker/pull/17#issuecomment-6396496254)
- Manifiesto RW-04: `d960056bd92329e2b759ac84b4323e2be3e610f52c5bb1dc30e10e5def1d7e61`.

P5b cerró con 2.042 tests PASS, un skip documentado, coberturas 94,56 % / 89,31 %, cuatro jobs y once harnesses PASS. El fallo histórico RW-02 permanece FAIL. No reabrir sus reintentos.

Antes de editar, verificar remote, objetos Git, punta remota de main, árbol, checkout, ramas y worktrees. Crear una rama desde el baseline verificado; sugerencia: `feat/p8c-watchlist-signal-outbox`. Si main difiere, detener trabajo dependiente del baseline y comunicar la divergencia; no incorporar otros cambios silenciosamente. No confundir un main local antiguo con la referencia remota.

Leer `AGENTS.md`, contexto, arquitectura, roadmap, quality gates, testing, deuda, threat model y contratos/ADRs P5a, P5b, P8a y P8b. Las restricciones de fases anteriores siguen vigentes para sus interfaces; este contrato autoriza exclusivamente el nuevo consumidor offline descrito aquí.

Archivar íntegramente este contrato en `docs/phases/P8C_OFFLINE_WATCHLIST_SIGNAL_OUTBOX_CONTRACT.md`. Añadir una entrada fechada al roadmap: P5b cerrada por decisión del Orchestrator en chat y P8c abierta. Actualizar el mapa AGENTS y los estados actuales necesarios con esa atribución, preservando informes y entradas históricos. No afirmar que se publicó un comentario remoto de cierre si no ocurrió.

## 3. Objetivo y motivo de la siguiente fase

Convertir una señal sintética verificada de P5b, seleccionada explícitamente, en una intención de alerta offline persistente, deduplicada y explicable, con preview seguro.

P5b produce `wsig1_`; P8a acepta exclusivamente eventos Discovery `evt3`. Son autoridades de evidencia diferentes. P8c crea una ruta propia de Watchlist, sin fabricar eventos Discovery ni ampliar implícitamente el outbox o el ledger Telegram existentes.

Resultado esperado: el operador puede preparar, consultar, verificar, recomputar y recuperar una alerta de demostración Watchlist. Ninguna operación de P8c envía mensajes.

## 4. Scope y exclusiones

**Incluido:** nuevo módulo de política/renderizado/admisión, SQLite independiente, identidad estable, replay/conflictos, consultas acotadas, verificación local, recomputación contra originales, backup/restore exclusivos, CLI, observabilidad, contratos, ADR y duodécimo harness offline.

**Fuera de alcance:** Telegram real o simulado como destino de esta nueva ruta; credenciales, bot/chat IDs, contactos, entrega, estados sent/confirmed, scheduler, polling, bulk enqueue, ingesta o precios reales, nuevas fuentes, oportunidades comerciales, cambios de reglas P5a/P5b, migraciones de bases existentes, retención automática, UI/API web y cierre de P5 global.

Presupuesto de llamadas del producto a proveedores o Telegram: **cero**. Descargar dependencias y consultar GitHub para el trabajo de ingeniería no constituye consumo de fuentes del producto.

No cambiar `ALERT_OUTBOX_V1`, `TELEGRAM_DELIVERY_V1`, sus schemas ni sus políticas de admisión para hacer entrar alertas Watchlist. La entrega de estas alertas requerirá otra fase y otro contrato.

## 5. Arquitectura y ownership

Definir ownership antes de implementar:

- Engineering Lead: integración, CLI, harnesses/CI, documentación y publicación.
- ARQ/BE: contrato semántico, frontera de admisión, identidad y renderer.
- DB-OWNER: nuevo esquema, transacciones, integridad, límites y recuperación.
- SEC/SRE: revisión de entradas, separación de rutas, logging y fallos.
- QA y REVIEWER: distintos de autores y entre sí, con probes propios sobre HEAD/tree final.

Usar solo los especialistas justificados. Separar archivos de autoría antes de paralelizar; análisis read-only puede ejecutarse en paralelo. No atribuir una revisión independiente a un autor de producto.

Nuevo paquete sugerido: `watchlist_alerts`. Nueva base con owner `card-market-tracker.watchlist-alert-outbox`, application_id exclusivo verificado contra todos los owners existentes y schema v1. Fijar el identificador en el ADR antes de escribir datos. No reutilizar CMTA, CMTD, CMTW ni CMTQ.

Se permite una extensión **aditiva, mínima y de solo lectura**, propiedad de P5b, si es necesaria para obtener un bundle consistente de señal y evaluaciones en una única transacción. Debe reutilizar la verificación profunda aceptada, no duplicar un verificador más débil. Mantener APIs existentes, schemas, identidades, errores y resultados compatibles. Esta autorización no permite refactorizaciones generales ni cambios en escritura, transiciones o recuperación de P5b.

Fuera de esa frontera y del registro aditivo de CLI/logging/harnesses, preservar los módulos operativos anteriores. El núcleo puro de política/renderer no dependerá de SQLite, reloj, red ni proveedor.

## 6. Admisión desde originales

Entrada explícita: paths distintos de Watchlist P5a, journal P5b y nuevo outbox, MANIFEST_V1 completo, `signal_id` exacto y `destination_key`. Sin auto-init, latest, selección implícita de revisión ni cursor que decida qué alertar.

Cada enqueue, incluso un replay antiguo, debe:

1. Validar paths/owners/schemas y MANIFEST_V1 completo mediante los contratos originales.
2. Leer en una única transacción read-only del journal la señal seleccionada y su par exacto de evaluaciones predecessor/current, con una verificación profunda completa del journal y un único presupuesto compartido. No repetir folds completos por cada campo si ya existe una lectura consistente verificada.
3. Rechazar señal ausente, baseline sin señal, vínculos inválidos, contenido corrupto o transición no elegible. No aceptar un JSON, hash, DTO o booleano `verified` del caller como autoridad.
4. Releer en P5a la revisión histórica exacta congelada en ambos snapshots, comprobar identidad canónica y configuración completas contra el manifiesto, y recalcular ambos resultados con el evaluador P5a sin cambiar sus reglas.
5. Comprobar señal, secuencia, regla, snapshots/resultados y enlaces con las identidades y transición fresh NO_MATCH→MATCH de P5b. Las dos reglas se admiten separadamente; el OR agregado no concede autoridad.
6. Construir una proyección semántica estricta y acotada de la evidencia y una admisión privada ligada a su contenido para el writer del nuevo outbox.

El bundle retenido comprende la señal completa y los dos snapshots normalizados con resultados recalculados e identidades. Sus snapshots incluyen la evidencia anterior que exige el evaluador. Excluir paths, tiempos de persistencia, head actual, contadores globales, run_id y hashes del archivo completo: posteriores appends del journal no deben alterar una alerta histórica.

La verificación es local y bajo los supuestos de revisiones inmutables y directorios confiables. No hay transacción distribuida entre las tres bases ni autenticación criptográfica del productor. Cada lectura de origen debe ser consistente; no afirmar un snapshot atómico global.

Una revisión histórica distinta de la vigente puede generar un preview de simulación, siempre etiquetado como tal. No equivale a una preferencia vigente ni a autorización actual de notificación. Las operaciones de esta fase no deciden enviar ni consultan latest para reinterpretar la historia.

## 7. Política, identidad y evidencia inmutable

Política nueva y versionada: `watchlist_synthetic_alert_v1`. Solo `WATCHLIST_RULE_ENTERED_MATCH`, reglas `price` y `restock`, `mode=synthetic`, evidencia declarada por el productor y verificada localmente. Canal exclusivamente `offline_preview`, estado exclusivamente `pending`.

`destination_key` es un alias local ASCII con gramática `^[a-z][a-z0-9_-]{0,63}$`; no es un chat ni una ruta de entrega. No leer configuración Telegram.

Identidad nueva, separada de `alt1`: prefijo `walt1_` y SHA256 con separación de dominio. Congelar:

`walt1_ + sha256(ASCII("CMT_WATCHLIST_ALERT_V1") + 0x00 + canonical({"identity_version":1,"destination_key":alias,"signal_id":wsig1})).hexdigest()`.

Canonical JSON: exactamente la codificación aceptada por P5b, con tipos estrictos, orden de claves, separadores compactos, ensure_ascii y prohibición de NaN. Incluir vectores con preimage literal, byte NUL real y digest esperado calculado por un oráculo independiente. No usar `evt3`, `cmp3`, `alt1` o `tdl1` ficticios.

Una combinación destino/señal produce una intención. La misma señal para dos aliases produce dos intenciones. Precio y reposición de una misma evaluación son señales y alertas distintas; un episodio posterior genera una nueva alerta.

Congelar intención, proyección semántica original, sus digests, texto renderizado, versiones y primer tiempo de preparación. El ID no contiene texto, renderer, paths ni clocks operativos; ante el mismo ID con contenido o versiones incompatibles, conflicto explícito, sin overwrite. No implementar rerender ni migración en esta fase.

Replay idéntico preserva bytes, primer tiempo de preparación y cardinalidades, incluso tras appends posteriores del journal o revisiones nuevas de Watchlist. Si los originales faltan o fallan verificación, enqueue/recompute falla; no convertirlo en un replay válido por encontrar el ID en el outbox. Get/preview/verify local siguen siendo operaciones diferentes.

No prometer deduplicación global entre copias, restauraciones o bases independientes, ni entrega exactly-once.

## 8. Renderer y preview

Texto determinista y seguro, máximo 4096 bytes UTF-8, plaintext, sin Markdown/HTML interpretables ni enlaces activos generados. Encabezado inequívoco: `SYNTHETIC — DEMONSTRATION ONLY`; indicar que no es una oferta real ni una notificación comercial.

Mostrar CMT ID, watch_id, revisión histórica exacta, regla, signal_id, contexto temporal explícito y razones/resultados relevantes. Para precio: EUR en céntimos y coste efectivo solo cuando los componentes estén disponibles y sean válidos; no inventar shipping, descuento o precio de referencia. Para reposición: describir la transición sintética de la regla, sin presentarla como stock observado de una tienda.

No añadir nombres, URLs, PII o campos arbitrarios del manifiesto. Escapar controles, saltos de línea de entrada, ESC, bidi y backslashes con la misma disciplina del renderer P8a. Fallar por oversize en lugar de truncar silenciosamente. Hash del mensaje sobre sus bytes UTF-8 exactos. Preview es read-only y no importa/invoca transporte.

## 9. Persistencia y concurrencia

Esquema mínimo STRICT, versionado, con inventario exacto de objetos, constraints, FK/índices y prohibición de mutaciones de registros inmutables. Evitar añadir tablas que no resuelvan un requisito de esta fase.

BEGIN IMMEDIATE debe comprometer intención y evidencia juntas. La primera admisión es recorded/prepared; un duplicado semánticamente idéntico es replay; un conflicto revierte todo. Dos procesos idénticos: una inserción y un replay. No resetear el presupuesto ni reintentar cambiando la evidencia.

Ningún enqueue escribe en Watchlist, journal, capturas, Discovery, outboxes previos o delivery ledger. Comprobar no mutación byte a byte en fuentes quiescentes; distinguir cambios deliberados de fixture por el probe.

## 10. Verificación y recomputación

- **Verify local:** exact schema/owner/version, integridad/FKs, tipos y tamaños antes de decodificar, proyección normalizada, resultados P5a recalculados, relaciones de la pareja, señales/identidades, política, texto/digests y registros completos. Rechazar corrupción aunque el atacante de prueba recalcule hashes y restaure triggers. Un fold local no prueba existencia o autenticidad de los originales.
- **Recompute contra originales:** alerta seleccionada + manifiesto completo + Watchlist/journal originales; repetir admisión y comparar toda la proyección, intención y renderizado. Fuentes ausentes o distintas fallan. Sin escrituras.
- No confiar en un resultado histórico persistido por tener un digest correcto. Cada operación nueva recomputa su propia evidencia; reutilización interna solo tras validación y dentro del mismo snapshot/operación. Sin caches globales o entre verificaciones independientes.

## 11. CLI y límites

Grupo sugerido `cmt watchlist-alert-outbox`, con paths explícitos y comandos init, enqueue, get, list, evidence-get, preview, verify, recompute, backup y restore. Enqueue selecciona **una señal**; no batch/bulk. Congelar argumentos y respuestas en contrato antes de implementar.

Respuestas JSON versionadas, tipos/campos exactos, categorías de error y exit codes coherentes con el proyecto. Sin traceback o SQL crudo en stdout/stderr de producto.

Límites autorizados:

- Input externo JSON ≤1 MiB, profundidad ≤16, nodos ≤20.000, strings ≤1024 donde corresponda; mantener límites originales más estrictos de P5a/P5b.
- Intención canónica ≤64 KiB; evidencia canónica completa por alerta ≤256 KiB; mensaje ≤4096 bytes UTF-8.
- List devuelve summaries, sin bundles ni mensajes completos; limit default100, max1000, respuesta ≤1 MiB y cursor keyset validado ligado a filtros/versión. Nunca devolver una página parcial con result=ok tras timeout/corrupción.
- Un presupuesto cooperativo por operación: default2 s, máximo5 s, positivo y finito. Compartirlo entre admisión, lecturas, transacción, verificación y recuperación; no dar cinco segundos nuevos a cada etapa. El harness puede pasar 5 explícitamente; no cambiar el default para ocultar coste.

Si una frontera original impone un límite menor, respetarlo. No ampliar contratos o límites anteriores unilateralmente.

## 12. Recuperación y seguridad

Backup consistente a destino nuevo; restore exclusivo sin sustituir archivos existentes. Verificar origen, copia y reapertura antes de exponer el destino, con lecturas/recomputaciones independientes y el mismo presupuesto. Preservar checks de owner, inode, hardlinks, reparse points y sidecars.

Aplicar la corrección aprendida de P5b: fallo de unlink tras publicación exclusiva debe compensar solo enlaces propios seguros y conservar el error original. No borrar reemplazos, enlaces ajenos o evidencia de recuperación. Persistent filesystem refusal puede requerir inspección manual; no prometer limpieza física incondicional.

Nada de restaurar/modificar originales o desactivar cuarentenas del ledger Telegram. Una copia del nuevo outbox sigue siendo solo preview.

Threat model: evidencia falsificada, relaciones inconsistentes, corrupción coherentemente rehasheada, inputs excesivos, contenido de control, cursores inválidos, carreras, lock/disk-full, timeout en cada etapa, caída de proceso, publicación incompleta y confusión entre preview sintético y alerta real. No afirmar resistencia frente a administrador hostil o cortes eléctricos físicos no ensayados.

## 13. Observabilidad y documentación

Logging JSON allowlisted y correlacionado: operación, resultado, categoría de error, duración y counts acotados. No volcar manifiestos, samples, mensajes completos, paths sensibles, aliases privados, token/chat IDs o excepciones crudas. IDs solo si su exposición está documentada y probada.

Entregables obligatorios:

- ADR-0014 para la ruta offline Watchlist y su separación de P8a/P8b.
- `WATCHLIST_ALERT_OUTBOX_V1` y `WATCHLIST_ALERT_OUTBOX_STORAGE_V1`, incluyendo proyección semántica, identidad, renderer, errores, CLI, límites, replay y fronteras de confianza.
- Arquitectura, threat model, LOGGING_V1 aditivo, testing/gates y runbook de recuperación actualizados.
- Deuda técnica con IDs nuevos solo si aparecen concesiones nuevas; no cerrar TD-001–TD-005 por esta fase.
- Ownership, Phase Completion Report y mapa de evidencia por AC.

## 14. Pruebas y gates

Unit, integration, contract y regression tests deben cubrir:

- Admisión desde manifest/revisión/señal originales y rechazo de DTOs/hashes autodeclarados; validación completa incluso en replay.
- Señal inexistente, baseline, UNKNOWN/INDETERMINATE/SKIPPED, predecessor expirado, reglas individuales, dos reglas y dos episodios; nada de regenerar señales que P5b no emitió.
- Vectores independientes de identidad, cambio de destino, aislamiento revisión/serie/producto y replay antiguo tras nuevos appends/revisiones.
- Renderer determinista, cantidades, campos desconocidos, controles/bidi, oversize y ausencia de rutas de envío.
- Corrupción local y coherente con hashes recalculados, originales distintos/ausentes y error sin escritura.
- Concurrencia real entre procesos, rollback en cada punto de escritura, crash/reapertura y no mutación de los almacenes originales.
- Backup/restore, corrupción introducida entre folds, timeout por etapa, fallos de fsync/link/unlink, hardlink adicional, reemplazos/sidecars ajenos y posterior recuperación.
- Límites, páginas/cursor, cancelación durante verificación, logging y cero intentos de sockets del producto.

Preservar todos los gates actuales: frozen installs, Ruff format/check, mypy strict, suite completa, cobertura separada ≥85 % líneas / ≥80 % ramas, sdist/wheel, instalación fuera del source, dependency audit y secret scan. No filtros de colección, excepciones amplias ni reducción de thresholds.

Añadir **duodécimo harness offline** y ejecutarlo junto a los once anteriores en installed wheel, Compose, AMD64 y ARM64/QEMU. Usar el pipeline normal desde un manifiesto sintético, revisiones P5a, cinco checkpoints P5b y sus cuatro señales; preparar alertas, comprobar replay/preview/recompute y backup/restore con procesos distintos. Mantener esa evidencia completa, sin reducir fixture para hacer pasar ARM64. Verificar UID10001/aislamiento de red donde corresponda.

Realizar mediciones locales acotadas del camino crítico sobre el mismo escenario en ARM64/QEMU cuando el entorno lo permita: validaciones, folds, copia, reapertura y publicación. Registrar al menos tres controles de backup y restore sin aumentar presupuesto; si no se dispone de QEMU local, declararlo y conservar CI como gate obligatorio. Evitar recomputación redundante y demostrar mediante probes que no se reutiliza autoridad de folds anteriores.

El CI final deberá tener cuatro jobs PASS sobre el HEAD/tree exacto. Una vez identificada una ejecución fallida, preservarla; no repetir jobs del mismo commit hasta obtener verde sin autorización. Los nuevos commits correctivos reciben su CI normal y sus revisiones afectadas. No confundir un PASS de timing local con validación remota ni con certificación Raspberry Pi física.

QA y REVIEWER ejecutarán probes propios con oráculos independientes. Publicar su código completo, helpers, instrucciones y resultados saneados recuperables desde GitHub, ligados a SHA/tree; hashes y rutas privadas por sí solos no bastan. Distinguir resultados históricos, nuevas ejecuciones y quién las realizó. Cualquier cambio posterior al candidato revisado exige renovar gates/revisiones aplicables.

## 15. Acceptance Criteria

| ID      | Criterio obligatorio                                                                                                          |
| ------- | ----------------------------------------------------------------------------------------------------------------------------- |
| AC-WA01 | Baseline/árbol/estado verificados; contrato y decisión de roadmap archivados con atribución correcta.                         |
| AC-WA02 | Enqueue selecciona una señal y revalida manifiesto completo, revisión P5a exacta y journal original.                          |
| AC-WA03 | Lectura journal consistente y profundamente verificada; DTOs/JSON/hashes de caller no autorizan escritura.                    |
| AC-WA04 | Evidencia semántica acotada, inmutable y suficiente para reconstruir resultados, transición y renderizado.                    |
| AC-WA05 | walt1\_ versionado con vectores independientes; separación total de identidades Discovery/delivery.                           |
| AC-WA06 | Una alerta por destino/señal; aislamiento de reglas, episodios, revisiones, series y productos.                               |
| AC-WA07 | Replay antiguo idempotente tras crecimiento de fuentes; conflictos y fuentes inválidas sin overwrite ni escritura parcial.    |
| AC-WA08 | Intención/evidencia atómicas; concurrencia y crash/reapertura preservan integridad.                                           |
| AC-WA09 | Preview determinista, plaintext y sintético explícito; límites/controles y ausencia de transporte comprobados.                |
| AC-WA10 | Verify local reconstruye evidencia y rechaza corrupción rehasheada; no afirma autenticidad del origen.                        |
| AC-WA11 | Recompute contra originales read-only, exacto y distinto de verify local.                                                     |
| AC-WA12 | CLI, input, páginas, cursores, errores y presupuesto compartido 2s/5s conformes.                                              |
| AC-WA13 | Backup/restore verificados independientemente, publicación exclusiva y compensación segura ante fallos.                       |
| AC-WA14 | Cero sockets del producto y no mutación de fuentes/prior stores; rutas Telegram anteriores siguen rechazando la nueva alerta. |
| AC-WA15 | Observabilidad allowlisted, threat model y protección de información sensible comprobados.                                    |
| AC-WA16 | Los once harnesses anteriores y el duodécimo pasan en wheel, Compose, AMD64 y ARM64/QEMU.                                     |
| AC-WA17 | Suite completa, coberturas y todos los gates de calidad/seguridad PASS sin debilitamiento.                                    |
| AC-WA18 | QA/REVIEWER independientes sobre HEAD/tree final, probes reproducibles publicados y hallazgos resueltos.                      |
| AC-WA19 | ADR-0014, contratos, runbook, arquitectura, deuda y documentación sincronizados con el candidato.                             |
| AC-WA20 | Informe final y evidencias publicados/readback; limitaciones y fallos previos conservados; sin merge ni cierre anticipado.    |

Cada AC requiere PASS/FAIL/BLOCKED y evidencia individual. El número de tests o la presencia de un método no demuestra por sí solo un criterio.

## 16. Ejecución, publicación y handoff

Empieza por auditar baseline y dependencias; después entrega el Engineering Brief y ownership a Codex. Congelar ADR/contratos/diseño antes de codificar identidades o schema. Resuelve decisiones rutinarias dentro de este contrato sin solicitar confirmaciones adicionales. Ante una incompatibilidad de alcance, identifica la decisión concreta que requiere al Orchestrator.

Autorizado: rama, commits de fase, PR, CI normal por nuevos commits y publicación saneada de informes/evidencia en el PR. **No autorizado: merge, bypass de protecciones, fuentes nuevas, llamadas a Telegram, aceptación final o cierre.** Preservar ramas, worktrees, originales y evidencias.

Usar conectores y CLI existentes autorizados sin extraer ni cambiar credenciales. Si una escritura remota falla, comunicar la limitación y entregar el texto listo; no afirmar publicación. Si una revisión automática rechaza una acción, indicar la acción y la razón y continuar únicamente por una alternativa permitida.

El Phase Completion Report incluirá: phase/status; branch/PR/commits/base/HEAD/tree; MODEL PROFILE USED; especialistas/ownership; objetivos e implementación; arquitectura/ADRs/contratos/DB/threat model; deuda y observabilidad; tests/gates; cuatro jobs exactos y logs completos; doce harnesses; QA/REVIEWER; AC-WA01–20 individualizados; mediciones y límites; incidencias/fallos conservados; enlaces públicos e informe de readback; recomendación al Orchestrator.

El Phase Lead debe contrastar directamente lo remoto que pueda y atribuir correctamente verificaciones locales de Codex y especialistas. No inventar ejecución, acceso a ZIP privado, identidad efectiva de modelos o verificación de hardware.

Si todos los gates aplicables pasan, proponer **READY_FOR_ORCHESTRATOR_REVIEW**. La aceptación y eventual autorización de integración serán otra decisión. Tras cualquier merge autorizado, se requerirán padres/árbol/diff/main y un nuevo CI push/main antes de que el Orchestrator pueda cerrar P8c.

P5 global permanece OPEN; TD-001–TD-005 OPEN; P2, P6a y Discovery retail BLOCKED. P8c no autoriza otra fase ni cambia esos estados.

**P8c — OPEN / IMPLEMENTATION AUTHORIZED.**