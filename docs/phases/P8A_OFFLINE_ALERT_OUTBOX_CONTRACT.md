# P8a — Offline Alert Outbox

## MODEL PROFILE

- **ChatGPT recomendado:** GPT-6.1 Sol / High en ChatGPT Work, si está disponible. En Chat normal, GPT-5.6 Sol / High si aparece en el selector.
- **Codex Engineering Lead recomendado:** GPT-6.1 Sol / Medium para coordinación y ejecución rutinaria; High para identidad, persistencia, concurrencia y recuperación.
- **Especialistas:** ARQ/DB-OWNER y BE para implementación; SEC/SRE para límites de confianza, mensajes y recuperación. QA y REVIEWER con GPT-6.1 Sol / High, independientes entre sí y de todos los autores.
- **Escalation:** primero High; GPT-6 Astra / High únicamente ante un bloqueo complejo reproducido y si está disponible. No Max/Ultra por defecto.
- Verifica disponibilidad en el cliente. Registra configuración solicitada, aceptada y realmente observable; no inventes introspección del backend ni cambios de modelo.
- Referencia oficial consultada el 2026-10-20: https://learn.chatgpt.com/docs/models?surface=web. Los niveles recomendados son una decisión del Orchestrator para esta fase.

## 1. Rol, apertura y objetivo

Actúa como Phase Lead de **P8a — Offline Alert Outbox** para Card Market Tracker.

El **00 — ORCHESTRATOR** abre esta fase el **2026-10-20, Europe/Madrid**, tras declarar **P4c: ACCEPTED / PHASE CLOSED** en su chat.

Repositorio: https://github.com/KastaTM/card-market-tracker

Rama: `feat/p8a-offline-alert-outbox`.

**Objetivo:** transformar eventos verificados del journal en intenciones de alerta duraderas, deduplicadas por evento y destino lógico, conservando las evidencias de todas las comparaciones que las sustentan.

P8a implementa preparación y almacenamiento offline. La entrega por Telegram será una fase posterior P8b; no constituye un requisito de aceptación de P8a.

Se autorizan diseño, implementación, rama, pruebas, documentación y PR. **No se autoriza merge.** Solo el Orchestrator acepta/cierra fases y amplía alcance.

## 2. Baseline y continuidad

| Objeto P4c cerrado | Identidad |
| --- | --- |
| PR integrado | https://github.com/KastaTM/card-market-tracker/pull/12 |
| Baseline/main | `b89fff319a94e5eb6e4b7bdad944e879bad371f6` |
| Árbol | `8f62a1d85b375ee839dcd95e09a578cb643c85b6` |
| Primer padre | `de63457bd6de26874a30d2afd688dcd8901e01ff` |
| Segundo padre | `9fb53144dec521d0dde49c02d41022be831421c2` |
| CI push/main | https://github.com/KastaTM/card-market-tracker/actions/runs/39462043464 |
| Informe de integración | https://github.com/KastaTM/card-market-tracker/pull/12#issuecomment-6296873582 |

P4c cerró con 1.170 pruebas PASS, un skip y cobertura 95,55 % / 90,89 %. Son resultados históricos; P8a necesita evidencia propia.

Lee `context.md`, `AGENTS.md`, operating model, arquitectura, ADRs, contratos Discovery/journal, quality gates, testing strategy, threat model, runbooks y deuda.

Verifica remote, refs, checkout y worktrees antes de editar. Conserva cambios y ramas ajenos. Si main avanzó, inspecciona y comunica el delta antes de sustituir la base.

Archiva este contrato en `docs/phases/P8A_OFFLINE_ALERT_OUTBOX_CONTRACT.md`. Actualiza el roadmap con **P4c cerrada / P8a abierta**, atribuido al Orchestrator en chat. Conserva los registros históricos y no inventes un comentario de cierre publicado.

## 3. Alcance y exclusiones

Dentro:

1. Preparación desde una comparación explícita del journal, contrastada con sus capturas originales.
2. Intención de alerta determinista y presentación en texto plano.
3. Outbox SQLite independiente con alertas pendientes y asociaciones a evidencias.
4. Inserción/replay/conflictos, concurrencia, consultas, preview, verificación, recomputación y backup/restore.
5. CLI, documentación, pruebas y octavo harness offline.

Fuera:

- Telegram, email, webhooks o cualquier envío externo.
- Tokens, chat IDs reales, registro de bots o contactos con personas.
- Dispatcher, leases, acknowledgements, estados sent/delivered, reintentos de transporte o scheduler.
- Nuevas fuentes, revisiones, paquetes reales o expansión de corpus.
- Precios, stock, retail, watchlist, oportunidades, launches y preorders.
- API/frontend, promoción canónica, borrado o retención automática.

**Presupuesto de adquisición de fuentes: cero.** Reutiliza exclusivamente R0/R1 y los perfiles synthetic ya autorizados. No readquieras originales descartados.

P2, P6a y Discovery retail siguen **BLOCKED**. P5 y P8b no se abren por este contrato.

## 4. Admisión desde evidencia verificada

La operación pública de preparación recibe:

- DB de capturas.
- DB del journal.
- DB del outbox.
- Un `comparison_id` explícito.
- Un destino lógico explícito.

No selecciona automáticamente “lo último”, no recorre todo el journal ni acepta un resultado JSON o evento autodeclarado.

Antes de escribir:

1. Recupera y valida la comparación completa mediante la frontera P4c.
2. Contrasta el request retenido contra las capturas originales utilizando el lector y comparador existentes.
3. Exige igualdad del comparison_id y del resultado semántico completo.
4. Prepara las intenciones y evidencias desde ese contenido congelado.
5. Persiste atómicamente en el outbox.

La comparación contrastada debe ser exactamente la utilizada para preparar las alertas. No se permite verificar una versión y consumir otra sin comprobar su igualdad.

Reutiliza componentes existentes sin reimplementar el algoritmo Discovery. Mantén puros el comparador y el renderer.

Un JSON, ID, digest, DTO o flag `verified` no concede autoridad. Si utilizas un recibo interno, debe emitirse después del recorrido verificado y ligar por contenido todos los campos consumidos. Documenta que es un límite de aplicación, no una firma frente a código privilegiado.

Ante origen ausente, corrupción, mismatch, perfil inválido o límite excedido: error explícito y cero escrituras.

## 5. Política de alertas e identidad

Política única y versionada: `discovery_reference_alert_v1`.

Tipos admitidos:

- `SET_REFERENCE_FIRST_OBSERVED`.
- `CANDIDATE_REFERENCE_FIRST_OBSERVED`.

Solo se aceptan eventos que realmente pertenezcan al resultado v3 contrastado.

`baseline` y `no_discoveries` producen preparación exitosa con cero alertas y cero asociaciones; no generan una alerta de “sin novedades”.

El destino es un alias lógico local, sin credenciales ni datos de un destinatario real. Define una gramática estricta y acotada, por ejemplo un token ASCII de hasta 64 caracteres. En esta fase el canal es exclusivamente `offline_preview`.

La clave de deduplicación es:

`(destination_key, event_id)`.

Define:

`alt1:` + SHA-256 del JSON canónico de:

`{"identity_version":1,"destination_key":DESTINO,"event_id":EVT3}`.

Documenta y prueba la preimagen exacta. Usa JSON finito, ASCII escaped, claves ordenadas y formato compacto.

No incluyas comparison_id, historia, ruta, reloj de inserción, run ID o renderer_version en esa identidad.

Consecuencias obligatorias:

- Mismo evento y mismo destino: una alerta.
- Mismo evento y otro destino: otra alerta.
- Mismo evento en otra ventana: misma alerta, nueva asociación de evidencia.
- Mismo alt1 con intención intrínseca diferente: conflicto, sin overwrite.
- Cambiar versión de renderer/política no autoriza automáticamente otro envío futuro; cualquier migración requiere contrato posterior.

