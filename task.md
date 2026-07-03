# Lista de Tareas - Menú de Categorías y Limpieza de Navbar

- [x] Modificar [index.html](file:///D:/bendito-taller-web-main/index.html) para remover el enlace de "Catálogo" y reestructurar la sección de categorías con el menú lateral rápido.
- [x] Modificar [catalogo.html](file:///D:/bendito-taller-web-main/catalogo.html) para remover el enlace de "Catálogo" del menú de navegación superior.
- [x] Modificar [videos.html](file:///D:/bendito-taller-web-main/videos.html) para remover el enlace de "Catálogo" del menú de navegación superior.
- [x] Modificar [carrito.html](file:///D:/bendito-taller-web-main/carrito.html) para remover el enlace de "Catálogo" del menú de navegación superior.
- [x] Realizar verificación de navegación y diseño responsivo en la página principal y secundarias.
- [x] Refinar el diseño del banner decorativo en `index.html` y `styles.css` para lograr un estilo profesional alineado con la imagen de referencia.
- [x] Reemplazar los corazones rosados por copos de nieve blancos en la tarjeta de categoría de Navidad (`.card-navidad`) en hover.
- [x] Reemplazar los corazones rosados por lunas y soles dorados giratorios en la tarjeta de categoría mística (`.card-mistico`) en hover.
- [x] Reemplazar los corazones rosados por velas y cruces en la tarjeta de categoría de Nichos (`.card-nichos`) en hover.
- [x] Reducir el margen de las lianas decorativas y el área de animación de las tarjetas a 12px de la orilla.
- [x] Utilizar la imagen real `img/ramas con hojas.png` para decorar el contorno interior de las tarjetas en hover.
- [x] Ajustar el `z-index` de las lianas decorativas a `4` para posicionar la imagen transparente por encima de los textos (`z-index: 3`).
- [x] Desplazar verticalmente la imagen de las lianas decorativas (`.card-inner::after`) hacia arriba por 5.5 cm (`margin-top: -5.5cm`) sin estirarla (`background-size: contain`).
- [x] Encoger la imagen decorativa superior un 20% verticalmente y estirarla un 20% más hacia los lados (scaleX(0.9216)/scaleY(0.768) inicial y scaleX(0.96)/scaleY(0.8) en hover) para cumplir con el tamaño deseado.
- [x] Tintar la imagen de las lianas decorativas en color blanco (#ffffff) usando filtros CSS (brightness(0) invert(1)).
- [x] Duplicar la imagen decorativa y utilizarla como espejo en la parte inferior (.category-card::after, margin-top: 5.5cm, scaleY(-1)), configurando las dimensiones a 12px, agrandando la escala un 200% (triple del tamaño) y estirándola un 20% más hacia los lados (scaleX(3.456)/scaleY(-2.88) inicial y scaleX(3.6)/scaleY(-3.0) en hover).
- [x] Actualizar el color primario de marca a #00B8A6 en variables y colores duros de styles.css.
- [x] Copiar y configurar la imagen de fondo CORAZONES 2.jpg para la tarjeta de Corazones en index.html and styles.css.
- [x] Crear el nuevo banner de puntos interactivos con color rosado empolvado, y respaldar comentando el banner original de ramas en index.html.
- [x] Transformar la imagen "logo en negro.jpg" en una versión de madera realista ("logo_madera.png").
- [x] Quitar el fondo del logo de madera y configurar iluminación frontal ("logo_madera_sin_fondo.png").
- [x] Reemplazar el GIF animado de la página principal en index.html por el logotipo de madera sin fondo.
- [x] Quitar/comentar las lianas/ramas decorativas de los cuadros principales de categorías en styles.css.
- [x] Desactivar los efectos y animaciones de iconos flotantes (corazones, velas, cruces, etc.) en hover en styles.css.
- [x] Quitar/comentar las transiciones de opacidad y color de fondo/bordes (.card-overlay y ::before) en hover en styles.css.
- [x] Procesar el fondo de las letras "fondo para letra.jpeg" a transparente y añadirlo como marco de fondo en las tarjetas (.card-content::before).
- [x] Estirar el marco del fondo de las letras (badge) un 40% horizontalmente (de 290px a 406px con background-size: 100% 100%).
- [x] Estirar el marco del fondo de las letras (badge) un 15% verticalmente (de 230px a 264px).
- [x] Cambiar el color del overlay de las tarjetas de categoría en styles.css del verde teal a verde oliva/caqui #97946B.
- [x] Ajustar la posición vertical del badge (top: calc(50% - 10px)) para centrarlo exactamente detrás del título de la categoría (h2).
- [x] Ocultar la leyenda "explorar colección" (.explore) de las tarjetas de categoría en styles.css.
- [x] Cambiar la imagen del badge de texto ("fondo_para_letra_transparent.png") por la nueva imagen "fondo letra.png" ubicada en D:\, copiándola a la carpeta img y actualizando styles.css.
- [x] Cambiar el color del overlay de las tarjetas de categoría en styles.css del verde oliva/caqui al color calipso claro (#50C8D8).
- [x] Centrar exactamente la nueva imagen del badge ("fondo_letra.png") de manera vertical (top: 50%) detrás de los textos de la categoría.
- [x] Cambiar el color del overlay de calipso degradado a color calipso plano (sólido con transparencia) en styles.css.
- [x] Crear un duplicado de pruebas del sitio copiado como index2.html y styles2.css para experimentar nuevos diseños de forma aislada.
- [x] Quitar el fondo calipso y de madera de los contenedores de tarjetas, y superponer la textura de madera semi-transparente y enmascarada dentro de la silueta del badge ("fondo_letra.png") en styles2.css.
- [x] Ajustar el color de los bordes del badge vintage (imagen de fondo) y del texto de las letras grandes (h2::after) al color café oscuro (#4b372d) que aparece en hover/active.
- [x] Copiar la imagen de rayas compartida como img/fondo_rayas.jpg y configurar .card-bg como un fondo uniforme (416px x 274px) centrado que sobrepasa el badge fondo_letra.png por 5px (~1.3mm) en sus cuatro lados en styles2.css.
- [x] Cambiar la tipografía de los títulos de las categorías (h2) a "Playfair Display", asignando el color café oscuro (#4b372d), aumentando el tamaño a 40px y añadiendo un borde blanco muy fino (2.5px) mediante superposición en styles.css y styles2.css.
- [x] Diseñar e implementar un toldo vintage a rayas (#B0BFAC y #95AB9E) con bordes festoneados/scallops en .main-navbar::before en styles.css y styles2.css (alargado ~0.5cm por parte a 80px de alto, y patrones escalados a 60px/120px), y ajustar scroll-margin-top a 160px en index.html e index2.html.




















- [x] Modificar `styles.css` y `styles2.css` para añadir estilos de `.nav-left`, `.categories-dropdown`, `.dropdown-btn`, `.dropdown-content`, `.dropdown-item`, `.search-bar-container`, `.search-btn` y sus respectivas reglas adaptativas (responsive).
- [x] Modificar `script.js` para actualizar `inicializarCategorias()`, implementar `toggleDropdown(e)`, `closeDropdown()`, `handleNavbarSearch()`, `triggerSearch()` y leer el parámetro `search` en `procesarParametrosURL()`.
- [x] Modificar `index.html` e `index2.html` para incorporar la nueva estructura del navbar con contenedor `.nav-left`, y quitar la barra lateral de categorías (`catalog-sidebar`).
- [x] Modificar `catalogo.html` para actualizar la estructura del navbar, quitar la barra lateral y remover el buscador redundante local.
- [x] Modificar `videos.html` y `carrito.html` para actualizar su estructura de navbar.
- [x] Verificar el correcto funcionamiento (población dinámica, búsqueda, redirecciones y diseño responsive en móvil/tablet).
- [x] Agregar un carrusel de imágenes autodeslizante de 480px de alto y 750px de ancho máximo sobre la cuadrícula de categorías en index.html e index2.html, con ajuste de imagen completo (object-fit: contain) y fácilmente ampliable en script.js.
- [x] Cambiar el color de fondo de los botones superiores "Bendito Taller" y "Carrito" al tono verde oscuro (#95AB9E) del toldo superior en styles.css y styles2.css.
- [x] Procesar la imagen "D:\fondo banner.jpeg" para atenuar las flores un 50% manteniendo el color de fondo exacto (guardado como img/fondo_banner.jpg).
- [x] Modificar styles.css y styles2.css para establecer la nueva imagen como fondo del banner de leyendas y desactivar el overlay de puntos (radial-gradient).
- [x] Agregar textura tipo algodón (paper_grain.svg) y pliegues de profundidad sutiles en la parte superior de 50px, e implementar un recurso SVG específico para las ondas inferiores (toldo_scallops_textured.svg) para aplicarles la textura y gradientes sin alterar la transparencia de la caída semicircular.
- [x] Reemplazar el toldo por la ilustración vintage compartida (img/toldo_vintage6_cropped.png), estirarlo al 100% de ancho de la barra y reducir su altura (60px escritorio, 45px tablet, 30px móvil) en styles.css y styles2.css, y sincronizar dynamic scroll-margin-top.
- [x] Promover todo el contenido y diseño experimental de styles2.css a styles.css para que index.html y todas las páginas tengan el nuevo diseño de tarjetas transparentes con badges elípticos de madera texturizada, y eliminar los archivos de prueba index2.html y styles2.css.
- [x] Optimizar la adaptabilidad y el diseño responsive en PC y celulares, aplicando escalabilidad por aspect-ratio a las tarjetas de categoría en pantallas <= 480px, ajustando fuentes y reduciendo el grid de videos a una sola columna para evitar cualquier desborde horizontal.
- [x] Cambiar la tipografía de los títulos de las categorías de 'Playfair Display' a 'Merriweather' en los archivos index.html, catalogo.html y styles.css.
- [x] Cambiar el color de fondo del banner de leyendas a #E6BDB3 y re-procesar la imagen de fondo con flores atenuadas sobre este nuevo tono.
- [x] Reducir las dimensiones de las imágenes del badge vintage (fondo_letra.png) un 15% (de 406x264px a 345x224px) y adaptar el diseño responsive.
- [x] Rediseñar la barra de navegación para celulares: ocultar el botón 'Bendito Taller', colocar 'Categorías' en su lugar como botón verde, centrar la lupa, y posicionar el carrito a la derecha.
- [x] Reducir las dimensiones de las imágenes del badge vintage (fondo_letra.png) un 15% adicional específicamente en la vista de celulares (ancho de 95% a 80% y max-width a 293px).
- [x] Cambiar el color del borde interior delgado del badge vintage (fondo_letra.png) a #E6BDB3 manteniendo el borde exterior grueso en café (#4b372d).
- [x] Remover por completo la animación de brillo (halo de luz/destello) del badge vintage en todas las vistas de pantalla por solicitud del usuario.
- [x] Agregar animación profesional y sutil de aura pulsante (badgeGlowPulse) en el drop-shadow del badge vintage (usando el color del borde interior #E6BDB3) al hacer hover.
- [x] Implementar destello metálico profesional (shimmer sweep) sobre el contenedor independiente .card-inner::after (con máscara de exclusión de centro, opacidad más tenue de 0.6, y velocidad extra lenta de 8.8s) para brillar solo en los bordes y evitar desalineaciones en hover.
- [x] Cambiar el color de la línea decorativa (.divider) que se expande bajo las categorías de verde teal a dorado (#FFBF00).
- [x] Acomodar las imágenes ramita.png y ramita1.png de D:\ en el banner rosado (.dots-banner-container) como decoración lateral simétrica con animaciones de balanceo (sway).
- [x] Hacer más transparentes las imágenes "ramita.png" y "ramita1.png" al menos un 50% (opacidad de ramita.png a 0.3, ramita1.png a 0.25 y hover a 0.5) y sincronizar los cambios.
- [x] Ajustar las ramas decorativas en la vista de celulares para mostrar una a cada lado con la misma transparencia, reduciendo su tamaño y re-centrando el texto del banner.
- [x] Separar las imágenes decorativas laterales (ramas) por al menos 1 cm (en desktop, tablet y móviles) para evitar que se superpongan entre ellas o choquen visualmente en el centro.
- [x] Separar las ramas 1 cm adicional hacia los lados y girarlas 90° (verticales) con animaciones de balanceo adaptadas.
- [x] Girar las ramas 180° grados en la dirección contraria (a -90°, apuntando hacia abajo) en la hoja de estilos y sincronizar.
- [x] Reemplazar las imágenes "ramita.png" y "ramita1.png" por la imagen "tapiz ramitas.png" en index.html y sincronizar.
- [x] Unir/pegar las ramas a los bordes del banner (left: 0) y aumentar su transparencia un 30% adicional (base 0.2, hover 0.35).
- [x] Girar las ramas horizontalmente (cenefa) a lo largo de todo el ancho del banner (arriba y abajo), estirando la imagen y adaptando el diseño responsivo.
- [x] Quitar todo el fondo del banner, eliminar los ajustes de ramas flotantes/cenefas, y usar la imagen "tapiz ramas largo.png" como fondo en index.html y styles.css.
- [x] Aplicar un 70% de transparencia (opacidad 0.3) exclusivamente al fondo "tapiz ramas largo.png" del banner en styles.css.
- [x] Hacer la imagen "tapiz ramas largo.png" un 50% más transparente (opacidad 0.15 / 85% de transparencia) en styles.css.
- [x] Hacer la imagen "tapiz ramas largo.png" un 50% más transparente adicional (opacidad 0.075 / 92.5% de transparencia) en styles.css.
- [x] Configurar el color de fondo del banner a #DDB6A8 manteniendo la transparencia del tapiz de ramas superior en styles.css.
- [x] Contraer la imagen "tapiz ramas largo.png" a 90px de alto y habilitar repetición horizontal para mayor definición y menor escala en styles.css.
- [x] Estirar la imagen de fondo "tapiz ramas largo.png" un 10% (de 90px a 99px de alto) en styles.css.
- [x] Estirar la imagen de fondo "tapiz ramas largo.png" un 20% más (de 99px a 119px de alto) en styles.css.
- [x] Recortar los bordes superior e inferior del banner en 1 cm (reduciendo el padding vertical de 40px/30px a 10px y min-height de 180px a 120px) en styles.css.
- [x] Recortar los bordes superior e inferior del banner en 1 cm adicional en la vista de celulares (reduciendo el padding de dots-banner-content a 0 y dots-banner-container a 4px 16px) en styles.css.
- [x] Configurar animación de iluminación en hover (transition: opacity 0.4s y opacity: 0.22) para que el tapiz de fondo brille al pasar el mouse por encima del banner en styles.css.
- [x] Acortar el espacio vertical arriba y abajo del logo principal (recortando los márgenes del archivo logo_madera_sin_fondo.png a 781x820px, y reduciendo el padding de la sección hero-section de 40px a 10px y la altura de la imagen a 340px) en index.html.
- [x] Cambiar los subtítulos/textos emergentes (.subtitle) en las tarjetas de categorías principales de index.html para que aparezcan debajo de los títulos principales (h2), agregando además margin-bottom: 6px a h2 en styles.css para mantener una separación simétrica.
- [x] Evitar que los títulos principales (h2) de las tarjetas de categorías suban al hacer hover y mantenerlos siempre en el centro vertical exacto del badge (removiendo margin-bottom de h2, posicionando .subtitle y .divider de forma absoluta a top: calc(50% + 28px) y calc(50% + 56px), y quitando translateY(-6px) en hover) en styles.css.
- [x] Cambiar los textos del cuadro principal de "Mexicanos y Calacas" en index.html, reemplazando el título "MEXICANOS" por "CALACAS" y el subtítulo "Tradición" por "y mexicanos".
- [x] Cambiar el subtítulo del cuadro principal de "Grabados" en index.html, reemplazando "Personalizados" por "estilo mexicanos".
- [x] Cambiar el subtítulo del cuadro principal de "Alados" en index.html, reemplazando "Alas de amor" por "diseños variados".
- [x] Cambiar el subtítulo del cuadro principal de "Nichos" en index.html, reemplazando "Especiales" por "tipo mexicanos".
- [x] Cambiar el subtítulo del cuadro principal de "Grabados" en index.html, reemplazando "estilo mexicanos" por "infantiles y más".
- [x] Cambiar el subtítulo del cuadro principal de "Navidad" en index.html, reemplazando "Temporada" por "todo el año".
- [x] Cambiar el subtítulo del cuadro principal de "DECO" en index.html, reemplazando "Decoración" por "originales y creativas".
- [x] Cambiar el subtítulo del cuadro principal de "STENCILS" en index.html, reemplazando "Pintura" por "creaciones propias".
- [x] Cambiar el subtítulo del cuadro principal de "MÍSTICO" en index.html, reemplazando "Energía" por "energía y conexión".
- [x] Cambiar el título del cuadro principal de "INSUMOS" a "COMPLEMENTOS" y su subtítulo de "Para crear" a "para tus proyectos" en index.html.
- [x] Cambiar el subtítulo del cuadro principal de "LIBROS 3D" en index.html, reemplazando "Tres dimensiones" por "fantasía y encanto".
- [x] Cambiar el título del cuadro principal de "COMPLEMENTOS" de vuelta a "INSUMOS" y su subtítulo de "para tus proyectos" a "complementarios" en index.html.
- [x] Cambiar el subtítulo del cuadro principal de "Nichos" en index.html, reemplazando "tipo mexicanos" por "estilo mexicanos".
- [x] Configurar los subtítulos (.subtitle) y divisores (.divider) en styles.css para estar siempre visibles y activos por defecto (opacity: 1 y scaleX(1)) en lugar de aparecer únicamente en hover.
- [x] Copiar la imagen "FONDO NICHOS.jpg" de D:\ a img/FONDO_NICHOS.jpg y aplicarla como textura de fondo del badge de letras en la tarjeta de Nichos (.card-nichos .card-content::after) en styles.css.
- [x] Copiar la imagen "fondo deco (2).jpg" de D:\bendito taller\CATALOGO LORE\fondo\fondo deco a img/fondo_deco_2.jpg y aplicarla como textura de fondo del badge de letras en la tarjeta de DECO (.card-deco .card-content::after) en styles.css.
- [x] Cambiar el subtítulo del cuadro principal de "DECO" en index.html, reemplazando "originales y creativas" por "creativa".
- [x] Ajustar la posición vertical de los subtítulos (.subtitle) y divisores (.divider) en styles.css para la vista de celular (@media (max-width: 480px)) a top: calc(50% + 18px) y calc(50% + 34px) para subirlos y hacer la composición más compacta y armónica.
- [x] Copiar la imagen "FONDO NAVIDAD.jpg" de D:\bendito taller\CATALOGO LORE\fondo\fondo navidad a img/FONDO_NAVIDAD.jpg y aplicarla como textura de fondo del badge de letras en la tarjeta de Navidad (.card-navidad .card-content::after) en styles.css.
- [x] Agrandar la imagen del toldo (.main-navbar::before) horizontalmente un 66% más (de 180% a 300% de background-size) en styles.css para la vista de celular/móvil (@media (max-width: 768px)) para que las líneas se vean más anchas.
- [x] Dividir la cuadrícula de categorías en index.html en tres bloques separados para intercalar los banners horizontalmente y ajustar espaciados (padding vertical).
- [x] Repetir el banner rosado debajo de los cuadros "nichos" y "calacas" con la frase "Ventas al detalle y al por mayor" en index.html.
- [x] Repetir el banner rosado debajo de los cuadros "navidad" y "stencils" con la frase "Productos complementarios para tus proyectos" en index.html.
- [x] Repetir el banner debajo de la tarjeta de "Libros 3D" con información sobre pedidos por Instagram y un botón de enlace interactivo con icono SVG.
- [x] Achicar las letras y el botón de enlace de los banners agregados en la vista de celulares (@media (max-width: 480px)) para mejorar la legibilidad y composición.
- [x] Unificar la altura (min-height) del segundo y tercer banner agregado recientemente mediante la clase .tall-banner y reglas adaptativas en CSS.
- [x] Reemplazar el icono de camión por los logos de Blue Express, Starken y Correos de Chile en el cuadro de "Envíos a Todo Chile" en index.html y catalogo.html, consolidando además los estilos CSS compartidos.
- [x] Mover el título "Explora Nuestras Categorías" dentro del primer banner interactivo superior de la página principal, posicionándolo bajo el texto descriptivo.
- [x] Sincronizar todos los archivos modificados con los repositorios Git locales (bendito-taller-carrito y bendito-taller-web).
- [x] Ajustar el alto del segundo banner agregado recientemente ("Productos complementarios para tus proyectos") para que coincida exactamente con la altura del primer banner, removiendo la clase ".tall-banner" en index.html.
- [x] Ajustar el alto del tercer banner ("Si tienes alguna duda o deseas hacer un pedido...") para que coincida con el primer banner, y posicionar el botón de Instagram al final de la leyenda (flex row) en index.html y styles.css.
- [x] Copiar las imágenes de logotipos de envío a color (logo_starken.png, Logo-Blue.png y correos-chile-logo.jpg) de D:\ a la carpeta img del proyecto y actualizar el diseño de la tarjeta de envíos (Starken/Blue Express en fila, Correos de Chile abajo al centro) en index.html, catalogo.html y styles.css.
- [x] Engranar y agrandar un poco el logo de Correos de Chile tanto en escritorio (a 42px de alto) como en celulares (a 34px de alto) en styles.css para un mejor balance visual.
- [x] Agrandar los logos de Starken y Blue Express un 20% (38px de alto en PC y 29px en celulares), e integrar la nueva imagen horizontal "correos-chile-logo1.jpg" para Correos de Chile (ajustada a 38px en PC y 29px en celulares) en index.html, catalogo.html y styles.css.
- [x] Actualizar la frase del cuadro de envíos reemplazando "cotización" por "pedido" y borrando la palabra "rápidamente" en index.html y catalogo.html.
- [x] Unificar la altura de los dos primeros banners repetidos ("Ventas al detalle..." y "Productos complementarios...") en la vista móvil de celular a una altura mínima de 80px (y 90px en tablet) en styles.css.
- [x] Eliminar la leyenda estática del inicio de catalogo.html e implementar un banner dinámico de categoría (#categoryHeaderBanner) en script.js, catalogo.html y styles.css, que muestra el título y subtítulo dentro de la silueta del badge vintage de madera sobre la imagen de fondo de cada categoría específica.
- [x] Agrandar un 50% la silueta de madera (a 435x240px) y las fuentes (título a 42px, subtítulo a 16px) del badge del banner de categorías en styles.css sin modificar la altura del banner contenedor (200px) y habilitando overflow visible para un efecto flotante 3D.
- [x] Evitar que la silueta y las letras sobresalgan del banner de categorías, configurando overflow: hidden y ajustando la altura de la silueta a la medida exacta del banner (200px en escritorio, 160px en móvil) en styles.css.
- [x] Tintar la silueta completa del badge vintage (`img/fondo_letra.png`) de color verde salvia mediante una máscara de CSS (`mask-image`) y `mix-blend-mode: multiply` en `.category-banner-badge::after`, eliminando el recuadro rectangular de fondo en `.category-banner-badge-inner`.
- [x] Evitar la deformación o estiramiento de las imágenes de fondo en el banner de categorías (`.category-header-banner`) mediante el uso del tamaño real de la foto (`background-size: auto`) y repetición completa en mosaico (`background-repeat: repeat`) tanto en escritorio como en móvil.
- [x] Eliminar el margen vertical superior del catálogo (`padding-top: 0px` en `#catalog-section`) en catalogo.html para posicionar el banner de categorías pegado a la barra de navegación que contiene el botón de carrito.
- [x] Habilitar la visualización ampliada de fotos de productos mediante el clic en su imagen en la grilla: se creó la función `abrirImagenGrande(id)` en script.js, se configuró el cursor interactivo en `.product-img-wrapper` en styles.css, y se diseñó una interfaz modal centrada con la foto a gran escala, título del producto y botón "Volver" verde salvia.
- [x] Copiar el archivo de textura `textura papel.png` de D:\ a la carpeta local img como `textura_papel.png`, y definirlo como el fondo (`background-image`) de los cuadros de características (`.feature-card`) en styles.css.
- [x] Copiar el archivo de textura `fondo cuaros blancos.jpeg` de D:\ a la carpeta local img como `fondo_cuadros_blancos.jpeg`, y definirlo como el fondo translúcido (`opacity: 0.55` en pseudo-elemento `::before`) de los cuadros de características (`.feature-card`) en styles.css.
- [x] Incrementar la translucidez del fondo de las tarjetas de características `.feature-card::before` reduciendo la opacidad a `0.35` (35% de opacidad) en styles.css para optimizar la legibilidad y contraste del texto y logotipos.
- [x] Copiar las imágenes `fondo cuaros blancos1.jpeg` y `fondo cuaros blancos2.jpeg` desde D:\ a la carpeta local img como `fondo_cuadros_blancos1.jpeg` y `fondo_cuadros_blancos2.jpeg`, y aplicarlas de forma selectiva a cada tarjeta de características (tarjeta 1: fondo_cuadros_blancos.jpeg, tarjeta 2: fondo_cuadros_blancos1.jpeg, tarjeta 3: fondo_cuadros_blancos2.jpeg) en styles.css usando selectores :nth-child.
- [x] Implementar redirección de retorno a Google Sites para el flujo activo: se configuró la bandera `fromSites` en `sessionStorage` en add.html, y se adaptaron cerrarPopup() y agregarProducto() en script.js, así como volverCatalogo() en carrito.html para redirigir a https://www.benditotaller.cl/ en lugar del nuevo index.html cuando la bandera esté activa.
- [x] Perfeccionar redirección de retorno en producción usando la ruta directa de Google Sites y seguimiento de referrer original (`referrerSites` en `sessionStorage`) en add.html, script.js y carrito.html para resolver el error DNS ERR_ADDRESS_UNREACHABLE en celulares y regresar incondicionalmente a Google Sites al pulsar "Volver al catálogo".
- [x] Corregir la URL fallback de Google Sites a `https://sites.google.com/view/bendito-taller/p%C3%A1gina-principal` (añadiendo el guión medio faltante) y adaptar las condiciones de coincidencia de referrer en add.html, script.js y carrito.html.
- [x] Resolver la redirección prematura del selector al iniciar: se cambiaron las llamadas del sistema de `cerrarPopup()` por `cerrarPopupSilencioso()` en abrirSelectorProducto() y abrirImagenGrande() dentro de script.js, asegurando que el modal no se cierre automáticamente tras 2 segundos al entrar y permitiendo al usuario elegir variantes y presionar botones con tranquilidad.
- [x] Unificar el diseño de tabla de precios (measures-list-layout) en todos los productos (simples y multimedidas), usando "Única" para la medida por defecto en productos simples, y borrar la leyenda "(4+)" de todos los títulos de columnas de precios de la web.
- [x] Integrar especificaciones de productos desde `productos_detalles.xlsx`: se procesó el archivo Excel para extraer las columnas de descripción y medida de cada producto por código, se insertaron estáticamente en `productos.js`, y se adaptaron las tarjetas de productos (renderCatalog) y el selector modal (abrirCompraModal) en `script.js` y `styles.css` para mostrar código, detalles y medida de forma alineada y compatible con móviles.
- [x] Intercambiar tamaños de letras en las tarjetas de productos: se modificó `styles.css` para aplicar un tamaño de 13px (11px en móvil) al código del producto (`.product-title`), y se aumentaron a 16px (13px en móvil) los subtítulos/detalles (`.product-desc`), los precios (`.price-row` / `.measure-price-row`) y el botón "Lo quiero" (`.product-action-btn`).
- [x] Agrandar los cuadros de productos y juntarlos: se modificó `.products-grid` en `styles.css` para reducir el espacio (gap) de `20px` a `12px` (y de `0.5cm` a `10px` en móvil) y aumentar la anchura mínima del producto de `210px` a `240px`, logrando tarjetas más amplias y con mayor espacio horizontal para los textos.
- [x] Renombrar columna de precios "Unitario" a "Unidad": se modificaron los encabezados de las tablas de precios en `script.js` para usar la etiqueta "Unidad", optimizando el espacio horizontal en las tarjetas de productos.
- [x] Remover columnas redundantes de "Medida" en productos simples: se reestructuró la visualización de precios para productos tipo `simple` en `script.js` y `styles.css` empleando una tabla de 2 columnas (Mayor y Unidad) sin la columna "Medida" ni la celda "Única", dado que la medida real ya se muestra arriba en la etiqueta de color verde.
- [x] Achicar códigos y agrandar subtítulos (detalles): se modificó `styles.css` para reducir en 2px el tamaño de los códigos (`.product-title` pasa de 13px a 11px en desktop, y de 11px a 9px en móvil) y aumentar en 1px los subtítulos/detalles (`.product-desc` pasa de 16px a 17px en desktop, y de 13px a 14px en móvil).
- [x] Probar nueva imagen de toldo en vista móvil: se copió `D:\TOLDO NUEVO.jpg` a la carpeta local del proyecto como `img/toldo_nuevo.jpg` y se configuró en `styles.css` como la imagen de fondo para `.main-navbar::before` dentro de la media query móvil con un `background-size: 100% 100%`.
- [x] Ajustar altura de toldo móvil a 70px: se modificó la altura del toldo a 70px en `styles.css` y se incrementó el scroll-margin-top de `#catalog-section` a 180px para prevenir superposiciones.
- [x] Recortar rodillo y soportes de toldo_nuevo.jpg: se programó un script en Python para recortar los bordes superior y laterales (rollers/pipe) de `toldo_nuevo.jpg`, logrando que la lona a rayas ocupe el 100% del ancho tal como se muestra en la captura de referencia `fe6afdcd-df76-4a53-a707-e576164fc5b3.jpg`.
- [x] Convertir toldo_nuevo.jpg a toldo_nuevo.png transparente: se utilizó un script en Python para aplicar un algoritmo de flood-fill y remover el fondo blanco bajo las ondas festoneadas, cargándolo en `styles.css` como PNG para que se mezcle con el color de la barra.



















