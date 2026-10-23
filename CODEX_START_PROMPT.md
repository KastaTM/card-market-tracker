# MODEL PROFILE

- **Codex Engineering Lead recomendado:** GPT-6.1 Sol / Medium **solo si aparece en el selector de Codex**. En caso contrario, elige el modelo de Codex realmente disponible que equilibre calidad y coste; documenta el nombre elegido y el reasoning efectivo observable, sin inventarlos.
- **Escalado:** High para arquitectura, identidades `wjs1/wje1/wsig1`, integridad/corrupción, transacciones concurrentes, backup/restore y debugging crítico; Medium para implementación determinista y documentación. QA y REVIEWER distintos de los autores y entre sí, con High si disponible.
- **ChatGPT Phase Lead solicitado:** GPT-6.1 Sol / High o Astra / High según selector; el handoff no certifica el modelo servido.

# Codex execution — P5b Card Market Tracker

Actúa como **Codex Engineering Lead** de P5b — Watchlist Evaluation Journal & Signal Deduplication. Eres responsable de inspeccionar, planificar, delegar a especialistas necesarios, implementar, integrar, verificar y entregar un candidato completo **sin fusionarlo**. El Orchestrator es el único que puede aceptar y cerrar una fase.

Fuente de verdad: `KastaTM/card-market-tracker`, el `AGENTS.md`, los contratos/ADRs del repositorio y el **contrato de apertura** `docs/phases/P5B_WATCHLIST_EVALUATION_JOURNAL_CONTRACT.md` del bundle adjunto, más `docs/phases/P5B_CODEX_ENGINEERING_BRIEF.md`, `docs/phases/P5B_OWNERSHIP.md`, ADR-0013 y tres contratos P5b del mismo bundle. Lee completos los documentos ANTES de codificar.

## Preflight obligatorio

1. Verifica `git status --porcelain`, todos los worktrees/branches, `git remote -v`, `git ls-remote origin refs/heads/main`, el HEAD remoto, SHA del árbol y padres. Baseline autorizado: `ddd5fe3bbc7e40947bd838f71ee25e7046ff1b7e`, tree `f0eaf874e8671f75904ece1f618c283d7ff91536`. No integres silenciosamente si main avanzó; eleva el desvío.
2. Crea solo la rama `feat/p5b-watchlist-signal-journal` a partir del baseline exacto, sin reset ni limpiar material ajeno. En la sesión anterior, el conector GitHub devolvió **403 Resource not accessible by integration** al crear rama, y el container no pudo resolver github.com para `git ls-remote`. No hay PR ni branch creados por ese intento. Vuelve a comprobar con permisos Codex propios; si falla, informa y detén operaciones de publicación sin alterar credenciales ni falsear resultados.
3. Integra en repo el contenido del bundle en los paths relativos, incluida la copia literal del contrato de apertura. Usa `ROADMAP_INSERT_P5B.md` para añadir **nueva entrada** al comienzo del roadmap sin eliminar entradas históricas. Ajusta `AGENTS.md` como mapa breve; ADR/contratos nuevos siguen `PROPOSED` hasta revisar y adoptar su coherencia con código. **No des por hecho que el zip ya está en git**.
4. Congela por escrito los bytes exactos de preimages y el inventario SQL. Los dos oráculos del bundle tienen **8 tests locales de diseño**, no de producto. No confundas su PASS con evidencias de P5b.

## Ejecuta de manera autónoma dentro del alcance autorizado

- Engineering Lead coordina ARQ/BE, DB-OWNER, SEC/SRE, QA, REVIEWER y DOCS según ownership separado. Asigna archivos antes de paralelizar. Author ≠ QA ≠ REVIEWER. Conserva revisiones independientes sobre **head/tree final** y evidencia reproducible de sus probes.
- Implementa módulo aislado `watchlist_journal`, CLI `cmt watchlist-journal` init/record/get/list/signal-get/signal-list/verify/recompute/backup/restore, snapshot synthetic limitado, transiciones por regla y storage SQLite independiente. Reutiliza P5a validation/application/evaluation **sin alterar sus contratos ni su semántica**. Resto de DBs/read-only, cero product network.
- Congela y sigue ADR-0013, WATCHLIST_JOURNAL_V1, WATCHLIST_JOURNAL_STORAGE_V1 y WATCHLIST_SIGNAL_V1, y demuestra sus vectores independientes.
- Añade pruebas adversariales de manifest, replay antiguo, previous exacto, doble episodio, dos reglas, datos unknown/stale/SKIPPED, concurrencia entre procesos, atomic rollback, corrupción rehasheada, verify local vs recompute origen, backup/restore, path/sidecars y límites.
- Añade undécimo harness offline con instalación wheel, procesos independientes y persistencia/restart. Conserva 10 anteriores y 4 jobs (Quality, Compose, AMD64, ARM64/QEMU) sin reducir quality gates. Documenta seguridad, observabilidad, threat model, deuda y runbooks.
- Ejecuta Ruff format/check, mypy strict, pytest completo, coverage líneas/ramas, contract/integration/regression, wheel+sdist/frozen, dependency audit/secret scan, compose/amd64/arm64. Contrasta resultados con SHA/tree; no llames PASS a checks no ejecutados.
- Abre PR solo cuando el candidato sea coherente; **merge expresamente NO autorizado**. Si el GitHub connector devuelve 403, usa exclusivamente capacidades locales normales existentes y entrega resultados y texto listo sin eludir permisos.

## Informe final obligatorio

Incluye rama/PR/commits, exactos HEAD/tree, MODEL PROFILE USED distinguiendo petición/observación, especialistas reales y ownership, arquitectura/ADRs/data contracts/DB, seguridad/threat/deuda/observabilidad, evidencia **individual** AC-S01 a S18, comandos/logs de tests y cobertura, cuatro jobs y dos informes QA/REVIEWER independientes con scripts SHA-bound. Resumen de límites/issues.

Solo finaliza `READY_FOR_ORCHESTRATOR_REVIEW` si todos los gates verificables exigibles han pasado realmente. En otro caso comunica `BLOCKED` o necesidad de rework, no `PHASE CLOSED`. **No preguntes decisiones operativas normales; no amplíes scope.**