No alteres cmp1/evt1/cmp2/evt2/cmp3/evt3 ni fingerprints históricos.

## 6. Intención, texto y evidencia por ventana

La intención conserva los campos intrínsecos necesarios: event_id, tipo, referencia completa, status/category, CMT ID congelado cuando exista, current_batch_id, captured_at, perfil y nivel de evidencia.

El texto se deriva exclusivamente de esos campos y de un renderer versionado. No depende de la historia o del comparison_id elegido primero.

Requisitos de presentación:

- Texto plano y determinista, sin interpretación HTML/Markdown.
- Máximo 4.096 bytes UTF-8 por mensaje, como límite propio de CMT.
- Identificar claramente los eventos synthetic.
- Describir novedad relativa a una ventana seleccionada.
- Distinguir candidato de entidad aceptada.
- No afirmar lanzamiento, disponibilidad comercial, precio, stock o novedad global.
- No fabricar nombres ni URLs ausentes de la evidencia.
- Tratar referencias y otros textos como entrada no confiable; definir representación segura de controles y saltos de línea.
- Preservar los valores originales en la evidencia aunque la presentación los escape.

Para cada asociación conserva comparison_id, digest semántico del journal y el evento completo con su evidencia de ventana. No sobrescribas una evidencia con otra.

**Caso obligatorio:** dos cmp3 distintos con el mismo evt3 deben producir una alerta para un destino y dos asociaciones diferentes, recuperables con sus evidencias completas.

Los relojes de preparación no sustituyen adquisición, captura o primera observación en ventana.

## 7. Almacenamiento y atomicidad

Usa un SQLite independiente con owner/application_id propios y schema v1. Las DB existentes permanecen sin migración: capturas schema2 y journal schema1.

Modelo lógico:

- Metadata de propiedad y versión.
- Alertas, con alt1, clave única destino/evento, intención canónica, mensaje congelado, versiones, digest, primer instante de preparación y estado `pending`.
- Asociaciones alerta–comparación, con FK local, clave compuesta y evidencia congelada.

No añadas tablas de entrega, intentos de red o scheduler. `pending` significa preparada y pendiente de una futura entrega; no significa enviada, recibida o leída.

Una transacción guarda todas las alertas y asociaciones de la comparación solicitada, incluidas las asociaciones nuevas a alertas existentes. Cualquier conflicto revierte la operación completa.

Replay idéntico no crea filas ni modifica mensajes, evidencia o primer timestamp. La respuesta distingue alertas nuevas, existentes y asociaciones nuevas/repetidas.

No prometas atomicidad distribuida entre capturas, journal y outbox. La verificación de origen precede al commit local del outbox; documenta el snapshot representado y el supuesto de inmutabilidad.

Reutiliza la política de rutas seguras/directorios confiables. Rechaza alias entre las tres DB, enlaces no admitidos, archivos de otro propietario y destinos existentes de init/backup/restore sin dañarlos. No inicialices implícitamente.

## 8. Operaciones, verificación y recuperación

Añade un grupo CLI separado, por ejemplo `cmt alert-outbox`, con:

- init.
- enqueue de una comparación explícita.
- get y list de alertas.
- listado paginado de evidencias de una alerta.
- preview de una alerta persistida.
- verify local.
- recompute de una asociación explícita contra journal y capturas.
- backup y restore.

El Engineering Brief fijará flags y respuestas exactos antes de implementar.

Preview es read-only: no envía, no consume pendientes, no cambia estado y no incrementa intentos.

Verify local comprueba esquema, inventario, integridad/FKs, límites, gramática, digests, identidad, mensaje/renderer y relaciones. No afirma autenticidad frente a una reescritura coherente del archivo.

