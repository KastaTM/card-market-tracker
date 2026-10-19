MODEL PROFILE

- **Recommended ChatGPT model:** GPT-6.1 Sol / High en ChatGPT Work, si está disponible. En Chat normal, GPT-5.6 Sol / High si aparece en el selector. Motivo: separar autorización de fuente, adquisición, identidad y comparabilidad entre revisiones preservando historia.
- **Recommended Codex model:** GPT-6.1 Sol / Medium para Engineering Lead y ejecución rutinaria; High para admisión, compatibilidad, integridad y depuración difícil.
- **Especialistas:** INTEGRATIONS/DATA, ARQ/DB-OWNER y BE/DISCOVERY: GPT-6.1 Sol / High en tareas justificadas. SEC/SRE revisa permisos y confianza. QA y REVIEWER: GPT-6.1 Sol / High, distintos entre sí y de todos los autores.
- **Escalation:** subir primero a High; GPT-6 Astra / High solo si persiste un bloqueo complejo reproducido y está disponible. No Max/Ultra por defecto.
- Verificar selectores antes de ejecutar. Registrar configuración solicitada, aceptada y realmente observable; no afirmar backend/reasoning verificados cuando no lo estén. La recomendación no cambia la configuración del cliente.
- Fuente oficial consultada el 2026-10-17: [https://learn.chatgpt.com/docs/models?surface=web](https://learn.chatgpt.com/docs/models?surface=web). Sol 6.1 pertenece a Work/Codex, no a Chat normal; disponibilidad sujeta a cliente/cuenta.

# P1c — Multi-Revision Metadata Capture

## 1. Rol y decisión de apertura

Actúa como Phase Lead de **P1c — Multi-Revision Metadata Capture** para Card Market Tracker.

El **00 — ORCHESTRATOR** abre esta fase el **2026-10-17, Europe/Madrid**, después del cierre formal **P4b: ACCEPTED / PHASE CLOSED**. Las fases anteriores conservan su aceptación. P1c es una ampliación autorizada y limitada de la ruta de metadatos de repositorio; no reabre P1b/P4b ni cualifica REST, mercado o retail.

Repositorio: [https://github.com/KastaTM/card-market-tracker](https://github.com/KastaTM/card-market-tracker)

Rama: `feat/p1c-multi-revision-metadata-capture`.

Objetivo: incorporar **una segunda captura real revisada**, tomada de otra revisión Git concreta de los mismos dos artefactos TCGdex, y comparar ambos snapshots bajo una política explícita y versionada. Dejar de equiparar identidad de adquisición con reglas de comparabilidad, sin debilitar las pruebas de cada captura.

Se autoriza investigación técnica acotada, adquisición indicada, implementación, rama, tests y PR. **No se autoriza merge.** Solo el Orchestrator acepta/cierra fases, amplía fuentes o cambia el alcance.

## 2. Baseline y registro del cierre anterior

| Objeto P4b aceptado         | Valor                                                                                                                                                            |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PR fusionado                | [https://github.com/KastaTM/card-market-tracker/pull/10](https://github.com/KastaTM/card-market-tracker/pull/10)                                                 |
| Baseline/main               | `112916382ce02486ca38eb14487220dbb24196e7`                                                                                                                       |
| Árbol                       | `c79edde3f13c5983d11505f5917f91559265b506`                                                                                                                       |
| Primer padre                | `430e2049c9ffdffb68508329df6556bfed62baa2`                                                                                                                       |
| Segundo padre/head revisado | `ab5e0fa7d4225c2ce137ce2261cd9686ef765a32`                                                                                                                       |
| CI push/main                | [https://github.com/KastaTM/card-market-tracker/actions/runs/39040138813](https://github.com/KastaTM/card-market-tracker/actions/runs/39040138813)               |
| Informe integración         | [https://github.com/KastaTM/card-market-tracker/pull/10#issuecomment-6235092935](https://github.com/KastaTM/card-market-tracker/pull/10#issuecomment-6235092935) |

1004 pruebas PASS, un skip y cobertura 96,13 % / 91,15 % son evidencia histórica P4b. P1c exige ejecución propia y revisión del candidato final.

Lee `context.md`, `AGENTS.md`, operating model, arquitectura, ADR-0003–0007, contratos v1/v2, fuentes P0.5b/P1b, runbooks, gates/testing, threat model y deuda. Verifica remote, refs, estado y worktrees antes de editar. Preserva ramas y cambios ajenos; no reset ni force-push. Si main avanzó, inspecciona y comunica el delta; no sustituir silenciosamente la base.

Archiva este contrato en `docs/phases/P1C_MULTI_REVISION_METADATA_CAPTURE_CONTRACT.md`. Registra en roadmap **P4b cerrada / P1c abierta**, atribuido al Orchestrator, con identidades/enlaces anteriores. El cierre se emitió en chat; no inventar comentario publicado. Conserva los snapshots históricos.

## 3. Fuente, revisiones y permiso concreto

Fuente única: `tcgdex/cards-database`. Revisiones autorizadas:

- **R0:** `4199850a6af49665db0080fa2bb9ef751750a406`, ya capturada/revisada en P1b. Reutilizar su paquete y tiempos originales, sin fabricar nueva adquisición.
- **R1:** `af57972e8f784c2507ab9e573c99bf02ae2e5e42`, fijada por el Orchestrator el 2026-10-17. La fase adquiere y contrasta sus cuatro paths; no seguir después `master/latest`.

| Path autorizado en R1                        | Git blob SHA-1 comprobado por el Orchestrator |
| -------------------------------------------- | --------------------------------------------- |
| `data/Sword & Shield/Darkness Ablaze.ts`     | `db48bc4a054b3b1c5bd2b6956257f20ba251c79c`    |
| `data/Sword & Shield/Darkness Ablaze/136.ts` | `6db89c69b56552fa4e09f26e0e90d14e97466411`    |
| `LICENSE`                                    | `c67ded0d5f0abc77b4fbdbfd37312f2a88de1b55`    |
| `README.md`                                  | `77bc8108c2cdb54c663e1fdf8c4502ac65f88734`    |

El Orchestrator consultó los cuatro artefactos R1 y comprobó su identidad y declaración de licencia. Los blobs coinciden con R0: **la proyección autorizada no ha cambiado**. Un commit diferente del repositorio no demuestra cambios en estos archivos ni en productos.

Base primaria de permiso: [LICENSE R1](https://github.com/tcgdex/cards-database/blob/af57972e8f784c2507ab9e573c99bf02ae2e5e42/LICENSE) y [README R1](https://github.com/tcgdex/cards-database/blob/af57972e8f784c2507ab9e573c99bf02ae2e5e42/README.md), que declara la base de datos bajo MIT. Conservar el aviso íntegro. No se concede licencia separada de marcas, imágenes o información de terceros.

Se autorizan consulta, extracción, retención local, fixture mínima con atribución, persistencia y comparación de la misma allowlist P1b:

- Set: literal `id`, `name.es`, `name.en`, fecha calendario `releaseDate` sin garantía regional.
- Carta: `name.es`, `name.en`, número textual desde filename, relación explícita al set aprobado e ID externo derivado `${set.id}-${stem}`.
- Metadatos de política, revisión, artefactos/digests, adquisición, captura y prueba de extracción.

Mantener namespace `tcgdex_repository`, variantes unknown y UUIDs curados. No inferir printings ni hacer matching por nombre. Cards pueden seguir como candidatos `unknown_variant`; sets requieren bindings explícitos y coherentes para aceptación.

Excluir imágenes, logos, efectos, descripciones, ataques, ilustrador, variantes, precios/stock, IDs de marketplaces, conteos, `updated`, idiomas ajenos y cualquier otro campo. Originales TS/README completos son temporales: no volcarlos a fixtures/logs/DB. Se retienen proyección mínima, aviso, locks y evidencia de extracción.

## 4. Alcance y resultado real esperado

Dentro:

1. Adquisición R1 acotada y trazable; extracción no ejecutable, hashes y contraste independiente de campos/licencia.
2. Paquete R1 versionado, revisado y admitido mediante un registro controlado de paquetes/políticas aprobados. Conservar R0 exactamente.
3. Persistencia/reconstrucción de ambas capturas en SQLite v2 sin migración ni reescritura de historia.
4. Perfil explícito que permita comparar exactamente R0/R1 separando alcance semántico de evidencia de adquisición.
5. Una ruta de comparación versionada **DISCOVERY_V3**, limitada a ese perfil, con pruebas sintéticas adversariales y ejecución real offline del par.

El resultado real exigido es comparación válida de las cuatro unidades, con historia R0 y current R1, **`no_discoveries`, cero eventos**. Sus proyecciones son iguales, sus revisiones y adquisiciones son diferentes. Esto acredita comparación entre capturas reales de revisiones del repositorio; **no acredita cambio de metadatos, alta de producto ni transición comercial real**.

Un evento positivo real no es objetivo ni requisito. Las pruebas positivas de novedad siguen siendo synthetic. No cambiar datos o tiempos para fabricar un descubrimiento.

Fuera: tercera revisión/paquete real, nuevos paths o corpus, REST/SDK/servidor upstream, fuente adicional, cliente HTTP de producción/scheduler, schema3/migración, event store, alertas, API/frontend, precios, retail, stock, preorders, promoción o nuevas identidades canónicas.

P2, P6a y Discovery retail continúan **BLOCKED**. REST TCGdex, eBay, GAME y Awin mantienen sus condiciones; Scrydex su rechazo para el uso EUR propuesto. No cuentas, compras o contactos externos.

## 5. Adquisición, tiempos y evidencia

Presupuesto P1c nuevo: **máximo 12 solicitudes de fuente** en total, secuenciales y con ledger compartido: hasta ocho lecturas de contenido R1 — cuatro para ingeniería y cuatro para QA si necesita readquisición — y hasta cuatro consultas de metadatos Git o intentos de recuperación. Cada retry/redirect que implique solicitud consume presupuesto. No superar ni transferir sobrantes de fases cerradas. Lecturas del Orchestrator previas son evidencia de apertura, no ejecución de ingeniería/QA.

Solo GitHub/raw GitHub para paths/revisiones autorizados y metadatos de esas identidades. No clones completos, enumeración de corpus, búsqueda de una revisión que produzca eventos, ejecución upstream o follow de URLs del payload. Caché puede reutilizarse con hash y procedencia comprobados; QA debe contrastar contenido, no simplemente confiar en el output del autor.

Verificar Git blob SHA-1 con header Git y SHA-256 de contenido, bytes UTF-8, tamaños y spans de campos. Los cuatro blobs R1 deben coincidir con la tabla. Una discrepancia exige error y reporte; no repinear ni ampliar permiso automáticamente.

Usar/revalidar el parser no ejecutable P1b con los mismos límites. No Node, `eval`, `exec`, imports dinámicos, SDK o compiler upstream. No convertir el parser diagnóstico histórico en autoridad de admisión.

Registrar inicios/finales reales de adquisición UTC y convención de captura R1 — por ejemplo, fin de la última lectura necesaria — sin usar la fecha del commit como captura. Importación/persistencia local sigue separada. R0 conserva su instante P1b. No reetiquetar lectura desde caché como nuevo fetch; declarar reutilización y tiempo original.

El paquete final R1 conserva esos tiempos inmutables. Reimportarlo mantiene captura/adquisición, aunque cambien token o instante de inserción. Los tiempos de ingeniería son una declaración del productor local respaldada por ledger, no un sello temporal autenticado del proveedor.

Todos los tests/CI/runtime de importación y comparación funcionan offline con paquetes mínimos revisados. La adquisición de ingeniería es separada; no se incorpora una conexión de datos a CI. Eliminar originales temporales después del contraste independiente y registrar la disposición sin publicar sus cuerpos.

## 6. Paquetes, admisión y persistencia

R0 permanece byte/semánticamente inalterado, con bundle SHA256 `3b43e1a78c117ef1ecb5cf200a4b2fc7e57af8fd29e3fcf29b06f4291ae58085` y projection SHA256 `53100248a987378fb3ca2273b7ec219747b876b515f57087faf6becdd0caa479`. R1 tendrá hash propio por revisión y tiempos aunque conserve la misma proyección.

Introducir `PINNED_REPOSITORY_BUNDLE_V2` o un contrato equivalente inequívocamente versionado para el paquete/registro multirrevisión. El registro de admisión es parte del código/configuración de confianza revisado en el candidato, no un registry arbitrario suministrado en la entrada. Autoriza exactamente estos dos paquetes finales y sus campos/revisiones; no una regla genérica «cualquier commit con MIT».

El registro vincula paquete completo, política, revisión, artefactos/digests, proyección, aviso y tiempos. QA y REVIEWER contrastan el lock R1 antes del freeze. Un hash recalculado por el llamador, un `observed` autodeclarado, una entrada de registro en el payload o un objeto Python forjado no conceden admisión. Una tercera captura/fecha/revisión necesita otra decisión.

Preservar el validador/contrato P1b v1 con su lock único. La nueva admisión se identifica por versión/entrypoint explícitos, nunca ampliando silenciosamente v1. La CLI puede extenderse con subcomando o dispatch versionado documentado, manteniendo todos los resultados anteriores.

Se autoriza una extensión de validación de envelopes para reconstruir R1 contra el registro revisado. SQLite conserva schema2, inventario/constraints y cinco tablas; no migración nueva. Scope/evidence_state siguen significando equivalencia de un paquete local revisado, no autenticación externa. Versionar cualquier cambio incompatible de envelope/scope; no inventar scope legacy ni modificar el contenido histórico.

Admisión, verify, query, replay, backup/restore y lectores deben reconstruir la variante autorizada adecuada. Evitar duplicar un verificador más permisivo. Valida de nuevo manifest/resolución/parent closure/snapshot antes de escribir o devolver evidencia. Rechazo previo a retención; transacción atómica, límites y errores existentes.

Replay conserva token/contexto/evidencia: igual es replay sin writes; distinto es conflicto sin sobrescritura. Fuente/revisión/adquisición/paquete/manifest/snapshot son pertinentes y no se eliminan del fingerprint para hacer comparables las capturas. Diferenciar explícitamente **equivalencia de replay** y **compatibilidad para comparar**.

Ni nuevos bindings ni UUIDs automáticos. El cambio de una referencia no modifica una entidad histórica. PERSISTENCE_V1 continúa synthetic-only. No sustituir provenance real por synthetic.

## 7. Perfil de comparabilidad y DISCOVERY_V3

P4b compara en v2 una semántica que incluye revisión, artefactos y tiempos de adquisición. Es insuficiente borrar esos campos globalmente: se perdería evidencia y se cambiaría un contrato aceptado. P1c añade una ruta **v3 explícita**, preservando v1/v2 y sus hashes/salidas.

Definir un perfil revisado, por ejemplo `tcgdex_swsh3_136_r0_r1_v1`, vinculado al registro anterior. Cada unidad comparada debe tener:

- Mismo repositorio/familia de evidencia, namespace, kind e idioma exactos.
- Mismo selector y conjunto exacto de paths autorizados para la unidad.
- Misma allowlist y transformación/semántica revisadas, con los dos paquetes como miembros explícitos.
- Completitud comprobada y ningún rechazo en la unidad seleccionada; todas las demás unidades/envelope se validan también.

Revisión Git, blobs, hashes de paquete, spans y tiempos son **evidencia por captura**. Pueden diferir solo dentro de la pareja expresamente revisada, sin convertirse en identidad canónica ni perderse del output/fingerprint. Esta regla no autoriza otras revisiones o bytes y no se aplica automáticamente a otras fuentes.

No equiparar R0/R1 por igualdad de nombres, IDs o digests autodeclarados. El lector/admisión verifica la pertenencia efectiva al perfil; el request solo solicita un perfil, no lo acredita. Paquetes fuera del registro, perfil desconocido, familia mezclada, selector/path/idioma distinto, partial/failed/legacy o política incompatible fallan.

Mantener una unidad explícita por lote, máximo32 históricos/33 lotes/33000 filas/1000 eventos y límites JSON existentes. El formato v3 puede derivar del request v2 añadiendo profile/version; documentarlo estrictamente. Darle entrypoint o dispatch explícito, sin fallback entre versiones. Una solicitud v2 no se convierte en v3 para evitar un mismatch.

Leer toda la ventana en una conexión ro/query_only y una transacción explícita, con reconstrucción íntegra, límites de bytes/léxicos antes de materializar, validación de todas las unidades y presupuesto existente 2s/default, 5s/max. Scope y filas no se ensamblan desde lecturas independientes. No escribir durante comparación, crear/migrar DB ni reparar journal.

Comparador puro e independiente del proveedor/SQLite. Reutilizar el núcleo de novedad relativa donde sea seguro, dejando la autorización/perfil en la frontera validada. Objetos/recibos Python no son autenticación contra código arbitrario dentro del proceso.

Semántica de eventos igual a P4b: unión histórica accepted/candidate, referencia completa, duplicados idénticos colapsados con índices originales, contradicciones rechazadas; set aceptado o candidato ausente de historia puede generar el evento correspondiente. No nuevas señales de metadata_changed, eliminación, lanzamiento, salud, precio o stock. No re-resolver historia contra un manifest actual.

Cronología por captura original: historia estrictamente anterior a current, empates historia-historia permitidos. Revision/commit date no sustituye captura. R0→R1 válido; R1→R0 falla; dos tokens del mismo paquete fallan por igualdad temporal. Los cuatro idiomas/kinds no son cuatro adquisiciones distintas.

Usar identidades `cmp3:` / `evt3:` con canonicalización documentada e inclusión del perfil y evidencia pertinente. Excluir ejecución/run ID/DB path/insertion time. El perfil normaliza compatibilidad, **no elimina fuente/revisión/digests/tiempos de la identidad de la comparación ni de la prueba de replay**. Orden de historia, replay y backup/restore preservan equivalencia; otro scope/perfil cambia identidad o falla. No tocar cmp1/evt1/cmp2/evt2 para inputs anteriores.

Discovery v1 sigue rechazando observed/mixto. Discovery v2 conserva la política aceptada; no se amplía su admisión a R1 silenciosamente. V3 admite el perfil nuevo; fixtures synthetic para su algoritmo/adversarios conservan familia y etiquetas explícitas, sin imitar una captura real aprobada.

## 8. Criterios de aceptación

| ID     | Condición verificable                                                                                                         |
| ------ | ----------------------------------------------------------------------------------------------------------------------------- |
| AC-M01 | Preflight, baseline y cierre P4b/apertura P1c atribuidos al Orchestrator y archivados                                         |
| AC-M02 | R1 adquirido dentro de presupuesto, con bytes/blobs/digests/tiempos y derechos por campo contrastados                         |
| AC-M03 | Proyección R1 coincide con R0; aviso MIT completo y ningún campo/cuerpo excluido retenido                                     |
| AC-M04 | Paquete R0 inalterado y R1 bloqueado por registro de confianza revisado; no admisión por autodeclaración/forgery              |
| AC-M05 | Nueva admisión versionada preserva PERSISTENCE_V1, bundle v1 e identidad curada sin promoción                                 |
| AC-M06 | SQLite schema2/historia/fingerprints previos intactos; nueva captura reconstruida coherentemente en todos los lectores/verify |
| AC-M07 | Replay/conflictos, reapertura, atomicidad y backup/restore preservan ambas capturas y sus tiempos                             |
| AC-M08 | Perfil permite exactamente R0/R1 con mismo scope/semántica y rechaza mezclas/terceros/cambios incompatibles                   |
| AC-M09 | V3 lee toda la ventana en un snapshot y valida todas las unidades; no mutación ni éxito parcial                               |
| AC-M10 | Cronología usa adquisición/captura originales; reimportación no redatación ni cambio temporal artificial                      |
| AC-M11 | Comparación real de las cuatro unidades R0→R1 devuelve no_discoveries y cero eventos con evidencia de ambos paquetes          |
| AC-M12 | Positivos sintéticos, contradicciones y límites prueban algoritmo e identidades cmp3/evt3; v1/v2 mantienen resultados/hashes  |
| AC-M13 | CLI, logging, errores/bounds/deadlines/provenance y no-network runtime son seguros y explícitos                               |
| AC-M14 | Wheel fuera del checkout, Compose, AMD64 y ARM64/QEMU ejecutan el recorrido entre procesos y recovery con UID10001            |
| AC-M15 | ADR, contratos, derechos, perfil, amenaza, runbooks, roadmap y deuda concuerdan con código/alcance                            |
| AC-M16 | Todos los gates/CI finales PASS, QA y REVIEWER independientes del autor y entre sí sobre el SHA/tree exactos                  |

El PASS de AC-M11 acredita una comparación real **sin cambios** de los artefactos seleccionados. No afirmar transición real de producto ni evento positivo real. Un requisito obligatorio sin evidencia es FAIL con razón, nunca PASS por inferencia.

## 9. Tests y quality gates

Source/admission: extracción determinista, spans UTF-8, licencia íntegra, exactitud SHA-1/SHA-256, registry/paquete/tiempos/revisión/proyección alterados, campos adicionales, objetos forjados, límites y rechazo antes de DB. No ejecutar código del proveedor. QA contrasta originales por método propio.

SQLite real: conservar datos v1/v2 ya existentes; ambos paquetes en DB nueva/migrada por la migración anterior; replay y conflictos por evidencia relevante; fallo atómico; corrupción incluso fuera de unidad seleccionada; parent closure/counts; locks/deadline; concurrencia/snapshot; backup/restore y revalidación. Lecturas no migran ni escriben.

Real end-to-end: R0 original y R1 adquirido, cuatro comparaciones válidas sin eventos, con manifest sin bindings y bindings de set curados; cards unknown_variant. Baselines, historia inversa y reimport igual tiempo, perfil incorrecto y R1 por ruta v2 no autorizada. Comparar dos revisiones no prueba que esos archivos cambiaron.

Synthetic: referencias nuevas/aliases/candidate→accepted, cambios de metadata sin novedad, reaparición, vacíos completos producer_declared, partial/failure/rechazos, scopes distintos, contradicciones/duplicados, v3 identities y forgeries. No modificar una fixture real y publicarla como captura observed.

Conservar los cinco harnesses actuales y añadir el nuevo a wheel/Compose/AMD64/ARM64: procesos separados de import/read/compare/replay/copy/reopen, fixtures read-only y runtime offline. Verificar import desde wheel fuera del checkout, UID10001, datos privados y salida restaurada equivalente. Preservar presupuestos runtime; los tests pueden usar timeout explícito existente sin cambiar defaults o quitar verificaciones, documentándolo.

Gates obligatorios: frozen install/lock; Ruff format/check; mypy strict; suite completa unit/contract/integration/regression/security/concurrency; cobertura de todo código propio ≥85 % líneas/≥80 % ramas; sdist/wheel fuera del source; dependency audit y secret scan; ARQ/DB/SEC/SRE/docs review; cuatro jobs Quality/Compose/AMD64/ARM64-QEMU y logs completos; QA/REVIEWER exact-candidate distintos de autores.

No reducir thresholds, eliminar pruebas ni introducir skips para conseguir verde. Excepciones de secret scan para nuevos digests públicos, si son necesarias, deben ser exactas por path/detector/valor, revisadas y probadas; nunca supresión general. QEMU no certifica Pi física.

## 10. Observabilidad, seguridad y límites

Logging estructurado distingue adquisición de ingeniería, admisión y comparación v3: run ID, duración, categorías fijas y conteos. No payloads/nombres/selectores/tokens/URLs/paths/SQL/excepciones crudas en logs. Output explícito solo evidencia contratada y acotada, sin manifest/bundle completo ni campos excluidos. Errores nunca equivalen a no_discoveries; counts null/events vacíos y códigos documentados preservando comandos anteriores.

Threat model: registry spoofing, paquetes de tercera revisión, elevación de producer timestamp a fuente autenticada, pérdida de provenance al normalizar comparabilidad, mezcla de snapshots, corrupción no seleccionada, identidad/hash incompatibles y falsa novedad por reimportación. Directorios locales confiables siguen siendo límite de seguridad.

TD-001–TD-005 permanecen abiertas. Esta fase mejora comparación local de dos paquetes revisados; no autentica productores independientes ni vacíos legacy, no añade cuotas/retención ni certifica cortes eléctricos. Registrar cualquier deuda nueva real con responsable/impacto/salida; no convertir funciones futuras excluidas en deuda artificial.

## 11. Organización y entregables

Codex Engineering Lead realiza preflight/plan/ownership e integra secuencialmente interfaces compartidas. INTEGRATIONS/DATA posee extracción/paquete/ledger; ARQ/DB-OWNER admisión/reconstrucción/compatibilidad; BE/DISCOVERY perfil y comparación. SEC/SRE revisa los riesgos. QA y REVIEWER son agentes independientes entre sí y de autores.

Paralelizar análisis o archivos disjuntos; Git, registro de confianza, lock y contratos compartidos se coordinan secuencialmente. No atribuir al merge reviews nuevas por igualdad de árboles. Registrar modelos heredados o solicitados sin inventar backend.

Entregables: contrato archivado/Engineering Brief/ownership; R1 mínimo+MIT y ledger de adquisición/campos/disposición; registro exacto de paquetes/perfil; nueva admisión y comparación v3; ADR siguiente número libre — previsiblemente ADR-0008 — y contratos versionados; tests/harness/CI; arquitectura/fuentes/runbooks/logging/threat/testing/gates/deuda/roadmap; PR abierto con report y ledger externo del SHA/tree/reviews/CI exactos.

El informe final traza AC-M01–M16, comandos/entornos, modelo realmente observable, Git/base/head/tree, todos los gates, arquitectura/DB/contratos, QA/REVIEWER, uso de fuente/presupuesto y limitaciones. Los hashes locales solo se atribuyen a quien los recalculó; no fingir lectura o ejecución independiente.

## 12. Handoff y aceptación

El primer mensaje del Phase Lead confirma objetivo, baseline, dos revisiones/paths, permiso/presupuesto, perfiles/modelos y exclusiones; después prepara Engineering Brief para Codex. Procede dentro de este alcance sin pedir otra aprobación operativa ni iniciar otra investigación general de fuentes.

Con todos los gates PASS: **READY_FOR_ORCHESTRATOR_REVIEW**. Si falta evidencia, informar FAIL/BLOCKED con acción concreta. No emitir ACCEPTED/PHASE CLOSED, mergear ni abrir otra fase.

El Orchestrator evaluará el candidato y podrá autorizar integración exacta. Después verificará merge real, padres base→head, árbol idéntico y CI nuevo `push/main` antes de cerrar P1c. Una tercera revisión, expansión de corpus o adquisición continua necesitará contrato posterior; no queda autorizada aquí.