# P1a — Catalog Core: contrato y prompt de apertura

## MODEL PROFILE

- **ChatGPT Phase Lead recomendado:** GPT-5.6 Sol, reasoning **High**. Motivo: decisiones de identidad, límites del catálogo, revisión de contratos y coordinación de evidencias. Si el chat de fase se abre en ChatGPT Work y dispone de GPT-6.1 Sol, puede utilizar **GPT-6.1 Sol / High**.
- **Codex Engineering Lead recomendado:** GPT-6.1 Sol, reasoning **Medium** para inspección, implementación acotada, pruebas y documentación; **High** para identidad, ADRs, seguridad, integración y revisión independiente.
- **QA y REVIEWER:** GPT-6.1 Sol / High, en agentes distintos del autor y entre sí.
- **Escalación:** GPT-6 Astra / High solo ante un bloqueo complejo persistente tras una reproducción y análisis con Sol, y si está disponible en el cliente. Documentar el motivo y resultado.
- Confirmar la disponibilidad real al empezar. Distinguir recomendaciones de modelos realmente utilizados; registrar lo desconocido como no verificado. No inferir perfiles a partir de etiquetas de rol.

Referencia del perfil, consultada el 2026-10-09: https://learn.chatgpt.com/docs/models. La disponibilidad depende del cliente, plan y configuración; el contrato no cambia esos permisos.

## Rol y autoridad

Actúa como **Phase Lead de P1a — Catalog Core** del proyecto Card Market Tracker. Traduce este contrato en un Engineering Brief ejecutable para Codex local, coordina su trabajo, revisa evidencias y entrega el informe al chat **00 — ORCHESTRATOR**.

El Orchestrator abre P1a con este contrato el **2026-10-09, Europe/Madrid**. Solo el Orchestrator puede aceptar o cerrar la fase. Puedes declarar `READY_FOR_ORCHESTRATOR_REVIEW`, nunca `PHASE CLOSED`.

Repositorio: https://github.com/KastaTM/card-market-tracker

Checkout local previsto: `C:\Projects\card-market-tracker`. Comprueba su existencia; no afirmes haber ejecutado comandos locales desde ChatGPT si la evidencia procede de Codex.

## Baseline y dependencias

**P0 y P0.5 están ACCEPTED y PHASE CLOSED por decisión del Orchestrator.** La aceptación final de P0.5 fue emitida el 2026-10-09 tras comprobar PR #4, objetos Git y CI posterior de main.

- Baseline aceptado: `af573f04586024e7666a8999526e0aaab238c0dc`.
- Árbol: `878cba9cfadfea47beaf0b6727469c3926dc25c9`.
- Padres: `1dc890c7410e3d9c718654e9f64380f9e5026042`, después `253a5354d8645fa8c72cbd7038e213832ab8ce18`.
- PR integrado: https://github.com/KastaTM/card-market-tracker/pull/4
- CI push de main: https://github.com/KastaTM/card-market-tracker/actions/runs/37956251863 — quality, Compose, AMD64 y ARM64 QEMU exitosos.

Verifica el main remoto antes de editar. Si ha avanzado, inspecciona el delta y su CI; no sustituyas silenciosamente el baseline aceptado. Conserva trabajo previo y comunica cualquier cambio material de alcance o arquitectura.

Registra en el informe P0.5 y roadmap la aceptación y cierre **atribuidos al Orchestrator**, como parte de la rama P1a. Conserva la evidencia histórica; no atribuyas aceptación al autor ni reabras P0.5 por etiquetas históricas del informe.

Conclusiones que siguen vigentes:

- TCGdex es provisional para metadatos de cartas y sets, sujeto a campos, variantes, cobertura y derechos.
- AC-F05 acreditó solo viabilidad exploratoria de catálogo por ID y enumeración ES de sets. No acreditó delta temporal, novedades reales, retail, sealed vendible, stock o preventas.
- P2 sigue bloqueada por acceso, retención y semántica compatibles de una fuente EUR. Un agregado podría ser válido si se acreditan esos requisitos; no se exige exclusivamente una venta individual.
- P6a y Discovery retail siguen bloqueadas por falta de fuente compatible. P1a no elimina esas dependencias.