Recompute contrasta una asociación explícita con el journal y sus capturas originales, recalcula la intención y verifica su correspondencia con la alerta. Origen ausente o cambiado es FAIL, aunque verify local pase.

Backup/restore preserva alertas, asociaciones, mensajes, versiones, digests, estado pending y primeros timestamps. Usa SQLite backup con snapshot consistente, destinos nuevos reservados y validación/reapertura.

Los tres backups son independientes. El runbook explica cómo restaurarlos y recomputar asociaciones antes de afirmar verificación de origen. No borres sidecars manualmente ni repares silenciosamente evidencia.

Prueba rollback, reapertura, dos escritores concurrentes y terminación real de un proceso durante una escritura. Distingue esas pruebas de pérdida eléctrica física.

## 9. Límites, errores y observabilidad

Preserva los límites y contratos de Discovery/journal anteriores.

Límites adicionales:

- Una comparación por enqueue, máximo 1.000 eventos.
- Máximo 16 MiB de contenido canónico preparado por operación; no partición ni éxito parcial para eludir el límite.
- Mensaje máximo 4.096 bytes UTF-8.
- Listados: default 100, máximo 1.000 resúmenes y 1 MiB de salida.
- Evidencias completas: recuperación de una asociación explícita y límite documentado compatible con el journal.
- Operaciones default 2 s, máximo explícito 5 s.
- Enqueue comparte presupuesto entre verificación de origen, preparación y escritura, sin reiniciarlo por etapa.

Aplica límites antes de cargas no acotadas, también con archivos SQLite manipulados. No cargues toda la historia con fetchall. Usa paginación keyset estricta y documenta su comportamiento ante inserciones concurrentes.

Verify completo puede fallar por deadline; revisión parcial nunca es PASS. Los presupuestos cooperativos no garantizan latencia frente a bloqueo del SO/dispositivo.

Errores categorizados, stdout versionado y sin éxito parcial. Exit 2 para contrato/input/conflicto; exit 1 para almacenamiento/origen/ejecución según mapa explícito. DB ausente no es lista vacía.

Logs: operación, run ID, duración, resultado, categorías y conteos acotados. Sin mensajes, referencias, destino lógico, rutas, payloads, SQL ni excepciones crudas. La salida explícita y los archivos requieren protección local.

No introducir cuotas globales o borrado automático.

## 10. Acceptance Criteria

| ID | Condición verificable |
| --- | --- |
| AC-A01 | Baseline, cierre P4c/apertura P8a, contrato y ownership documentados |
| AC-A02 | Admisión desde comparación explícita y capturas originales, sin autoridad por autodeclaración |
| AC-A03 | Contraste y consumo del mismo contenido congelado; fallos sin escrituras |
| AC-A04 | alt1 y deduplicación destino/evento deterministas, con preimagen independiente |
| AC-A05 | Mismo evt3 en dos ventanas: una alerta y dos evidencias conservadas |
| AC-A06 | Replay sin reescritura; conflictos atómicos; primer timestamp preservado |
| AC-A07 | Renderer seguro, determinista, acotado y honesto sobre synthetic/candidatos/ventana |
| AC-A08 | DB independiente; capturas, journal, identidades y contratos anteriores intactos |
| AC-A09 | Concurrencia, rollback, interrupción de proceso y reapertura sin filas parciales |
| AC-A10 | Consultas paginadas y preview read-only, sin simular entrega |
| AC-A11 | Verify local y recompute distinguen consistencia de contraste con origen |
| AC-A12 | Backup/restore y seguridad de rutas preservan contenido y estado |
| AC-A13 | R0→R1 real prepara cero alertas; positivos exclusivamente synthetic; cero adquisición |
| AC-A14 | Límites, errores, logging y octavo harness offline comprobados |
| AC-A15 | ADR, contratos, arquitectura, runbook, amenazas, deuda y roadmap coherentes |
| AC-A16 | Todos los gates PASS; QA y REVIEWER independientes sobre SHA/tree final exactos |

