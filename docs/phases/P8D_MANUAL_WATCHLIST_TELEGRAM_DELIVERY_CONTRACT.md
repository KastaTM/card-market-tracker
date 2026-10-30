# P8d — Manual Watchlist Telegram Delivery

**From:** 00 — ORCHESTRATOR\
**To:** nuevo chat P8d — Phase Lead\
**Fecha:** 2026-10-28\
**Proyecto:** `KastaTM/card-market-tracker`\
**Estado:** OPEN / IMPLEMENTATION AUTHORIZED; operaciones reales sujetas al gate y autorización específicos de este contrato.

Actúa como Phase Lead. Coordina con Codex Engineering Lead la implementación, pruebas y evidencias. Solo el Orchestrator acepta el candidato, autoriza merge y declara PHASE CLOSED.

## 1. MODEL PROFILE

- **ChatGPT Phase Lead recomendado:** GPT-6.1 Sol / High si figura en el selector; alternativa GPT-6 / High o el perfil más capaz realmente disponible. Registrar la selección, sin inventar disponibilidad o introspección del backend.
- **Motivo:** integrar evidencia histórica, autorización de entrega, efectos externos, fencing y recuperación sin duplicados.
- **Codex Engineering Lead recomendado:** GPT-6.1 Sol / Medium para coordinación, CLI, documentación y trabajo mecánico; High para admisión, consentimiento, SQLite, concurrencia, transporte y fallos ambiguos.
- **Especialistas críticos, QA y REVIEWER:** solicitar GPT-6.1 Sol / High, registrando sustituciones observables.
- Escalar a GPT-6 Astra / High, si está disponible, solo por un bloqueo de razonamiento justificado.
- Distinguir en MODEL PROFILE USED lo recomendado, los argumentos de selección observables y el modelo/reasoning efectivo no verificable.

## 2. Estado recibido y baseline

El Orchestrator ha declarado **ACCEPTED / PHASE CLOSED — P8c** en chat el 2026-10-28, después de verificar la integración del PR #18. No se atribuye esa declaración al Phase Lead.

| Objeto                       | SHA                                        |
| ---------------------------- | ------------------------------------------ |
| Baseline main / merge PR #18 | `9dda9fba0aa9646a67596657d4ae9a7088903808` |
| Árbol                        | `dfd0414242cff364aad6082411ae88aef728783e` |
| Primer padre                 | `228d5c8d0d91edf03ddb86a489c8232eeb7c08bc` |
| Segundo padre                | `d82aba73d9bc0eb455f8664e3ccddc0134ea9d9c` |

Evidencia histórica:

- PR #18: [https://github.com/KastaTM/card-market-tracker/pull/18](https://github.com/KastaTM/card-market-tracker/pull/18)
- CI push/main: [https://github.com/KastaTM/card-market-tracker/actions/runs/40737659939](https://github.com/KastaTM/card-market-tracker/actions/runs/40737659939)
- Integración/readback: [https://github.com/KastaTM/card-market-tracker/pull/18#issuecomment-6477774198](https://github.com/KastaTM/card-market-tracker/pull/18#issuecomment-6477774198)
- Informe inmutable: [https://github.com/KastaTM/card-market-tracker/blob/9b2014c78c17093f29656a5fb504f233fe714c15/docs/evidence/P8C_INTEGRATION_9dda9fba/P8C_INTEGRATION_COMPLETION_REPORT.md](https://github.com/KastaTM/card-market-tracker/blob/9b2014c78c17093f29656a5fb504f233fe714c15/docs/evidence/P8C_INTEGRATION_9dda9fba/P8C_INTEGRATION_COMPLETION_REPORT.md)
- Corrección RW-01: [https://github.com/KastaTM/card-market-tracker/blob/57bdf94391be307197df2a59526acf59bc6ff681/docs/evidence/P8C_RW01_d82aba73/RW01_CORRECTIVE_IMPLEMENTATION_REPORT.md](https://github.com/KastaTM/card-market-tracker/blob/57bdf94391be307197df2a59526acf59bc6ff681/docs/evidence/P8C_RW01_d82aba73/RW01_CORRECTIVE_IMPLEMENTATION_REPORT.md)

P8c cerró con 2.250 tests PASS, un skip preexistente, coberturas 94,15 % / 88,31 %, cuatro jobs, doce harnesses y regresión RW-01 PASS. Son resultados históricos, no gates de P8d.

Antes de editar, verificar remote, main remoto, commit/árbol/padres, checkout, ramas y worktrees. Crear rama desde ese baseline: sugerencia `feat/p8d-watchlist-telegram-delivery`. Si main difiere, comunicar la divergencia antes de trabajo dependiente del baseline; no integrar avances silenciosamente. Un main local antiguo no es la referencia remota.

Leer contexto, AGENTS, arquitectura/ADRs, roadmap, calidad/testing/deuda/threat model y contratos/runbooks P5a, P5b, P8a, P8b y P8c. Archivar íntegramente este prompt en `docs/phases/P8D_MANUAL_WATCHLIST_TELEGRAM_DELIVERY_CONTRACT.md`. Añadir entrada fechada al roadmap y mapa AGENTS: P8c cerrada y P8d abierta por esta decisión de chat, preservando historia y RW-01. No inventar un comentario remoto de cierre.

## 3. Objetivo y límites

Entregar manualmente a un destino privado de Telegram **el texto sintético histórico exacto de una alerta P8c seleccionada**, con originales verificados, consentimiento específico, ledger durable y prevención conservadora de reenvío ante incertidumbre.

Incluido: nueva ruta de admisión y ledger propio, registro/validación de destino privado, preparación offline, envío manual de un registro, recibo, replay, verificación/recomputación, consultas acotadas, recuperación/cuarentena, CLI, documentación, pruebas y decimotercer harness.

Fuera de alcance: scheduler, polling, envío masivo, drain/all-send, contactos o grupos/canales, texto arbitrario, cambios en reglas/renderer P8c, precios/fuentes reales, oportunidades comerciales, delivery de otros tipos, migraciones de almacenes anteriores, interfaz web, retención automática y cierre de P5 global.

La alerta seguirá diciendo `SYNTHETIC — DEMONSTRATION ONLY` e indicando revisión histórica. Su envío no acredita stock/precio real, preferencia vigente, frescura de mercado ni lectura humana. La antigüedad no se reinterpretará usando latest o un reloj nuevo.

La apertura autoriza desarrollar y probar offline la nueva ruta, **no realizar llamadas reales a Telegram**. El gate AC-WT20 define la autorización puntual necesaria. La autorización histórica T17 de P8b y sus credenciales/destino no se heredan como permiso de nuevo envío.

## 4. Arquitectura y ownership

Asignar ownership antes de paralelizar:

- Engineering Lead: integración, CLI/logging, harnesses/CI, documentación, Git y publicación.
- ARQ/BE: admisión, consentimiento, identidades y protocolo.
- DB-OWNER: esquema, máquina de estados, deduplicación, claim/fencing y recuperación.
- SEC/SRE: secretos, transporte, efectos ambiguos, timeouts y operabilidad.
- QA y REVIEWER: distintos de autores y entre sí, con probes propios sobre HEAD/tree final.

Usar solo roles justificados; análisis read-only puede ser paralelo, autoría exige archivos delimitados. No presentar pruebas de autor como QA independiente.

Crear módulo propio, sugerido `watchlist_delivery`, y SQLite independiente con owner `card-market-tracker.watchlist-telegram-delivery`, application_id nuevo comprobado contra todos los owners y schema v1. No reutilizar CMTD, CMTY, CMTA, CMTW o CMTQ. Fijar el identificador en ADR antes del writer.

Reutilizar **sin modificar** el transporte HTTPS ya aceptado de P8b, su validación de respuestas y sus tipos, mediante un adaptador/puerto estrecho. No llamar a P8b.prepare/send para introducir walt1\_/wsig1\_ donde exige alt1:/evt3:. No modificar el ledger, schemas, identidades o admisión P8b ni inventar eventos Discovery.

Se permite un lector aditivo mínimo, de solo lectura y propiedad P8c, si hace falta exponer una pareja alerta/evidencia consistente. Debe preservar toda verificación aceptada. Evitar refactorizaciones generales o un framework universal de delivery. Registro aditivo/lazy de CLI y logging: P8c debe conservar sus pruebas que deniegan importación de Telegram y acceso al token.

## 5. Originales y consentimiento específico

Preparación recibe explícitamente cuatro paths distintos: Watchlist P5a, journal P5b, outbox P8c y nuevo ledger; MANIFEST_V1 completo, walt1\_ seleccionado y alias privado. Sin auto-init, latest, selección en lote ni JSON autodeclarado como autoridad.

Antes de persistir una preparación:

1. Revalidar owners/paths, manifiesto completo, señal y revisión P5a/P5b originales mediante la ruta aceptada P8c. Verificación local del outbox por sí sola no concede autoridad.
2. Obtener alerta/evidencia completas de una lectura consistente del outbox, ejecutar recomputación contra originales y comprobar que la proyección seleccionada continúa idéntica. Comparar texto UTF-8 exacto, versión, identidad y digests; snapshots globales entre bases no son atómicos.
3. Confirmar policy=watchlist_synthetic_alert_v1, mode=synthetic, canal offline_preview, estado pending y señal genuina WATCHLIST_RULE_ENTERED_MATCH. Ningún preview arbitrario o hash del caller autoriza entrega.
4. Congelar el vínculo completo a alerta/señal, watch/revisión/configuración, evidencia y mensaje, y a la ruta privada. Una admisión privada ligada al contenido y al presupuesto concede autoridad al nuevo writer; debe resistir DTO falso, copia, mutación, uso en otra operación o renovación del deadline.

El alias P8c identifica un preview, **no consentimiento de envío**. La ruta debe ser privada, explícita, inmutable y atestada por el operador, con alias coincidente. Las actualizaciones idempotentes de validated_at no cambian la identidad de ruta.

Además, exigir un reconocimiento específico de demostración histórica al preparar una entrega, ligado al alert_id/signal_id, revisión, message/evidence digests y route digest exactos. Congelarlo como parte del binding. Definir en contrato el comando/flag y el runbook para que el operador revise el preview y confirme esa selección, sin pedir secretos en chat. No interpretar una preferencia histórica habilitada como consentimiento actual.

La atestación local presupone un proceso/operador confiable; no es firma criptográfica ni prueba de una identidad humana frente a administrador hostil.

Cada intento aún no confirmado debe revalidar originales y bindings antes del claim y de cualquier sendMessage. Si faltan o cambian, fallar sin enviar. No adaptar ni rerenderizar el texto para que encaje: el mensaje es el original exacto, ≤4096 bytes UTF-8.

## 6. Identidad y deduplicación

Una señal puede tener varios previews P8c por alias. Para impedir duplicarla cambiando alias, la identidad nueva se define por **provider + signal_id** dentro de esta autoridad de ledger:

`wtdl1_ + sha256(ASCII("CMT_WATCHLIST_TELEGRAM_DELIVERY_V1") + 0x00 + canonical({"identity_version":1,"provider":"telegram","signal_id":wsig1})).hexdigest()`.

Canonical igual a P8c: claves ordenadas, ASCII escapado, separadores compactos, tipos estrictos y sin NaN. Vectores independientes con preimage literal, NUL real y digest esperado. No incluir token, bot/chat IDs, clocks, nonce o paths en el ID.

Enforce UNIQUE(provider,signal_id) y binding inmutable al primer alert_id/alias/ruta/consentimiento/texto/evidencia aceptados. Repreparación idéntica es replay; cambiar alias/ruta o contenido bajo la misma señal es conflicto sin overwrite ni nuevo envío. Una señal de otro episodio es otra entrega. No prometer deduplicación entre copias o ledgers diferentes ni exactamente-una-entrega global.

Aplicar la lección de RW-01: toda invariante global exigida por verify debe cumplirse también dentro de la transacción de prepare/claim. En particular, para un mismo watch_id/revision los registros retenidos no pueden comprometer configuraciones completas incompatibles provenientes de originales distintos. Congelar el digest canónico de entrada y sus claves; admitirlo solo tras reconstrucción original. No particionar esta invariante por alias, serie o ruta.

Probar fuentes genuinas independientes con mismo watch/revisión y configuración diferente; el segundo prepare debe fallar sin dañar verify/backup. Permitir copias semánticamente equivalentes y revisiones/productos diferentes.

## 7. Ledger y protocolo de entrega

Esquema STRICT mínimo, exacto y versionado: metadata/cuarentena, rutas, entregas con bindings inmutables, claims e historial de resultados. Constraints, índices, FK y triggers; tipos/tamaños guardados en SQL antes de materializar. No borrar ni sobrescribir intentos o recibos.

Estados: ready, in_flight, retryable, confirmed, permanent_failure, uncertain. Adoptar la semántica conservadora P8b mediante contrato nuevo, sin modificar el anterior:

- prepare y recompute son offline. No lectura del token ni instanciación de transporte por prepare.
- Antes de claim: verificar ledger saludable/no cuarentenado, consentimiento/ruta, originales, estado/cooldown/contador y configuración/identidad del bot. Fallo previo deja cero claims/envíos nuevos.
- BEGIN IMMEDIATE comprueba de nuevo estado y bindings; persiste claim único, ordinal y ownership/fencing impredecible, y pasa a in_flight **antes** de sendMessage. No transacción SQLite durante HTTP.
- Cada invocación send hace como máximo un sendMessage; dos procesos concurrentes no pueden compartir un claim o duplicar el envío.
- Solo el attempt_id/owner vigente puede finalizar por CAS. Recuperación o finalización tardía no puede sobrescribir un resultado posterior ni sacar un terminal de su estado.
- Confirmed requiere aceptación válida del proveedor y recibo durable. Un response perdido, timeout, 5xx, éxito malformado o fallo local después de posible aceptación es uncertain o queda in_flight bloqueado si ni siquiera se pudo persistir el resultado.
- Crash después del claim nunca habilita reenvío automático. Recovery manual exige worker-quiesced y solo lleva un in_flight pendiente a uncertain; no force, reset a ready o resolver uncertain como no-enviado sin prueba.
- Solo un 429 explícito y estrictamente válido puede habilitar retryable/not_before, máximo tres intentos vitalicios. Cada nuevo intento es una acción manual distinta; sin bucles, backoff daemon ni reintento de uncertain/confirmed. Los permisos reales de calificación siguen limitados a un intento total.
- Confirmed replay desde otro proceso no lee token ni llama a red ni exige originales disponibles: comprueba el recibo/binding local y devuelve replay. Un ledger cuarentenado bloquea cualquier comando send, incluido ese camino; get/verify siguen disponibles como lecturas.

La hora de cooldown, gramática UTC, detección conservadora de clock skew y límites de attempt/retry_after deben congelarse en contrato. No confundir timeout antes del claim, resultado incierto tras el claim y error de confirmación local.

## 8. Transporte, secretos y deadlines

Solo endpoint oficial HTTPS y métodos getMe, getChat, sendMessage del transporte P8b. TLS verificado, sin redirecciones, proxies ambientales, debug, retries o URL arbitraria. Mensaje exacto con previews de enlaces deshabilitados; sin parse_mode, entities, topic ni edición de texto.

Token únicamente en el entorno local previsto por el transporte, nunca en argumentos, DB, fixtures, IPC, logs, errores, informe o chat. Bot/chat IDs y recibos completos permanecen privados; CLI ordinaria devuelve proyecciones saneadas. No publicar capturas ni respuestas HTTP brutas.

Conservar límites y validadores P8b: respuesta ≤64 KiB, UTF-8/JSON estrictos, profundidad acotada, duplicados/NaN/bool-as-int rechazados. Confirmación comprueba ok=true, message_id positivo, bot correcto, chat privado exacto, fecha válida y texto exactamente igual. Aceptación no implica lectura humana.

Operaciones locales: presupuesto compartido default2/max5 segundos, finito positivo, desde parsing hasta respuesta. Validación de destino/send: presupuesto **global** default15/max30 segundos, compartido entre admisión local, metadata, red y persistencia final. La fase de originales dentro de send tendrá además un máximo local conjunto de5s; no regalar5s nuevos a cada helper. Reservar tiempo de persistencia conservador sin extender el deadline.

Reutilizar supervisión de transporte P8b para DNS/connect/write/read/respuesta lenta; un socket timeout aislado no satisface el límite global. SQLite/filesystem/stdout mantienen deadlines cooperativos: declarar el límite ante syscalls bloqueantes, no prometer tiempo real duro. Ningún agotamiento de presupuesto puede producir un nuevo envío automático.

## 9. Verificación y recuperación

Verify local: owner/header/schema exactos, integridad/FK, límites/JSON, bindings/IDs/rutas/consentimiento, unicidades e invariante watch/revisión, historial contiguo, claim/owner vigente, estados, contadores, cooldown y recibos coherentes. No confundir commitments opacos con autenticación de originales.

Recompute read-only: seleccionar entrega y revalidar P5a/P5b/P8c originales con manifiesto completo, texto y bindings exactos. Fuentes ausentes/distintas fallan. Local verify puede pasar mientras recompute falla; documentar y probar la diferencia.

Backup consistente exclusivo y verificado; restore a destino nuevo debe establecer **cuarentena global durable antes de exponer el archivo** y verificarla tras reapertura. Incluye entregas desconocidas por un backup antiguo y preparaciones nuevas. Sin comando de desactivación de cuarentena en P8d. No reutilizar una copia restaurada para volver a enviar.

Tres verificaciones independientes donde aplique; no compartir autoridad entre origen, copia y reapertura. Mismo presupuesto. Preservar inode/hardlink/reparse/sidecar/owner safety, fsync y compensación de unlink post-link. No alterar fuentes o ledgers anteriores ni borrar archivos ajenos/evidencia de recuperación. Persistent filesystem refusal puede dejar nombres para inspección manual.

Las cuatro bases no tienen commit distribuido. Ledger único confiable, orígenes inmutables y directorios confiables son supuestos operativos; sustitución coherente por administrador, clonación de autoridades, hardware Pi y pérdida eléctrica física no están certificados.

## 10. CLI y observabilidad

Grupo sugerido `cmt watchlist-telegram-delivery`. Congelar antes de implementar init, destination-add/validate, prepare, send, get/list, verify/recompute, recover, backup/restore; ningún comando bulk, arbitrary-text, force, resend-uncertain o unquarantine.

Paths e identidades explícitos; aliases con gramática P8c, IDs versionados nuevos y cerrados. Sin auto-init. Paginación por keyset, default100/max1000/≤1 MiB, cursor ligado a filtros/versión. Parsing con límites existentes de1MiB/depth16/nodos20.000 y límites más estrictos heredados.

Respuestas y errores versionados, exit codes cerrados y estados explícitos. Solo un completion log estructurado por invocación: operación, resultado/categoría, estado, duración, IDs locales validados y contadores permitidos. No token, rutas personales, bot/chat IDs, texto, cantidades, muestras, preferencias, SQL o excepciones crudas. No registrar success antes de saber el resultado durable; error no significa ausencia de efecto remoto.

## 11. Documentación y pruebas obligatorias

Congelar ADR-0015, `WATCHLIST_TELEGRAM_DELIVERY_V1` y `WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1`, ownership, protocolo de estados, runbook de calificación/recuperación y límites antes de codificar schema/identidades. Actualizar arquitectura, threat model, LOGGING_V1 aditivo, testing/gates, roadmap/deuda. No cerrar TD-001–TD-005; añadir deuda nueva si hay concesiones nuevas.

Tests unit/integration/contract/regression, con fallos primero:

- Preparación desde originales genuinos y consentimiento exacto; falso DTO/recibo, copia/mutación/uso tardío/cambio de Budget, originales ausentes o alterados y source-byte nonmutation.
- Identidad independiente, aliases alternativos para la misma señal, otra ruta/configuración bajo mismo ID, dos episodios; RW-01 entre fuentes genuinas y carrera de escritores incompatibles.
- Un envío, recibo durable, cierre/reapertura y confirmed replay con transporte/token ausentes y sockets denegados.
- Dos procesos sender; claim durable observado antes de HTTP; crash antes/después de claim, durante respuesta y antes/después de recibo; finalización tardía/CAS y recuperación explícita.
- 429 válido/not_before/attempt cap; permanentes4xx, ambiguos408/409/425,5xx, JSON truncado/duplicado, bot/chat/texto incorrectos, TLS/error de red y persistencia local fallida. Nunca transformar incertidumbre en retryable.
- Bloqueos/ENOSPC/timeouts por etapa, foreign hot-journal antes de writable open, corrupción coherentemente rehasheada, owner/schema ajenos, restore de backup viejo y global quarantine frente a una entrega posterior no conocida por el backup.
- Límites, cursores, deadline global y de originales, DNS/response drip, logging/privacy/first stdout y red cero en todas las operaciones offline.

CI siempre sin credenciales y con transporte falso. No invocar Telegram real desde tests, runners o agentes. Añadir **decimotercer harness offline** que construya el pipeline P5a→P5b→P8c con los cinco checkpoints/cuatro señales completos, elija una alerta, prepare/envíe con fake, compruebe recibo/replay/recompute/recovery/cuarentena en procesos distintos y no mutación de fuentes. Los doce harnesses anteriores se conservan.

Cuatro jobs obligatorios: Quality, Compose, AMD64 y ARM64/QEMU; trece harnesses por entorno, UID10001/private files/network none donde aplique. Frozen installs, Ruff format/check, mypy strict, suite completa sin filtros, cobertura ≥85 % líneas / ≥80 % ramas, build sdist/wheel, instalación fuera de source, dependency audit y secret scan. No ampliar timeouts/thresholds, reducir fixtures o saltar tests para obtener verde.

Mediciones acotadas de recuperación/admisión en QEMU local cuando esté disponible, con ≥3 controles backup/restore en el fixture completo y presupuesto contractual. Declarar indisponibilidad local y exigir siempre CI ARM64. Job duration no es una medida por operación ni prueba Pi físico.

QA y REVIEWER distintos ejecutarán probes propios sobre HEAD/tree final. Publicar código completo, helpers, instrucciones y resultados saneados recuperables, no solo hashes/rutas privadas. Conservar fallos y diferenciar simulación, ejecución real, CI y revisión estática. No repetir un job fallido del mismo SHA hasta obtener verde sin autorización; commits correctivos reciben su CI normal y renovaciones aplicables.

## 12. Gate real — AC-WT20, autorización separada

Este gate es obligatorio para aceptar P8d completa. Mientras no se ejecute, declarar **BLOCKED — LIVE_UNVERIFIED**, sin presentar fake/CI/P8b-T17 como confirmación real.

Primero terminar implementación/gates offline, PR en borrador y expediente de preflight. El Phase Lead deberá obtener autorización explícita y específica del operador para **una alerta sintética exacta y un único destino privado**. Debe quedar registrada localmente con fecha, candidato HEAD/tree, signal/alert/delivery IDs, digests del mensaje/evidencia y ruta; la proyección pública excluye IDs personales. Preparar el procedimiento concreto antes de pedir esa autorización.

La confirmación debe distinguir revisión histórica del estado actual y reconocer que se enviará una demostración sintética. El token se configura solo localmente; nunca solicitar su pegado en chat ni publicar el chat ID. Si el operador no autoriza, parar solo el trabajo dependiente y entregar el estado BLOCKED con el resto de evidencia completada.

Límites de calificación P8d, globales para esta prueba y no renovables por proceso:

- Métodos metadata: máximo8 llamadas totales getMe/getChat, instrumentadas.
- **Máximo1 intento real de sendMessage total**, incluyendo fallidos o ambiguos.
- Sin terceros, contactos, grupos, compras, nuevas fuentes o entrega comercial.
- No repetir automáticamente ante timeout/fallo/incertidumbre. Otro intento requiere nueva decisión expresa del Orchestrator y del operador; no usar el retryable de producto como permiso de calificación adicional.

Evidencia exigida: destino privado validado, mensaje/digests exactos, aceptación válida del proveedor, un claim/intento, recibo durable y estado confirmed tras reapertura. Replay desde otro proceso, sin token y con red bloqueada, debe producir cero nuevas llamadas y conservar historial de un intento. Verificar fuentes intactas y ledger no restaurado/cuarentenado.

Originales live y ledger permanecen privados. Publicar solo attestation saneada, hashes y conclusiones, sin token/bot/chat IDs, PII, texto íntegro, URL autenticada, respuesta HTTP bruta o excepción sensible. QA/REVIEWER revisarán el expediente read-only sin nuevas llamadas. Distinguir evidencia instrumental/recibo de declaraciones del operador; no afirmar captura independiente de tráfico ni lectura humana si no existe.

Si cambia el código después de la prueba, renovar gates/revisiones afectados y evaluar la aplicabilidad de la evidencia real; no repetir el envío sin nueva autorización específica.

## 13. Acceptance Criteria

| ID      | Criterio obligatorio                                                                                                                          |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-WT01 | Baseline/estado/árbol verificados; contrato y cierre P8c/apertura P8d archivados con atribución correcta.                                     |
| AC-WT02 | Ledger/owner/schema propios; rutas P8b, P8c y anteriores preservadas; transporte P8b reutilizado sin ampliar su autoridad.                    |
| AC-WT03 | Admisión completa desde P5a/P5b/P8c originales; snapshots/bindings exactos, sin autoridad de DTO/caller/local-verify.                         |
| AC-WT04 | Reconocimiento específico de simulación histórica y consentimiento ligado a contenido/ruta; alias no autoriza envío.                          |
| AC-WT05 | wtdl1\_ con oráculos independientes; dedup provider+signal y conflictos de alias/ruta/contenido sin overwrite.                                |
| AC-WT06 | Invariantes globales, incluida entrada watch/revisión, preservadas transaccionalmente por prepare/claim y verify.                             |
| AC-WT07 | Claim durable previo a HTTP; dos procesos no duplican el envío; fencing impide finalizaciones tardías.                                        |
| AC-WT08 | Texto original exacto, HTTPS/TLS/response validation y secretos privados; ningún texto arbitrario o parse_mode.                               |
| AC-WT09 | Recibo durable y confirmed replay sin token/red/orígenes; proveedor aceptado no implica lectura humana.                                       |
| AC-WT10 | Estados,429manual/cooldown/límite3 y errores ambiguos conformes; uncertain/confirmed nunca se reenvían automáticamente.                       |
| AC-WT11 | Presupuestos local2/max5 y global15/max30 compartidos; supervisión de DNS/IO, no deadline renovado por helper.                                |
| AC-WT12 | Verify local e historial/recompute original read-only distintos y coherentes; corrupción rechazada.                                           |
| AC-WT13 | Backup/restore exclusivos, cuarentena global durable incluso para entregas desconocidas, sin force/unquarantine.                              |
| AC-WT14 | Crash/rollback/ENOSPC/timeout/link/unlink/hardlink/sidecar/recovery seguros y fuentes intactas.                                               |
| AC-WT15 | CLI/páginas/cursor/errores/exit/logging limitados y privados; operaciones offline sin token/transporte/red.                                   |
| AC-WT16 | Trece harnesses en wheel,Compose,AMD64,ARM64/QEMU con fixture completo y regresiones anteriores.                                              |
| AC-WT17 | Suite completa,coverage,format/lint/types/build/external wheel/audit/secret scan y cuatro jobs finales PASS.                                  |
| AC-WT18 | QA/REVIEWER distintos de autores, probes propios sobre SHA/tree final, código/helpers/resultados públicos y saneados.                         |
| AC-WT19 | ADR0015/contratos/schema/threat/runbooks/observabilidad/deuda/ownership sincronizados con el candidato.                                       |
| AC-WT20 | Calificación real específicamente autorizada: ≤8metadata,≤1send,aceptación/recibo durable,reopen,replay otro proceso red0 y revisión saneada. |
| AC-WT21 | Informe final/publicación/readback completos, fallos conservados, limitaciones explícitas y ninguna aceptación/merge/cierre prematuros.       |

Un método presente o test fake no satisface por sí solo un AC. Cada criterio requiere PASS/FAIL/BLOCKED y evidencia individual. AC-WT20 no tiene waiver implícito.

## 14. Ejecución y handoff

Comenzar por auditar baseline y fronteras; elaborar Engineering Brief y ownership; congelar ADR/contratos/protocolo antes de implementar. Resolver elecciones rutinarias dentro del alcance sin solicitar confirmaciones adicionales. Escalar solo cambios de alcance/contrato o autorizaciones reales que este texto reserva.

Autorizado: rama, commits, PR de fase, CI normal por nuevos commits, pruebas offline y publicación saneada de evidencia en el PR. No autorizado por esta apertura: llamadas reales, merge, force push/bypass, cambio de protecciones, nuevas fuentes o PHASE CLOSED. Preservar ramas/worktrees/originales/evidencias; no extraer/cambiar credenciales o permisos para sortear errores de conectores.

Si no puede publicarse, entregar el informe listo y declarar la limitación. Recuperar las publicaciones para comprobar su correspondencia; no afirmar readback o publicación no observados. Ante rechazo de revisión automática, comunicar acción y razón, y continuar solo por alternativa permitida.

Phase Completion Report obligatorio: phase/status; base/branch/PR/commits/HEAD/tree; MODEL PROFILE USED real; especialistas/ownership; objetivos/implementación; arquitectura/ADRs/contratos/DB/threat; deuda/observabilidad; tests y gates; cuatro jobs/logs completos/trece harnesses; QA/REVIEWER; AC-WT01–21 individualizados; expediente live saneado o bloqueo preciso; incidencias/limitaciones; enlaces/readback; recomendación al Orchestrator.

El Phase Lead contrasta directamente lo remoto disponible y atribuye ejecuciones locales y privadas a sus actores, sin inventar acceso al Windows/ZIP o efectivo backend. Solo con todos los gates, incluido el real, proponer **READY_FOR_ORCHESTRATOR_REVIEW**. Con live pendiente: **BLOCKED — LIVE_UNVERIFIED**, no cierre.

Tras aceptación habrá otra autorización de merge. Después del merge se exigirán identidad/padres/árbol/diff/main y nuevo CI push/main antes del cierre exclusivo del Orchestrator.

P5 global y TD-001–TD-005 permanecen OPEN. P2, P6a y Discovery retail permanecen BLOCKED. P8d no abre ninguna fase posterior ni autoriza alertas comerciales.

**P8d — OPEN / IMPLEMENTATION AUTHORIZED. LIVE EXECUTION NOT AUTHORIZED BY THIS PROMPT.**