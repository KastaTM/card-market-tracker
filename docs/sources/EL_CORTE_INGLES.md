# El Corte Inglés — ficha de viabilidad retail

**Consulta:** 2026-10-07 (Europe/Madrid). **Clase:** `CONDITIONAL`; valor de catálogo observado, integración sin autorización. **Método:** lectura de categoría, fichas y enlace legal de la tienda principal; sin GET exploratorio directo. **Probe:** 0/5 solicitudes.

## Referencias primarias y hechos

- **Observado — tienda pertinente:** la [categoría Pokémon/Juguetes](https://www.elcorteingles.es/pokemon/juguetes/) mostró cajas y sobres JCC entre otros juguetes. La [ficha de caja Mega-Greninja ex](https://www.elcorteingles.es/juguetes/A200971037-caja-pokemon-mega-greninja-ex-jcc-pokemon-bandai/) muestra referencia `001044850503937`, EAN `0196214141995`, modelo `PC10413`, caja de ocho sobres y etiqueta «Exclusivo». La misma ficha muestra límites de compra **contradictorios** (máximo 3 y máximo 1): no normalizar ninguno como regla estable sin aclaración. La [ficha de sobre Juntos de Aventuras](https://www.elcorteingles.es/juguetes/A200971013-sobre-cartas-pokemon-expansion-juntos-de-aventuras-pokemon-bandai-modelos-surtidos/) indica `Producto surtido`, referencia `001044850503903`, EAN `0196214107182` y entrega de una variante según existencias; EAN/referencia no identifican la variante concreta.
- **Documentado — condiciones aplicables:** el pie de la tienda principal enlaza a [Condiciones de uso](https://cuenta.elcorteingles.es/condiciones-de-uso/), pero el contenido no fue legible mediante la herramienta de consulta (página sin texto extraíble). **No se aplican por analogía** los [términos del supermercado](https://www.elcorteingles.es/supermercado/ayuda/es/terminos-legales/) a la tienda de juguetes; ese subservicio sí restringe explícitamente robots y extracción, pero no resuelve el contrato de esta ficha. No se identificó permiso de API o monitorización para juguetes.
- **Inferido:** la ficha se presenta en el canal propio de El Corte Inglés; no se observó oferta Marketplace en las fichas revisadas. No se generaliza a todas las referencias. `Exclusivo` es etiqueta comercial, no prueba de lanzamiento, autenticidad de stock o derechos de datos.

## Cobertura y límites

| Dimensión | Conclusión |
| --- | --- |
| Singles / sealed | Se observaron sobres y cajas sellados; no cobertura de singles individuales. Las cartas incluidas no equivalen a listings de singles. |
| España, UE, idioma, EUR | Tienda y fichas en español, mercado español. No se extrajo precio de las fichas consultadas ni se confirmó divisa, impuestos, portes o cobertura UE para esos artículos; no extrapolar. |
| Precio / stock | «Añadir a la cesta» aparece en la representación textual, pero no confirma stock ni precio final por destino. No se observó oferta numérica fiable. |
| Nuevo listing, preventa, coming soon | Ninguna de esas señales quedó verificada para Pokémon TCG. La página de categoría carece de fecha de alta visible; `first_seen_at` sería observación propia autorizada. |
| IDs, variante, condición | Referencia, modelo, EAN y surtido en fichas. Sin condición de carta, variante efectiva ni identidad canónica. |
| Paginación, frescura, histórico | No verificados; no se observó API pública, cuota, tarifa de datos o SLA. |
| Retención, redistribución | No se pudo confirmar licencia de extracción o almacenamiento de listado/precios de la tienda principal; tampoco permiso para redistribuir texto, imágenes o histórico. |

## Decisión de probe y riesgo

**Sin probe:** la pregunta era si un GET limitado puede descubrir nuevas referencias Pokémon de la tienda principal. Como las condiciones enlazadas no fueron legibles y no hay autorización clara, se evitó el GET técnico. No se efectuaron solicitudes directas, no hay estado HTTP/tamaño/campos de probe y no se guardó payload. No se usó una política de otro subdominio como sustituto contractual.

**Riesgos:** condiciones no verificadas, categoría que mezcla JCC con juguetes ajenos, producto surtido mal identificado, límite de compra contradictorio, precio/portes/stock no observados y cambios de página. **Próximo paso condicionado:** obtener texto vigente de condiciones de la tienda principal o autorización escrita de El Corte Inglés para acceso, frecuencia, retención y uso; solo entonces plantear probe. **AC-F05 retail:** no satisfecho por El Corte Inglés.
