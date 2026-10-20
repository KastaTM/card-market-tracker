# P4c — Discovery Result & Event Journal

## MODEL PROFILE

- **ChatGPT recomendado:** GPT-6.1 Sol / High en ChatGPT Work, si está disponible en el selector. En Chat normal, GPT-5.6 Sol / High si aparece disponible. Motivo: definir atomicidad, identidad y conservación de evidencia sin ampliar las fuentes.
- **Codex Engineering Lead recomendado:** GPT-6.1 Sol / Medium para coordinación y ejecución rutinaria; High para almacenamiento, contratos, concurrencia y depuración compleja.
- **Especialistas:** ARQ/DB-OWNER, BE/DISCOVERY y SEC/SRE, con GPT-6.1 Sol / High para el trabajo que lo justifique. QA y REVIEWER: GPT-6.1 Sol / High, distintos entre sí y de todos los autores.
- **Escalation:** subir primero a High; GPT-6 Astra / High únicamente ante un bloqueo complejo reproducido y si está disponible. Sin Max/Ultra por defecto.
- La selección depende de cuenta, cliente y rollout. Verifica disponibilidad; registra modelo/reasoning solicitados, aceptados y realmente observables. No atribuyas introspección del backend ni cambios de configuración que no hayas realizado.
- Fuente oficial consultada el 2026-10-19: [https://learn.chatgpt.com/docs/models?surface=web](https://learn.chatgpt.com/docs/models?surface=web). Sol 6.1 está disponible en Work/Codex, no en Chat normal. Los niveles recomendados son una decisión del Orchestrator para esta tarea.

## 1. Apertura, rol y objetivo

Actúa como Phase Lead de **P4c — Discovery Result & Event Journal** de Card Market Tracker.

El **00 — ORCHESTRATOR** abre P4c el **2026-10-19, Europe/Madrid**, después de declarar **P1c: ACCEPTED / PHASE CLOSED** en este chat. Esta decisión autoriza una subfase de persistencia de Discovery antes de P8a; no altera el significado de las fases originales.

Repositorio: [https://github.com/KastaTM/card-market-tracker](https://github.com/KastaTM/card-market-tracker)

Rama: `feat/p4c-discovery-result-journal`.

**Objetivo:** conservar de forma duradera y consultable los resultados de Discovery v3 y cada aparición de sus eventos, con replay idempotente, transacciones atómicas y evidencia original. Proporcionar una base para la futura entrega de alertas sin implementar transporte ni estados de entrega.

Hoy las comparaciones son reproducibles, pero su salida no constituye un registro persistido de resultados/eventos. P4c resuelve ese hueco. P2/P6a siguen bloqueadas por fuentes; no se añadirá otra captura real para simular progreso o fabricar novedad.

Se autorizan diseño acotado, implementación, rama, pruebas, documentación y PR. **No se autoriza merge.** Solo el Orchestrator acepta, cierra fases o amplía este alcance. Procede con las decisiones ordinarias de implementación sin solicitar confirmaciones repetidas.

## 2. Baseline y continuidad

| Objeto P1c cerrado            | Identidad                                                                                                                                                        |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PR integrado                  | [https://github.com/KastaTM/card-market-tracker/pull/11](https://github.com/KastaTM/card-market-tracker/pull/11)                                                 |
| Baseline / main               | `de63457bd6de26874a30d2afd688dcd8901e01ff`                                                                                                                       |
| Árbol                         | `41c0f758c8a4bf09cc719a1ce16073245a5aadda`                                                                                                                       |
| Primer padre                  | `112916382ce02486ca38eb14487220dbb24196e7`                                                                                                                       |
| Segundo padre                 | `8af647697dd67859b38fc007d493a54642a1d62f`                                                                                                                       |
| CI push/main                  | [https://github.com/KastaTM/card-market-tracker/actions/runs/39205644646](https://github.com/KastaTM/card-market-tracker/actions/runs/39205644646)               |
| Integration Completion Report | [https://github.com/KastaTM/card-market-tracker/pull/11#issuecomment-6272628048](https://github.com/KastaTM/card-market-tracker/pull/11#issuecomment-6272628048) |

P1c cerró con 1.068 pruebas PASS, un skip heredado y cobertura 95,62 % / 90,82 %. Son evidencias históricas; P4c necesita su propia ejecución sobre su candidato final.

Lee `context.md`, `AGENTS.md`, operating model, arquitectura, ADRs, contratos de persistencia/captura y DISCOVERY_V1/V2/V3, documentación de P1c, quality gates, testing strategy, threat model, runbooks y deuda. Verifica remote, refs, estado y worktrees antes de editar. Conserva cambios y ramas ajenos. Si `main` difiere del baseline, inspecciona y comunica el delta antes de trabajar sobre otra base; no la sustituyas silenciosamente.

Archiva este prompt como `docs/phases/P4C_DISCOVERY_RESULT_JOURNAL_CONTRACT.md`. Registra en el roadmap **P1c cerrada / P4c abierta**, atribuido a la decisión del Orchestrator en chat, con las identidades anteriores. Conserva los snapshots históricos. No inventes un comentario de cierre publicado en GitHub.

## 3. Alcance y exclusiones

Dentro del alcance:

1. Un servicio que recibe un request DISCOVERY_V3 y una DB de capturas existente, reconstruye/verifica la ventana con la ruta P1c y ejecuta el comparador puro existente.
2. Un journal SQLite independiente para guardar request normalizado, resultado completo, digest de contenido y apariciones de eventos.
3. Replay, conflictos, concurrencia, consultas acotadas, verificación y backup/restore del journal.
4. CLI, contratos, observabilidad, pruebas y séptimo harness offline.

Fuera: nuevas fuentes, nuevas revisiones o paquetes reales, expansión de corpus, HTTP de producción, scheduler, Telegram/email/webhooks, envío de mensajes, delivery/outbox/leases/acknowledgements, políticas de reintento de transporte, watchlist, precios, stock, retail, preorders, launches, matching o promoción canónica, API/frontend, análisis de mercado y retención destructiva.

**Presupuesto de adquisición de fuentes: cero.** Reutiliza los dos paquetes aprobados R0/R1, con sus revisiones, bytes/proyecciones, licencias y relojes originales. Leer código/CI del repositorio CMT no es adquirir una fuente. No acceder a TCGdex ni readquirir originales descartados. Ninguna prueba requiere secretos o credenciales de Telegram.

P2, P6a y Discovery retail permanecen **BLOCKED**. P8a y P5 no se abren por este contrato.

## 4. Límite arquitectónico y admisión

Mantén el comparador v3 puro. El servicio de aplicación orquesta lectura, comparación y escritura; el comparador no importa SQLite/journal ni ejecuta IO.

La admisión pública para registrar una comparación recibe **request v3 + ruta de capturas + ruta de journal**. Reutiliza `read_multi_revision_snapshots` y el comparador existente, con las validaciones completas de admisión, perfil, todas las unidades, cronología y límites. No re-resolver contra un manifest actual ni reimplementar el algoritmo.

No aceptes como prueba suficiente un JSON de resultado, `ScopedDiscoveryResult` público, IDs/digests declarados ni un objeto con banderas `verified`. Un DTO interno del escritor solo puede emitirse después de ese recorrido y debe ligar request/resultados por contenido. Sus consumidores deben revalidar el recibo y límites. Documenta el límite: es autoridad de aplicación en un proceso local confiable, no una firma ni resistencia a código privilegiado comprometido.

Errores de lectura, comparación o validación no generan entradas exitosas ni filas parciales. No archives `result:error` como `no_discoveries`. Los fallos operativos se registran en logs categorizados, sin crear una base de intentos en esta fase.

La transacción de lectura de capturas produce un snapshot coherente y verificado antes de escribir el journal. No hay atomicidad distribuida entre las dos bases: las capturas verificadas son inmutables por contrato, el resultado representa ese snapshot y el commit atómico pertenece al journal. Documenta y prueba este límite.

## 5. Almacenamiento y compatibilidad

**Decisión autorizada:** SQLite separado para el journal, con identidad de aplicación propia y schema v1 independiente. La DB de capturas conserva schema2 y sus cinco tablas, sin migración ni nuevas tablas. No conviertas accidentalmente un archivo de capturas en journal o viceversa.

El modelo lógico del journal tiene exactamente tres tablas de negocio/propiedad:

- Metadata de propiedad y versión del journal.
- Comparaciones, con clave `comparison_id` (`cmp3:`), request normalizado, resultado v3 canónico completo, digest SHA-256 del contenido semántico y primer instante de persistencia.
- Apariciones de eventos, con clave compuesta `(comparison_id, event_id)`, FK a comparación y ordinal determinista. Puede almacenar una representación normalizada o el evento completo, pero debe reconstruir exactamente el evento del resultado padre.

Usa constraints, índices, integridad/FKs y validación exacta de inventario/versiones. Las tres tablas no impiden índices o triggers documentados, ni tablas internas de SQLite si fueran necesarias por el motor. No desarrolles un framework de migraciones: solo inicialización explícita de journal v1 y rechazo seguro de versiones desconocidas.

`init` crea únicamente un journal nuevo mediante reserva segura en directorio confiable. No sobrescribe archivos existentes ni inicializa implícitamente durante record/list/get/verify. Rutas de capturas, journal y destino de backup/restore deben distinguirse también frente a alias/enlaces según la política existente; prueba samefile/hardlink/symlink donde la plataforma lo soporte. No dañes un archivo ajeno al rechazarlo. Mantén las restricciones de directorios locales confiables de TD-003.

Guardar request normalizado y resultado debe preservar profile/context/current/history, clocks, adquisición, scopes, extracción, counts, referencias, categorías y CMT ID congelado exactamente como v3 los emite. No copies bundles, manifests completos, filas fuente, nombres extra ni cuerpos upstream para justificar un ID. Conserva los avisos MIT existentes y documenta atribución de la mínima evidencia real retenida.

El digest usa JSON finito, ASCII escaped, compacto y ordenado, con receta explícita en contrato; cubre versión del journal, request y resultado semánticos. `first_recorded_at`, ruta, run ID y duración quedan fuera de él. El instante de primera persistencia es UTC local y no sustituye captura/adquisición ni fecha de evento.

## 6. Identidades, replay y ventanas

No cambies `cmp3:`/`evt3:`, sus preimágenes ni sus serializaciones. Tampoco cmp1/evt1/cmp2/evt2 o fingerprints históricos.

- Mismo `comparison_id` y mismo request/resultado canónicos: replay sin nuevas filas, sin reescritura y con `first_recorded_at` original.
- Mismo `comparison_id` con contenido semántico diferente: conflicto explícito y cero mutaciones; compara contenido, no solo digest. Prueba la rama mediante un mecanismo interno de test sin abrir admisión de JSON público.
- Otra comparación válida: entrada independiente aunque comparta current o eventos.
- Cada evento del resultado tiene exactamente una aparición en esa comparación; orden y conteo son coherentes. Cero eventos implica cero apariciones.

**Caso obligatorio:** `evt3` excluye historia de su identidad, pero la evidencia del evento contiene comparison_id e historia. Dos ventanas distintas pueden generar el mismo `evt3` con evidencia diferente. Conserva ambas apariciones y sus resultados completos; no colapses evidencias ni declares conflicto por ese caso. No hagas `event_id` globalmente UNIQUE en apariciones.

La deduplicación de persistencia es por comparación y aparición. No significa entrega exactamente una vez, novedad global, primera aparición del producto en el mundo ni permanencia del evento frente a cualquier cambio de ventana. Una consulta por `event_id` debe hacer visible que hay varias comparaciones, con paginación, sin elegir una evidencia arbitraria.

`baseline` y `no_discoveries` son resultados exitosos que también se conservan. El recorrido real obligatorio registra las cuatro comparaciones R0→R1 con `no_discoveries` y cero apariciones. Los eventos positivos persistidos se demuestran solo con capturas synthetic explícitas del perfil autorizado.

## 7. Transacciones, recuperación y verificación

Una sola transacción atómica guarda comparación y todas sus apariciones. Dos escritores concurrentes con la misma comparación terminan en una inserción y un replay coherente, o en error acotado de lock/deadline; nunca éxito parcial, filas duplicadas o overwrite. Ventanas distintas con el mismo evt3 deben poder coexistir.

Prueba fallos después de insertar comparación y durante apariciones, rollback, reapertura entre procesos y recuperación tras interrupción de proceso. No atribuyas resistencia a cortes eléctricos físicos a estas pruebas.

Hay dos niveles de verificación explícitamente distintos:

1. **Verify local del journal:** propiedad/esquema, integridad/FKs, JSON y límites, digest completo, índices/orden/counts y correspondencia exacta entre apariciones y resultado. No autentica el origen frente a un administrador que reescribe coherentemente el archivo.
2. **Recompute de una comparación explícita:** con la DB de capturas suministrada, reconstruir su request retenido, releer todas las capturas por la ruta P1c, recalcular y contrastar `comparison_id` y resultado semántico completo. Fuente ausente/cambiada/corrupta no es PASS ni borra o repara la entrada. Si el origen no se suministra, no afirmar que este segundo nivel pasó.

Local verify y recompute son read-only, sin inicializar, migrar o reparar. No necesitan nuevos datos externos. Una alteración coherente de la evidencia local debe detectarse por recompute cuando las capturas originales permiten demostrarla.

Backup/restore debe producir un journal consistente usando la API adecuada de SQLite, validar destino y contenido y preservar comparaciones, apariciones, digests y primera persistencia. Reutiliza patrones seguros existentes sin acoplar inventarios de ambos tipos de DB. No prometas un backup atómico de dos bases: captura y journal se gestionan por separado y el runbook explica la recomputación tras restaurarlos.

## 8. CLI, consultas, límites y observabilidad

Añade un grupo separado, por ejemplo `cmt discovery-journal`, con init, record, get, list, event-occurrences, verify, recompute, backup y restore. Los nombres exactos de flags pueden decidirse en el Engineering Brief, manteniendo esos casos de uso y el contrato estricto. `record` usa `--captures-db`, `--journal-db` y `--request`; no admite `--result` ni selección automática de última captura/historia.

No modifiques el stdout, códigos de salida ni efectos laterales de `discover`, `discover-scoped` o `discover-multi-revision`. Journal record tiene respuesta propia con estado insertado/replay, comparison_id y conteos; get recupera el resultado v3 retenido y su metadata del journal sin modificarlo.

List y event-occurrences devuelven resúmenes acotados, orden estable y paginación keyset con cursor estricto. Nunca `fetchall` o salida de toda la historia. Default 100, máximo 1.000 filas por página. Get devuelve una sola comparación y no expande todas las comparaciones de un evento.

Se mantienen los límites originales v3: request 1 MiB, profundidad 16, 20.000 nodos, string 1.024, historia 32, 33 batches/33.000 registros, 1.000 registros por batch y 1.000 eventos. No elevarlos ni rebajarlos silenciosamente en las rutas antiguas.

Límites adicionales del journal: máximo **16 MiB** de resultado canónico por comparación; salida de resúmenes paginados máximo 1 MiB. Verifica tamaños antes de cargas/allocations no acotadas, también ante SQLite manipulado, y serializa/calcula digest de forma acotada. Un resultado v3 válido pero demasiado grande para el journal falla con `input_limit` y cero escritura; la comparación pura original conserva su contrato. Documenta esta limitación y evita duplicar evidencia innecesariamente en memoria.

Operaciones con presupuesto finito: default 2 s, máximo explícito 5 s. Record comparte presupuesto entre lectura/verificación/comparación y escritura, sin reiniciar el reloj por etapa; las demás operaciones tienen presupuesto completo propio. Acota SQLite busy/progress y bucles de aplicación. Explica que no es garantía de latencia frente a bloqueo del SO/dispositivo. Verify completo puede fallar por deadline en una base grande; no convertir revisión parcial en PASS. No hay cuotas globales ni borrado automático.

Errores con categorías fijas: input/version/profile/unsupported evidence, path/owner/schema, missing, conflict, corruption, locked/deadline y IO según contratos. JSON propio versionado; stdout sin éxito parcial, exit 2 para inputs/contrato y exit 1 para fallos de almacenamiento/ejecución; documenta el mapa exacto preservando comandos previos. No convertir DB ausente en lista vacía.

Logs estructurados: operación, run ID, duración, inserted/replay/error y conteos acotados. Sin payloads, nombres, referencias, selectors, tokens, rutas, SQL ni excepciones crudas. La salida explícita del usuario puede incluir la evidencia contratada y requiere protección local.

## 9. Acceptance Criteria

| ID     | Condición verificable                                                                                         |
| ------ | ------------------------------------------------------------------------------------------------------------- |
| AC-J01 | Baseline verificado; contrato archivado; cierre P1c/apertura P4c y ownership documentados                     |
| AC-J02 | Journal separado, identidad/schema propios; init seguro; DB de capturas schema2 y cinco tablas intactas       |
| AC-J03 | Record solo desde request v3 + capturas verificadas; DTO/JSON/digest autodeclarados no conceden admisión      |
| AC-J04 | Request/resultado/evidencia/clocks se conservan; digest canónico documentado; hashes anteriores intactos      |
| AC-J05 | Inserción, replay sin reescritura y conflicto sin overwrite preservan primer instante y contenido             |
| AC-J06 | Mismo evt3 en dos cmp3 conserva ambas apariciones y evidencias; no falsa deduplicación global                 |
| AC-J07 | Atomicidad, rollback, escritores concurrentes y recuperación entre procesos sin filas parciales               |
| AC-J08 | Baseline/no_discoveries persistidos; cuatro comparaciones reales R0→R1 sin eventos; positivos synthetic       |
| AC-J09 | Get/list/event-occurrences estrictos, paginados, deterministas y read-only; errores no son vacíos             |
| AC-J10 | Verify local detecta corrupción/relaciones/digests; recompute contrasta origen completo sin confundir niveles |
| AC-J11 | Backup/restore conserva equivalencia; destinos/alias seguros; límites de dos DB documentados                  |
| AC-J12 | Límites de bytes/filas/tiempo/logs y errores comprobados, incluida DB hostil y resultado demasiado grande     |
| AC-J13 | Cero adquisición nueva; paquetes/guards/v1/v2/v3/identidad canónica/semántica existentes preservados          |
| AC-J14 | Wheel externo, Compose, AMD64 y ARM64/QEMU ejecutan los siete harnesses, incluido journal entre procesos      |
| AC-J15 | ADR/contratos/arquitectura/runbook/threat model/deuda/roadmap coherentes con implementación                   |
| AC-J16 | Todos los gates CI finales PASS; QA y REVIEWER independientes entre sí y de autores sobre SHA/tree exactos    |

Un criterio sin evidencia es FAIL o BLOCKED con causa, nunca PASS por intención o por el informe de un autor.

## 10. Pruebas y gates obligatorios

Pruebas unitarias/contrato/integración/regresión y adversariales cubren admisión forjada, datos mutados tras emisión, bool como int, campos extra, JSON duplicado/no finito/profundidad/tamaño, versión/DB ajena, ausente, links/rutas, corrupción coherente e incoherente, counts/ordinal/FK divergentes, locks/deadlines y concurrencia.

Incluye prueba independiente del caso mismo evt3/diferente cmp3; rollback con fallo inyectado; replay tras reapertura; recuperación de interrupción de proceso; paginación sin duplicados/omisiones en una vista estática y semántica explícita bajo inserciones concurrentes; verificación/recompute tras restauración; evidencia con tiempos de inserción distintos pero identidad igual. Un cursor no equivale a snapshot de toda la paginación: documenta las garantías reales.

QA realiza probes propios con expectativas independientes, no solo vuelve a ejecutar los tests de los autores. Contrasta digests e identidades sin copiar el helper bajo prueba. REVIEWER revisa el candidato final y cualquier cambio posterior invalida la atestación de ese SHA hasta nuevo contraste.

Añade `scripts/discovery_journal_smoke.py` o equivalente como séptimo harness: init, importación de capturas aprobadas/synthetic, record, reopen, get/list, replay, dos ventanas/mismo evento, verify/recompute, backup/restore. Distintos procesos, fixtures read-only, runtime offline, wheel instalado fuera del checkout, UID 10001 en contenedores y datos privados. Conserva los seis harnesses existentes.

Gates: instalación frozen y lock coherente; Ruff format/check; mypy strict; suite completa; cobertura de todo código propio ≥85 % líneas y ≥80 % ramas; sdist/wheel y ejecución externa; dependency audit; secret scan; revisiones ARQ/DB/SEC/SRE/docs; Quality/Compose/AMD64/ARM64-QEMU PASS con cuatro logs completos del candidato final.

No reducir thresholds, eliminar regresiones o añadir skips para lograr verde. Excepciones de secret scan, si hacen falta, exactas por path/detector/valor y con test; ninguna supresión general. No atribuir hardware Raspberry Pi físico ni cortes eléctricos a QEMU.

## 11. Decisiones, organización y entregables

Redacta el siguiente ADR libre, previsiblemente **ADR-0009**, sobre journal separado, modelo comparación/aparición, atomicidad, niveles de verificación y límites de recuperación. Nuevos contratos **DISCOVERY_JOURNAL_V1** y **DISCOVERY_JOURNAL_STORAGE_V1**, con esquema lógico/físico, serialización, límites, errores y compatibilidad. Documenta logging sin reversionar contratos antiguos innecesariamente.

Engineering Lead prepara plan/brief y ownership. ARQ/DB-OWNER posee contrato/DB; BE/DISCOVERY servicio/CLI; SEC/SRE revisa admisión, rutas, corrupción y recuperación. QA y REVIEWER son agentes no autores, distintos entre sí. Paraleliza solo análisis o archivos disjuntos; operaciones Git, contratos/interfaces compartidos e integración se coordinan secuencialmente. No necesitas todos los roles posibles ni varios autores para una misma pieza.

Entregables: contrato archivado, Engineering Brief, ownership, implementación, tests/harness/CI, ADR, contratos, arquitectura, threat model, testing/gates, runbook de las dos bases y recuperación, roadmap y deuda actualizados; PR abierto y Phase Completion Report con AC-J01–J16, base/head/tree, CI/logs completos, comandos/entornos y atestaciones exactas.

TD-001–TD-005 permanecen abiertas salvo autorización posterior específica: esta fase no cierra health de fuentes, Pi físico, confinamiento ante administrador hostil, cuotas/retención ni autenticación de vacíos legacy. Registra nueva deuda solo si hay un compromiso real con impacto, dueño y salida; funciones excluidas no son deuda artificial.

No guardes evidencias voluminosas temporales como cambios de producto. Publica el informe del candidato exacto en el PR y verifica por lectura de vuelta. Si falla la publicación, describe el fallo y entrega el cuerpo completo sin inventar éxito. Registra modelos realmente observables y atribuye cada prueba/revisión a su ejecutor.

## 12. Primer mensaje y handoff

Tu primera respuesta confirma apertura, objetivo, baseline, journal separado, diferencias entre comparación/aparición, admisión desde capturas, cero adquisición, perfiles de modelos y exclusiones. Después prepara el Engineering Brief concreto para Codex y dirige la fase hasta completar todos los gates.

No detengas el trabajo en un plan o promesa. Dentro del alcance, resuelve decisiones ordinarias y corrige fallos hasta disponer de candidato revisable. Un bloqueo real se reporta con evidencia y acción concreta; una ampliación material de fuente, DB de capturas, semántica de Discovery o transporte vuelve al Orchestrator.

Con todos los gates completos, entrega **READY_FOR_ORCHESTRATOR_REVIEW**. No emitas ACCEPTED/PHASE CLOSED, no hagas merge y no abras otra fase.

El Orchestrator revisará el candidato exacto y, si procede, autorizará su integración. El cierre exigirá después merge real, padres base→head, igualdad de árbol y nuevo CI push/main con los cuatro jobs/logs verificados.