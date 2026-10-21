# P8b — Telegram Alert Delivery

## Prompt de apertura para el chat de fase

**From:** 00 — ORCHESTRATOR\
**To:** P8b — Phase Lead\
**Proyecto:** Card Market Tracker — `KastaTM/card-market-tracker`\
**Fecha:** 2026-10-21\
**Estado:** OPEN — IMPLEMENTATION AUTHORIZED\
**Autoridad de aceptación, integración y cierre:** exclusivamente 00 — ORCHESTRATOR.

Actúa como Phase Lead de P8b. Dirige el trabajo del Engineering Lead y las revisiones independientes hasta entregar un candidato concreto, probado y revisable. Este contrato autoriza implementación y preparación de PR; el merge requiere autorización posterior del Orchestrator.

## 1. Decisión y baseline

P8a — Offline Alert Outbox queda **ACCEPTED / PHASE CLOSED** por decisión del Orchestrator en este chat. P8b abre la entrega manual y acotada por Telegram a partir del outbox existente.

Baseline autorizado:

| Elemento              | Identidad                                  |
| --------------------- | ------------------------------------------ |
| Repositorio           | KastaTM/card-market-tracker                |
| PR integrado anterior | #13                                        |
| Main / merge de P8a   | `ac35d4df0f3a006ff60bb026de992c366e19cc09` |
| Árbol                 | `d604d3b8362c30af8b5dd516eddc0d8095fe7bf9` |
| Primer padre          | `b89fff319a94e5eb6e4b7bdad944e879bad371f6` |
| Segundo padre         | `cf3c8f17128a5459d4d0f9228b2f1456e120817b` |

Evidencias históricas:

- [PR #13](https://github.com/KastaTM/card-market-tracker/pull/13).
- [Integración P8a](https://github.com/KastaTM/card-market-tracker/pull/13#issuecomment-6311625604).
- [CI push/main P8a](https://github.com/KastaTM/card-market-tracker/actions/runs/39565851306): 1.361 PASS, un skip; cobertura 95,30 % líneas / 90,41 % ramas; cuatro jobs PASS y ocho harnesses offline.

Esos resultados son antecedentes, no pruebas de P8b. Verifica baseline, árbol y estado remoto antes de modificar. Si main ha avanzado, informa de la divergencia y solicita resolución de baseline, sin incorporar cambios silenciosamente. Preserva checkout, ramas, trabajo ajeno y worktrees. Usa una rama dedicada, sugerida `feat/p8b-telegram-alert-delivery`.

Actualiza el roadmap atribuyendo la decisión P8a cerrada / P8b abierta a este contrato del Orchestrator; no inventes una aprobación publicada en GitHub.

## 2. Objetivo y límite funcional

Entregar por Telegram una alerta ya admitida por P8a, conservar evidencia durable del intento y evitar reenvíos conocidos o potencialmente duplicados.

El recorrido será explícito: seleccionar una alerta y su evidencia, comprobar sus capturas originales, preparar una entrega para un destino autorizado, ejecutar como máximo un intento por invocación y consultar el resultado tras reiniciar.

Alcance:

- Un adaptador Telegram.
- Destino privado del operador, identificado numéricamente y asociado a un alias lógico de P8a.
- Ledger SQLite de entrega separado.
- CLI manual y operaciones de diagnóstico, verificación, backup y restore.
- Una prueba real controlada de calificación, sujeta al apartado 9.

Fuera de alcance: scheduler, daemon, polling continuo, webhooks, recepción de comandos, envío masivo, grupos/canales/topics, contactos descubiertos automáticamente, pagos, broadcasts, watchlist, nuevas señales, precios, retail, nuevas adquisiciones y otros canales.

P2, P6a y Discovery retail siguen **BLOCKED**. P5 no se abre. TD-001–TD-005 siguen **OPEN**. Esta fase no amplía derechos de fuentes ni autoriza explotación comercial de datos.

## 3. Modelos, razonamiento y responsables

Perfil solicitado, condicionado a la disponibilidad real en cada entorno:

| Responsabilidad            | Modelo solicitado | Reasoning solicitado | Motivo                                              |
| -------------------------- | ----------------- | -------------------- | --------------------------------------------------- |
| Phase Lead en ChatGPT Work | GPT-6.1 Sol       | High                 | Contrato, riesgos, contraste de evidencia y handoff |
| Codex Engineering Lead     | GPT-6.1 Sol       | Medium               | Implementación incremental y coordinación           |
| ARQ/DB y SEC/SRE           | GPT-6.1 Sol       | High                 | Estados durables, concurrencia y secretos           |
| QA independiente           | GPT-6.1 Sol       | High                 | Probes propios y fallos entre red y commit          |
| REVIEWER independiente     | GPT-6.1 Sol       | High                 | Auditoría del candidato exacto                      |

Escala el Engineering Lead a High para la máquina de estados, fencing, recuperación, restauración y clasificación de resultados inciertos. Si persiste un desacuerdo crítico, solicita revisión adicional con GPT-6 Astra / High, si está disponible, antes de congelar el candidato.

No bloquees trabajo rutinario por un selector ausente: documenta la alternativa disponible y su motivo. No atribuyas un modelo o razonamiento efectivo que el entorno no permita verificar. Incluye **MODEL PROFILE USED** en cada informe, distinguiendo solicitado, observable y desconocido.

La independencia de QA y REVIEWER es obligatoria: personas/agentes distintos de los autores y entre sí, pruebas propias y revisión del SHA final. Sus informes deben identificar head y árbol. Una revisión publicada como comentario es evidencia; no la presentes como GitHub formal review si no lo es.

## 4. Arquitectura y compatibilidad obligatorias

Lee primero contexto, instrucciones aplicables, contratos, ADRs, runbooks, deuda, workflow y pruebas existentes. Presenta un Engineering Brief breve y continúa con decisiones rutinarias dentro del contrato.

Preserva:

- Identidades canónicas, `cmp3`, `evt3`, `alt1`, capturas R0/R1 y bundles admitidos.
- Comparadores y Discovery v1/v2/v3, journal, esquemas de capturas y journal.
- Outbox schema v1, sus tres tablas y el contenido de alertas/evidencias.
- `channel=offline_preview`, `state=pending` y renderizado inmutable de P8a.

El ledger de P8b expresa el estado de transporte. No conviertas el outbox histórico en una cola mutable ni cambies sus filas a sent. Envía exactamente el texto almacenado y validado por P8a: no vuelvas a renderizarlo, truncarlo o adornarlo, ni añadas identificadores al mensaje.

Separa aplicación, transporte y almacenamiento. El adaptador recibe una orden validada por la aplicación; no expongas una CLI de envío de texto arbitrario. La preparación y cada intento deben comprobar la alerta, la asociación seleccionada al journal y la recomputación contra capturas originales mediante los mecanismos existentes. Una mera verificación local de hashes no sustituye esa comprobación.

Capturas, journal y outbox se abren para lectura. Congela y vincula por digest el contenido comprobado con la entrega preparada. Rechaza cambios de mensaje, evidencia o ruta; no prometas atomicidad distribuida entre las bases.

Documenta un ADR nuevo, con el siguiente número libre —previsiblemente ADR-0011—, y contratos versionados para entrega y almacenamiento. Define antes de implementar: identidad determinista, unicidad por alerta y ruta autorizada, estados, transiciones, recibos, límites y recuperación. No permitas crear otra entrega de la misma alerta mediante cambios silenciosos de alias, bot o chat.

## 5. Destinos, credenciales y transporte

Una asociación de destino fija alias, proveedor, bot_id y chat_id privado. Comprueba la identidad del bot y el tipo/identidad del chat con las operaciones oficiales de lectura. La titularidad del chat requiere declaración del operador: una respuesta de la API no demuestra por sí sola que sea suyo.

No reasignes un alias existente a otro bot/chat para eludir deduplicación. Rotar el token del mismo bot no crea una entrega nueva; un bot distinto provoca conflicto.

El token se configura localmente mediante una variable de entorno documentada o un mecanismo local equivalente justificado. Nunca lo solicites por el chat, lo pongas en argumentos CLI, persistas en SQLite, commits, fixtures, logs, capturas, informes, URLs publicadas o excepciones sin sanear. No reutilices credenciales de otros proyectos.

Transporte de producción:

- HTTPS al endpoint oficial fijo de Telegram, con validación TLS.
- POST de texto plano; sin parse_mode, entidades añadidas ni previews de enlaces.
- Sin redirects, retries implícitos, endpoint arbitrario ni proxies heredados automáticamente.
- Sin respuestas completas del proveedor en logs; valida una proyección mínima y descarta datos personales innecesarios.
- Tamaño de respuesta acotado, por ejemplo 64 KiB; validación estricta de JSON, tipos, identificadores y campos críticos.
- Límites del mensaje de P8a preservados.
- Timeout total nuevo explícito y acotado: propuesta 15 s por defecto, máximo 30 s. Define presupuestos por etapa y evita lecturas que prolonguen indefinidamente el plazo.
- Las operaciones SQLite conservan sus límites existentes. Nunca mantengas una transacción abierta mientras esperas a Telegram.

Preferencia por dependencias existentes o biblioteca estándar. Justifica cualquier dependencia nueva y renueva lock, auditoría y gates correspondientes.

Referencia primaria: [Telegram Bot API](https://core.telegram.org/bots/api), especialmente autenticación, getMe, getChat, sendMessage y ResponseParameters. Consulta su versión vigente al implementar. La API devuelve un Message al aceptar sendMessage; el contrato local definirá **confirmed** como aceptación acreditada por la API y registrada durablemente. No significa lectura humana.

## 6. Máquina de estados y resultados inciertos

Estados semánticos mínimos: ready, in_flight, retryable, confirmed, permanent_failure y uncertain. Puedes adaptar nombres con equivalencia explícita en el contrato.

Reglas obligatorias:

1. Persiste la intención y reclama el intento atómicamente **antes** de llamar a sendMessage.
2. Un CAS/claim durable y un identificador de intento impiden dos envíos concurrentes. Finalizar exige la titularidad vigente del intento; un proceso antiguo no puede finalizar el intento de otro.
3. Una segunda invocación de una entrega confirmed devuelve replay sin enviar. Reabrir la base y reiniciar el proceso conserva este comportamiento.
4. Confirma únicamente con respuesta válida, identidad del destino y mensaje coherentes, recibo mínimo y commit local satisfactorio.
5. Timeout, desconexión, respuesta ambigua, éxito malformado, 5xx o fallo local posterior a una posible aceptación se clasifican conservadoramente como uncertain.
6. Un crash después del claim no autoriza reenvío automático, incluso si pudo ocurrir antes de la llamada HTTP. La recuperación privilegia evitar duplicados.
7. No reclames una operación in_flight solo por vencimiento de tiempo. Define recuperación con quiescencia explícita del trabajador y fencing; no conviertas uncertain en ready automáticamente.
8. Un rechazo inequívoco y validado puede ser permanent_failure. Un 429 explícito con retry_after válido puede ser retryable con not_before persistido.
9. Cada invocación realiza como máximo un intento de envío. Un retry por 429 requiere una invocación posterior, respeta not_before y un máximo finito —propuesta: tres intentos totales—. No duermas ni hagas bucles esperando.
10. uncertain no tiene reenvío ni bypass force en P8b. Documenta resolución operativa sin fabricar recibos o marcar confirmed sin evidencia.

No prometas exactly-once extremo a extremo. Un commit local y una aceptación remota no son atómicos. Explica la posibilidad de entrega omitida cuando se decide no reintentar un resultado incierto.

La garantía local presupone un único ledger activo y sus directorios confiables. Clonar bases o ejecutar autoridades independientes queda fuera de esa garantía.

## 7. Persistencia, CLI y recuperación

Ledger propio con esquema versionado, validación de tablas/índices/relaciones, transacciones atómicas y datos suficientes para auditar ruta, alerta, mensaje, intento y recibo. Valida contenido además de estructura; conflictos no sobrescriben historia.

Ofrece operaciones coherentes con la CLI existente para init, destino, prepare, send, get/list, verify, recovery, backup y restore. Los nombres finales pueden ajustarse al estilo del repositorio.

- prepare y preview no envían ni consultan Telegram implícitamente.
- La validación remota del destino es una operación explícita.
- send requiere una entrega concreta; no selecciona todas las pendientes ni la “última”.
- list usa paginación y límites; define códigos de salida y errores categorizados.
- verify local y recompute contra orígenes se distinguen en salida y documentación.
- Backup consistente y restore a destino nuevo, sin sobrescribir datos existentes.
- Conserva las protecciones de archivos principales y sidecars SQLite; no borres archivos de otro proceso o evidencias tras un fallo.

**Restore y duplicados:** una copia anterior puede desconocer envíos realizados después. Por ello, en P8b un ledger restaurado queda globalmente en cuarentena para envío; permite inspección y verificación, pero no despacho ni un force que la omita. Documenta la necesidad de reconciliación externa antes de una futura habilitación, fuera del alcance de esta fase. Esto cubre también entregas ausentes en la copia, no solo filas in_flight. No presentes el backup como recuperación automática segura de capacidad de envío.

Demuestra rollback, reapertura, contención, corrupción, fallos de disco simulados y restauración en cuarentena. No atribuyas resistencia a cortes eléctricos reales.

## 8. Seguridad y observabilidad

Actualiza threat model y runbook. Trata mensaje, configuración, respuestas HTTP y bases como entradas no confiables.

Logs estructurados con identificadores locales de entrega/intento, resultado, transición, duración, categoría de error y replay. No publiques tokens, URL autenticada, cuerpo completo, nombres, chat_id/bot_id ni mensajes personales. Guarda los identificadores necesarios en el ledger local con controles de acceso; utiliza alias y referencias saneadas en evidencias públicas.

Prueba redacción también ante excepciones del cliente, errores TLS, redirects, cuerpo malicioso y descripciones que reflejen el token. La seguridad no debe depender de que un llamador recuerde ocultar la excepción.

No mezcles señales de salud con alertas de mercado ni envíes incidencias técnicas por Telegram en esta fase.

## 9. Gate real de Telegram y autorización del operador

La implementación, fixtures, revisión y CI continúan sin credenciales. No detengas trabajo independiente para pedir el token o una confirmación prematura.

Antes del gate real, prepara un candidato limpio, instrucciones locales concretas y revisables, y una alerta **sintética** generada por el recorrido normal capturas → journal → outbox → ledger.

La apertura de P8b **no autoriza enviar a un destinatario desconocido**. El operador debe identificar y autorizar su chat privado y ejecutar el comando explícito de envío, o instruir expresamente al agente para enviar esa alerta a ese destino. No vuelvas a pedir autorización si ya existe con ese alcance.

Presupuesto de calificación:

- Hasta ocho llamadas de metadatos getMe/getChat.
- Un solo intento sendMessage autorizado; sin retry automático real.
- Sin operaciones de contactos, grupos, otros bots ni otros servicios.

Evidencia mínima:

1. Código ejecutado identificado por SHA exacto y entorno limpio.
2. Una alerta sintética, destino autorizado y contenido congelado.
3. Una respuesta de aceptación validada y recibo durable saneado.
4. Replay de la misma operación y reapertura en otro proceso sin nuevos envíos.
5. Contador de invocaciones de transporte y evidencia del recibo; la observación humana, si existe, se declara como tal.

Publica el resultado en comentarios/evidencias saneadas sin modificar el candidato solo para añadir secretos o datos personales. Si el código cambia después, determina qué gates y revisiones deben renovarse; no atribuyas la prueba al nuevo SHA sin justificar la equivalencia del runtime. Otro intento real requiere ampliación explícita del presupuesto.

Si falta acceso al entorno local, token o destino autorizado, termina todo el trabajo restante y entrega instrucciones listas para ejecutar. Marca este gate **BLOCKED / LIVE_UNVERIFIED**, identifica la dependencia concreta y no declares todos los AC PASS. Una simulación no acredita envío real. Este gate es obligatorio para recomendar el cierre completo de P8b; no se elimina por falta de credenciales.

## 10. Acceptance Criteria — AC-T01–AC-T18

| AC  | Condición verificable                                                                             |
| --- | ------------------------------------------------------------------------------------------------- |
| T01 | Baseline exacto, contrato de fase y roadmap con decisiones atribuidas correctamente               |
| T02 | Componentes, identidades y esquemas anteriores preservados; outbox inmutable                      |
| T03 | Binding privado explícito, identidad del bot/chat comprobada y cambios conflictivos rechazados    |
| T04 | Preparación y envío vinculados a alerta, evidencia y recomputación original; sin texto arbitrario |
| T05 | Mensaje exacto de P8a enviado sin alteración; contrato de ruta e identidad determinista           |
| T06 | Ledger validado, persistencia atómica, replay y conflictos sin sobrescritura                      |
| T07 | Claim concurrente y fencing impiden envíos simultáneos o finalización obsoleta                    |
| T08 | Recibo válido y durable para confirmed; replay tras reinicio sin envío                            |
| T09 | Crashes y resultados ambiguos producen estado conservador, sin reenvío                            |
| T10 | Rechazos y 429 clasificados; not_before y máximo de intentos respetados                           |
| T11 | Cliente HTTPS acotado, validación estricta, sin redirects/retries/SSRF                            |
| T12 | Secretos y datos personales protegidos en configuración, logs y errores                           |
| T13 | CLI explícita, diagnósticos claros, lecturas/paginación y recursos acotados                       |
| T14 | Backup consistente, restore exclusivo y cuarentena global sin bypass                              |
| T15 | Nuevos tests y noveno harness offline; regresiones y gates completos PASS                         |
| T16 | QA y REVIEWER independientes sobre SHA/árbol final, hallazgos cerrados                            |
| T17 | Gate real autorizado de una alerta sintética, recibo y replay acreditados                         |
| T18 | ADR, contratos, threat model, runbooks, límites, deuda e informe trazables                        |

Cada AC debe enlazar evidencia concreta. Distingue PASS, FAIL y BLOCKED; no uses un porcentaje de cobertura como prueba de semántica.

## 11. Pruebas y quality gates

Pruebas propias y adversariales:

- Flujos válidos, JSON/tipos incorrectos, destino inesperado, contenido/recibo alterado.
- Dos procesos sobre la misma entrega, locks, CAS perdido y finalizador obsoleto.
- Crash antes del HTTP, durante la llamada y tras aceptación antes/durante el commit.
- 429, not_before, límites de intentos; 4xx, 5xx, timeout y respuesta incompleta.
- Redacción, token reflejado, redirects y respuesta excesiva.
- Replay tras reinicio, backup/restore anterior al envío y entregas que faltan en la copia.
- Orígenes incoherentes, outbox cambiado, corrupción y recuperación de sidecars.
- Importar, preview, prepare y smokes offline no generan conexiones accidentales.

Añade un noveno harness reproducible con transporte falso, procesos separados y ledger durable. Ningún test CI necesita token, chat real, acceso Telegram o secretos. Conserva los ocho harnesses anteriores.

Cuatro jobs obligatorios: Quality, Compose, linux/amd64 y linux/arm64 QEMU. Ejecución desde wheel instalado fuera del árbol fuente, UID 10001 y persistencia entre invocaciones.

Gates: instalación frozen, Ruff format/check, mypy strict, suite completa, cobertura mínima 85 % líneas / 80 % ramas sin bajar umbrales existentes más exigentes, sdist/wheel, dependency audit, secret scan y smokes completos. Investiga regresiones de cobertura relevantes; no inventes un objetivo igual al porcentaje histórico.

ARM64/QEMU no certifica Raspberry Pi física. El gate real manual es adicional al CI; no introduce una dependencia de red en los harnesses offline.

## 12. Entregables y handoff

Entrega:

- Engineering Brief y contrato de fase incorporado.
- Implementación, contratos, ADR y documentación operativa.
- Tests, noveno harness y CI reproducible.
- Informes QA y REVIEWER con SHA/árbol, métodos, probes propios y limitaciones.
- Evidencia saneada del gate real, o bloqueo explícito con instrucciones concretas.
- PR abierto, sin merge, con Phase Completion Report publicado y recuperado por lectura.

El informe final incluirá: MODEL PROFILE USED; base/head/tree; commits y archivos; AC individualizados; cuatro jobs y logs completos; pruebas/cobertura; revisiones; hallazgos y correcciones; seguridad; arquitectura/DB; deuda y limitaciones; enlaces de evidencia y recomendación.

No declares ACCEPTED ni PHASE CLOSED. Presenta **READY_FOR_ORCHESTRATOR_REVIEW** y una recomendación fundada, o **BLOCKED** si T17 u otro gate obligatorio no puede completarse.

Tras una aceptación futura, solo el Orchestrator podrá autorizar el merge del head/árbol exactos. Después se verificarán el merge real, padres base→head, igualdad de árbol, cero diferencias y nuevo CI push/main antes de cerrar P8b.

Empieza por el preflight y el Engineering Brief. Continúa autónomamente dentro del alcance autorizado hasta dejar un candidato completo y revisable.