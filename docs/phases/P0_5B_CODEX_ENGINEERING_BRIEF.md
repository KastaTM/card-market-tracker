# MODEL PROFILE

**ChatGPT Phase Lead**
- Recomendación del contrato: GPT-6.1 Sol / High en Work, si está disponible; GPT-5.6 Sol / High en Chat normal, si está disponible.
- Objetivo: decisiones entre fases, interpretación de evidencias, derechos de uso y revisión de resultados.
- No asumir que una recomendación acredita disponibilidad o ejecución real.

**Codex Engineering Lead**
- Modelo recomendado: GPT-6.1 Sol.
- Reasoning: Medium para inspección, investigación documental, edición y automatización mecánica.
- Escalar a High para licencias, fronteras de datos, seguridad, decisiones arquitectónicas o integración.

**Especialistas**
- INTEGRATIONS/DATA: GPT-6.1 Sol / High.
- SEC: GPT-6.1 Sol / High.
- ARQ/DB-OWNER: GPT-6.1 Sol / High.
- QA: GPT-6.1 Sol / High.
- REVIEWER: GPT-6.1 Sol / High.

QA y REVIEWER deben ser agentes diferentes, independientes de los autores y entre sí.

**Escalado:** primero High. Considerar GPT-6 Astra / High exclusivamente para bloqueos complejos reproducidos y si está disponible. Si algún modelo no aparece en Codex, seleccionar una alternativa realmente disponible y comunicar la desviación.

Registrar modelos solicitados, modelos efectivamente seleccionados y límites de verificación.

---

# ENGINEERING BRIEF — P0.5b Real Source Qualification

## 1. Autoridad y objetivo

Actúa como **Codex Engineering Lead** de Card Market Tracker.

Esta ejecución pertenece a **P0.5b — Real Source Qualification**, abierta por el Orchestrator el 2026-10-13.

El ChatGPT Phase Lead coordina y revisa tu entrega. Solo el Orchestrator puede aceptar, autorizar la integración o declarar PHASE CLOSED.

**Repositorio:** https://github.com/KastaTM/card-market-tracker

**Checkout local previsto:** `C:\Projects\card-market-tracker`

**Rama autorizada:** `docs/p05b-real-source-qualification`

**Objetivo:** determinar mediante evidencia primaria si existe una ruta compatible con usos mínimos reales de CMT para catálogo Pokémon ES/EN, mercado EUR con histórico o Discovery retail.

Una investigación rigurosa que concluya que las rutas siguen bloqueadas es válida.

No inventes permisos, accesos operativos o fuentes viables para satisfacer los Acceptance Criteria.

## 2. Baseline confirmado externamente

El Phase Lead comprobó el repositorio remoto de GitHub el 2026-10-13.

- `main`: `6385c952a9f2024c8b7bdb33d37fa21017029bd5`
- Tree: `8fa2abeb9f4e8991bab1b2895fc397f64bb39a19`
- Primer padre: `734641a7ef920688677cdea6bc82f908a2856927`
- Segundo padre: `c5ed228af831a2a6ed8a12c7072777d3908296a5`
- PR #7: fusionado.
- La rama P0.5b no estaba presente en el remoto durante la comprobación.

Estas verificaciones NO acreditan el estado del checkout Windows.

Antes de editar:

1. Ejecuta `git remote -v`, `git status --porcelain=v1`, `git branch -vv` y `git worktree list`.
2. Ejecuta `git fetch origin`, verifica `origin/main`, su árbol y los padres del commit.
3. Inspecciona ramas, worktrees y cambios preexistentes.
4. Si el baseline avanzó, compara el delta y evalúa su efecto antes de continuar.
5. Conserva cualquier trabajo ajeno. No sobrescribas, no fuerces refs y no hagas rebase silencioso.
6. Crea una rama o worktree aislado únicamente después de establecer la identidad y limpieza necesarias.

## 3. Fuente de verdad y lecturas obligatorias

Lee antes de modificar:

- `context.md`, `AGENTS.md`.
- `docs/ENGINEERING_OPERATING_MODEL.md`.
- `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`.
- `docs/QUALITY_GATES.md`, `docs/TESTING_STRATEGY.md`.
- `docs/CODING_STANDARDS.md`, `docs/RISK_REGISTER.md`.
- `docs/TECHNICAL_DEBT.md`.
- `docs/threat-model/THREAT_MODEL.md`.
- Informes y contratos P0.5, P1a, P3a y P4a.
- ADR-0003, ADR-0004 y ADR-0005.
- Contratos `INGESTION_V1`, `MANIFEST_V1`, `PERSISTENCE_V1`, `STORAGE_V1`, `DISCOVERY_V1` y `SOURCE_INGESTION_V0`.
- Matriz, selección y fichas existentes en `docs/sources/`.