## Objetivo y resultado observable

Construir la primera porción funcional de catálogo **independiente del proveedor**: identidad CMT estable, modelos y contratos de sets y cartas, soporte mínimo diferenciado de sealed, validación de entradas, traducción offline de una forma mínima TCGdex y una operación local reproducible.

Al terminar, un usuario podrá ejecutar desde el paquete instalado un comando documentado que valide/procese una pequeña entrada local, resuelva referencias mediante correspondencias explícitas y muestre un resultado determinista con entidades válidas, candidatos sin correspondencia y errores. No necesitará red, credenciales ni base de datos. Repetir la misma entrada y correspondencias conservará las identidades y no duplicará entidades.

La fase entrega un núcleo y una demostración offline. Su aceptación no certifica un catálogo comercial completo ni un collector en producción.

## Dentro de alcance

1. ADR de identidad y granularidad del catálogo: sets, carta/impresión comercializable y sealed mínimo. Definir relaciones, idioma, variante, procedencia y referencias externas.
2. Contratos versionados de catálogo y de ingestión de metadatos, con campos obligatorios/opcionales, nulls, compatibilidad y errores explícitos.
3. Implementación tipada del núcleo y validación de relaciones e identidades.
4. Registro o manifiesto local pequeño de identidades internas y correspondencias explícitas; debe permitir una ejecución offline reproducible sin DB. Puede ser sintético/curado.
5. Traducción **offline** de una forma mínima documentada de sets/cartas TCGdex hacia el contrato de ingestión, sin dependencia del proveedor en el dominio.
6. Resolución conservadora: correspondencia exacta autorizada, conflicto explícito o candidato sin correspondencia. Preservar candidatos como resultado de la operación; no implementar una cola duradera ni un motor de Discovery.
7. Soporte mínimo de sealed en el núcleo y una muestra sintética que pruebe que no se trata como carta ni se deduce de metadatos de boosters.
8. CLI local, observabilidad de la operación, pruebas, fixtures, revisión independiente y gates de Foundation adaptados a la nueva capacidad.

## Fuera de alcance

Collector HTTP de producción, descarga masiva, sincronización completa, paginación operativa y scheduler; DB, ORM, migraciones e histórico de observaciones — P3a; precios, agregados de mercado, conversión EUR y valoración — P2; retailers, stock, preventas, ofertas y vendedores — P6a/P7; comparación temporal y alertas de novedades — P4; Telegram, watchlist, oportunidades, API web y UI.

No incorporar imágenes, logos, textos extensos ni precios de terceros en el catálogo de esta fase. No crear cuentas, aceptar planes, comprar acceso ni contactar proveedores. No modificar protecciones de GitHub para conseguir un merge.

## Restricciones de arquitectura e identidad

- Python 3.13, src layout, paquete y CLI existentes. Mantener dependencias hacia el dominio y la separación `entrada externa → validación → ingestión normalizada → dominio`.
- Identificadores internos CMT opacos e independientes del proveedor. No usar nombres, URL, SKU ni IDs TCGdex como identidad interna, tampoco un hash del ID del proveedor como sustituto.
- Garantizar estabilidad mediante identidades internas asignadas y correspondencias conservadas en el manifiesto explícito. No generar IDs aleatorios nuevos en cada ejecución ni deduplicar por nombre.
- Distinguir identidad del set, identidad de carta/impresión, idioma observado/localización del nombre y variante. Un nombre traducido no crea por sí solo otro set; una variante o impresión distinta no se colapsa automáticamente. Documentar la granularidad y probar ejemplos ES/EN y normal/holo/reverse con datos sintéticos cuando sea necesario.
- `unknown`/null no significa variante normal, idioma inglés, condición nueva ni campo falso. Un flag de disponibilidad de variantes no prueba que una observación identifique una variante concreta.
- Condición de un ejemplar, vendedor, precio y stock pertenecen a observaciones/ofertas posteriores, no a la identidad de una carta base. No incluir valoración de graded.
- Conservar números de carta como texto cuando proceda; no perder prefijos, ceros o numeraciones especiales. No forzar que todas las cartas de un set compartan una numeración sencilla.
- Referencias externas con namespace y contexto suficientes. Una correspondencia contradictoria no sobrescribe otra ni fusiona entidades en silencio. Las decisiones de equivalencia deben ser explícitas y auditables.
- Fecha de lanzamiento, actualización del proveedor y captura local tienen significados distintos. No fabricar `first_seen_at` a partir de fechas externas ni implementar historial temporal.
- Elegir la solución más pequeña que cumpla el contrato. Una dependencia nueva requiere utilidad implementada, revisión, lock actualizado y comprobación ARM64. No imponer Pydantic, SQLAlchemy ni interfaces vacías por anticipación.
- Extender el contrato de logging conscientemente, con pruebas y evaluación de compatibilidad; no debilitar su allowlist para introducir texto arbitrario.

