# Fnac España — ficha de viabilidad retail

**Consulta:** 2026-10-07 (Europe/Madrid). **Clase:** `CONDITIONAL` para integración de datos; semántica comercial `DOCUMENTED_ONLY`. **Método:** revisión de condiciones, ayuda y ficha oficiales; sin GET exploratorio directo. **Probe:** 0/5 solicitudes porque no consta permiso para explotación automatizada y retención.

## Referencias primarias y hechos

- **Documentado — licencia:** las [condiciones generales de Fnac.es](https://www.fnac.es/condiciones-generales-fnac-es) reservan los derechos sobre contenido y prohíben explotar, reproducir, distribuir o usar el contenido de la web con fines comerciales sin autorización expresa. Tampoco documentan API abierta, cuotas, licencia de conservación o redistribución para CMT. No se deduce autorización de automatización de la mera navegación pública.
- **Documentado — ofertas:** [Fnac explica su Marketplace](https://www.fnac.es/criterios-de-clasificacion): una misma ficha puede reunir oferta Fnac y ofertas de vendedores asociados; la transacción de terceros es con el vendedor, no con Fnac. La [ayuda de disponibilidad](https://www.fnac.es/ayuda?question=como-comprobar-online-si-un-producto-esta-disponible-en-la-tienda-139275) distingue compra online, tienda física y Marketplace. Por tanto, vendedor, condición, precio, stock y envío pertenecen a la **oferta**, no solo al producto.
- **Documentado — precio y logística:** las [condiciones](https://www.fnac.es/condiciones-generales-fnac-es) indican precios web con impuestos indirectos incluidos y gastos de envío/gestión separados, calculados según destino y modalidad. El stock web puede agotarse durante la compra. `En stock Fnac.es`, `bajo pedido`, `preventa` y `no disponible` tienen significados distintos; una preventa depende del cupo del proveedor y no garantiza entrega. Las [opciones de envío](https://www.fnac.es/ayuda?question=que-tipos-envio-a-domicilio-ofrece-fnac-cuales-los-plazos-entrega) diferencian la venta propia y el Marketplace, y señalan que Fnac no realiza envíos internacionales desde su canal propio.
- **Observado — sealed:** la [ficha de caja Pokémon Arceus](https://www.fnac.es/Caja-coleccion-Bandai-Pokemon-con-figura-Arceus-Juegos-de-mesa-Juego-de-cartas/a9032111) muestra SKU `1983707`, EAN `0820650503085`, producto sellado con sobres y estado `Agotado` / `No disponible en tienda` en la lectura. Esa ficha no acredita precio actual ni oferta comprable. Una opinión que dice «vendido por Fnac» es testimonio histórico de usuario, no vendedor actual verificable.
- **Inferido:** SKU/EAN son pistas para conciliación; un EAN puede cubrir un surtido o distintas ofertas, por lo que no es identidad canónica. Un listado nuevo exigiría comparar primeras observaciones propias autorizadas; Fnac no expone aquí un `first_seen_at` estable.

## Cobertura y límites

| Dimensión | Conclusión |
| --- | --- |
| Singles / sealed | Caja sellada observada. No se verificó cobertura sistemática de singles ni condiciones de carta. |
| España, UE, idioma, EUR | Sitio español, textos en castellano, tarifas en EUR. No extrapolar envío propio a toda la UE; terceros tienen condiciones propias. |
| Precio | Oferta publicada, con impuesto indirecto según condiciones; no es venta realizada, MSRP ni valor de mercado. Portes dependen de oferta/destino/método. |
| Stock / preorder / coming soon | La tabla de condiciones da semántica de estados; no se observó una preventa Pokémon activa ni etiqueta genérica *coming soon*. Separar online, tienda y tercero. |
| SKU / variantes / frescura / paginación | SKU y EAN en ficha puntual. No se validaron paginación, frecuencia, fechas de alta, histórico, variantes ni sincronía Marketplace. |
| Acceso / coste / retención | Lectura manual pública; sin credenciales ni coste de consulta documentado. Derecho de automatización, cuotas, almacenamiento histórico y redistribución no concedidos. |

## Decisión de probe y riesgo

**Sin probe:** la pregunta era si un GET acotado puede distinguir oferta Fnac de tercero y capturar un nuevo sealed/preventa. Las condiciones no autorizan la explotación de contenidos requerida para un monitor histórico; tampoco hay mecanismo documentado para repetición/retención. No se hicieron llamadas directas ni se guardó payload de catálogo; no existen códigos HTTP o tamaños de respuesta de probe. Hace falta autorización expresa para avanzar.

**Riesgos:** confundir Marketplace con venta propia; mezclar ofertas con condiciones/envíos distintos; deducir `AVAILABLE` de una ficha agotada; considerar bajo pedido como stock; tomar precio sin portes como coste; reseñas antiguas como evidencia actual; variación por domicilio/socio. **Próximo paso condicionado:** acordar acceso y licencia con Fnac, especificando tratamiento separado de oferta propia y tercero, frecuencia, retención y redistribución. **AC-F05 retail:** no satisfecho por Fnac.