Archiva el contrato íntegro de P0.5b y este Engineering Brief en `docs/phases/`.

Actualiza roadmap e informe histórico P4a para reflejar únicamente la decisión de cierre atribuida al Orchestrator y la apertura P0.5b.

No atribuyas a Codex una aceptación anterior hecha por el Orchestrator.

## 4. Restricciones arquitectónicas

La implementación actual conserva:

- Identidad canónica independiente del proveedor.
- Catálogo y resolver P1a.
- Histórico inmutable/replay P3a.
- Comparación temporal P4a.
- Restricción de persistencia y Discovery a capturas `synthetic`.

**DATABASE CHANGES: none.**

No modificar esquemas, migraciones, modelos de runtime ni controles `synthetic-only`.

No reclasificar datos `observed` como `synthetic`.

No integrar collectors reales, schedulers, alertas, scraping continuo, importadores productivos ni modelos de precios/stock.

No añadir dependencias runtime.

Se autorizan documentación, investigación pública, probes condicionados, helpers mínimos de stdlib y tests offline cuando estén justificados.

## 5. Equipo, ownership y coordinación

Engineering Lead: propietario exclusivo de Git, rama, integración documental, roadmap, contratos compartidos y quality gates.

INTEGRATIONS/DATA: investigación read-only de fuentes, cobertura, campos, semántica y propuestas de probes.

SEC: evaluación de derechos por campo, condiciones de retención, atribución, publicación y riesgos de datos externos.

ARQ/DB-OWNER: propuesta documental de provenance, captura, lotes vacíos, compatibilidad y fronteras de dominio.

QA: reproducción independiente de checks offline, validación de evidencia y contraste documental.

REVIEWER: revisión final independiente de decisiones, scope, permisos, seguridad, documentación y exact-SHA.

Fija ownership de paths antes de delegar. Paraleliza únicamente análisis read-only o edición de archivos realmente disjuntos.

No ejecutes probes simultáneos. Todo el equipo comparte un único presupuesto de solicitudes.

## 6. Investigación prioritaria — TCGdex

Esta es la prioridad principal.

Fuentes oficiales iniciales:

- https://tcgdex.dev/reference/card
- https://tcgdex.dev/reference/set
- https://tcgdex.dev/reference/set-brief
- https://tcgdex.dev/rest/sets
- https://tcgdex.dev/rest/filtering-sorting-pagination
- https://tcgdex.dev/faq
- https://tcgdex.dev/markets-prices
- https://github.com/tcgdex/cards-database
- https://github.com/tcgdex/cards-database/blob/master/LICENSE

**Preguntas obligatorias:**

1. ¿Qué campos concretos de sets/cartas ES y EN provienen de artefactos cubiertos por la licencia MIT del repositorio?
2. ¿Qué correspondencia exacta existe entre archivos fuente, modelos del repositorio y respuesta REST localizada?
3. ¿Permite la licencia conservar y comparar esos campos? ¿Qué copyright, aviso o atribución acompaña a la copia?
4. ¿Hay elementos derivados de terceros cuyo uso no queda cubierto?
5. ¿Son compatibles los campos mínimos con `INGESTION_V1`?
6. ¿Qué ocurre cuando falta traducción, variante, fecha o identificación?
7. ¿Qué distingue un ID estable de un identificador susceptible de cambio?
8. ¿La paginación permite enumerar sets sin confundir orden o ausencia con novedad/baja?
9. ¿Cuál sería el alcance mínimo de captura verificable y repetible?
10. ¿Qué diferencias existen entre variante disponible y printing realmente observado?

**Allowlist inicial a verificar:**

- `id`
- `name`
- `localId`
- `set.id`
- `releaseDate`
- `cardCount.total`
- `cardCount.official`
- `updated`
- Flags específicos y documentados de `variants`

La allowlist definitiva exige correspondencia con los artefactos y derechos aplicables.

Excluir por defecto imágenes, logos, símbolos gráficos, precios, marketplace IDs, descripciones extensas, marcas gráficas y extras externos.