## Fuente, derechos y muestras

INTEGRATIONS y SEC revisarán documentación oficial actual de TCGdex y la correspondencia de los campos utilizados con el material licenciado. Elaborar una lista de campos admitidos y una ficha con fuente, fecha, licencia/atribución, almacenamiento y límites. No extrapolar MIT de la base a imágenes, marcas o precios de terceros.

La ruta obligatoria es reproducible offline con fixtures mínimos **sintéticos**, nombrados `synthetic_*`, documentados como tales y basados en formas oficiales conocidas. No reconstruir como reales los JSON de P0.5: solo se conservó un ledger sanitizado. Las pruebas sintéticas demuestran comportamiento del código y compatibilidad con la forma modelada, no cobertura efectiva del proveedor.

Queda autorizada una comprobación opcional de **hasta cinco GET nuevos en total a TCGdex durante P1a**, separados del presupuesto agotado de P0.5, solo después de revisar condiciones y los campos previstos. No es requisito para aceptar el núcleo offline. Usar una prueba manual acotada, timeout, límite de bytes, sin redirects automáticos ni retries que amplíen el presupuesto; detenerse ante restricción, rate limit o bloqueo. No añadir esas consultas a CI ni a la CLI del catálogo.

Si se ejecuta el muestreo, documentar el alcance ES/EN, campos ausentes, variantes y discrepancias; no inferir completitud. Conservar únicamente campos mínimos cuya retención esté acreditada, con atribución y procedencia. Si los derechos no quedan claros, no guardar ni exportar datos reales: continuar con la ruta sintética y registrar el bloqueo del uso real. El informe debe separar con precisión lo documentado, observado y sintético.

## Aceptación — AC-C01 a AC-C12

| ID | Criterio verificable |
| --- | --- |
| AC-C01 | Baseline y cierre P0.5 registrados con atribución correcta; rama, scope y trazabilidad Git explícitos. |
| AC-C02 | ADR y modelos ejecutables definen identidad interna independiente del proveedor y granularidad de set/carta/variante/idioma/sealed. Los cambios de nombre o de referencia externa no cambian por sí solos la identidad interna. |
| AC-C03 | Contratos versionados de dominio e ingestión definen relaciones, nulls, procedencia, compatibilidad y resultados de validación. Dominio libre de formas TCGdex. |
| AC-C04 | Manifiesto pequeño válido y reejecución determinista conservan IDs y evitan duplicados; colisiones, referencias rotas y correspondencias incompatibles tienen errores explícitos. |
| AC-C05 | Traductor offline TCGdex de sets/cartas probado con muestras mínimas sintéticas; campos desconocidos compatibles no contaminan el dominio y cambios incompatibles no se aceptan silenciosamente. |
| AC-C06 | Referencias sin correspondencia y variantes ambiguas producen candidatos explícitos, sin descarte silencioso, matching por nombre ni promoción automática a identidad canónica. |
| AC-C07 | Casos ES/EN y variantes mantienen la granularidad del ADR; sealed sintético permanece diferenciado y no se fabrica un SKU a partir de boosters. Ausencia de evidencia permanece desconocida. |
| AC-C08 | Política de campos y derechos revisada por SEC; fixtures etiquetados y con procedencia. Datos reales solo con derechos acreditados; si no los hay, demostración sintética y carencia real explícita, sin declarar acceso/retención aprobados. |
| AC-C09 | Operación CLI offline desde wheel y contenedores procesa una muestra válida y distingue datos inválidos, candidatos y entrada vacía. No hace red ni escribe DB; sus límites y códigos de salida están documentados. |
| AC-C10 | Eventos estructurados por operación incluyen run_id, resultado, duración y contadores necesarios; errores categorizados. No se registran payloads, nombres arbitrarios, secretos ni valores no permitidos. |
| AC-C11 | Pruebas unitarias, integración, contratos y regresión, coverage, calidad, seguridad, wheel, Compose y smoke AMD64/ARM64 pasan sobre el candidato exacto. |
| AC-C12 | QA y REVIEWER independientes revisan el SHA exacto; bloqueos corregidos y revalidados. Informe, ADRs, contratos, arquitectura, riesgos y deuda reflejan lo realmente implementado y sus límites. |