Un criterio sin evidencia es FAIL/BLOCKED con causa, nunca PASS por intención.

## 11. Tests y quality gates

Pruebas significativas cubren:

- DTO/JSON/ID/digest forjados y mutación tras validación.
- Reescritura coherente del journal detectada contra capturas.
- Mismo evento/dos ventanas; dos destinos; replay después de restaurar.
- Conflicto de mensaje/intención para la misma identidad.
- Rollback tras inserciones parciales y escritores concurrentes.
- Interrupción de proceso, reapertura y recuperación.
- Inputs hostiles, controles de texto, Unicode y límites de bytes.
- Corrupción de relaciones/digests/versiones y SQLite sobredimensionado.
- Alias entre archivos, sidecars, locks y deadlines.
- Paginación estática y concurrente; preview sin mutación.
- Cuatro comparaciones reales sin eventos ni alertas.
- Eventos synthetic claramente etiquetados.

QA debe construir probes y expectativas propios, incluidos hashes e identidad. REVIEWER revisa código, contratos, seguridad y evidencia del candidato exacto. Cambios posteriores requieren renovar las revisiones afectadas.

Añade un octavo harness offline para init, enqueue, preview, replay, evidencias compartidas, verify/recompute y backup/restore, entre procesos separados.

Ejecuta los ocho harnesses en wheel instalado fuera del checkout, Compose, AMD64 y ARM64/QEMU; fixtures read-only, red deshabilitada en runtime, UID 10001 y datos privados en contenedores.

Gates obligatorios: instalación frozen/lock, Ruff format/check, mypy strict, suite completa unit/contract/integration/regression/security/concurrency, cobertura ≥85 % líneas y ≥80 % ramas, sdist/wheel externo, dependency audit, secret scan y cuatro jobs CI PASS con logs completos.

No reducir thresholds, eliminar regresiones ni añadir skips para obtener verde. QEMU no certifica hardware Raspberry Pi ni cortes eléctricos.

## 12. Organización, documentación y handoff

Engineering Lead prepara plan y ownership. ARQ/DB-OWNER posee almacenamiento/contrato; BE servicio/renderer/CLI; SEC/SRE revisa confianza, contenido y recuperación. QA y REVIEWER son distintos entre sí y de todos los autores.

Paraleliza análisis o archivos disjuntos. Coordina Git, contratos e interfaces compartidos secuencialmente.

Redacta el siguiente ADR libre, previsiblemente ADR-0010, sobre identidad de alerta, evidencias por ventana, almacenamiento independiente y ausencia de transporte. Añade contratos versionados de intención/outbox y almacenamiento, con receta de hashes, gramática, errores y límites.

Actualiza arquitectura, threat model, runbooks, testing/gates, roadmap y deuda. TD-001–TD-005 siguen abiertas; no atribuyas a esta fase autenticación de productores, confinamiento ante administrador hostil, cuotas o Pi físico.

Entrega PR abierto con Phase Completion Report: AC-A01–A16, base/head/tree, modelo observable, comandos/entornos, gates, cuatro logs completos, pruebas independientes, limitaciones y evidencia publicada recuperada por lectura de vuelta.

La primera respuesta del Phase Lead confirma objetivo, baseline, deduplicación destino/evento, asociaciones por ventana, cero adquisición, ausencia de transporte y perfiles de modelos. Después prepara el Engineering Brief para Codex y dirige el trabajo hasta completar la fase.

Procede con decisiones operativas ordinarias dentro del alcance. No te detengas en un plan; comunica bloqueos reales con evidencia y acciones concretas.

Con todos los gates completos, devuelve **READY_FOR_ORCHESTRATOR_REVIEW**.

No emitas ACCEPTED/PHASE CLOSED, no hagas merge ni abras P8b. La integración requerirá autorización exacta del Orchestrator y el cierre exigirá merge real, padres ordenados, árbol idéntico y nuevo CI push/main verificado.