MIT del repositorio no prueba automáticamente que cada campo servido por la API pueda reutilizarse sin restricciones independientes.

No usar `variants_detailed` para inventar printings observados.

**Resultado esperado:** ficha revisada por campos, permisos, semántica, cobertura y accesibilidad. Puede concluir `QUALIFIED_FOR_NARROW_USE` solo cuando el alcance técnico y los derechos estén acreditados.

## 7. Investigación de mercado EUR

Máximo dos rutas.

**Ruta M1 — eBay Browse**

Reevaluar únicamente los puntos necesarios para determinar si existe un uso limitado compatible de listings activos en EUR y España.

Fuentes:
- https://developer.ebay.com/develop/api/buy
- https://developer.ebay.com/api-docs/buy/buy-requirements.html
- https://developer.ebay.com/join/api-license-agreement

Comprobar acceso productivo, credenciales, autorización, retención, display, mezclas de datos, estadísticas derivadas, cuotas, país de marketplace, moneda, paginación y semántica de las ofertas.

No clasificar listings activos como ventas realizadas.

No repetir íntegramente la investigación P0.5 sin evidencia nueva.

**Ruta M2 — Scrydex**

Fuentes:
- https://scrydex.com/docs/getting-started/prices
- https://scrydex.com/docs/pokemon/listings
- https://scrydex.com/docs/pokemon/price-history
- https://scrydex.com/pricing
- https://scrydex.com/terms

Preguntas:
- ¿Existe EUR operativo o continúa anunciado solo para el futuro?
- ¿Los precios son agregados, ventas individuales o tendencias?
- ¿Qué moneda y mercado cubre cada registro?
- ¿Qué significan sus timestamps?
- ¿Se puede conservar histórico propio y bajo qué condiciones?
- ¿El acceso necesita clave, equipo, plan o aprobación?
- ¿Hay cobertura ES/EU acreditada y relevante para CMT?

La documentación oficial consultada el 2026-10-13 sigue describiendo USD/JPY y EUR como expansión futura. Verifica y fecha esa evidencia en el ledger.

Sin cuenta, coste autorizado o derechos suficientes, no realizar llamadas autenticadas ni contratar planes.

No convertir precios estadounidenses a EUR para simular mercado europeo.

## 8. Investigación retail/feed

Máximo dos rutas.

**Ruta R1 — GAME España**

Revisar cambios materiales frente a `docs/sources/GAME_ES.md`.

Comprobar:
- Oferta de productos sealed en España.
- SKU/product ID y variantes surtidas.
- Diferencia entre `PRÓXIMAMENTE`, preorder y stock.
- Precio, moneda, impuestos y envío.
- Derecho de acceso automatizado y conservación de observaciones.
- Enumeración, paginación y ausencia de artículos.

La existencia de una página pública no autoriza monitorización ni retención.

No efectuar scraping ni probe si las condiciones no lo permiten.

**Ruta R2 — Awin Product Feeds**

Primer candidato nuevo: plataforma de feeds de afiliación, materialmente distinta del HTML directo de retailer.

Fuentes:
- https://help.awin.com/developers/docs/product-feed-publisher-guide-intro
- https://help.awin.com/developers/docs/product-feed-list-download
- https://help.awin.com/developers/docs/downloading-feeds-using-create-a-feed
- https://help.awin.com/apidocs/retail-publisher-productapidocumentation-1

Preguntas:
- ¿Qué requiere ser publisher/partner y acceder a un anunciante concreto?
- ¿Qué puede utilizarse para una herramienta personal no pública?
- ¿Existen programas y feeds con productos Pokémon ES/EU verificables sin crear cuenta?
- ¿Qué permisos regulan conservación, comparación, histórico y redistribución?
- ¿Qué campos ofrecen SKU, EAN/GTIN, precio, EUR, envío, disponibilidad, stock, preventa y fecha de actualización?
- ¿Los datos distinguen anunciante, retailer propio y tercero?
- ¿Cómo se detectan nuevos SKUs sin asumir que una ausencia implica retirada?
- ¿Cuál es la cobertura real y la política de actualización?

El soporte documental de un campo no demuestra que exista en un feed concreto.

Si las condiciones exigen alta, asociación o token, registrar la acción humana pendiente, pero no ejecutarla.

No investigar más proveedores fuera del límite aprobado sin elevar la propuesta.

## 9. Matriz de derechos por campo

