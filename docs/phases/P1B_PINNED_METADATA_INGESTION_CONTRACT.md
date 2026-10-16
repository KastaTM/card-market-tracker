MODEL PROFILE

- Recommended ChatGPT model: **GPT-6.1 Sol / High**, en ChatGPT Work si el selector lo ofrece. Para Chat normal: **GPT-5.6 Sol / High**, si está disponible. Motivo: fronteras de autorización, procedencia, identidad y compatibilidad de datos históricos.
- Recommended Codex model: **GPT-6.1 Sol / Medium** para Engineering Lead y ejecución rutinaria; **High** para decisiones de integridad, migración y depuración difícil.
- ARQ/DB-OWNER, INTEGRATIONS/DATA y SEC/SRE: **GPT-6.1 Sol / High**, en tareas justificadas y con ownership separado.
- QA y REVIEWER: **GPT-6.1 Sol / High**; dos agentes independientes entre sí y de los autores, sobre el candidato final exacto.
- Escalation: subir primero a High. **GPT-6 Astra / High** solo ante un bloqueo complejo reproducido que persista y si está disponible. No usar Max/Ultra por defecto.
- Comprobar los selectores antes de delegar. Registrar modelo/reasoning solicitados, aceptados y efectivamente verificables; no atribuir una configuración de backend que no pueda observarse. Si falta un modelo, informar de las alternativas disponibles sin inventarlas.
- Referencia oficial de disponibilidad consultada el 2026-10-14: [https://learn.chatgpt.com/docs/models?surface=web](https://learn.chatgpt.com/docs/models?surface=web). Sol 6.1 corresponde a Work/Codex; no presentarlo como opción de Chat normal.

# P1b — Pinned Metadata Ingestion & Capture Scope

## 1. Rol y decisión del Orchestrator

Actúa como Phase Lead de **P1b — Pinned Metadata Ingestion & Capture Scope**, para Card Market Tracker. Este documento es el contrato completo de apertura emitido por **00 — ORCHESTRATOR**, el **2026-10-14 UTC**.

El Orchestrator confirma **P0.5b: ACCEPTED / PHASE CLOSED**, tras la comprobación de integración y CI, y abre **P1b** exclusivamente con el alcance definido aquí. P0, P0.5, P1a, P3a y P4a conservan su cierre.

Repositorio: [https://github.com/KastaTM/card-market-tracker](https://github.com/KastaTM/card-market-tracker)

Rama autorizada: `feat/p1b-pinned-metadata-ingestion`.

Tu función es traducir este contrato a un Engineering Brief, coordinar a Codex Engineering Lead, contrastar evidencia y presentar un candidato revisable. Solo el Orchestrator puede aceptar, cerrar, ampliar alcance o autorizar integración. Esta apertura autoriza implementación, pruebas, rama y PR; **no autoriza merge**.

## 2. Baseline vinculante

| Elemento aceptado P0.5b | Valor                                                                                                                                                          |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PR fusionado            | [https://github.com/KastaTM/card-market-tracker/pull/8](https://github.com/KastaTM/card-market-tracker/pull/8)                                                 |
| Head revisado           | `302e8d3f3155c14091d26841b8a230791109f220`                                                                                                                     |
| Merge/main              | `acca10e406dac8809edc289c3077a6ec8785a622`                                                                                                                     |
| Árbol integrado         | `26011d0375f3716a7fffb31956665eb97567a0df`                                                                                                                     |
| Primer padre            | `6385c952a9f2024c8b7bdb33d37fa21017029bd5`                                                                                                                     |
| Segundo padre           | `302e8d3f3155c14091d26841b8a230791109f220`                                                                                                                     |
| CI push/main            | [https://github.com/KastaTM/card-market-tracker/actions/runs/38595222923](https://github.com/KastaTM/card-market-tracker/actions/runs/38595222923)             |
| Informe de integración  | [https://github.com/KastaTM/card-market-tracker/pull/8#issuecomment-6172918452](https://github.com/KastaTM/card-market-tracker/pull/8#issuecomment-6172918452) |

Los cuatro jobs PASS, 611 pruebas, un skip y coberturas 97,79 % / 94,43 % son evidencia histórica de P0.5b. P1b exige ejecución propia sobre su candidato.

Antes de editar, lee `context.md`, `AGENTS.md`, operating model, arquitectura, ADR-0003–0005, contratos existentes, testing/quality gates, threat model, deuda y los documentos de P0.5b. Verifica remote, refs, worktrees y cambios locales. Preserva trabajo ajeno. Si `main` difiere del baseline, inspecciona y comunica el delta; no sustituir silenciosamente la base autorizada ni resetear trabajo.

Archiva este contrato en `docs/phases/P1B_PINNED_METADATA_INGESTION_CONTRACT.md`. Registra el cierre P0.5b y la apertura P1b en roadmap, atribuidos al Orchestrator. Conserva los informes anteriores como snapshots históricos; no inventar comentarios publicados de cierre.

## 3. Objetivo y resultado esperado

Entregar el primer recorrido reproducible de **metadatos reales mínimos**, desde dos artefactos concretos del repositorio TCGdex hasta observaciones validadas, resolución conservadora y persistencia SQLite con contexto de captura y procedencia inmutables.

El recorrido debe funcionar offline con un paquete mínimo revisado. Debe demostrar reapertura, replay, rechazo de alteraciones, aislamiento de la ruta real autorizada y migración segura desde la historia synthetic existente.

Esta fase implementa una ruta específica de repositorio. No cualifica el REST TCGdex ni el catálogo completo. Las dudas generales de cobertura no impiden comprobar dos artefactos y cuatro proyecciones lingüísticas, siempre que se describa exactamente ese límite.

## 4. Decisión de fuente y campos autorizados

El Orchestrator autoriza **consulta, extracción, retención local, fixture mínima publicada con atribución y conservación histórica de la proyección permitida** de estos dos archivos, en esta revisión:

Repositorio: `tcgdex/cards-database`.

Commit: `4199850a6af49665db0080fa2bb9ef751750a406`.

| Artefacto exacto                             | Git blob SHA-1 comprobado                  | Uso                                               |
| -------------------------------------------- | ------------------------------------------ | ------------------------------------------------- |
| `data/Sword & Shield/Darkness Ablaze.ts`     | `db48bc4a054b3b1c5bd2b6956257f20ba251c79c` | Set `swsh3`, proyecciones ES y EN                 |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | `6db89c69b56552fa4e09f26e0e90d14e97466411` | Carta, número textual `136`, proyecciones ES y EN |
| `LICENSE`                                    | `c67ded0d5f0abc77b4fbdbfd37312f2a88de1b55` | Aviso MIT íntegro                                 |
| `README.md`                                  | `77bc8108c2cdb54c663e1fdf8c4502ac65f88734` | Declaración de licencia de la base de datos       |

Base primaria: [LICENSE fijada](https://github.com/tcgdex/cards-database/blob/4199850a6af49665db0080fa2bb9ef751750a406/LICENSE) y [README fijado](https://github.com/tcgdex/cards-database/blob/4199850a6af49665db0080fa2bb9ef751750a406/README.md), que declara la base de datos bajo MIT. El permiso sobre material cubierto exige conservar el aviso completo. No constituye licencia separada de marcas, ilustraciones o datos de terceros.

Las cuatro lecturas del Orchestrator verificaron licencia, declaración y contenido de ambos artefactos en esa revisión. La fase debe conservar evidencia propia de extracción y QA. El parser diagnóstico de P0.5b sigue sin acreditación de producción; no reutilizarlo como si hubiera pasado estos gates.

Allowlist de salida:

| Dato                       | Transformación admitida y semántica                                                                                         |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Set `id`                   | Literal del archivo; referencia externa contextual, nunca CMT ID                                                            |
| Set `name.es`, `name.en`   | Idioma exacto; sin fallback entre idiomas                                                                                   |
| Set `releaseDate`          | Fecha calendario declarada; no fecha regional española ni instante de lanzamiento probado                                   |
| Carta `name.es`, `name.en` | Idioma exacto; nombres no usados como identidad                                                                             |
| Número de carta            | Stem textual del archivo, `136`; no conversión numérica ni pérdida de ceros/prefijos                                        |
| Relación carta → set       | Importación declarada al archivo de set aprobado, validada sin resolver ni ejecutar imports                                 |
| ID externo de carta        | Derivación explícita `${set.id}-${stem}`: `swsh3-136`; identificador local de esta ruta, sin garantía de estabilidad futura |
| Contexto y evidencia       | Repositorio, commit, path/blob/digest, política/extractor versionados, idioma, tiempos y alcance descritos abajo            |

Usar un namespace propio para la ruta de repositorio, por ejemplo `tcgdex_repository`. No equiparar automáticamente sus referencias a las del REST. Fijar su valor en el contrato y pruebas antes de implementar. El commit pertenece a la procedencia, no al namespace o identidad estable de producto.

La carta carece de evidencia de un ejemplar/finish capturado: **variant = unknown**. No derivar una printing normal/reverse ni un binding a partir de su array de variantes. Con las reglas actuales puede y debe seguir como candidato `unknown_variant`; ello no impide persistir la evidencia. Sets solo se aceptan con un binding curado explícito y coherente.

Excluir de la proyección retenida: imágenes, logos, símbolos, URLs de imágenes, efectos, ataques, descripciones, ilustrador, precios, stock, sealed, IDs de marketplaces, variantes, conteos, `updated` y cualquier campo no enumerado. Los originales pueden leerse temporalmente para extraer/verificar, pero no se incorporan íntegros a fixtures, logs ni DB.

## 5. Dentro y fuera de alcance

Dentro:

- Una adquisición manual y acotada de los cuatro artefactos fijados; extracción sin ejecución de TypeScript y construcción reproducible de un paquete mínimo con aviso MIT y ledger de campos/digests.
- Un adaptador aislado para ese paquete, que produzca `Observation` genéricas y use el resolver/manifest actuales.
- Una frontera dedicada de admisión real que verifique política, artefactos y proyección autorizada. Cambiar únicamente un string de provenance no concede acceso a almacenamiento.
- Captura/scope persistido incluso cuando no haya observaciones admitidas, con resultados y evidencia explícitos; migración SQLite versionada y recuperación.
- Comandos locales mínimos para importar/verificar/consultar el paquete y migrar. El diseño concreto de CLI se documenta; nombres no fijados por este contrato.
- Actualización de arquitectura, contratos, política de fuente, amenaza, runbooks, deuda y trazabilidad.

Fuera:

- REST TCGdex, SDK, servidor/compiler upstream, ejecución de código upstream, rastreo del repo, corpus completo, nuevas revisiones o actualización automática de la selección.
- Precios, mercado EUR, retail/stock, sealed, preorders, lanzamiento, autenticación de productores externos, cuentas nuevas, compras o contactos con terceros.
- Scheduler, daemon de adquisición, frontend/API, señales, entrega Telegram, promoción de candidatos, retención/quotas automáticas.
- Comparación temporal de datos reales. **P4a mantiene su frontera synthetic**; no introducir real Discovery por la extensión de storage.
- Resolver todas las TD abiertas o certificar hardware Pi/pérdidas eléctricas reales.

P2, P6a y Discovery retail siguen **BLOCKED**. TCGdex REST, eBay Browse, GAME y Awin conservan sus condiciones; Scrydex mantiene `REJECTED_FOR_PROPOSED_USE` para la referencia EUR propuesta. Esta apertura no les concede permiso de ingestión.

## 6. Adquisición, extracción y confianza

Presupuesto nuevo P1b: **máximo ocho solicitudes de contenido**, exclusivamente a los cuatro paths anteriores y el commit fijado. Permite cuatro lecturas para extracción y cuatro para contraste independiente QA. Cada intento, retry o redirect que implique una nueva solicitud consume presupuesto; mantener ledger compartido y ejecución secuencial. Caché local puede reutilizar bytes ya adquiridos. El presupuesto de P0.5b terminó y no se reutiliza.

Usar GitHub o contenido raw de GitHub para esos paths; no seguir URLs extraídas del payload, no endpoints API TCGdex, no clonación íntegra de la fuente ni bypass. Si el entorno no puede adquirirlos, presentar el bloqueo o reutilizar una copia con procedencia verificable; no sustituir por una revisión mutable.

El importador runtime y todo CI operan **sin red**. No se necesita un cliente HTTP de producción en esta fase. La adquisición de ingeniería y la importación offline son operaciones distintas.

Verificar bytes UTF-8, tamaño y digest; distinguir Git blob SHA-1 de SHA-256 de contenido. Recalcular ambos desde bytes cuando corresponda. No llamar SHA-256 al SHA-1 proporcionado por GitHub. Preservar offsets/identificación de campos y versión de la transformación en el ledger.

El extractor usa una gramática limitada no ejecutable o un procedimiento igualmente determinista con validación inequívoca de las posiciones autorizadas. Nunca `eval`, `exec`, Node, imports dinámicos, compilación o instalación de dependencias upstream. Una regex que encuentre un nombre en cualquier parte del archivo no acredita su procedencia. Sintaxis/campos ambiguos, duplicados o incompatibles producen error explícito.

Retener únicamente el paquete normalizado mínimo, su lock/política aprobada, digests de los originales, evidencia de la extracción y aviso MIT. Fixtures del parser que necesiten contenido excluido deben ser sintéticas y declaradas. QA contrasta la proyección con los originales fijados de forma independiente; no basa su PASS solo en el output del extractor autor.

La frontera de almacenamiento debe validar contra una política/lock controlada y revisada, que vincule artefactos, campos y digest de la proyección. Un JSON aportado por un usuario con hashes y `observed` autodeclarados no adquiere autoridad por contenerlos. Un objeto Python construido manualmente tampoco elude esta validación.

Explicar el límite de confianza: comprobación contra artefactos/paquete revisados, no autenticación de la verdad física del producto, de un productor independiente ni de disponibilidad actual del proveedor. No introducir firmas o servicios externos sin necesidad.

## 7. Contratos y arquitectura

Mantener `External Source → Validated Source Model → Normalized Ingestion → Domain → Storage`. Shapes TCGdex, parser y política permanecen fuera del dominio y del comparador. Preferir librería estándar y dependencias runtime actuales; cualquier incorporación exige necesidad concreta, ADR y audit.

Preservar UUIDv4 curados, igualdad completa de referencias, null exacto, números textuales, relaciones y snapshots inmutables. Ningún hash, nombre o ID externo crea identidad CMT. Los candidatos no reciben CMT ID. No modificar el manifest automáticamente.

Definir un contrato versionado de paquete/captura y una nueva frontera de persistencia. `PERSISTENCE_V1` conserva su entrada synthetic-only; no ampliar silenciosamente su enum o eliminar su guard. Un contrato nuevo debe describir la admisión estrecha de `observed` para esta ruta. `documented` no pasa automáticamente a autorización de persistencia.

Cada captura nueva registra como mínimo:

- Identificador estable de lote/captura y policy/extractor versionados.
- Fuente, método `pinned_repository_bundle`, revisión, artefactos y digests comprobados.
- Namespace, entity kind, idioma y selector exacto; una unidad de scope no mezcla contextos. El paquete puede agrupar unidades enlazadas explícitamente.
- Conjunto exacto de paths seleccionados y completados, resultado, conteos de entrada/aceptados/candidatos/rechazados y evidencia de validación.
- Tiempo de adquisición del artefacto y captura declarada, con convención y UTC; tiempo de importación/persistencia separado. Reimportar un paquete offline no lo convierte en una nueva observación live ni permite redatar su adquisición con el reloj de importación.
- Estado de evidencia que distinga paquete/artefactos verificados de declaración legacy o del productor.

El conjunto autorizado contiene el set y la carta en ES/EN. Una traducción requerida ausente, archivo no leído, digest incorrecto o error del parser no constituye captura vacía válida. Rechazos por resolución no equivalen a cero registros fuente. Una captura parcial no se eleva a completa ni se usa como evidencia de ausencia.

Definir en contratos las diferencias entre éxito no vacío, vacío válido de una selección explícita, parcial/rechazos y fallo. No hace falta fabricar un vacío real en esta selección: sus reglas negativas y soporte genérico pueden probarse con datos sintéticos. Los errores de adquisición no requieren almacenar payloads ni convertir la DB en un journal de red.

Un scope persistido acredita contexto registrado y validación realizada. No acredita cobertura total del catálogo ni ausencia de productos. TD-005 se aborda para nuevas capturas, conservando el límite de historia legacy y de productores independientes.

## 8. SQLite, migración y recuperación

Se autoriza una migración **schema v1 → v2**, limitada a contexto/procedencia y la nueva admisión. ARQ/DB-OWNER documentan tablas, constraints, relaciones, validación y alternativas en ADR. No introducir PostgreSQL, ORM ni event store.

- Migración explícita mediante comando; leer/consultar no migra ni escribe automáticamente. Rechazar de forma segura versiones futuras/no soportadas.
- Preflight de schema/integridad y backup verificado antes de cambiar una DB existente. Migración transaccional; interrupción/fallo deja v1 íntegra o v2 íntegra, nunca éxito parcial. Respaldos originales y destinos no se sobrescriben silenciosamente.
- Mantener observaciones, entidades, UUIDs, timestamps, snapshots y fingerprints históricos. No resolver otra vez historia contra un manifest nuevo ni recalcular fingerprints v1 con reglas v2.
- Lotes antiguos sin scope quedan explícitamente legacy/no verificados; no rellenarlos como si sus datos acreditaran un contexto de captura. Vacíos v1 conservan su limitación `request_attested_empty`.
- Inicialización nueva y lectura de v1/v2 tienen comportamiento explícito. Mantener funcionalidad de comandos P0/P1a/P3a/P4a sobre bases soportadas y equivalencia de resultados synthetic; actualizar pruebas de versión solo cuando reflejen el cambio autorizado.
- Backup/restore/verify entienden v2 y sus relaciones. Restaurar v1 permite conservarla y migrarla explícitamente; el rollback operativo consiste en restaurar el backup verificado, no en borrar historia v2.
- Contexto de captura y registros se leen en un único snapshot transaccional. Validar integridad, relaciones, índices/conteos y límites; datos manipulados no se devuelven como verificados.
- Replay v2 incluye todo el contexto relevante: política, fuente/revisión/digests, selección/completitud, tiempos, proyección normalizada, contexto de manifest y snapshots. Token igual/contexto equivalente produce replay sin cambios; contexto distinto produce conflicto sin sobrescribir. El hash demuestra equivalencia, no autenticidad.
- Mantener límites de input/lectura/tiempo existentes. Documentar límites propios para artefactos/paquete/scope, sin acceso ilimitado a disco ni lecturas sin cota.

Los entrypoints synthetic existentes siguen rechazando real input antes de retenerlo. La ruta nueva rechaza procedencia/política/artefactos no autorizados. Las lecturas Discovery P4a rechazan una selección observada o mixta de forma explícita; no filtran esas filas para generar un resultado aparentemente completo.

## 9. Criterios de aceptación

| ID     | Condición verificable                                                                                                                        |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-I01 | Git preflight, contrato archivado, baseline exacto y decisión P0.5b/P1b registrados con atribución correcta                                  |
| AC-I02 | Política por campo/uso para los dos artefactos y aviso MIT íntegro; ninguna fuente/campo adicional retenido                                  |
| AC-I03 | Extracción determinista no ejecutable, blobs/digests/proyección contrastados y presupuesto trazable                                          |
| AC-I04 | Adaptador emite las cuatro proyecciones ES/EN con números/relaciones/fechas correctos y sin fallback ni finish inventado                     |
| AC-I05 | Resolución preserva identidad curada, contradicciones y candidatos sin CMT ID; ninguna promoción automática                                  |
| AC-I06 | Frontera real rechaza objetos/paquetes/políticas alterados o autodeclarados; PERSISTENCE_V1 mantiene synthetic-only                          |
| AC-I07 | Contexto de captura persistido, versionado e inmutable; tiempos de adquisición/captura/importación diferenciados                             |
| AC-I08 | Vacío/partial/rechazos/fallo distinguidos; falta de artefacto/traducción no produce captura completa vacía; límites de verificación expresos |
| AC-I09 | Migración v1→v2, fallo/interrupción y recuperación probados; historia/fingerprints v1 preservados, legacy scope sin fabricación              |
| AC-I10 | Escritura atómica, replay/conflictos y reapertura entre procesos funcionan sobre metadatos autorizados                                       |
| AC-I11 | Lecturas acotadas/coherentes, verify y backup/restore v2 detectan corrupción y preservan contexto/relaciones                                 |
| AC-I12 | Regresiones P0/P1a/P3a/P4a pasan; Discovery rechaza observado/mixto y no elude su frontera                                                   |
| AC-I13 | CLI/errores/logs categorizados y seguros; no payloads, secrets ni éxito aparente ante fallo                                                  |
| AC-I14 | Wheel fuera del checkout, Compose, AMD64 y ARM64/QEMU ejecutan el nuevo recorrido offline entre procesos con UID 10001                       |
| AC-I15 | ADRs, contratos, fuente, threat model, runbooks, deuda y evidencia coinciden con código y no amplían permisos                                |
| AC-I16 | Gates y CI del candidato final PASS; QA y REVIEWER independientes sobre SHA/árbol exactos, sin bloqueos pendientes                           |

Trazar cada AC a tests, archivos, comandos, logs o revisiones. Un criterio obligatorio sin ejecución/evidencia es FAIL con razón; no presentarlo como N/A.

## 10. Pruebas y gates obligatorios

Pruebas unitarias/contrato: formato/versión/tipos/nulls/duplicados/bounds; idiomas exactos; campos y paths no permitidos; artefactos/commit/blob/proyección alterados; sintaxis ambigua y código ejecutable; ausencia de imports ejecutados; candidatos/contradicciones y namespace contextual.

Pruebas con SQLite real: backup v1, migración v2, conservación exacta de contenido histórico y replay v1; rollback/fault injection; scope legacy/vacío; foreign keys/conteos/política manipulados; replay y conflictos por diferencias relevantes; locks/timeout; snapshot de lectura coherente; backup/restore v1/v2.

Integración CLI: importar el paquete licenciado revisado en DB nueva y migrada, cerrar/reabrir en otro proceso, consultar contexto, repetir token, provocar conflicto y comprobar cero mutaciones, backup/restore y límites synthetic/Discovery. Los cambios temporales/adversariales de datos reales se prueban con fixtures **synthetic**, no se publican como capturas reales.

Conservar todos los harnesses previos. Añadir un harness P1b reutilizable por wheel/Compose/AMD64/ARM64 con fixtures read-only y red deshabilitada. Debe probar persistencia entre procesos y recuperación; ejecutar una función varias veces en el mismo proceso no basta.

Gates:

- Frozen install y lock consistente; Ruff format/check; mypy strict.
- Suite completa: unit, contract, integration, migration, regression; cobertura global de código propio ≥85 % líneas y ≥80 % ramas, incluyendo errores/migración.
- sdist/wheel y ejecución instalada fuera del árbol fuente.
- Dependency audit, secret scan y revisión SEC/SRE.
- Revisión ARQ/DB-OWNER y de contratos/política/licencia.
- Cuatro jobs CI conservados: Quality, Compose, AMD64 y ARM64/QEMU; logs completos/steps comprobados, sin llamadas a fuentes dentro de CI.
- QA y REVIEWER distintos de los autores y entre sí; revisiones del candidato final exacto.

No rebajar thresholds, eliminar regresiones ni añadir skips para obtener verde. Un cambio legítimo de aserciones de versión se documenta y mantiene las invariantes verificadas. QEMU no acredita hardware Pi nativo ni resistencia a cortes eléctricos reales.

## 11. Observabilidad y seguridad

Logs estructurados con run ID, duración, contadores y categorías fijas para extracción/política/captura/migración/replay/backup; ningún body, nombre de producto, path/URL arbitrario, SQL, token de lote ni excepción cruda. Contexto consultable en salida explícita y acotada según contrato; no volcarlo automáticamente al log.

Entradas y artefactos no confiables, validación previa a almacenamiento, límites de bytes/profundidad/nodos/strings y presupuesto. No seguir URLs ni paths dictados por payload; no escapes del directorio previsto, ejecución upstream, contactos ni credenciales de fuente. El permiso de lectura pública no convierte información excluida en fixture permitida.

Conservar permisos locales, UID 10001 y límites de directorios confiables. Identificar amenazas nuevas de spoofing de provenance, lock/policy manipulada, migración interrumpida y falsa completitud. Las revisiones deben distinguir integridad local de autenticidad externa.

## 12. Organización y entregables

Codex Engineering Lead realiza preflight, ownership y coordinación. Roles mínimos justificados: ARQ/DB-OWNER para contratos/migración; INTEGRATIONS/DATA para extracción/adaptador/política; SEC/SRE para límites/seguridad; QA y REVIEWER independientes. Se pueden combinar especialidades de autor, nunca autores con QA/REVIEWER.

Paralelizar únicamente análisis o archivos con ownership disjunto. Git, lockfile, contratos compartidos y DB se coordinan secuencialmente. Registrar tareas, modelos solicitados/aceptados y límites de independencia. No atribuir nuevas reviews a un merge por igualdad de árboles.

Entregables mínimos:

1. Contrato archivado, Engineering Brief y ownership.
2. Extracción/adaptador, paquete mínimo/lock, aviso MIT, evidencia por campo y ledger de solicitudes.
3. Captura/procedencia, nueva persistencia, migración/verify/backup/restore y CLI documentados.
4. ADR de ruta/captura/migración y contratos versionados, conservando documentos v1 como historia.
5. Tests/harness offline y cuatro jobs CI con logs completos.
6. Arquitectura, threat model, runbooks, source selection/matrix, roadmap y deuda actualizados.
7. Informes QA y REVIEWER del candidato final.
8. PR abierto con Phase Completion Report y ledger externo que ligue base/head/tree, ACs, reviews y CI sin commits circulares para insertar su propio SHA.

TD-001–TD-005 permanecen abiertas al inicio. Se puede proponer reducción/cierre parcial con evidencia y alcance preciso; el Phase Lead no cierra deuda que exceda lo probado. TD-005 legacy/independent-producer no se declara resuelta por persistir un scope nuevo.

## 13. Handoff y revisión final

El primer mensaje del Phase Lead confirma comprensión de objetivo, baseline, fuente exacta/allowlist, presupuesto, exclusiones, modelos y plan para Codex. Después procede con el Engineering Brief; no repite una investigación general P0.5b ni pide otra autorización para el trabajo aquí definido.

Informe final requerido: MODEL PROFILE USED; Git identity/base/head/tree; alcance entregado; AC-I01–I16; gates PASS/FAIL con evidencia exacta; arquitectura/DB/data contracts; QA/REVIEWER; source-rights/semantics y límites; deuda; rework si existe; enlaces y recomendación.

Solo termina **READY_FOR_ORCHESTRATOR_REVIEW** cuando todos los gates obligatorios estén PASS. Si falta evidencia o existe bloqueo, informa FAIL/BLOCKED con acciones concretas. No emitir ACCEPTED ni PHASE CLOSED, ni mergear ni abrir otra fase.

El Orchestrator revisará el candidato y podrá autorizar integración sobre identidad exacta. Después será necesario verificar merge real, padres ordenados base→head, igualdad de árbol y CI nuevo `push/main` antes del cierre P1b. Una eventual P4b de Discovery sobre metadatos reales necesita contrato posterior; no queda abierta aquí.