# TCGdex — ficha de viabilidad P0.5

**Consulta:** 2026-10-07 (UTC). **Clasificación:** `VERIFIED` para acceso puntual al catálogo de cartas y expansiones ES/EN; `CONDITIONAL` para precios como fuente de mercado y para retención/redistribución de esos precios. Cinco solicitudes directas, sin clave ni payload persistido. La prueba no demuestra completitud, SLA ni operación continua.

## Fuentes primarias y condiciones

- [REST](https://tcgdex.dev/rest), [FAQ](https://tcgdex.dev/faq), [card](https://tcgdex.dev/reference/card), [set](https://tcgdex.dev/reference/set), [paginación](https://tcgdex.dev/rest/filtering-sorting-pagination) y [precios](https://tcgdex.dev/markets-prices), consultados 2026-10-07.
- [Repositorio oficial de la base](https://github.com/tcgdex/cards-database/blob/master/README.md) y su [licencia MIT](https://github.com/tcgdex/cards-database/blob/master/LICENSE), consultados 2026-10-07. La licencia de la base no acredita por sí sola derechos de redistribución de precios agregados de Cardmarket/TCGplayer, imágenes ni marcas de terceros.

**Documentado:** API REST HTTPS/GET/JSON, gratis y sin clave. No publica un límite duro; pide uso considerado y cachear cuando se requieran datos en volumen. La base pública se presenta bajo MIT. No encontré una regla específica de retención, atribución o redistribución de los *precios de terceros* en las páginas revisadas; queda por aclarar antes de guardar histórico o republicarlos. No se creó cuenta ni se aceptó un plan.

## Capacidad y semántica

| Aspecto | Evidencia documentada y límite |
| --- | --- |
| Catálogo singles y sets | `id`, `localId`, `name`, `category`, `rarity`, `set`, `variants`, `updated` en carta; set `id`, `name`, `cardCount`, `releaseDate`, `cards`. IDs del proveedor solo como identificadores externos, nunca identidad canónica CMT. Faltas de carta/ID erróneo son posibles según FAQ. |
| ES / EN y Europa | FAQ declara español e inglés. La prueba confirmó traducción del nombre del mismo set (`swsh3`) y acceso a la carta en ambos idiomas; `Furret` conserva el mismo nombre y no prueba traducción de cartas. No se midió completitud de ES. `pricing.cardmarket` se documenta en EUR y mercado europeo, pero no filtra España, idioma de ejemplar, vendedor, impuestos o envío. EUR no implica precio realizable en España. |
| Sealed | El set y algunas cartas describen `boosters` (ilustraciones/nombres de sobres), pero la referencia no demuestra un catálogo de SKUs vendibles, cajas, ETB, bundles, exclusivas, stock o reservas. No tratar los boosters como cobertura sealed comercial. |
| Variantes y condición | `variants` ofrece flags normal/reverse/holo/firstEdition; en las dos cartas probadas apareció además `variants_detailed`, que la FAQ todavía describe como campo en desarrollo. No se observó condición, idioma de ejemplar, gradación ni vendedor en el agregado. La FAQ reconoce errores de emparejamiento entre rarezas e IDs de marketplace. |
| Precios | `pricing.cardmarket` ofrece agregados EUR (`avg`, `low`, `trend`, ventanas 1/7/30 días, foil); `pricing.tcgplayer` ofrece USD. Son datos derivados de esos marketplaces, no proveedores independientes adicionales. `low` es mínimo listado/agregado; `avg` y `trend` no equivalen a una venta individual verificada ni a MSRP. Precio ausente es normal. |
| Fechas y frescura | `releaseDate` es fecha del set, no primera aparición en CMT ni fecha de preventa. `updated` de carta excluye cambios de precios. Los precios llevan su propio `updated`; el proveedor declara Cardmarket diario y TCGplayer horario a diario, sin SLA observado en esta prueba. `first_seen_at` debe ser observación propia. No hay histórico completo de transacciones. |
| Descubrimiento y paginación | Listas de sets y cartas con filtros y orden. La paginación es optativa; `pagination:page` y `pagination:itemsPerPage` permiten acotar respuestas. Descubrir un set no demuestra descubrir SKUs o lanzamientos retail. |

## Prueba directa mínima

**Método:** PowerShell 5.1 `HttpClient` con HTTPS, GET, `AllowAutoRedirect=false`, timeout 12 s, máximo leído 65 537 bytes por respuesta; se imprimieron solo hora UTC, URL, estado, bytes y nombres de campos/conteos/nombres breves. No se guardó payload ni identificador personal. La primera ejecución falló **antes de emitir HTTP** por no cargar `System.Net.Http`; se cargó el ensamblado y se hicieron exactamente cinco solicitudes. Un `200` aislado verifica solo el acceso puntual.

| UTC | GET (sin secretos) | Resultado observado |
| --- | --- | --- |
| 2026-10-07 16:59:52 | `https://api.tcgdex.net/v2/en/sets/swsh3` | 200, 21 922 B; set `Darkness Ablaze`, `releaseDate=2020-08-14`, 201 cartas; campos `cardCount,cards,id,legal,logo,name,releaseDate,serie,symbol,tcgOnline,abbreviation`. |
| 2026-10-07 16:59:52 | `https://api.tcgdex.net/v2/es/sets/swsh3` | 200, 21 966 B; set `Oscuridad Incandescente`, mismo `releaseDate` y 201 cartas; mismos campos de nivel superior. |
| 2026-10-07 16:59:52 | `https://api.tcgdex.net/v2/en/cards/swsh3-136` | 200, 3 048 B; `Furret`; campos `id,localId,name,rarity,set,variants,variants_detailed,updated,pricing` entre otros; `pricing` contiene `cardmarket,tcgplayer`. |
| 2026-10-07 16:59:52 | `https://api.tcgdex.net/v2/es/cards/swsh3-136` | 200, 2 942 B; `Furret`; mismos campos relevantes y dos claves de `pricing`. No se inspeccionaron valores ni fechas de precios. |
| 2026-10-07 17:00:12 | `https://api.tcgdex.net/v2/es/sets?pagination:page=1&pagination:itemsPerPage=2` | 200, 213 B; exactamente 2 elementos; primer elemento con `id,name,cardCount`. |

**Inferencia para selección:** candidato fuerte para *semilla de catálogo de singles/sets* de P1a, sujeto a muestreo adicional de cobertura y validación de variantes. La capa de precios EUR es una señal exploratoria condicionada por licencia, calidad de matching y semántica; no sirve aún como fuente de mercado independiente ni como histórico libremente reutilizable. Retail sealed y descubrimiento de SKUs requieren otra fuente.

## RW-01 — Discovery de sets, evaluación de la evidencia existente

**Revisión documental:** 2026-10-07; cinco solicitudes originales, ninguna solicitud adicional. Pregunta de rework: ¿la lista ES ya consultada ofrece una ruta distinta del detalle por ID para proponer sets desconocidos para CMT? [Búsqueda de sets](https://tcgdex.dev/rest/sets) y [SetBrief](https://tcgdex.dev/reference/set-brief) documentan enumeración sin un ID de entrada, con `id`, `name` y `cardCount`. La [paginación y orden](https://tcgdex.dev/rest/filtering-sorting-pagination) son configurables; el orden documentado por defecto es `releaseDate > localId > id`, ASC. La primera página no significa las últimas expansiones.

**Observado:** los primeros cuatro GET recuperaron un set y una carta conocidos, en ES/EN. El quinto GET fue una lista sin IDs predeterminados: dos elementos, 213 B, con `id,name,cardCount` en el primero. El autor confirmó que su salida original sólo conservó esos conteos y nombres de campos, no valores de IDs/nombres ni JSON. No se observó un segundo snapshot, una diferencia entre listas ni un candidato nuevo. Los detalles ES/EN no constituyen dos observaciones temporales de discovery.

**Inferido, no ejecutado:** una futura observación de la lista podría comparar la referencia externa con referencias ya observadas bajo `source_key + entity_kind=set + source_record_id`, conservando el idioma de la observación por separado. Si la referencia no tiene correspondencia previa, se propondría un candidato local pendiente, con procedencia, `captured_at` y `first_seen_at` propios; el nombre/ID del proveedor no sería identidad canónica. Desconocido para CMT no significa recién publicado por TCGdex ni lanzamiento nuevo mundial. Diferencias de idioma tampoco prueban dos sets distintos. No se implementó comparación, persistencia ni detección P4.

**Condiciones y conservación:** la FAQ permite acceso gratuito sin clave y recomienda caché; la base oficial MIT permite reutilización con su copyright y aviso de permiso. Esto respalda estudiar conservación mínima de metadatos de sets con procedencia/licencia, sin conceder derechos sobre imágenes, marcas o precios de terceros. La correspondencia entre campos API y material licenciado y la política concreta de conservación deben revisarse antes de implementar. No se amplió la retención de muestras en este rework.

**Pendiente para una ruta fiable:** tipos/valores reales de todos los elementos, estabilidad de IDs y renombrados, cobertura ES, páginas siguientes y fin, duplicados, orden efectivo y desempate, cambios concurrentes entre páginas, latencia de altas y conservación de campos. El ledger sin payload impide reconstruir el JSON exacto o una comparación offline. No se infiere baja de un set por ausencia en una página.

**AC-F05 propuesto PASS, sólo viabilidad exploratoria:** catálogo por ID conocido y enumeración de candidatos de sets son dos rutas funcionales pequeñas probadas, aunque compartan proveedor; el criterio exige rutas, no proveedores distintos ni un detector temporal implementado. El fundamento es lista no vacía + estructura mínima observada + semántica oficial, además del resultado HTTP. QA y REVIEWER independientes aceptaron esta lectura acotada; QA inicialmente pidió delta/baseline y revisó esa exigencia al contrastar el texto exacto. Ninguno acredita novedad real, cobertura completa u operación continua. No resuelve SKUs retail, sealed vendible, stock ni preventas; no convierte TCGdex en otro proveedor ni su precio en otro mercado independiente.