Cada fuente debe tener una ficha fechada con:

- Campo/grupo exacto y origen/upstream.
- Uso mínimo solicitado.
- Documento primario, sección y fecha.
- Licencia/condición aplicable.
- Retención, actualización, borrado y atribución.
- Evidencia `documented`, `observed`, `inferred` o `unknown`.
- Incertidumbre y acción de resolución.

**Decisiones separadas obligatorias:**

| Acción | Decisión |
|---|---|
| Consultar transitoriamente | YES / NO / CONDITIONAL |
| Guardar muestra mínima | YES / NO / CONDITIONAL |
| Almacenar en CMT futuro | YES / NO / CONDITIONAL |
| Publicar fixture o documentación con valores reales | YES / NO / CONDITIONAL |
| Comparar, derivar o generar histórico | YES / NO / CONDITIONAL |

Tratar display privado, redistribución y explotación comercial como usos distintos.

La falta de prohibición expresa no equivale a permiso concedido.

## 10. Protocolo de probes

**No hay autorización automática para consultar datos por el mero hecho de existir este brief.**

Primero documenta el acceso y la compatibilidad del uso.

Solo están permitidos GET públicos sin autenticación o lectura de archivos oficiales pequeños cuando los derechos y condiciones sean compatibles.

Presupuesto compartido:

- Máximo 12 solicitudes directas de datos en toda P0.5b.
- Máximo 6 por proveedor.
- Ejecución serial.
- Timeout máximo 15 segundos.
- Respuesta máxima 256 KiB.
- Listas limitadas preferiblemente a 10 elementos por página.
- Sin reintentos automáticos.
- Sin paginación masiva.
- Sin redirects ajenos a destinos oficiales previamente documentados.
- Sin seguimiento de URLs contenidas en payloads.
- 401, 403, 429 o exceso de cuota: detener ese probe.

Antes de cada llamada documenta:

- Pregunta concreta.
- Endpoint.
- Justificación de permiso.
- Allowlist.
- Presupuesto.
- Tratamiento de respuesta.
- Interpretación y límites.

No enviar credenciales, cookies privadas ni aceptar nuevos contratos.

Una respuesta HTTP 200 solo acredita la respuesta puntual, no fiabilidad continua ni licenciamiento.

Si no existe permiso de retención, descartar payload y guardar exclusivamente diagnóstico técnico no sensible: fecha UTC, endpoint seguro, status, bytes, tipos, estructura, conteos y conclusión.

Las fixtures reales solo son admisibles si está acreditado el derecho de conservar y publicar esos campos. En caso contrario, usar fixtures sintéticas identificadas como tales.

No incorporar datos reales a la DB actual.

## 11. Decisiones y frontera futura

Para cada ruta entregar un veredicto:

- `QUALIFIED_FOR_NARROW_USE`
- `CONDITIONAL`
- `REJECTED_FOR_PROPOSED_USE`

Evaluar por separado:

- ACCESS
- RETENTION
- SEMANTICS
- COVERAGE
- OPERATIONAL_LIMITS

No emitir un veredicto positivo por promedio.

Proponer documentalmente el camino:

`External Source → Validated Source Model → Normalized Ingestion → CMT Domain`

Preservar procedencia y fecha de captura.

Distinguir:
- `captured_at`
- `provider_updated_at`
- `first_seen_at`
- `release_date`
- `price_observed_at`
- `sold_at`

Cuando una semántica no sea acreditable, declararla desconocida.

Tratar expresamente TD-005: contexto de captura para productores múltiples y lotes vacíos sin inventar una migración ni afirmar que la atestación del productor equivale a evidencia independiente.

No modificar schema1, identidad, historial, comparador ni runtime.

## 12. Observabilidad, seguridad y fallo

Mantener ledger de investigación/probes con:

- run ID
- proveedor y ruta
- pregunta
- timestamp UTC
- categoría de resultado
- HTTP status cuando exista
- duración y bytes
- presupuesto consumido
- decisión de retención
- referencia a evidencia y limitaciones

Distinguir denegación de acceso, timeout, rate limit, payload inválido, ausencia de datos, respuesta parcial y operación correcta.

Una fuente inaccesible nunca equivale a cero productos.

SEC revisará derechos, credenciales, redacción de logs, inputs no confiables, riesgo de contaminación de datos, publicaciones y amenazas introducidas.

Preservar TD-001–TD-005 y registrar riesgos o deuda nueva solo cuando esté justificado.

