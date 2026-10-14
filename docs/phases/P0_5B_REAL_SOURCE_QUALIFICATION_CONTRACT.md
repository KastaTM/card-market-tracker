MODEL PROFILE
- ChatGPT Phase Lead: GPT-6.1 Sol / High en Work si está disponible; GPT-5.6 Sol / High para Chat normal si está disponible. Motivo: resolver dependencias de acceso, campos, derechos, semántica y decisiones entre fases con evidencia primaria.
- Codex Engineering Lead: GPT-6.1 Sol / Medium para inspección, documentación, probes pequeños y evidencia; High para fronteras de datos, interpretación de restricciones y revisión de integración.
- INTEGRATIONS/DATA, SEC y ARQ/DB-OWNER: GPT-6.1 Sol / High para preguntas concretas. PO puede combinarse con el Lead.
- QA y REVIEWER: GPT-6.1 Sol / High, dos agentes independientes de autores y entre sí. Registrar configuración solicitada/aceptada y ejecución realmente verificable.
- Escalar primero a High; GPT-6 Astra / High solo si persiste un bloqueo complejo tras reproducción/análisis con Sol y el cliente lo permite. No Max/Ultra por defecto.
- Comprobar disponibilidad en el selector. La recomendación no cambia el cliente ni acredita backend/reasoning introspectable. Si falta el modelo, comunicar opciones disponibles sin inventar disponibilidad.
- Fuente oficial consultada el 2026-10-13: [https://learn.chatgpt.com/docs/models?surface=web](https://learn.chatgpt.com/docs/models?surface=web). GPT-6.1 Sol pertenece a Work/Codex; no ofrecerlo como modelo de Chat normal.
# P0.5b — Real Source Qualification: contrato y prompt de apertura
## Rol y decisión de apertura
Actúa como Phase Lead de **P0.5b — Real Source Qualification** para Card Market Tracker.
El Orchestrator abre esta fase mediante este contrato el **2026-10-13, Europe/Madrid**. Su objetivo es convertir las dependencias de fuentes en decisiones concretas y revisables. No reabre ni invalida P0.5: es una investigación complementaria sobre los usos reales que ahora necesitan P1a/P3a/P4a.
Repositorio: [https://github.com/KastaTM/card-market-tracker](https://github.com/KastaTM/card-market-tracker)\
Checkout local previsto: C:\Projects\card-market-tracker\
Rama autorizada: docs/p05b-real-source-qualification
Coordina la investigación, traduce el contrato a un Engineering Brief para Codex y entrega un candidato con evidencia. Solo el Orchestrator acepta/cierra fases, modifica dependencias o autoriza integración.
## Baseline y decisiones vigentes
P0, P0.5, P1a, P3a y P4a están **ACCEPTED / PHASE CLOSED**. P4a se cerró el 2026-10-13 tras comprobar el merge real y CI push/main.
| Objeto P4a aceptado      | Valor                                                                                                                                                          |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PR fusionado             | [https://github.com/KastaTM/card-market-tracker/pull/7](https://github.com/KastaTM/card-market-tracker/pull/7)                                                         |
| Baseline/main comprobado | 6385c952a9f2024c8b7bdb33d37fa21017029bd5                                                                                                                       |
| Árbol                    | 8fa2abeb9f4e8991bab1b2895fc397f64bb39a19                                                                                                                       |
| Primer padre             | 734641a7ef920688677cdea6bc82f908a2856927                                                                                                                       |
| Segundo padre            | c5ed228af831a2a6ed8a12c7072777d3908296a5                                                                                                                       |
| CI push/main exacto      | [https://github.com/KastaTM/card-market-tracker/actions/runs/38471731980](https://github.com/KastaTM/card-market-tracker/actions/runs/38471731980)                     |
| Ledger integración       | [https://github.com/KastaTM/card-market-tracker/pull/7#issuecomment-6155836622](https://github.com/KastaTM/card-market-tracker/pull/7#issuecomment-6155836622) |
Los cuatro jobs pasaron; 611 pruebas, un skip y cobertura 97,79% líneas/94,43% ramas son evidencia histórica P4a. No presentarlos como resultados nuevos sin ejecución propia.
Verifica Git/remote/refs/cambios antes de editar y preserva ramas/worktrees ajenos. Si main avanzó, inspecciona el delta y eleva un baseline distinto que afecte dependencias; no reemplazarlo silenciosamente.
Archiva este contrato y registra dentro de esta rama el cierre P4a atribuido al Orchestrator y la apertura P0.5b en roadmap y una nota histórica del informe P4a. No convertir su snapshot prepublicación en supuesta ejecución posterior ni inventar un comentario de cierre.
P2, P6a y Discovery retail continúan BLOCKED. TCGdex sigue provisional. TD-001–TD-005 permanecen abiertas. La DB y el runtime actuales admiten únicamente capturas synthetic para persistencia/Discovery: **no etiquetar datos reales como synthetic ni eludir ese control**.
Decisión de secuencia: realizar ahora cualificación de fuentes, antes de abrir otro componente consumidor de datos reales. Ninguna fuente o fase queda desbloqueada por esta apertura.
## Objetivo y criterio de éxito
Determinar si existe al menos una ruta **accesible, documentada y compatible con un uso mínimo concreto** de CMT:
1. Metadatos Pokémon ES/EN de sets/cartas que puedan retenerse y compararse.
2. Referencia de mercado EUR con acceso y derechos de histórico adecuados.
3. Feed/retailer compatible con ofertas, productos sealed, precio/stock o Discovery retail.
Prioridad: **metadatos TCGdex**, después alternativas limitadas de mercado/retail.
Una conclusión negativa o condicionada es válida: la fase puede estar técnicamente completa con todas las rutas bloqueadas si investigó y contrastó lo requerido. No fabricar una fuente viable para satisfacer un AC ni confundir cierre de investigación con permiso de integración/uso.
## Dentro de alcance
- Releer P0.5, fichas/matriz/selección existentes y decisiones posteriores. Reutilizar evidencia fechada como histórica.
- Cualificar TCGdex a nivel de campos, artefactos y usos mínimos; contrastar documentación API, repositorio oficial y licencia aplicable.
- Evaluar como máximo **dos rutas de mercado EUR y dos rutas retail/feed**, con foco en alternativas materialmente distintas. Pueden ser proveedores existentes o nuevos.
- Contrastar al menos una ruta de mercado y una retail/feed. Una segunda ruta de cada grupo se justifica por su posibilidad de resolver una carencia distinta, no por llenar la matriz.
- Como máximo **tres proveedores nuevos**. No volver a investigar íntegramente los ocho anteriores ni repetir una ruta rechazada sin evidencia nueva que pueda cambiar su resultado.
- Investigar APIs públicas, dumps oficiales/licenciados y feeds autorizados como posibles rutas. Distinguir acceso documental, acceso disponible y acceso operativo probado.
- Probes puntuales condicionales y acotados, únicamente cuando el uso esté justificado por las condiciones públicas y pueda realizarse dentro de la autorización.
- Documentar cambios mínimos que una futura fase necesitaría para consumir datos reales, contexto de captura y procedencia sin romper identidad ni historia.
- Matriz final, políticas por campo, evidencia reproducible, riesgos/pendientes y recomendación de siguiente fase.
## Fuera de alcance
Collector operativo, scheduler, scraping recurrente, feed masivo, importer de producción, persistencia real en la DB CMT, cambios de esquema/migraciones, relajación synthetic-only, modificación del comparador o resolución de TD-005 en runtime.
No precios/alertas/UI nuevos, compras, planes de pago, trials con obligaciones, altas/cuentas, aceptación de nuevos términos, contactos externos, uso de credenciales ajenas o sesiones privadas. No eludir acceso, bloqueos, rate limits, robots, CAPTCHA o restricciones de uso.
La lectura documental de páginas públicas no equivale a autorización de monitorización ni a probe de API. No convertir una licencia de código en licencia de datos, imágenes, marcas o precios derivados.
## Preguntas obligatorias y política por campo
Para cada ruta seleccionada, entregar una ficha fechada con URLs primarias, sección/artículo/commit/tag de licencia cuando exista, fecha de consulta y evidencia exacta suficiente. Las fuentes secundarias sirven para localizar, no para acreditar condiciones.
Separar siempre **documentado / observado / inferido / desconocido**.
### Acceso y operación
API/dump/feed/archivo; autenticación/approval/membership; restricciones por país/cuenta; coste actual verificado; cuotas, frecuencia permitida, paginación/orden/final de lista; respuestas parciales, cache, cambios de contenido y retirada del servicio. Acceso público sin clave no prueba derecho a conservar o redistribuir.
No reutilizar precios, condiciones o fechas del informe 2026-10-07 como vigentes sin comprobarlas. Si una página no es accesible, documentar el intento y la incertidumbre; un snippet no sustituye la lectura de la fuente.
### Derechos y usos concretos
Definir usos separados: evaluación transitoria; retención de metadatos; histórico; comparación/derivación; display privado; publicación de fixtures/docs; redistribución; uso comercial futuro. No exigir todos los usos para recomendar uno mínimo viable, ni inferirlos por silencio.
Tabla por campo/grupo:
- Campo y origen preciso, incluyendo proveedor upstream cuando exista.
- Uso mínimo solicitado y permiso/restricción documentado.
- Retención/duración/actualización/borrado/atribución/avisos requeridos.
- Clasificación de evidencia y incertidumbre.
- Puede consultarse, guardarse como muestra mínima, almacenarse en CMT futuro o publicarse: sí/no/condicional, cada acción por separado.
Priorizar para catálogo: referencia externa, kind, nombre, idioma, relación set/card, número textual, release date, card count, variantes y timestamps disponibles. **Excluir imágenes, logos, marcas gráficas, precios y extras de terceros** salvo evaluación separada con evidencia específica. MIT de un repositorio no acredita automáticamente todo el JSON servido por una API.
Una fuente primaria accesible y aplicable puede acreditar un uso sin contactar al proveedor. Si el alcance es ambiguo, no afirmar permiso: registrar qué aclaración falta y continuar investigación independiente.
### Semántica y cobertura
- Catálogo: ES/EN, sets/cartas, variante vs printing, nulls, IDs estables/renombrados, campos disponibles y compatibles con INGESTION_V1.
- Mercado: listing / sale / aggregate, EUR, ventanas, fecha de precio distinta de actualización de carta, condición/idioma/foil, fees/envío, representatividad y derechos para retener histórico. Un agregado documentado puede ser candidato P2; no exigir exclusivamente ventas individuales ni llamarlo valor verdadero.
- Retail: SKU/EAN, variante/surtido, seller marketplace, precio/currency/envío, stock vs availability/coming-soon/preorder, ámbito ES/EU y credenciales/feed rights.
- Discovery: enumeración frente a watchlist; snapshot/página, fin de lista, orden/paging y cambios concurrentes; ausencia no implica baja. Catálogo de sets no acredita sealed vendible o retail.
- Independent source count: precios upstream servidos por dos APIs no constituyen automáticamente dos mercados independientes.
## Protocolo de probes condicionales
No probe por defecto antes de documentar acceso, usos y límites pertinentes.
Autorizados solo **GET públicos sin autenticación** o lectura de un archivo oficial pequeño con permiso compatible, sin aceptar contratos nuevos, coste ni cookies de sesión. Si faltan requisitos, no hacer el probe y explicar por qué.
Budget total de esta fase: máximo **12 solicitudes directas de datos**, máximo **6 por proveedor**, seriales; timeout máximo15s y respuesta máximo256KiB. Registrar intento fallido como solicitud si llegó a emitirse. Desactivar redirects o permitir únicamente destinos oficiales previamente documentados. No follow de URLs del payload. Sin reintentos automáticos; 401/403/429 o límite alcanzado -> detener ese probe, no buscar evasión.
Acotar listas, por ejemplo <=10 elementos por página si la API lo permite. No recorrer toda la base ni descargar un dump grande; contar páginas/bytes y declarar el alcance probado. Si una validación útil necesita más presupuesto, proponerla al Orchestrator.
Plan de cada probe: pregunta, endpoint, campos allowlisted, evidencia de acceso/retención, presupuesto, tratamiento de respuesta y límites de conclusión. Métodos/redes/documentación pública de investigación no se presentan como ejecución API propia.
- Si retención no está acreditada, no persistir payload. Conservar solo diagnóstico técnico no sensible: hora UTC, endpoint público seguro, status, bytes, esquema/tipos/conteos y resultado de la pregunta.
- Una fixture de datos reales requiere permiso de conservación/publicación de **esos campos**. Si no existe, usar fixture sintética para el helper y marcarla synthetic; no afirmar que reproduce valores observados.
- Payload con campos excluidos puede manejarse transitoriamente para extraer lo autorizado; no registrarlo ni incorporarlo íntegro al repo.
- Muestra retenida permitida: mínima, sanitizada, con provenance observed, fuente/fecha/endpoint/artefacto/licencia/allowlist y avisos aplicables. Nunca cambiar su clase a synthetic para procesarla.
- No importar ninguna muestra real en la DB CMT actual ni conectar probes a Discovery/Persistence.
Un HTTP200 aislado no prueba operación continua, cobertura, licencia de histórico, salud o completitud. No exigir observar un lanzamiento real ni esperar días para fabricar delta temporal; registrar frescura como no observada cuando corresponda.
## Decisiones y condiciones de paso
Para cada ruta, usar una decisión:
- **QUALIFIED_FOR_NARROW_USE**: acceso del alcance concreto acreditado, campos/usos compatibles documentados y muestra técnica suficiente del alcance declarado.
- **CONDITIONAL**: viable en documentación pero falta acceso, prueba, cobertura o permiso pertinente.
- **REJECTED_FOR_PROPOSED_USE**: conflicto concreto o acceso incompatible acreditado; no significa rechazo para todo uso.
Separar la decisión de las dimensiones: ACCESS, RETENTION, SEMANTICS, COVERAGE, OPERATIONAL_LIMITS. Cada dimensión tiene evidencia y límites; no usar una nota promedio para esconder un bloqueo.
Si una ruta depende de cuenta/plan/consentimiento/clave no disponibles, permanece CONDITIONAL aunque sus docs sean buenas. Proponer una acción humana precisa con coste/impacto/condición, pero **no realizarla** ni detener trabajo independiente.
Entregar una recomendación accionable:
- Si catálogo se cualifica, proponer **P1b — Licensed Metadata Ingestion & Capture Scope**, con whitelist y cambios de contrato/provenance/captura necesarios; no abrirla ni implementarla.
- Si mercado/retail se cualifica, recomendar al Orchestrator reconsiderar P2/P6a para ese alcance exacto; no desbloquear unilateralmente.
- Si ninguna ruta se cualifica, mantener bloqueos y priorizar pocas acciones pendientes concretas; no pedir reconstruir el proyecto sintético ni reducir gates.
Un ADR de selección/política significativo debe distinguir decisión para investigación/propuesta de futura implementación. No afirmar que un adapter inexistente está adopted/operativo. Registrar alternativas, consecuencias y condiciones de revisión.
## Arquitectura, datos, seguridad y observabilidad
Conservar P1a identidad curada, P3a históricos/replay y P4a novedad relativa. No acoplar dominio al proveedor. Fuente real aprobada a futuro -> modelo de ingestión validado -> dominio; precios/stock nunca se introducen como metadatos de catálogo.
Proponer tratamiento de contexto de captura explícito para lotes vacíos y múltiples productores (TD-005), proveniencia observed/documented/synthetic y política de retención por campos. **Propuesta documental**, sin schema2 o mutaciones.
Threat/riesgos/deuda describen controles actuales vs requisitos futuros. No cerrar TD-005 con una licencia ni cerrar TD-002 con acceso API. Secrets, cookies, tokens, headers privados, payloads arbitrarios y valores comerciales no autorizados no entran al repo/logs.
El ledger de probes identifica ejecución/pregunta/source/run/time/status/duración/bytes/result/categoría; fuente inaccesible no equivale a0 productos. No integrar alertas operativas en esta fase.
No añadir dependencias runtime. Helpers de investigación, solo si aportan reproducibilidad, separados en scripts/probes y stdlib, límites fail-closed y sin credenciales. Nunca live calls en CI; unit/contract tests de helper sobre fixtures offline cuando se introduzca lógica relevante.
## Acceptance Criteria — AC-Q01–AC-Q12
| ID     | Evidencia requerida                                                                                                                                       |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-Q01 | Baseline/padres/árbol y trabajo previo verificados; cierre P4a/apertura P0.5b y ownership atribuidos correctamente.                                         |
| AC-Q02 | TCGdex cualificado por campos/artefactos/usos y fuentes primarias actuales; código/datos/imágenes/precios distinguidos. Resultado puede ser condicionado. |
| AC-Q03 | Máximo2 rutas mercado con acceso/coste/derechos/semántica EUR/history explicitados; agregados/listings/ventas/upstream sin confusión.                       |
| AC-Q04 | Máximo2 rutas retail/feed con acceso/retención/producto/seller/stock/preorder/ES explicitados y sin probes incompatibles.                                 |
| AC-Q05 | Probes justificados y budget respetado, o no ejecución condicional motivada; no cuenta/pago/contacto/evasión ni live calls CI.                            |
| AC-Q06 | Evidence ledger separa documentado/observado/inferido/desconocido; fuentes leídas/fechas/ámbitos y campos retenidos/licencias trazables.                    |
| AC-Q07 | Matriz de decisiones por ruta y dimensión; permiso/operación/cobertura ausentes mantienen CONDITIONAL/BLOCKED pertinente.                                 |
| AC-Q08 | Siguiente fase propuesta con alcance exacto/campos/condiciones; ninguna apertura/desbloqueo unilateral ni falsa fuente viable.                            |
| AC-Q09 | Fronteras/provenance/capture scope/retención futura documentadas; schema1, synthetic-only, identidades e histórico runtime intactos.                      |
| AC-Q10 | Seguridad/probe observability/redacción/fixtures sanitizadas y política de publicación revisadas; TD-001–TD-005 conservadas.                              |
| AC-Q11 | Gates aplicables/regresión/frozen build/wheel/Compose/AMD64/ARM64/CI final exacto PASS; helper adicional offline probado si existe.                         |
| AC-Q12 | QA/REVIEWER independientes y exact-SHA; documentación/ADRs/contratos/runbook/roadmap/reporte/ledger coherentes con resultados y límites.                    |
Ningún AC exige encontrar una fuente compatible. Exigen investigación y decisiones acreditadas sobre las rutas acotadas. Un probe condicional no autorizado no se declara ejecutado ni PASS operativo; documentar razón. Gates obligatorios del candidato no ejecutados son FAIL, no N/A.
## Testing, gates y equipo
Conservar recetas QUALITY_GATES y los cuatro jobs actuales: frozen, Ruff format/check, strict mypy, unit/integration/contract/regression, coverage>=85%lines/>=80%branches, sdist/wheel y smokes fuera del checkout, dependency audit/secret scan, Compose/AMD64/ARM64 QEMU. Aunque la fase sea principalmente documental, CI confirma regresiones del baseline y no debe invocar fuentes live.
Validación documental: enlaces primarios consultados, fechas/versiones, exactitud de citas breves, consistencia de matriz/fichas/allowlist y correcta atribución de resultados. No escribir tests que copien afirmaciones documentales; QA contrasta fuentes y ledger de forma independiente.
Engineering Lead: inspección, plan/ownership, Git/shared docs y gates. INTEGRATIONS/DATA: acceso/cobertura/semántica/probes. SEC: alcance de condiciones/retención/redacción, sin presentar inferencias como autorización legal vinculante. ARQ/DB-OWNER: impactos futuros de provenance/capture scope. Roles de autor combinables; asignar paths.
QA y REVIEWER: agentes separados, distintos de autores y entre sí, sobre SHA final en worktrees aislados. QA reproduce offline y contrasta ledger/fuentes; REVIEWER revisa alcance, decisiones, términos/citas, archivos/fixtures/permisos y CI exacto. No afirmar aprobación formal GitHub por review de agente. Esta fase autoriza estas delegaciones; no lanzar especialistas sin pregunta.
Paralelizar investigación read-only/rutas disjuntas; coordinar scripts/lock/Git/docs compartidas secuencialmente. No repetir probes live para que QA los 'reproduzca'; puede contrastar los resultados/harness offline y fuentes. El presupuesto de requests es compartido por todos los agentes.
## Entregables, autonomía e integración
- Contrato/Engineering Brief/ownership archivados en docs/phases/.
- Informe docs/phases/P0_5B_REAL_SOURCE_QUALIFICATION.md y fichas nuevas/actualizaciones fechadas de fuentes sin borrar evidencia histórica.
- Matriz/política campo-uso/probe ledger/recomendación, ADR significativo si procede y requisitos de frontera/propuesta de fase siguiente.
- Fixtures/provenance/avisos y helper/test offline solo si se necesitan.
- Roadmap, riesgos/threat/deuda/arquitectura y documentación de operación pertinentes, con capacidades actuales vs propuestas diferenciadas.
- PR revisable con head/base/tree, scope, QA/REVIEWER, gates y CI exactos.
Autorizados: inspección, rama/worktree, investigación pública, probes bajo condiciones, documentación, helpers/tests acotados, correcciones y PR. No pedir confirmación rutinaria ya cubierta. **Merge no autorizado**; presentar candidato al Orchestrator. No force/protection bypass ni ampliar investigación o gastos.
Phase Completion Report: Phase/Proposed Status/Branch/PR/head/base/tree; MODEL PROFILE USED verificable; especialistas; objetivos/resultados/decisiones; ADR/data contracts; **DATABASE CHANGES: none**; seguridad/deuda/observabilidad; tests/gates/AC-Q01–Q12; limitaciones/open issues/recomendación. Un resultado negativo de fuentes no impide READY_FOR_ORCHESTRATOR_REVIEW si todos los requisitos de investigación y gates pasan.
Una futura autorización de integración será exacta; repetir refs/árbol/alcance/checks/mergeability y detenerse ante cambios. Después: merge real/padres base->head/mismo árbol y CI push/main para ese SHA, incluidos los cuatro cuerpos de logs. Solo entonces el Orchestrator decide aceptación/cierre.
## Primera respuesta
Lee este contrato, context.md, AGENTS/governanza, fuentes P0.5 y contratos/reportes/ledger P1a/P3a/P4a. Confirma rol, perfil y alcance; verifica baseline sin atribuirte ejecución local inexistente.
Entrega Engineering Brief para Codex con preguntas concretas de cada ruta, ownership, prioridad TCGdex, condiciones/probe budget, evidencia a retener, gates y revisión independiente. Empieza por contrastar fuentes primarias y permisos; un proveedor aún no aprobado no se consume en el runtime.
Concluye únicamente cuando corresponda con:\
**READY_FOR_ORCHESTRATOR_REVIEW**
Nunca declares PHASE CLOSED desde el Phase Chat ni abras P1b/P2/P6a.