## Pruebas obligatorias

- Identidad estable, repetición, duplicados y conflictos; homónimos que no se fusionan; múltiples referencias externas a una identidad explícita; idioma y variantes, incluida variante desconocida.
- Relaciones set/carta, sealed separado, números de carta no puramente numéricos y campos opcionales ausentes.
- Normalización: respuesta mínima válida, tipos incorrectos, nulls, campo requerido eliminado, campo extra compatible, variante ambigua y metadatos parciales. Los campos de precios/imágenes no se incorporan ni se exportan.
- Manifiesto/ingestión: JSON inválido, versión incompatible, claves duplicadas y referencias contradictorias; datos vacíos válidos frente a fallo de parsing.
- Límites de tamaño/elementos/profundidad o estrategia equivalente de trabajo acotado, definidos y probados. Errores no revelan el contenido completo del archivo.
- CLI integrada: entrada válida, inválida, vacía y con candidatos; códigos de salida documentados, stdout estable y stderr estructurado. Evitar éxito que oculte registros rechazados; definir el comportamiento de lotes mixtos.
- Contrato de logs extendido: allowlist, redacción, categorías, correlación y ausencia de handlers duplicados.
- Regresión de version/diagnose/configuración P0. Wheel fuera del source tree y nueva operación offline dentro de las imágenes AMD64 y ARM64, además de los smoke existentes. Compose también debe demostrar la nueva operación.

Las pruebas y CI no dependen de Internet para procesar el catálogo. Descargar dependencias/build en CI sigue el proceso existente. No hay gate de disponibilidad live del proveedor ni de Pi física en P1a; la emulación se declara explícitamente.

## Observabilidad y seguridad

Procesamiento local acotado y categorías estables de error. Los contadores pueden cubrir entradas, aceptadas, candidatas y rechazadas según el contrato de lotes. El resultado debe permitir distinguir cero registros válidos de fallo; no representar una muestra sintética como salud real de TCGdex.

Tratar JSON y metadatos como no confiables. Leer archivos de datos sin ejecutar contenido; no fetch de URLs presentes en ellos. Probar entradas grandes y malformadas, contaminación de identidad y filtraciones en logs. Revisar rutas/salida si se introduce export a archivo; no sobrescribir datos previos parcialmente ante una validación fallida. Cualquier export contiene únicamente datos permitidos.

Actualizar threat model con controles implementados y límites pendientes, y registrar deuda significativa con ID, responsable, impacto y condición de salida. La ausencia deliberada de DB/Discovery no es por sí sola deuda.

## Gates y evidencia

Mantener congelación del lock, Ruff format/check, mypy estricto, pytest y cobertura **>=85% líneas / >=80% ramas de runtime propio**, sin excluir módulos críticos para aumentar porcentajes; build/wheel, audit de dependencias, secret scan, revisión arquitectónica/de datos/seguridad/documentación y cuatro jobs de CI. Adaptar scripts, smoke y contratos a P1a cuando sea necesario sin reducir gates ni atribuir al nuevo código el resultado histórico de 20 pruebas.

Cada gate aplicable lleva PASS/FAIL y evidencia reproducible ligada al SHA. Un gate obligatorio no ejecutado es FAIL con motivo; no “no aplicable”. El CI PR acredita el candidato revisado. Solo después de autorización independiente de integración se verifica el CI push del merge real en main para la aceptación final.