## 13. Archivos de entrega

Crear o actualizar coherentemente:

- `docs/phases/P0_5B_REAL_SOURCE_QUALIFICATION_CONTRACT.md`
- `docs/phases/P0_5B_CODEX_ENGINEERING_BRIEF.md`
- `docs/phases/P0_5B_OWNERSHIP.md`
- `docs/phases/P0_5B_REAL_SOURCE_QUALIFICATION.md`
- `docs/sources/SOURCE_MATRIX.md`
- `docs/sources/SOURCE_SELECTION.md`
- Fichas fechadas de las rutas seleccionadas y Awin.
- Ledger de evidencias y probes dentro de la documentación de fase o fuentes.
- Propuesta documental de política campo-uso y captura/provenance.
- `docs/ROADMAP.md`
- Nota histórica pertinente en el informe P4a.
- ADR significativo, solo si realmente existe decisión arquitectónica o política que lo justifique.
- Actualizaciones pertinentes de arquitectura, riesgos, threat model, deuda y runbooks.

No borrar la evidencia histórica P0.5.

## 14. Quality gates

Validar sobre el candidato final:

- Baseline, permisos y diff de scope.
- Instalación frozen, lockfile intacto.
- Ruff format/check.
- Strict mypy.
- Tests unitarios, integración, contract y regresión existentes.
- Cobertura mínima: 85% líneas, 80% ramas.
- sdist/wheel y ejecución fuera del checkout.
- Dependency audit y secret scan.
- Docker Compose.
- linux/amd64.
- linux/arm64 QEMU.
- Los cuatro jobs existentes de CI.
- Integridad de documentos, enlaces y licencias.
- QA y REVIEWER independientes sobre SHA exacto.

Seguir las recetas reales de `docs/QUALITY_GATES.md` y CI.

Si se introduce un helper, probarlo offline con fixtures sintéticas, límites adversariales y errores.

No añadir llamadas live al CI.

Un gate obligatorio no ejecutado es FAIL, no N/A.

## 15. Acceptance Criteria

Validar exactamente AC-Q01 a AC-Q12 del Phase Contract.

Cada AC debe vincularse a:
- Documento o cambio concreto.
- Evidencia primaria.
- Prueba/comando.
- SHA y tree.
- Revisor.
- Resultado PASS/FAIL.
- Limitaciones explícitas.

Una ruta `CONDITIONAL` o rechazada puede satisfacer los criterios de investigación si la decisión está acreditada.

No forzar una fuente viable para lograr un PASS.

## 16. Autonomía e integración

Tienes autorización para inspección, investigación pública, edición documental, rama/worktree aislado, probes compatibles, correcciones, validaciones y creación de PR.

No solicitar confirmación por tareas rutinarias dentro del contrato.

**Merge no autorizado.**

No realizar pagos, altas, contactos externos, aceptación de condiciones, integración live ni ampliaciones de scope.

Si aparece un bloqueo real, continuar en paralelo con el trabajo independiente permitido y documentar lo que exige decisión del Phase Lead/Orchestrator.

## 17. Entrega al Phase Lead

Antes de declarar el candidato listo:

1. Congelar head, base y tree.
2. Ejecutar gates reproducibles.
3. Obtener QA y REVIEWER independientes sobre el SHA final.
4. Resolver hallazgos bloqueantes y repetir validación afectada.
5. Publicar PR revisable sin merge.
6. Verificar los checks del candidato exacto.
7. Entregar evidencia de las fuentes, matriz, decisiones y pendientes.

El Phase Completion Report debe contener:

- Phase, Proposed Status.
- Branch/PR/head/base/tree.
- MODEL PROFILE USED verificable.
- Especialistas y ownership.
- Objetivos, resultados y decisiones de fuente.
- Arquitectura y ADRs.
- Data contracts.
- DATABASE CHANGES: none.
- Threat model y technical debt.
- Observabilidad y probe ledger.
- Tests y quality gates PASS/FAIL.
- AC-Q01–AC-Q12.
- Limitaciones y cuestiones abiertas.
- Recomendación para P1b/P2/P6a dentro del alcance acreditado.

Si todo lo exigido está demostrado, finalizar con:

**READY_FOR_ORCHESTRATOR_REVIEW**

Nunca declarar PHASE CLOSED, aceptar una fase, hacer merge ni abrir unilateralmente P1b/P2/P6a.