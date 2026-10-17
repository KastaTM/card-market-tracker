MODEL PROFILE

- **Recommended ChatGPT model:** GPT-6.1 Sol / High en ChatGPT Work, si está disponible. Para Chat normal, GPT-5.6 Sol / High si aparece en el selector. Motivo: definir comparabilidad, temporalidad y niveles de evidencia sin confundir contexto persistido con autenticidad externa.
- **Recommended Codex model:** GPT-6.1 Sol / Medium para Engineering Lead e implementación rutinaria; High para lectura transaccional, integridad, compatibilidad y depuración compleja.
- **Especialistas:** ARQ/DB-OWNER y BE/DISCOVERY, GPT-6.1 Sol / High. SEC/SRE revisa fronteras y límites. QA y REVIEWER: GPT-6.1 Sol / High, agentes distintos entre sí y de los autores.
- **Escalation:** subir primero el razonamiento a High; GPT-6 Astra / High solo ante un bloqueo complejo reproducido que persista y si el cliente lo ofrece. No Max/Ultra por defecto.
- Comprobar disponibilidad en los selectores; registrar configuración solicitada, aceptada y realmente verificable. Una delegación aceptada no acredita el backend efectivo. No afirmar cambios de modelo no observados.
- Disponibilidad contrastada el 2026-10-16 en documentación oficial: [https://learn.chatgpt.com/docs/models?surface=web](https://learn.chatgpt.com/docs/models?surface=web). Sol 6.1 se ofrece en Work/Codex, no en Chat normal. Las recomendaciones no cambian permisos ni configuración del usuario.

# P4b — Scoped Capture Discovery

## 1. Rol, apertura y objetivo

Actúa como Phase Lead de **P4b — Scoped Capture Discovery**, para `KastaTM/card-market-tracker`.

El **00 — ORCHESTRATOR** abre esta fase el **2026-10-16, Europe/Madrid**, después de declarar **P1b: ACCEPTED / PHASE CLOSED**. P0, P0.5, P1a, P3a, P4a y P0.5b conservan su cierre.

Objetivo: permitir Discovery offline sobre **unidades explícitas de capturas con scope persistido en SQLite v2**, conservando los niveles de evidencia y las fronteras de autorización. El resultado describe referencias observadas por primera vez en una ventana seleccionada; no descubre automáticamente lanzamientos, productos nuevos en el mercado ni cambios de stock.

La fase incorpora una ruta nueva, versionada y de solo lectura que enlaza captura P1b y comparación. P4a/`DISCOVERY_V1` conserva su comportamiento synthetic-only. No se sustituye ni se debilita su guard.

Repositorio: [https://github.com/KastaTM/card-market-tracker](https://github.com/KastaTM/card-market-tracker)

Rama autorizada: `feat/p4b-scoped-capture-discovery`.

Se autoriza implementación, rama, pruebas y PR. **El merge requiere autorización posterior sobre el candidato exacto.** Solo el Orchestrator acepta/cierra fases, cambia alcance o abre la siguiente.

## 2. Baseline y evidencia histórica

| Objeto P1b aceptado         | Identidad                                                                                                                                                      |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PR fusionado                | [https://github.com/KastaTM/card-market-tracker/pull/9](https://github.com/KastaTM/card-market-tracker/pull/9)                                                 |
| Baseline/main               | `430e2049c9ffdffb68508329df6556bfed62baa2`                                                                                                                     |
| Árbol                       | `c3988a86cedf525cce364bd9cc4709689c510053`                                                                                                                     |
| Primer padre                | `acca10e406dac8809edc289c3077a6ec8785a622`                                                                                                                     |
| Segundo padre/head revisado | `252c394141948e3ab77a54bcf628e4290ba69652`                                                                                                                     |
| CI push/main                | [https://github.com/KastaTM/card-market-tracker/actions/runs/38877640587](https://github.com/KastaTM/card-market-tracker/actions/runs/38877640587)             |
| Informe de integración      | [https://github.com/KastaTM/card-market-tracker/pull/9#issuecomment-6212185019](https://github.com/KastaTM/card-market-tracker/pull/9#issuecomment-6212185019) |

777 pruebas PASS, un skip y 96,85 % líneas/92,62 % ramas son evidencia histórica P1b. P4b necesita sus propios resultados y revisiones.

Lee `context.md`, `AGENTS.md`, operating model, arquitectura, ADR-0003–0006, contratos CATALOG/INGESTION/MANIFEST/PERSISTENCE/STORAGE/DISCOVERY, bundle/capture P1b, testing/gates, threat model y deuda antes de diseñar. Verifica remote, refs, worktrees y cambios locales. Preserva trabajo ajeno; no reset, force-push ni cambio silencioso del baseline. Si main avanzó, inspecciona el delta y eleva cualquier incompatibilidad.

Archiva este contrato en `docs/phases/P4B_SCOPED_CAPTURE_DISCOVERY_CONTRACT.md`. Registra en roadmap el cierre P1b y apertura P4b, atribuidos al Orchestrator, con sus enlaces. La declaración de cierre se emitió en el chat; no inventar un comentario de cierre publicado. Conserva los informes previos como snapshots históricos.

## 3. Límite real que define la fase

El paquete aprobado P1b contiene dos artefactos, cuatro proyecciones ES/EN y **un único instante de adquisición/captura**. Su lock incluye ese tiempo. Dos importaciones con tokens diferentes no forman dos observaciones temporalmente distintas del proveedor.

Por tanto, la demostración real obligatoria de P4b consiste en seleccionar cada unidad del paquete, validar su evidencia y producir un baseline sin eventos. Comparar reimportaciones de esa misma captura como historia debe fallar por igualdad temporal. No alterar el reloj ni el paquete para fabricar una transición real.

Las comparaciones positivas, ausencia relativa de referencias y vacíos se demuestran mediante capturas **synthetic** persistidas con `persist_capture`, con origen y límites explícitos. Esto acredita el algoritmo y su integración con storage; **no acredita haber observado un cambio real entre dos capturas del proveedor**. El informe debe mantener esa distinción.

La fase puede satisfacer todos sus AC sin un evento positivo real, porque no se autoriza adquirir una segunda revisión ni construir otro paquete real. No convertir esta limitación en una investigación de fuentes o una ampliación unilateral.

## 4. Alcance autorizado y exclusiones

Dentro:

- Contrato `DISCOVERY_V2` y comando separado, por ejemplo `cmt discover-scoped --db PATH --request REQUEST_JSON`.
- Selección inequívoca de una unidad por captura, usando contexto y selector persistidos.
- Lectura de todas las capturas seleccionadas y sus registros/evidencias en un único snapshot SQLite.
- Validación de origen, scope, completitud, cronología, snapshots y comparabilidad.
- Comparador puro, determinista e independiente del proveedor/SQLite, con evidencia versionada y sin escrituras.
- Fixtures sintéticas, casos reales mínimos ya aprobados, harness entre procesos, regresiones y documentación.

Fuera:

- Nuevos paquetes reales, artefactos, revisiones o políticas de admisión; nuevo acceso a fuentes: **cero solicitudes**.
- REST TCGdex, nuevos proveedores, corpus completo, precios, retail, stock, sealed observado, preorders o lanzamientos.
- Cambio de schema SQLite, nueva migración, modificación de datos históricos, manifest, fingerprints almacenados o captura P1b.
- Promoción/revisión interactiva de candidatos, allocation de CMT IDs, event store, deduplicación durable, alertas, scheduler, API o frontend.
- Autenticación de productores independientes, resolución global de TD-005, certificación Pi o cortes eléctricos físicos.

La única admisión `observed` sigue siendo el paquete P1b aprobado, namespace `tcgdex_repository`, revisión `4199850a6af49665db0080fa2bb9ef751750a406`, bundle SHA256 `3b43e1a78c117ef1ecb5cf200a4b2fc7e57af8fd29e3fcf29b06f4291ae58085`. Retener su aviso MIT. Un string `observed` o digest autodeclarado no concede autoridad.

P2, P6a y Discovery retail siguen **BLOCKED**. REST TCGdex/eBay/GAME/Awin conservan sus condiciones y Scrydex su rechazo para el uso EUR propuesto. La apertura autoriza consumir evidencia ya admitida en la ruta nueva; no concede otra licencia de fuente.

## 5. Request v2 y selección de unidades

Fijar mediante contrato y tests una forma estricta equivalente a:

```
{
  "version": 2,
  "context": {"namespace": "tcgdex_repository", "kind": "set", "language": "es"},
  "current": {"batch_id": "bd9cc4b8-eace-4567-8364-93cc4eccddc5", "selector": "swsh3"},
  "history": []
}
```

`history` contiene entradas de la misma forma que `current`, como máximo 32, con UUIDv4 únicos, distintos de current. Una unidad por batch en una solicitud. Canonicalizar el orden de historia sin ocultar duplicados. Versión integer 2, nunca bool; unknown keys, referencias adicionales, índices arbitrarios, SQL/URLs/paths de entrada son inválidos. Los paths internos del scope solo se leen como metadatos; nunca se abren.

Contexto: namespace con gramática/bound P1a, kind set/card/sealed, idioma es/en/null exacto. Selector no vacío, máximo 256 caracteres. La coincidencia de namespace/kind/language/selector identifica **exactamente una unidad persistida**. Cero coincidencias o ambigüedad son errores, nunca vacío ni selección aproximada.

`record_indexes` proviene exclusivamente de esa unidad validada. Leer/validar el lote completo antes de extraerla; conservar índices originales, sin renumerar filas para simular un lote independiente. Unidades ajenas validadas no aportan referencias al resultado; esta exclusión es una selección explícita de scope, no un filtrado de rechazos o procedencias.

Todos los índices deben existir y la partición completa de unidades/filas/conteos debe ser válida. Un rechazo dentro de la unidad seleccionada produce `incomplete_evidence`, incluso en baseline. Unidades ajenas no se comparan, pero su presencia no exime de validar la integridad del envelope y snapshot completo.

Límites: request 1 MiB, profundidad 16, 20.000 nodos, strings/keys 1.024; sin claves duplicadas, números no finitos ni Unicode inválido. Hasta 33 lotes, 33.000 registros leídos/validados y 1.000 eventos. Una vez superado un límite, error global sin truncamiento presentado como éxito.

## 6. Evidencia admitida y comparabilidad

La ruta v2 requiere schema2 y capture envelope válido. Schema1 o `legacy_unverified` no disponen del scope requerido: error explícito, sin inferirlo del request/manifest/filas ni migrar. Los usuarios históricos mantienen su ruta v1 con sus limitaciones.

Dos familias admitidas, sin mezclarlas dentro de una ventana:

1. `verified_local_pinned_bundle`: solo admisión P1b reconstruida contra el paquete aprobado. El scope prueba validación del paquete local revisado, no autenticidad física ni cobertura del proveedor.
2. `producer_declared` synthetic: solo capturas sintéticas con scope persistido y revalidado. Sigue siendo declaración del productor local, incluido un vacío completo; nunca etiquetarla como autenticada independientemente.

Validar la coherencia de mode/evidence_state/provenance en todos los registros. Rechazar ventanas con datos observed y synthetic mezclados; no normalizarlos a una procedencia común. No aceptar `documented` por analogía.

La comparabilidad exige mismo contexto, selector y conjunto exacto de paths seleccionados, además de familia de evidencia y semántica/método/política compatibles. No inferir que dos listas distintas de artefactos cubren el mismo universo. Ordenar listas no cambia su conjunto; cambiar un path o selector es un cambio de scope, no una referencia recién descubierta.

En esta fase no existen políticas reales distintas compatibles: cualquier paquete observado diferente del aprobado se rechaza. Para synthetic, definir la correspondencia de sus campos genéricos sin fabricar un repositorio/método real.

Requerir captura completa para la selección y outcome global compatible: parcial/fallo no se convierte en completo porque algunas filas hayan podido leerse. Para el bundle, `complete_nonempty` es respecto a los paths seleccionados. En synthetic, `complete` requiere selected == completed. Rechazos no son vacío; faltas de artefacto/idioma no son ausencia. Un vacío synthetic válido conserva scope/evidence_state persistidos.

Cada historia debe ser estrictamente anterior al current por `captured_at` original normalizado. Empates históricos entre sí son válidos. Igualdad con current o historia futura son errores. No ordenar/fechar por insertion time, run ID, release_date, ejecución o token. Sin historia, baseline tras validar todo current; no usar implicit global history.

## 7. Algoritmo y semántica de salida

Conservar la semántica relativa de P4a aplicada a la unidad explícita:

- Clave de referencia completa: namespace/kind/external_id/language/variant.
- Unión histórica de referencias aceptadas y candidatas de todas las unidades seleccionadas. Una referencia candidata después aceptada ya estaba vista.
- Referencia actual ausente de la historia: set aceptado → `SET_REFERENCE_FIRST_OBSERVED`; candidato → `CANDIDATE_REFERENCE_FIRST_OBSERVED`; card/sealed aceptados no generan esos eventos.
- Nombres/fechas o cambio de binding no crean referencia nueva. Otro external ID con el mismo CMT ID sí es otra referencia, sin afirmar otro producto real.
- Duplicados idénticos se colapsan preservando sus índices; contradicciones de observación/status/target para una referencia dentro de una unidad invalidan la operación. Cambios legítimos entre capturas no son contradicción intralote.
- Baseline sin eventos; `no_discoveries` o `discoveries` solo después de una comparación válida. No emitir eliminaciones, lanzamiento, stock, global novelty ni source-health.

Snapshots congelados: nunca resolver contra un manifest actual ni promover candidatos. UUIDs curados, null exacto, números textuales y variant unknown se conservan. El comparador no conoce formatos TCGdex ni hace I/O.

Salida JSON v2 debe incluir resultado, comparison_id, contexto, selección actual/histórica, scope/evidence_state de cada unidad, captura original, conteos y eventos. Diferenciar conteos de lotes/registros validados de los registros/referencias de las unidades comparadas, con nombres inequívocos y tests. No presentar cuatro unidades del bundle como cuatro adquisiciones independientes.

Cada evento conserva referencia, tipo, status/category/CMT ID congelados, token current, captura, índices originales y evidencia de la ventana/scope seleccionado. `first_observed_in_window_at` solo significa primera evidencia en la ventana escogida. No crear `first_seen` global.

Definir hashes nuevos `cmp2:` y `evt2:` con canonicalización documentada. Incluir scope y familia de evidencia para no colisionar con v1 u otra unidad. Comparison identity incorpora request canónico y evidencia/contenido relevantes; event identity identifica la aparición en la captura/unidad actual, estable al reordenar la historia. Excluir reloj de ejecución, run ID, duración, DB path y primer tiempo de persistencia de la identidad semántica. Alteraciones relevantes cambian identidad o se rechazan; backup/restore, replay y distinto orden de historia preservan salida equivalente.

No modificar `cmp1:`/`evt1:` ni salidas v1. Hashes son identidad/equivalencia, nunca autenticación ni garantía exactly-once.

## 8. Lectura consistente, fronteras y compatibilidad

Leer schema, metadatos, capture envelopes, todas las filas/relaciones necesarias y unidades de la ventana en **una transacción de lectura explícita sobre una conexión**. No ensamblar una comparación mediante llamadas independientes a `query_capture` con snapshots diferentes.

Reutilizar validaciones de P1b: byte-length SQL antes de materializar envelopes, límites léxicos antes de JSON completo, reconstrucción de paquete/scope/resolver retenido y comparación de snapshots/contadores/parent closure. Evitar validadores más permisivos en la nueva ruta. Se pueden extraer helpers comunes manteniendo ownership y regresiones.

Mantener modo ro/query_only, presupuesto 2 s por defecto/máximo 5 s y progreso/lock handling. No crear DB, reparar, migrar, escribir cache ni borrar journal. Ausencia, corrupción, lock y deadline producen errores categorizados, no ausencia de descubrimientos. Datos corruptos en una unidad no deben quedar ocultos al seleccionar otra unidad del mismo envelope.

Constructores/dataclasses aportados por Python no conceden evidencia almacenada/verificada. Los entrypoints públicos revalidan request y snapshots/alcance; la aplicación solo atribuye procedencia DB tras la lectura validada. No introducir un bypass de la política observed para facilitar tests del comparador. Fixtures alteradas para probar rechazos o cambios son synthetic, con provenance coherente.

Preservar PERSISTENCE_V1 y la admisión P1b intactas, schema v1/v2, migración/replay/backup existentes y límites de entrada. Nueva funcionalidad de lectura no puede autorizar escritura de datos reales. `cmt discover` v1 sigue rechazando observed/mixto. El nuevo comando acepta solo request v2; no hacer fallback silencioso entre versiones.

## 9. Criterios de aceptación

| ID     | Condición verificable                                                                                                                     |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| AC-S01 | Preflight, contrato, baseline, cierre P1b y apertura P4b registrados con atribución correcta                                              |
| AC-S02 | Request v2 estricto, acotado, selección exacta de una unidad y tratamiento determinista de historia                                       |
| AC-S03 | Captura/scope/filas de toda la ventana se leen y validan en un único snapshot transaccional                                               |
| AC-S04 | Observed limitado al paquete P1b, synthetic explícito y ventanas mixtas/legacy/no soportadas rechazadas                                   |
| AC-S05 | Comparabilidad exige contexto/selector/paths/familia compatibles, sin filtrado que invente completitud                                    |
| AC-S06 | Completo/vacío/partial/fallo/rechazo/missing se distinguen con niveles de evidencia honestos                                              |
| AC-S07 | Cronología usa captura original; reimportaciones del único paquete real no se convierten en historia temporal válida                      |
| AC-S08 | Novedad relativa, unión de candidatos/aceptados, duplicados y contradicciones funcionan sin crear identidad ni promoción                  |
| AC-S09 | cmp2/evt2 y salida son deterministas, sensibles a scope y estables con replay/backup/restore/orden de historia                            |
| AC-S10 | Las cuatro unidades reales producen baseline correcto sin eventos; pruebas temporales positivas son synthetic y se identifican como tales |
| AC-S11 | Operación de solo lectura, errores/bounds/deadline/corrupción y concurrencia no producen éxito parcial ni mutaciones                      |
| AC-S12 | Regresiones P0/P1a/P3a/P4a/P1b pasan con contratos/guards e identidades v1 preservados                                                    |
| AC-S13 | Wheel fuera del checkout, Compose, AMD64 y ARM64/QEMU prueban el recorrido nuevo offline entre procesos con UID 10001                     |
| AC-S14 | ADR, DISCOVERY_V2, extensión de lectura, logging, runbook, amenaza, deuda y permisos coinciden con implementación                         |
| AC-S15 | Todos los gates y cuatro jobs del candidato final PASS; QA y REVIEWER independientes sobre SHA/árbol exactos                              |

No existe AC que exija acreditar un cambio real del proveedor. El informe debe declarar expresamente que tal cambio no se ha demostrado, sin esconderlo tras un PASS del algoritmo synthetic. Tampoco declarar FAIL un AC distinto por exigirle retrospectivamente otra fuente no autorizada.

## 10. Pruebas y quality gates

Unit/contract: tipos/versiones/duplicate keys/Unicode/bounds; selección inexistente/ambigua, selector/path/language/variant exactos; conteos/particiones/índices; families/provenance falsificadas; objetos Python forjados; baseline válido y negativo; history duplicate/actual/futuro/empates; scope alterado y vacíos declarados.

Comparación synthetic persistida: nuevo set aceptado, candidato sin CMT ID, alias al mismo target, candidato después aceptado, metadata edit sin novedad, reaparecer tras vacío dentro de ventana, vacío completo, partial/fallo, rechazos dentro de unidad, contradicciones/duplicados, unidades ajenas y varios scopes en un lote. Probar que un scope distinto no fabrica una comparación válida.

Real mínimo: importar el bundle autorizado sin editarlo, comprobar las cuatro unidades (con manifest sin binding y bindings curados de set coherentes), baseline sin eventos e índices originales. Segundo token del mismo bundle conserva captura y su comparación como historia falla por cronología. El comando v1 continúa rechazándolo. No adquirir fuentes para estas pruebas.

SQLite/concurrencia: envelope o filas/conteos corruptos, corrupción en otra unidad del envelope, límites previos a materialización, versions unsupported, schema1/legacy; snapshot estable frente a escritura intercalada y detección en siguiente lectura. Probar no mutación lógica/de schema/contenido, replay y backup/restore con igualdad semántica. No usar el reloj local como sustituto de la captura.

Crear harness P4b reutilizable por wheel/Compose/AMD64/ARM64: preparar capturas, cerrar/reabrir en procesos distintos, comparar y verificar invariantes. Conservar todos los harnesses previos. Contenedores UID 10001, fixtures read-only y networking deshabilitado; ejecución instalada fuera del checkout con import verificado.

Gates obligatorios: frozen install/lock consistente; Ruff format/check; mypy strict; suite completa unit/contract/integration/regression/negative/concurrency; cobertura código propio ≥85 % líneas/≥80 % ramas; sdist/wheel/install fuera del source; dependency audit y secret scan; revisiones ARQ/DB/SEC/SRE/documentación; cuatro jobs Quality/Compose/AMD64/ARM64-QEMU con logs completos; QA y REVIEWER finales independientes.

No eliminar regresiones, reducir thresholds o añadir skips para conseguir verde. Gate obligatorio no ejecutado = FAIL con razón. QEMU no certifica Pi física ni resistencia a cortes eléctricos.

## 11. Observabilidad, seguridad y deuda

Logs estructurados con run ID, operación v2 distinguible, duración, resultado, categorías fijas y conteos acotados. Fallo: counts null y events vacíos, sin éxito aparente. Definir exit 0 para baseline/no_discoveries/discoveries, 2 para request/scope/cronología/evidencia incompleta o no soportada, 1 para almacenamiento/IO/schema/corrupción/lock/timeout; conservar códigos históricos.

No registrar nombres, referencias, selector, paths, tokens de lotes, SQL, payloads o excepciones crudas. La salida explícita muestra solo evidencia contratada, sin bundle/manifest completo ni campos excluidos de la fuente. No añadir cliente HTTP, servicios, secrets o dependencias runtime sin necesidad y aprobación de alcance.

Threat model: scope spoofing, elevación de producer_declared a verificado, mezcla de instantes, falsa completitud por filtrado, redatación de reimportación, colisiones de identidad y validación divergente. La integridad local no prueba verdad externa. Conservar directorios locales confiables y límites operativos existentes.

TD-001–TD-005 siguen abiertas. P4b no autentica capturas legacy/vacías de productores independientes ni cierra TD-005 por consumir un scope persistido. No abrir deuda artificial por funciones futuras excluidas.

## 12. Organización, entregables y handoff

Codex Engineering Lead coordina Git, plan, interfaces y ownership. ARQ/DB-OWNER posee lectura/snapshot/contratos; BE/DISCOVERY posee request/comparador/CLI según ownership acordado; SEC/SRE realiza revisión justificada. QA y REVIEWER son agentes distintos de autores y entre sí. Solo paralelizar análisis o archivos disjuntos; Git/lock/shared contracts se coordinan secuencialmente.

Entregables:

1. Contrato archivado, Engineering Brief y ownership/model profile used.
2. Nueva ruta v2 de selección/lectura/comparación/CLI, sin schema nuevo ni escrituras.
3. ADR significativo, siguiente número libre — previsiblemente ADR-0007 — y `DISCOVERY_V2`, documentando compatibilidad v1 y extensión read-only de storage/capture.
4. Tests, fixtures synthetic con ledger, harness y cuatro jobs ampliados preservando anteriores.
5. Arquitectura, runbook, logging, threat model, testing/gates, roadmap y deuda actualizados con alcance preciso.
6. PR abierto, QA y REVIEWER del SHA/tree final, Phase Completion Report y ledger externo con AC-S01–S15, Git/CI/logs/reviews, resultados y limitación temporal real. Evitar commits circulares para insertar el SHA de su propio informe.

El primer mensaje del Phase Lead confirma baseline, alcance, evidencia permitida, exclusiones, modelos y plan; luego prepara el Engineering Brief para Codex. No pide otra aprobación para el trabajo definido aquí ni transforma P4b en otra fase de source qualification.

Con todos los gates PASS y sin bloqueos: **READY_FOR_ORCHESTRATOR_REVIEW**. Si falta evidencia, informar FAIL/BLOCKED con acciones concretas. No emitir ACCEPTED/PHASE CLOSED ni mergear ni abrir fases.

El Orchestrator revisará el candidato y, si procede, autorizará su integración exacta. Después se exigirán merge real, padres base→head, árbol idéntico y CI nuevo `push/main` antes del cierre. La futura adquisición de una segunda captura real compatible requerirá otra autorización; no está abierta en este contrato.