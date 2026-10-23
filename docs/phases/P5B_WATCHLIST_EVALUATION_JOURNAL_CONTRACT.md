# P5b — Watchlist Evaluation Journal & Signal Deduplication

## Prompt de apertura del chat de fase

**From:** 00 — ORCHESTRATOR\
**To:** P5b Phase Lead\
**Proyecto:** Card Market Tracker — `KastaTM/card-market-tracker`\
**Fecha:** 2026-10-23\
**Estado:** OPEN — IMPLEMENTATION AUTHORIZED\
**Autoridad de aceptación, integración y cierre:** exclusivamente 00 — ORCHESTRATOR.

Actúa como Phase Lead de P5b. Dirige el trabajo hasta entregar un candidato completo, probado y revisable. P5b amplía la trazabilidad de las simulaciones de Watchlist; no declara completa toda P5.

## 1. Decisión y baseline

**P5a — Watchlist Core & Offline Rule Evaluation: ACCEPTED / PHASE CLOSED**, declarado por el Orchestrator en este chat el 2026-10-23 tras contrastar la integración y su nuevo CI.

| Objeto                  | Identidad autorizada                                                                                            |
| ----------------------- | --------------------------------------------------------------------------------------------------------------- |
| Repositorio             | KastaTM/card-market-tracker                                                                                     |
| Base/main de P5b        | `ddd5fe3bbc7e40947bd838f71ee25e7046ff1b7e`                                                                      |
| Árbol de la base        | `f0eaf874e8671f75904ece1f618c283d7ff91536`                                                                      |
| Primer padre de la base | `d1038df1625a9727b44760866266b7124bb1d91a`                                                                      |
| Segundo padre           | `02ab89677afe11901ea5a2b1b8826604ce543c2f`                                                                      |
| PR anterior             | [#15 — MERGED](https://github.com/KastaTM/card-market-tracker/pull/15)                                          |
| CI posterior al merge   | [39978853326](https://github.com/KastaTM/card-market-tracker/actions/runs/39978853326)                          |
| Informe de integración  | [Integration Completion Report](https://github.com/KastaTM/card-market-tracker/pull/15#issuecomment-6369193856) |

P5a entregó 1.876 pruebas PASS, un skip, cobertura 94,67 % / 89,41 %, cuatro jobs y diez harnesses. Son resultados históricos, no pruebas ejecutadas para P5b.

Verifica Git/remote/main/árbol y estado de trabajo antes de modificar. Rama sugerida: `feat/p5b-watchlist-signal-journal`. Preserva ramas, worktrees y evidencias existentes. Si main ha avanzado, comunica la divergencia de baseline sin integrar cambios silenciosamente.

Incorpora este contrato al repositorio y añade una entrada nueva al roadmap que registre P5a cerrada/P5b abierta, atribuida a esta decisión de chat. No afirmes que se publicó un comentario remoto de cierre si no ocurrió; conserva las entradas e informes históricos.

P2, P6a y Discovery retail permanecen **BLOCKED**. TD-001–TD-005 siguen **OPEN**. P5 completo permanece abierto.

## 2. MODEL PROFILE

Perfiles solicitados, según disponibilidad real:

- ChatGPT Phase Lead: **GPT-6.1 Sol / High en Work**; si se usa Chat normal, **Astra / High** cuando figure en el selector.
- Codex Engineering Lead: **GPT-6.1 Sol / Medium**.
- ARQ/DB-OWNER y SEC/SRE: **GPT-6.1 Sol / High** para diseño crítico.
- QA y REVIEWER independientes: **GPT-6.1 Sol / High**.

Medium para implementación rutinaria; High para identidad, orden temporal, transiciones, CAS y recuperación. Escala a Astra / High si persiste un desacuerdo crítico. No bloquees decisiones rutinarias por un selector ausente: documenta la alternativa disponible.

Incluye **MODEL PROFILE USED**, distinguiendo petición, selección observable e internals no verificables. No inventes el modelo o reasoning efectivo. [Referencia oficial de disponibilidad](https://learn.chatgpt.com/docs/models).

Asigna ownership antes de paralelizar. QA y REVIEWER serán distintos de los autores y entre sí, con probes propios vinculados al SHA/árbol final.

## 3. Objetivo y utilidad

P5a calcula un predicado puro. P5b debe permitir conservar una secuencia explícita de esas evaluaciones y responder:

- Qué revisión de configuración y muestras sintéticas produjeron cada resultado.
- Cuál fue la primera evaluación usada como baseline de una secuencia.
- Cuándo una regla pasó de NO_MATCH a MATCH entre evaluaciones seleccionadas.
- Si una repetición es replay, una condición sigue en MATCH o existe otra transición posterior.
- Si el historial y las señales pueden reconstruirse sin confiar en filas de resultado autodeclaradas.

El producto será un **journal independiente y durable de evaluaciones/señales sintéticas**, consultable por CLI. No implementes entrega ni conexión con outboxes.

## 4. Alcance autorizado

Incluye:

- Admisión mediante manifest completo, revisión Watchlist existente y muestras P5a.
- Snapshot inmutable de entrada validada, configuración y resultado recalculado.
- Secuencias independientes, baseline explícito y señales por regla.
- Identidades deterministas, replay/conflictos y transacciones atómicas.
- Consultas, verificación local profunda, recomputación contra Watchlist, backup/restore.
- Undécimo harness offline.

**Retención nueva y acotada:** P5b autoriza guardar copias normalizadas de las muestras sintéticas necesarias únicamente en su nuevo journal. La base Watchlist de P5a continúa guardando solo preferencias/revisiones; no se relaja su prohibición de persistir muestras o evaluaciones allí.

Fuera de alcance:

- Fuentes, precios/stock comerciales, URLs, credenciales o nuevas adquisiciones.
- Scheduler, daemon, consultas automáticas de última muestra o procesamiento masivo.
- Nuevos eventos Discovery, modificación de cmp3/evt3/alt1 o promoción de candidatos.
- Puente a P8a/P8b, otros outboxes, delivery, mensajes o pruebas reales Telegram.
- Cambios de reglas de P5a, descuentos de mercado, oportunidades o cierre completo de P5.

Presupuesto de red de producto: **cero**. Instalación/build/auditoría por canales de desarrollo existentes no autoriza acceso a fuentes o destinatarios.

## 5. Admisión y snapshot verificable

Una operación record recibe:

- Base Watchlist P5a y base de journal distintas y explícitas.
- Manifest completo, watch_id y revisión exacta.
- Muestra actual, previa opcional y as_of explícito.

Reutiliza los validadores y la aplicación/evaluador P5a **sin modificarlos**. Revalida manifest completo, identidad y revisión; nunca aceptes resultados MATCH/JSON, hashes o snapshots aportados por el llamador como autoridad.

Deriva y congela:

- Configuración y proyección canónica de la revisión seleccionada.
- Versiones de contratos/política.
- Actual, previa y as_of normalizados.
- Resultado completo de P5a, reglas y razones individuales.

La entrada actual se admite solo con provenance synthetic. No se retienen extras, manifest completo, nombres ni datos personales si no son necesarios para recomputar la política; la identidad canónica congelada incluye sus relaciones necesarias. Rechaza datos incompatibles y muestras malformadas incluso para revisiones deshabilitadas.

Una revisión histórica explícita es válida para simulación. No la presentes como configuración actualmente vigente ni como autorización de notificación. Cambiar revisión abre otra secuencia y no reprocesa automáticamente el historial anterior.

Los datos de origen son de solo lectura. Congela el snapshot validado antes de la escritura atómica; documenta la falta de atomicidad distribuida y el supuesto de revisiones/orígenes inmutables. Construir una dataclass o una bandera verified no puede saltarse la admisión.

## 6. Identidades y secuencias

Congela en ADR/contratos los preimages exactos antes de implementar.

**Secuencia:** combinación de watch_id, revisión, versión de política de señales y series_key sintética. Las reglas se evalúan individualmente dentro de esa secuencia. No mezcles series, productos, variantes o revisiones.

**Evaluación:** identidad determinista versionada —prefijo sugerido wje1— derivada del contenido semántico normalizado: revisión/configuración/identidad congeladas, versiones, muestras completas y as_of. Excluye reloj de inserción, ruta de archivo, run_id, orden físico y destinatarios.

**Señal:** identidad determinista versionada —prefijo sugerido wsig1— que vincule secuencia, regla y evaluaciones anterior/actual. Un par elegible produce como máximo una señal por regla, sin nombres ni mensajes en su identidad.

Incluye vectores de identidad con preimage literal y digest esperado. QA debe recalcularlos independientemente del helper productivo. Distingue identidad local de autenticación de origen.

## 7. Orden, continuidad y replay

Para una evaluación nueva:

- observed_at actual avanza estrictamente respecto al último actual de la secuencia.
- as_of no retrocede respecto al último as_of.
- sample_id actual no se reutiliza dentro de la secuencia.
- Desde la segunda evaluación, el operador debe aportar previous y su forma canónica debe ser exactamente la muestra actual del predecesor registrado.
- No rellenes previous, no selecciones latest implícitamente, no reordenes ni insertes historia en mitad de la secuencia.

La primera evaluación puede tener previous válido externo a la secuencia; aun así es solo baseline.

Excepciones de repetición:

- Misma evaluación semántica ya registrada: replay, incluso si existe historial posterior.
- Replay no mueve el head, no duplica señales ni cambia la primera fecha de persistencia.
- Mismo sample_id de la secuencia con contenido, as_of o resultado distinto: conflicto.
- Mismo instante con otra muestra o predecessor distinto: error de cronología/conflicto, sin mutaciones.
- Un cambio en configuración/identidad para la misma revisión es conflicto, no otra secuencia.

Una evaluación se registra una vez por observación seleccionada y secuencia. Volver a evaluar la misma muestra con otro as_of no constituye una nueva observación y no puede usarse para avanzar el journal. Explica esta decisión en el contrato.

## 8. Política de señales — congelar antes de implementar

Usa los resultados **por regla** de P5a, no el OR agregado para decidir todas las señales.

| Situación                                                      | Señales nuevas                                       |
| -------------------------------------------------------------- | ---------------------------------------------------- |
| Primera evaluación de la secuencia, incluso MATCH              | 0; baseline                                          |
| Regla anterior NO_MATCH y actual MATCH, con continuidad fresca | 1 para esa regla                                     |
| MATCH → MATCH                                                  | 0                                                    |
| Actual NO_MATCH                                                | 0; queda como nuevo baseline no satisfecho           |
| Actual INDETERMINATE o SKIPPED                                 | 0; interrumpe continuidad conocida                   |
| INDETERMINATE/SKIPPED → MATCH                                  | 0; nuevo baseline satisfecho                         |
| Predecesor caducado respecto al nuevo as_of                    | 0; nuevo baseline                                    |
| Cambio de revisión/política/serie                              | Secuencia independiente, primer registro sin señales |

**Continuidad fresca** requiere muestra actual y muestra del predecesor dentro de max_age_seconds respecto al as_of de la evaluación actual, con el borde inclusivo P5a y previous igual al predecesor. Un NO_MATCH que fue fresco al registrarse puede haber caducado ahora; no lo uses para inferir una transición nueva.

Conserva sin cambios la semántica de P5a: datos desconocidos no son OUT_OF_STOCK, dinero en enteros EUR, precio incluye envío conocido, validación antes de SKIPPED y frescura antes de stock.

Tras NO_MATCH→MATCH→MATCH→NO_MATCH→MATCH, deben existir exactamente dos señales de esa regla. Si dos reglas entran en MATCH en el mismo paso, pueden producir dos señales distintas. Un MATCH de precio no oculta una transición independiente de reposición.

Tipo semántico sugerido: WATCHLIST_RULE_ENTERED_MATCH, con regla price/restock, modo synthetic y referencias a las evaluaciones. No lo etiquetes como evento real de mercado o prueba de reposición de una tienda. La observación se limita a los puntos seleccionados; no garantiza ausencia de cambios intermedios.

## 9. Persistencia, concurrencia e integridad

Nuevo SQLite con owner/application_id/schema_version propios; diseño mínimo justificado, sin framework genérico ni migraciones de bases aceptadas.

Una transacción atómica registra:

1. Evaluación inmutable.
2. Todas las señales derivadas, incluso cero.
3. Nuevo head/proyección de secuencia.

La transacción verifica el predecesor/head vigente o deriva el fold bajo su snapshot; evita decisiones basadas en un head leído antes y ya obsoleto. Ante conflicto concurrente no debe quedar ninguna inserción parcial.

Dos procesos con la misma evaluación: una inserción y un replay. Dos sucesores incompatibles del mismo head: como máximo uno avanza; el otro falla sin sobreescribir. Nada de retries que cambien automáticamente la evidencia elegida.

Evalúa cada regla mediante una función pura de transición. Su resultado es derivado, no un DTO arbitrario aceptado por almacenamiento.

La verificación profunda reconstruye:

- Esquema exacto, índices, relaciones y owner/version.
- Identidad y contenido normalizado de cada registro.
- Resultados P5a recalculados desde snapshots.
- Orden, unicidad de muestra y enlaces de predecesor.
- Fold completo, conjunto exacto de señales y heads actuales.

Detecta señales añadidas, ausentes o cambiadas, heads atrasados/adelantados, huecos, duplicados y resultados alterados aunque se hayan rehasheado campos locales.

## 10. Verificación local y recomputación original

**verify local:** solo lee el nuevo journal y comprueba consistencia/recomputación de sus snapshots y secuencias.

**recompute contra Watchlist:** selecciona un registro explícito; reabre la revisión original en P5a, valida de nuevo el manifest completo, compara identidad/configuración y ejecuta el evaluador sobre las muestras retenidas. Revisión ausente, identidad incompatible o resultados distintos fallan.

Ambas operaciones son de solo lectura. La segunda vincula la configuración al origen Watchlist; no autentica un proveedor de precios ni prueba que las muestras declaradas synthetic procedan de una fuente independiente. No afirmes recomputación de muestras comerciales.

Un administrador que reescriba coherentemente todas las autoridades locales permanece fuera de la garantía. No prometas autenticidad criptográfica de archivos o retención eterna.

## 11. CLI, límites y recuperación

CLI sugerida: cmt watchlist-journal, con init, record, get/list, signal-get/signal-list, verify, recompute, backup y restore. Congela nombres, argumentos, salida JSON y errores antes de implementar.

- Sin init implícito ni barridos de todas las watchlists.
- record procesa una evaluación explícita.
- Consultas paginadas, default 100/max 1.000, límite 1 MiB y cursores vinculados a filtros/orden.
- Parsers de entrada con 1 MiB/depth 16/nodes 20.000/string 1.024 y límites más estrechos de campo ya vigentes.
- Fija un límite pequeño de registro canónico, por ejemplo 64 KiB, incluyendo snapshots/resultado.
- Presupuesto local compartido default 2 s/max 5 s, aplicado a toda la operación.
- Whole-history verify que agote el presupuesto falla; no devuelve PASS parcial.

Backup consistente y restore a destino nuevo con verificación antes de exposición, sin reemplazar archivos existentes. Preserva protecciones de inode, directorios confiables y sidecars; no borres evidencia de otro proceso al limpiar.

El restore recupera este historial hasta la copia; no recupera automáticamente registros posteriores ni coordina otras bases. No toca outboxes o ledgers Telegram y no levanta su cuarentena. No se implementa entrega, así que no atribuyas al journal garantías globales de exactly-once ni introduzcas un estado sent.

## 12. Compatibilidad, ADR y documentación

Preserva sin cambios los paquetes operativos aceptados, incluido watchlist de P5a. Permite registro mínimo en CLI/logging, documentación y wiring del nuevo harness. Un nuevo módulo/paquete dedicado reutilizará interfaces públicas existentes.

Nuevos documentos:

- ADR siguiente libre, previsiblemente **ADR-0013**.
- WATCHLIST_JOURNAL_V1.
- WATCHLIST_JOURNAL_STORAGE_V1.
- WATCHLIST_SIGNAL_V1.

Actualiza arquitectura, logging, threat model, testing/gates, roadmap, deuda y recuperación. Explica la autorización limitada a retener muestras sintéticas en el nuevo journal y por qué no cambia los contratos P5a/P2.

No añadas tipos Watchlist al ALERT_OUTBOX_V1 ni al journal Discovery. P8a exige evidencia Discovery v3, por lo que no admite estos resultados sin una futura decisión de contrato/fase.

## 13. Pruebas y quality gates

Prueba como mínimo:

- Admisión por manifest/revisión originales y rechazo de resultados autodeclarados.
- Primera evaluación MATCH sin señal; segunda elegible con transición.
- Repetición estable, dos episodios y dos reglas sin ocultación por OR.
- UNKNOWN, INDETERMINATE, SKIPPED, caducidad y reinicio de continuidad.
- Revision/serie independientes, muestras fuera de orden, sample_id reutilizado y previous incorrecto.
- Replay antiguo sin mover head ni timestamps; conflictos sin sobrescritura.
- Dos procesos iguales y sucesores incompatibles.
- Fallos entre registro/señales/head, rollback y reapertura.
- Corrupción de señales/head/historia y resultados rehasheados.
- verify local frente a origen ausente/cambiado en recompute.
- Backup/restore exclusivo, fallos de IO y sidecars.
- Límites, cursores/errores/logs saneados y cero sockets.
- Nonmutation de Watchlist y demás bases aceptadas.

Añade **undécimo harness offline**, wheel instalado fuera del source, procesos separados, reinicio y persistencia. Demuestra baseline→señal→replay→sin duplicado→otro episodio, verificación/recomputación y backup/restore.

Conserva los diez harnesses anteriores. Cuatro jobs: Quality, Compose, AMD64 y ARM64/QEMU. Frozen install, Ruff format/check, mypy strict, suite completa, cobertura mínimo 85 % líneas/80 % ramas o umbrales vigentes superiores, sdist/wheel, dependency audit y secret scan. No reduzcas gates ni ocultes regresiones. Explica variaciones de cobertura.

QA y REVIEWER ejecutarán probes propios sobre head/tree final, con oráculos de fold e identidad independientes y código/evidencia reproducibles publicados. No basta con enlaces a rutas privadas.

Observabilidad: logs estructurados de operación, categoría, resultado, duración y contadores. Excluye muestras, precios, preferencias, nombres, rutas y payloads. El stdout detallado/DB/backup es información local sensible del operador.

No existe gate live ni permiso para Telegram. QEMU y pruebas de proceso no acreditan hardware Pi ni cortes eléctricos reales.

## 14. Acceptance Criteria — AC-S01–AC-S18

| AC  | Condición verificable                                                                    |
| --- | ---------------------------------------------------------------------------------------- |
| S01 | Baseline exacto, contrato archivado y registro P5a cerrada/P5b abierta                   |
| S02 | Admisión mediante manifest/revisión originales; P5a recalculado, no resultados confiados |
| S03 | Snapshot completo y acotado, solo synthetic; retención únicamente en nuevo journal       |
| S04 | Identidades versionadas y vectores independientes para evaluaciones/señales              |
| S05 | Secuencias independientes por revisión/serie/política, sin mezclar productos             |
| S06 | Baseline inicial sin señales aunque sea MATCH                                            |
| S07 | Transiciones por regla correctas; MATCH persistente y OR no duplican/ocultan señales     |
| S08 | Incertidumbre, desactivación y caducidad interrumpen continuidad sin falsos positivos    |
| S09 | Cronología/as_of/previous/sample_id estrictos y sin selección implícita                  |
| S10 | Replay antiguo idempotente y conflictos sin mutaciones                                   |
| S11 | Registro/señales/head atómicos y concurrencia con un avance válido                       |
| S12 | Verificación profunda reconstruye resultados, fold, señales y heads                      |
| S13 | Recompute vincula revisión original y distingue consistencia de autenticidad             |
| S14 | CLI/paginación/recursos acotados, logs seguros y cero red                                |
| S15 | Reopen, rollback y backup/restore exclusivos sin afectar otras bases                     |
| S16 | Compatibilidad previa, undécimo harness y cuatro jobs del candidato PASS                 |
| S17 | QA/REVIEWER independientes sobre SHA/tree final, hallazgos corregidos                    |
| S18 | ADR/contratos/threat/runbook/deuda/observabilidad e informe trazables                    |

Cada AC tendrá evidencia individual. FAIL/BLOCKED se declaran, no se convierten en PASS por estar implementado un método o presente un test.

## 15. Ejecución y handoff

Lee AGENTS.md y documentos aplicables. Presenta un Engineering Brief breve con los contratos/invariantes congelados y continúa con decisiones normales dentro del alcance.

Autoriza creación de rama, implementación, pruebas y PR abierto. **El merge no está autorizado por esta apertura.**

El Phase Completion Report incluirá:

- Branch/base/commits/head/tree y MODEL PROFILE USED.
- Ownership real, funcionalidad, arquitectura, contratos y DB.
- AC-S01–S18 individualizados.
- Tests/cobertura, cuatro jobs y logs completos contrastados.
- Dos informes independientes con probes reproducibles del SHA final.
- Hallazgos/correcciones, observabilidad, seguridad, límites y deuda.
- Publicación en el PR y recuperación por lectura del contenido completo.

Si el conector devuelve403, usa solo capacidades locales existentes y autorizadas, sin extraer/cambiar credenciales. Si no puedes publicar, entrega texto listo y declara el bloqueo; no afirmes publicación.

No declares ACCEPTED ni PHASE CLOSED. Entrega **READY_FOR_ORCHESTRATOR_REVIEW** solo cuando los gates estén acreditados. El Orchestrator decidirá aceptación, integración y cierre de esta subfase; P5 completo y futuras conexiones reales seguirán necesitando decisión explícita.

Empieza por preflight y Engineering Brief; continúa hasta dejar el candidato completo y revisable.