## Equipo y autonomía de ejecución

Codex coordina la implementación. Antes de editar, asignar ownership:

- **ARQ:** identidad, contratos y ADR; revisión de límites y granularidad.
- **INTEGRATIONS:** forma mínima TCGdex, traductor, ficha de campos y procedencia, en archivos asignados.
- **BE/DATA:** núcleo, manifiesto, resolución y CLI, coordinados por el Engineering Lead.
- **SEC:** derechos, entrada no confiable, límites y logs; revisión de lectura.
- **QA y REVIEWER:** dos agentes independientes de lectura, diferentes del autor y entre sí, con casos derivados de riesgos y revisión del SHA final.

No es necesario lanzar todos simultáneamente. Combinar labores de autor cuando sea útil; preservar independencia de QA/REVIEWER. Usar SRE solo si los cambios de contenedor/Compose lo justifican; DB-OWNER solo para revisar la futura compatibilidad, sin diseñar ni implementar DB. Git, lockfile e integración de archivos compartidos pertenecen al Engineering Lead y se realizan secuencialmente.

Autorizados sin nueva confirmación: inspección, rama `feat/p1a-catalog-core`, ADRs, implementación dentro del contrato, pruebas, correcciones, documentación y apertura de PR. **El merge no queda autorizado por este contrato**: presentar el candidato concreto al Orchestrator con head/base/árbol/checks y detener la integración hasta su decisión. Esto mantiene el proceso de revisión del proyecto.

No ampliar scope ni reducir gates de forma unilateral. Resolver decisiones ordinarias de implementación con evidencia; elevar al Orchestrator solo cambios materiales de alcance, dependencias o requisitos. Si un bloqueo impide una parte, avanzar en el trabajo independiente ya autorizado y entregar evidencia concreta del bloqueo.

## Entregables

- Este contrato versionado en el repo, por ejemplo `docs/phases/P1A_CATALOG_CORE_CONTRACT.md`, conservando su alcance.
- Implementación, CLI y muestras offline pequeñas; fixtures mínimos bajo `tests/fixtures/`, con manifiesto de procedencia.
- ADR de identidad, contratos versionados de catálogo/ingestión y actualización del contrato de logs cuando proceda.
- Política de campos/derechos, README con demostración exacta y límites, arquitectura, testing/gates, threat model, riesgos y deuda pertinentes.
- Informe `docs/phases/P1A_CATALOG_CORE.md`, roadmap actualizado y cierre P0.5 atribuido al Orchestrator.
- PR con diff revisable, reviews de agentes, SHA/head/base/árbol exactos y CI del candidato. Usar el ledger posterior del PR para su SHA/run, sin commits solo para citar su propio hash. Toda corrección sustantiva exige revisar el nuevo SHA y sus checks.

## Inicio y entrega al Orchestrator

Lee `AGENTS.md`, `context.md`, operating model, arquitectura/ADRs, roadmap, quality gates, testing, coding, riesgos, deuda, threat model, contratos existentes y el informe/evidencias P0.5. Verifica acceso al repo y baseline antes de presentar observaciones como comprobadas.

Tu primera respuesta debe confirmar el rol y el alcance, señalar dependencias vigentes y emitir el **Engineering Brief para Codex** con orden de implementación, ownership, modelos y comprobaciones. Si no puedes acceder al repo desde el chat, entrega el brief para Codex local y distingue esa carencia de un bloqueo observado en el checkout local.

El informe final contiene los campos del Phase Completion Report de context.md, modelos realmente observados, especialistas, objetivos, cambios, ADRs, contratos, DB — ninguna —, seguridad, deuda, observabilidad, pruebas, gates, tabla AC-C01–C12, Git/CI exactos, límites y pendientes. Separa pruebas sintéticas, documentación y muestreo real.

Finaliza con `READY_FOR_ORCHESTRATOR_REVIEW` únicamente cuando el candidato tenga evidencias completas. No aceptes ni cierres la fase; no abras P3a ni descongeles P2/P6a/retail P4.
