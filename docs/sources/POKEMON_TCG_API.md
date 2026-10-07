# Pokémon TCG API (legacy) — ficha de viabilidad P0.5

**Consulta:** 2026-10-07 (UTC). **Clasificación:** `REJECTED` para una integración nueva; `CONDITIONAL` solo para una migración de un usuario que ya tenga clave vigente. Sin prueba directa: la retirada anunciada y el cierre de altas hacen improcedente emplear presupuesto de probes en esta ruta nueva. No se usaron credenciales.

## Fuentes primarias y acceso

- [Documentación principal y aviso de retirada](https://docs.pokemontcg.io/), [rate limits](https://docs.pokemontcg.io/getting-started/rate-limits/), [búsqueda de cartas](https://docs.pokemontcg.io/api-reference/cards/search-cards/), [objeto carta](https://docs.pokemontcg.io/api-reference/cards/card-object/) y [objeto set](https://docs.pokemontcg.io/api-reference/sets/set-object/), consultados 2026-10-07.

**Documentado:** la API está deprecada; las nuevas altas están cerradas y las claves existentes funcionarán hasta **2027-03-01**. La documentación permite llamadas V2 sin clave, con 1 000 solicitudes/día y máximo 30/minuto; con clave indica 20 000/día por defecto. La V1 dejó de recibir datos en 2021; cualquier transición sería V2. No hay coste de suscripción publicado en esas páginas, pero la continuidad termina en la fecha anunciada. No encontré en las páginas consultadas una licencia expresa para retener o redistribuir datos/precios de terceros; tratarlo como pendiente, no como permiso.

## Cobertura documentada y límites

| Aspecto | Resultado |
| --- | --- |
| Singles y sets | Carta V2: `id`, `name`, `set`, `number`, `rarity`, imágenes y precios opcionales; set: `id`, `name`, `series`, `printedTotal`, `total`, `releaseDate`, `updatedAt`. Son IDs externos. No hay evidencia de catálogo de sealed SKUs, cajas, ETB, stock, reservas o nuevas fichas retail. |
| ES / EN / región | Ejemplos y campos de carta en inglés. La fecha `releaseDate` de set es **de EE. UU.** según su referencia; no es fecha de España ni primera aparición. No se documentó cobertura de nombres de carta en español en las referencias revisadas. |
| Precios EUR y USD | `cardmarket` incorpora agregados EUR (`averageSellPrice`, `lowPrice`, `trendPrice`, ventanas 1/7/30 días, variantes foil); `tcgplayer` incorpora USD. Son datos derivados de marketplaces, no fuentes independientes. `lowPrice` no es venta realizada; `avg1/7/30` son agregados descritos como promedios de ventas, sin transacciones ni vendedor individual verificables desde la ficha. No incluyen de forma documentada envío, impuestos, disponibilidad española ni condición/idioma específico de cada ejemplar. |
| Variantes/condición | La referencia enumera `tcgplayer` por normal/holo/reverse/primera edición y agregados `cardmarket` foil/no foil; `lowPriceExPlus` incorpora umbral EX+. Esto no representa una ficha completa por idioma, condición y vendedor. Valores de precio pueden ser `null`. |
| Frescura e histórico | `set.updatedAt` y `cardmarket.updatedAt`/`tcgplayer.updatedAt` son marcas de actualización documentadas. `releaseDate` no es `first_seen_at`; éste tendría que observarlo CMT. Ventanas agregadas de precio no equivalen a histórico bruto retenible. Sin garantía de frescura futura tras deprecación. |
| Paginación | `page`, `pageSize` (máximo 250), `select`, `orderBy`, `q`; respuesta con `page`, `pageSize`, `count`, `totalCount`. No se probó acceso operativo. |

**Observado:** solo contenido de la documentación oficial; **cero solicitudes directas a `api.pokemontcg.io`** y ningún payload conservado. Las muestras JSON publicadas en la documentación son ejemplos del proveedor, no observaciones CMT.

**Inferencia para selección:** no basar P1a ni P2 en esta API por cierre de altas y fecha de fin. Si el usuario aporta más adelante una clave existente autorizada, podría estudiarse una transición temporal con fecha de retirada y sin asumir licencias de precios; eso requiere decisión nueva. La ruta alternativa de catálogo debe provenir de otra fuente.
