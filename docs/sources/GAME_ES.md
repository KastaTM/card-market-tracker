# GAME España — ficha de viabilidad retail

**Consulta:** 2026-10-07 (Europe/Madrid). **Clase:** `CONDITIONAL` para integración; catálogo público solo como evidencia documental. **Método:** lectura de páginas oficiales mediante navegador/buscador, sin GET exploratorio directo ni extracción automatizada. **Probe:** 0/5 solicitudes; no se obtuvo autorización inequívoca para monitorización automatizada.

## Referencias primarias y hechos

- **Documentado — condiciones:** el [aviso legal de GAME](https://www.game.es/informacion-legal) regula `www.game.es`; atribuye la condición de usuario al acceder y exige respetar restricciones de copia, distribución y explotación de contenidos. No concede licencia de API, retención de listas de productos/precios ni redistribución. El portal puede cambiar o interrumpirse sin aviso. La información obtenida no se puede comercializar o divulgar de cualquier modo según sus condiciones.
- **Observado — catálogo:** la [categoría de cartas Pokémon](https://www.game.es/Pokemon-cartas-coleccionables) y la [ficha de una caja sellada](https://www.game.es/coleccionables/cartas-pokmon/merchandising/caja-ultra-premium-de-cartas-pokemon-30-aniversario-castellano-surtido/266954) muestran un producto con código GAME `266954`, idioma castellano, variante *surtida*, fecha de lanzamiento 6-11-2026, precio mostrado en EUR y estado `PRÓXIMAMENTE`, junto a «Avísame cuando esté disponible en web». Esto acredita que una ficha pública puede mostrar *coming soon*; no acredita reserva aceptada, disponibilidad ni estabilidad del campo. La variante surtida implica que un SKU no identifica la variante recibida.
- **Inferido:** GAME vende como retailer propio en esa ficha; no apareció una oferta de vendedor tercero en la página consultada. No se generaliza a todo su catálogo. El código de producto puede servir como identificador externo, nunca como identidad canónica CMT.

## Cobertura y semántica para CMT

| Dimensión | Evidencia y límite |
| --- | --- |
| Singles / sealed | Se observaron cajas y sobres sellados; no se acreditó catálogo de singles individuales ni variantes/condición de cartas. |
| España, Europa, idioma, EUR | Portal español y ficha en castellano con EUR. Cobertura de envíos fuera de España y precio efectivo por destino: no verificados. |
| Precio, impuestos, envío | Precio visible de oferta retail; no es precio de venta realizada, MSRP ni referencia de mercado. Impuestos y portes finales no comprobados; no calcular coste de adquisición con precio de ficha únicamente. |
| Stock y ciclo | `PRÓXIMAMENTE` + aviso no equivale a compra, reserva ni stock. Una ficha con fecha de lanzamiento no da fecha de primera aparición. `first_seen_at` tendría que ser una observación propia autorizada. |
| SKU, paginación, frescura, histórico | Código externo visible en ficha. No se verificaron paginación, SLA de actualización, histórico ni semántica estable de resultados de búsqueda. |
| Acceso, coste, cuotas | Páginas visibles sin credenciales en lectura manual. No se halló API pública ni cuota/tarifa de uso de datos autorizada para CMT. |
| Retención y redistribución | No hay permiso documentado para guardar un histórico de ofertas, copiar descripciones/imágenes o republicar contenido. Requiere acuerdo/licencia específica. |

## Decisión de probe y riesgo

**Sin probe:** la cuestión era si existe una vía permitida de GET para detectar nuevos SKUs y cambios de precio/stock. El aviso legal no la autoriza y restringe explotación de contenido; un HTTP 200 no resolvería el derecho a conservar ni repetir observaciones. No se hicieron llamadas directas, no hay URL/status/tamaño/fields de probe y no se guardaron payloads. `robots.txt` tampoco sería una autorización.

**Riesgos:** dependencia de HTML cambiante; restricciones de acceso/licencia; precio visible sin portes; `PRÓXIMAMENTE` confundido con preorder; variantes surtidas mal emparejadas; disponibilidad de web distinta de tienda; comentarios de usuarios no confiables. **Próximo paso condicionado:** obtener autorización escrita de GAME que cubra acceso, frecuencia, almacenamiento mínimo, retención y uso; después diseñar un probe acotado y revisar condiciones actuales. **AC-F05 retail:** no satisfecho por GAME.
