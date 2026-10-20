// Estado Global
let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
let categoriaActiva = "all";
let busquedaActual = "";
let productoActual = null;
let opcionPreseleccionada = "";

// Cargar categorías en el dropdown superior al inicializar
function inicializarCategorias() {
    const dropdownContent = document.getElementById("categoriesDropdownContent");
    if (!dropdownContent) return;
    
    dropdownContent.innerHTML = "";
    
    // Opción para "Todas las categorías"
    const allBtn = document.createElement("a");
    allBtn.className = "dropdown-item";
    allBtn.id = "dropdown-btn-all";
    allBtn.href = "#";
    allBtn.innerHTML = "📋 Todas las categorías";
    allBtn.onclick = (e) => {
        e.preventDefault();
        setCategory("all");
        closeDropdown();
    };
    dropdownContent.appendChild(allBtn);

    // Generar enlaces para cada categoría del CATEGORIAS_MAP
    Object.entries(CATEGORIAS_MAP).forEach(([key, label]) => {
        const item = document.createElement("a");
        item.className = "dropdown-item";
        item.id = `dropdown-btn-${key}`;
        item.href = "#";
        
        // Asignar iconos amigables para cada categoría
        let icon = "📦";
        if (key === "corazones") icon = "❤️";
        else if (key === "corazones-alados") icon = "👼";
        else if (key === "nichos-y-altares") icon = "🏛️";
        else if (key === "mexicanos-y-calacas") icon = "💀";
        else if (key === "grabados") icon = "✏️";
        else if (key === "navidad") icon = "🎄";
        else if (key === "deco") icon = "🏡";
        else if (key === "stencil") icon = "🎨";
        else if (key === "mistico-y-mas") icon = "🕉️";
        else if (key === "libros-3d") icon = "📚";
        else if (key === "pascua") icon = "🐰";
        
        item.innerHTML = `${icon} ${label}`;
        item.onclick = (e) => {
            e.preventDefault();
            setCategory(key);
            closeDropdown();
        };
        dropdownContent.appendChild(item);
    });
}

// Control del Dropdown de Categorías
function toggleDropdown(e) {
    e.stopPropagation();
    const content = document.getElementById("categoriesDropdownContent");
    if (content) {
        content.classList.toggle("show");
    }
}

// Función para cerrar el dropdown
function closeDropdown() {
    const content = document.getElementById("categoriesDropdownContent");
    if (content) {
        content.classList.remove("show");
    }
}

// Cerrar al hacer click fuera del dropdown
window.addEventListener("click", (e) => {
    if (!e.target.closest(".categories-dropdown")) {
        closeDropdown();
    }
});

// Establecer categoría activa y volver a renderizar
function setCategory(catKey) {
    // Si no estamos en la página del catálogo (no existe el productsGrid), redirigimos
    if (!document.getElementById("productsGrid")) {
        if (catKey === "all") {
            window.location.href = "catalogo.html";
        } else {
            window.location.href = `catalogo.html?category=${catKey}`;
        }
        return;
    }

    categoriaActiva = catKey;
    
    // Actualizar clases activas en los botones del dropdown
    document.querySelectorAll(".dropdown-item").forEach(btn => {
        btn.classList.remove("active");
    });
    
    const activeBtn = document.getElementById(`dropdown-btn-${catKey}`);
    if (activeBtn) activeBtn.classList.add("active");
    
    // Actualizar parámetro en la URL sin refrescar
    const url = new URL(window.location);
    if (catKey === "all") {
        url.searchParams.delete("category");
    } else {
        url.searchParams.set("category", catKey);
    }
    window.history.replaceState({}, document.title, url.pathname + url.search);
    
    renderCatalog();
}

// Buscar productos en tiempo real desde la barra de navegación
function handleNavbarSearch() {
    const searchInput = document.getElementById("searchInput");
    if (!searchInput) return;
    const query = searchInput.value.trim();
    
    // Si estamos en la página del catálogo, filtramos en tiempo real
    if (document.getElementById("productsGrid")) {
        busquedaActual = query.toLowerCase();
        
        // Actualizar parámetro en la URL sin refrescar
        const url = new URL(window.location);
        if (query) {
            url.searchParams.set("search", query);
        } else {
            url.searchParams.delete("search");
        }
        window.history.replaceState({}, document.title, url.pathname + url.search);
        
        renderCatalog();
    }
}

// Buscar productos al presionar Enter o hacer clic en la lupa (🔍)
function triggerSearch() {
    const searchInput = document.getElementById("searchInput");
    if (!searchInput) return;
    const query = searchInput.value.trim();
    
    if (document.getElementById("productsGrid")) {
        busquedaActual = query.toLowerCase();
        renderCatalog();
    } else {
        window.location.href = `catalogo.html?search=${encodeURIComponent(query)}`;
    }
}

// Alternar visibilidad de la barra de búsqueda en celular
function toggleSearchInput(event) {
    event.stopPropagation();
    const container = document.querySelector(".search-bar-container");
    if (!container) return;
    const input = container.querySelector("input");
    if (!input) return;
    
    if (window.innerWidth <= 768) {
        if (!container.classList.contains("active")) {
            container.classList.add("active");
            input.focus();
        } else {
            if (input.value.trim() !== "") {
                triggerSearch();
            } else {
                container.classList.remove("active");
            }
        }
    } else {
        triggerSearch();
    }
}

// Cerrar barra de búsqueda al hacer clic fuera
window.addEventListener("click", (e) => {
    const container = document.querySelector(".search-bar-container");
    if (container && !e.target.closest(".search-bar-container")) {
        const input = container.querySelector("input");
        if (input && input.value.trim() === "") {
            container.classList.remove("active");
        }
    }
});

// Mantener función original para compatibilidad
function handleSearch() {
    handleNavbarSearch();
}

// Datos y función para banner dinámico de categoría
const CATEGORY_BANNER_DATA = {
    "all": {
        title: "Productos",
        subtitle: "Catálogo completo",
        bg: "img/fondo_rayas.webp"
    },
    "corazones": {
        title: "Corazones",
        subtitle: "Colección",
        bg: "img/CORAZONES_2.webp"
    },
    "corazones-alados": {
        title: "Alados",
        subtitle: "diseños variados",
        bg: "img/fondo_alados.webp"
    },
    "nichos-y-altares": {
        title: "Nichos",
        subtitle: "estilo mexicanos",
        bg: "img/FONDO_NICHOS.webp"
    },
    "mexicanos-y-calacas": {
        title: "Calacas",
        subtitle: "y mexicanos",
        bg: "img/fondo_calacas.webp"
    },
    "grabados": {
        title: "Grabados",
        subtitle: "infantiles y más",
        bg: "img/fondo_grabados.webp"
    },
    "navidad": {
        title: "Navidad",
        subtitle: "todo el año",
        bg: "img/FONDO_NAVIDAD.webp"
    },
    "deco": {
        title: "Deco",
        subtitle: "creativa",
        bg: "img/fondo_deco_2.webp"
    },
    "stencil": {
        title: "Stencils",
        subtitle: "creaciones propias",
        bg: "img/fondo_stencil.webp"
    },
    "mistico-y-mas": {
        title: "Místico",
        subtitle: "energía y conexión",
        bg: "img/fondo_mistico.webp"
    },
    "otros-insumos": {
        title: "Insumos",
        subtitle: "complementarios",
        bg: "img/fondo_insumos.webp"
    },
    "libros-3d": {
        title: "Libros 3D",
        subtitle: "fantasía y encanto",
        bg: "img/fondo_3d.webp"
    },
    "pascua": {
        title: "Pascua",
        subtitle: "de resurrección",
        bg: "img/fondo_pascua.webp"
    }
};

function actualizarBannerCategoria() {
    const banner = document.getElementById("categoryHeaderBanner");
    const titleEl = document.getElementById("categoryBannerTitle");
    const subtitleEl = document.getElementById("categoryBannerSubtitle");
    if (!banner || !titleEl || !subtitleEl) return;

    const bannerData = CATEGORY_BANNER_DATA[categoriaActiva] || CATEGORY_BANNER_DATA["all"];

    if (busquedaActual) {
        titleEl.textContent = "Buscador";
        subtitleEl.textContent = `Resultados para "${busquedaActual}"`;
        banner.style.backgroundImage = "url('img/fondo_rayas.webp')";
    } else {
        titleEl.textContent = bannerData.title;
        subtitleEl.textContent = bannerData.subtitle;
        banner.style.backgroundImage = `url('${bannerData.bg}')`;
    }
    banner.style.display = "flex";
}

// Verificar si un producto es nuevo (creado hace 20 días o menos)
function esProductoNuevo(p) {
    if (!p || !p.fecha_creacion) return false;
    const fecha = new Date(p.fecha_creacion);
    if (isNaN(fecha.getTime())) return false;
    const ahora = new Date();
    const diffDias = (ahora - fecha) / (1000 * 60 * 60 * 24);
    return diffDias >= 0 && diffDias <= 20;
}

// Renderizar grilla de catálogo
function renderCatalog() {
    const grid = document.getElementById("productsGrid");
    if (!grid) return;
    grid.innerHTML = "";
    actualizarBannerCategoria();
    
    // Obtener sólo productos padres (filtrar los aliases de medidas que apuntan a padres)
    // Se invierte el orden (.reverse()) para que los productos más recientes agregados al catálogo queden al inicio
    const parentKeys = Object.keys(productos).filter(key => !productos[key].parent).reverse();
    
    let productosFiltrados = parentKeys.filter(key => {
        const p = productos[key];
        const clasificacion = clasificarProducto(key, p);
        
        // 1. Filtrar por categoría
        if (categoriaActiva !== "all" && (!clasificacion || !clasificacion.includes(categoriaActiva))) {
            return false;
        }
        
        // 2. Filtrar por búsqueda
        if (busquedaActual) {
            const matchesId = key.toLowerCase().includes(busquedaActual);
            const matchesNombre = (p.nombre || "").toLowerCase().includes(busquedaActual);
            const matchesCodigo = (p.codigo || "").toLowerCase().includes(busquedaActual);
            return matchesId || matchesNombre || matchesCodigo;
        }
        
        return true;
    });

    // Ordenar productosFiltrados:
    // 1. Productos con etiqueta 'nuevo' (creados hace 20 días o menos) van primero arriba
    // 2. Si ambos son nuevos o ambos son estándar, se respeta el orden cronológico más reciente primero
    productosFiltrados.sort((a, b) => {
        const nuevoA = esProductoNuevo(productos[a]);
        const nuevoB = esProductoNuevo(productos[b]);
        if (nuevoA && !nuevoB) return -1;
        if (!nuevoA && nuevoB) return 1;
        return 0;
    });

    if (productosFiltrados.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px 0; font-size: 16px;">No se encontraron productos en esta categoría. 📦</div>`;
        return;
    }

    productosFiltrados.forEach((key, idx) => {
        const p = productos[key];
        let precioHtml = "";
        
        if (p.tipo === "medidas") {
            let rowsHtml = "";
            p.opciones.forEach(op => {
                rowsHtml += `
                    <div class="measure-price-row">
                        <span class="measure-label">${op.medida}</span>
                        <span class="price-value special">$${op.mayor.toLocaleString("es-CL")}</span>
                        <span class="price-value">$${op.unitario.toLocaleString("es-CL")}</span>
                    </div>
                `;
            });
            precioHtml = `
                <div class="measures-list-layout">
                    <div class="measure-price-row header-row">
                        <span>Medida</span>
                        <span>Mayor</span>
                        <span>Unidad</span>
                    </div>
                    ${rowsHtml}
                </div>
            `;
        } else if (p.tipo === "variantes") {
            const minPrecio = Math.min(...p.opciones.map(o => o.precio));
            const maxPrecio = Math.max(...p.opciones.map(o => o.precio));
            precioHtml = `
                <div class="price-row">
                    <span>Valor:</span>
                    <span class="price-value">$${minPrecio.toLocaleString("es-CL")} - $${maxPrecio.toLocaleString("es-CL")}</span>
                </div>
            `;
        } else {
            // simple
            const mayorStr = p.mayor ? `$${p.mayor.toLocaleString("es-CL")}` : "N/A";
            precioHtml = `
                <div class="measures-list-layout simple-layout">
                    <div class="simple-price-row header-row">
                        <span>Mayor</span>
                        <span>Unidad</span>
                    </div>
                    <div class="simple-price-row">
                        <span class="price-value special">${mayorStr}</span>
                        <span class="price-value">$${p.unitario.toLocaleString("es-CL")}</span>
                    </div>
                </div>
            `;
        }

        const esNuevo = esProductoNuevo(p);
        const badgeNuevoHtml = esNuevo ? `
            <div class="product-badge-nuevo">
                <span class="badge-icon">⭐</span>
                <span>NUEVO</span>
            </div>
        ` : '';

        const card = document.createElement("div");
        card.className = "product-card";
        card.id = `prod-${key}`;
        card.style.animationDelay = (idx * 0.05 + 0.15) + 's';
        card.innerHTML = `
            <div class="product-img-wrapper" onclick="abrirImagenGrande('${key}')" title="Ver imagen en grande">
                ${badgeNuevoHtml}
                <img 
                    src="${p.imagen}" 
                    alt="${p.nombre}" 
                    class="product-img"
                    loading="lazy"
                    onerror="this.src='https://via.placeholder.com/200?text=Sin+Foto'"
                >
            </div>
            <div class="product-info">
                <h4 class="product-title">${p.codigo || p.nombre}</h4>
                ${p.descripcion ? `<div class="product-desc" title="${p.descripcion}">${p.descripcion}</div>` : ''}
                ${p.medida_original ? `<div class="product-spec-medida">Medida: ${p.medida_original}</div>` : ''}
                <div class="product-prices">
                    ${precioHtml}
                </div>
                <button class="product-action-btn" onclick="abrirCompraModal('${key}')">
                    🛒 Lo quiero
                </button>
            </div>
        `;
        grid.appendChild(card);
    });
}

// Abrir imagen en grande (Lightbox)
function abrirImagenGrande(id) {
    if (!productos[id]) return;
    const p = productos[id];
    cerrarPopupSilencioso();

    const popup = document.createElement("div");
    popup.id = "popupProducto";
    popup.className = "modal-overlay";
    popup.onclick = (e) => {
        if (e.target === popup) cerrarPopup();
    };

    popup.innerHTML = `
    <div class="modal-container" style="max-width: 600px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 20px; padding: 24px; box-sizing: border-box;">
        <h2 style="margin: 0; font-family: var(--font-serif); font-size: 24px; color: #4b372d;">${p.nombre}</h2>
        
        <div style="width: 100%; border-radius: var(--radius-md); overflow: hidden; background: #ffffff; border: 1px solid rgba(75, 55, 45, 0.1); box-shadow: var(--shadow-md); display: flex; align-items: center; justify-content: center; padding: 10px; box-sizing: border-box;">
            <img src="${p.imagen}" alt="${p.nombre}" style="max-width: 100%; max-height: 60vh; object-fit: contain; display: block; border-radius: var(--radius-sm);" onerror="this.src='https://via.placeholder.com/400?text=Sin+Foto'">
        </div>
        
        <button onclick="cerrarPopup()" class="modal-btn-secondary" style="width: 100%; margin-top: 10px; font-weight: bold; background: linear-gradient(135deg, #95AB9E 0%, #7d9084 100%); color: white; border: none; border-radius: var(--radius-sm); padding: 12px; cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
            ⬅ Volver
        </button>
    </div>
    `;

    document.body.appendChild(popup);
    document.body.classList.add("modal-open");
    requestAnimationFrame(() => popup.classList.add("active"));
}

// Abrir Selector Modal para comprar
function abrirCompraModal(id) {
    if (!productos[id]) return;
    
    // Si apunta a un producto padre
    if (productos[id].parent) {
        opcionPreseleccionada = productos[id].preselect;
        productoActual = productos[productos[id].parent];
        productoActual.key = productos[id].parent;
    } else {
        opcionPreseleccionada = "";
        productoActual = productos[id];
        productoActual.key = id;
    }
    
    abrirSelectorProducto();
}

function abrirSelectorProducto() {
    const p = productoActual;
    let opcionesHTML = "";

    /* MEDIDAS */
    if (p.tipo === "medidas") {
        opcionesHTML = `
        <div class="modal-input-group">
            <label for="medidaSelect">Medida disponible</label>
            <select id="medidaSelect" class="modal-select" onchange="actualizarPreciosModal()">
                ${p.opciones.map(op => {
                    const selected = (opcionPreseleccionada && op.medida.toLowerCase().replace(/[^a-z0-9]/g, "") === opcionPreseleccionada.toLowerCase().replace(/[^a-z0-9]/g, "")) ? "selected" : "";
                    return `
                    <option value="${op.medida}|${op.mayor}|${op.unitario}" ${selected}>
                        ${op.medida}
                    </option>
                    `;
                }).join("")}
            </select>
        </div>
        `;
    }

    /* VARIANTES */
    if (p.tipo === "variantes") {
        opcionesHTML = `
        <div class="modal-input-group">
            <label for="varianteSelect">Opción / Espesor</label>
            <select id="varianteSelect" class="modal-select" onchange="actualizarPreciosModal()">
                ${p.opciones.map(op => `
                    <option value="${op.nombre}|${op.precio}">
                        ${op.nombre}
                    </option>
                `).join("")}
            </select>
        </div>
        `;
    }

    // Remover modal anterior si existe
    cerrarPopupSilencioso();

    const popup = document.createElement("div");
    popup.id = "popupProducto";
    popup.className = "modal-overlay";
    popup.onclick = (e) => {
        if (e.target === popup) cerrarPopup();
    };

    popup.innerHTML = `
    <div class="modal-container">
        <h2>${p.codigo || p.nombre}</h2>
        ${p.descripcion ? `<p class="modal-product-desc" style="color: #6b5a50; margin: 4px 0 12px 0; font-size: 14px; line-height: 1.4;">${p.descripcion}</p>` : ''}
        ${p.medida_original ? `<p class="modal-product-spec-medida" style="color: var(--primary-color); margin: 0 0 16px 0; font-size: 13px; font-weight: 600;">Medida: ${p.medida_original}</p>` : ''}
        
        <div class="modal-image-wrapper">
            <img src="${p.imagen}" alt="${p.nombre}" class="modal-image" onerror="this.src='https://via.placeholder.com/150?text=Sin+Foto'">
        </div>
        
        ${opcionesHTML}
        
        <div id="modalPreciosInfo"></div>
 
        <div style="display: grid; grid-template-columns: 100px 1fr; gap: 12px;">
            <div class="modal-input-group">
                <label for="cantidadProducto">Cantidad</label>
                <input
                    type="number"
                    id="cantidadProducto"
                    value="1"
                    min="1"
                    class="modal-input"
                    oninput="actualizarPreciosModal()"
                >
            </div>
            
            <div class="modal-input-group">
                <label for="obsProducto">Observación adicional</label>
                <textarea
                    id="obsProducto"
                    placeholder="Ej: detalles de grabado u opción (opcional)"
                    class="modal-textarea"
                    style="height: 43px; padding: 10px;"
                ></textarea>
            </div>
        </div>

        <button onclick="agregarProducto()" class="modal-btn-primary">
            Lo quiero
        </button>

        <button onclick="cerrarPopup()" class="modal-btn-secondary">
            Cancelar
        </button>
    </div>
    `;

    document.body.appendChild(popup);
    document.body.classList.add("modal-open");
    requestAnimationFrame(() => popup.classList.add("active"));
    actualizarPreciosModal();
}

function actualizarPreciosModal() {
    const p = productoActual;
    const container = document.getElementById("modalPreciosInfo");
    if (!container) return;

    let unitario = 0;
    let mayor = 0;
    let tempItem = { codigo: p.codigo, medida: "", variante: "" };

    if (p.tipo === "medidas") {
        const select = document.getElementById("medidaSelect");
        if (select) {
            const data = select.value.split("|");
            tempItem.medida = data[0];
            mayor = parseInt(data[1]);
            unitario = parseInt(data[2]);
        }
    } else if (p.tipo === "simple") {
        unitario = p.unitario;
        mayor = p.mayor || p.unitario;
    } else if (p.tipo === "variantes") {
        const select = document.getElementById("varianteSelect");
        if (select) {
            const data = select.value.split("|");
            tempItem.variante = data[0];
            unitario = parseInt(data[1]);
            mayor = unitario;
        }
    }

    const norm = obtenerCodigoItemNormalizado(tempItem);
    const normBase = obtenerCodigoBaseNormalizado(tempItem);
    const es30 = esMedida30cm(norm);
    const inputCantidad = parseInt(document.getElementById("cantidadProducto").value) || 1;

    // Regla de Aros
    if (esItemAros(normBase)) {
        let badgeHTML = "";
        let activePrice = 750;
        if (inputCantidad >= 20) {
            activePrice = 400;
            badgeHTML = `<div style="font-weight: 600; color: #2e7d32; margin-top: 4px; font-size: 12px;">🎉 ¡Precio Mayorista (20+) aplicado!</div>`;
        } else if (inputCantidad >= 10) {
            activePrice = 500;
            badgeHTML = `<div style="font-weight: 600; color: #2e7d32; margin-top: 4px; font-size: 12px;">🎉 ¡Precio Mayorista (10+) aplicado!</div>`;
        } else {
            const yaEnCartAros = obtenerCantidadArosEnCart();
            const totalAros = yaEnCartAros + inputCantidad;
            if (totalAros >= 20 && yaEnCartAros > 0) {
                badgeHTML = `<div style="font-weight: 600; color: #2e7d32; margin-top: 4px; font-size: 12px;">🎉 ¡Se aplicará precio de $400 al agregarlo! (Combina con los ${yaEnCartAros} que ya tienes)</div>`;
            } else if (totalAros >= 10 && yaEnCartAros > 0) {
                badgeHTML = `<div style="font-weight: 600; color: #2e7d32; margin-top: 4px; font-size: 12px;">🎉 ¡Se aplicará precio de $500 al agregarlo! (Combina con los ${yaEnCartAros} que ya tienes)</div>`;
            } else {
                badgeHTML = `<div style="font-weight: 500; color: var(--text-muted); margin-top: 4px; font-size: 12px;">✨ Lleva 10+ unidades por $500 c/u o 20+ por $400 c/u.</div>`;
            }
        }
        
        container.innerHTML = `
        <div style="background: rgba(125, 139, 99, 0.08); border: 1px dashed var(--primary-color); border-radius: 12px; padding: 10px; margin-bottom: 14px; text-align: center; font-size: 13px;">
            <div style="font-weight: 700; color: var(--text-main); font-size: 14px;">🏷️ Precio: $${activePrice.toLocaleString("es-CL")} c/u</div>
            ${badgeHTML}
        </div>
        `;
        return;
    }

    // Regla de combinación general
    const grp = obtenerGrupoDeItem(normBase);
    const esInter = esItemIntercambiable(norm);
    
    let yaEnCart = 0;
    let minQty = 4;
    let esCombinable = false;
    let descGrupo = "";

    // Contar total del mismo grupo en el carrito
    const tempCart = JSON.parse(localStorage.getItem("carrito")) || [];
    
    if (esInter) {
        esCombinable = true;
        tempCart.forEach(item => {
            const itemNorm = obtenerCodigoItemNormalizado(item);
            if (esItemIntercambiable(itemNorm)) {
                if (esMedida30cm(itemNorm) === es30) {
                    yaEnCart += item.cantidad;
                }
            }
        });
        minQty = 4;
        descGrupo = es30 ? "esta categoría (30 cm)" : "esta categoría (20 cm o simples)";
    } else if (grp) {
        esCombinable = true;
        tempCart.forEach(item => {
            const itemNormBase = obtenerCodigoBaseNormalizado(item);
            const itemGrp = obtenerGrupoDeItem(itemNormBase);
            if (itemGrp && itemGrp.id === grp.id) {
                yaEnCart += item.cantidad;
            }
        });
        minQty = grp.min;
        descGrupo = "esta categoría combinable";
    } else if (noCombinables3.has(normBase)) {
        minQty = 3;
    } else if (noCombinables6.has(normBase)) {
        minQty = 6;
    }

    const totalCantidad = yaEnCart + inputCantidad;
    let aplicaMayoristaModal = (totalCantidad >= minQty) || (inputCantidad >= minQty);
    let activePrice = aplicaMayoristaModal ? mayor : unitario;

    if (mayor && mayor < unitario) {
        let badgeHTML = "";
        
        if (aplicaMayoristaModal) {
            badgeHTML = `<div style="font-weight: 600; color: #2e7d32; margin-top: 4px; font-size: 12px;">🎉 ¡Precio Mayorista aplicado!</div>`;
        } else {
            if (esCombinable) {
                badgeHTML = `<div style="font-weight: 500; color: var(--text-muted); margin-top: 4px; font-size: 12px;">✨ Lleva <span style="color: var(--primary-color); font-weight: 700;">${minQty} o más</span> de ${descGrupo} para activar Mayorista: <span style="color: var(--primary-color); font-weight: 700;">$${mayor.toLocaleString("es-CL")}</span> c/u</div>`;
            } else {
                badgeHTML = `<div style="font-weight: 500; color: var(--text-muted); margin-top: 4px; font-size: 12px;">✨ Llevando <span style="color: var(--primary-color); font-weight: 700;">${minQty} o más</span>: <span style="color: var(--primary-color); font-weight: 700;">$${mayor.toLocaleString("es-CL")}</span> c/u</div>`;
            }
        }

        container.innerHTML = `
        <div style="background: rgba(125, 139, 99, 0.08); border: 1px dashed var(--primary-color); border-radius: 12px; padding: 10px; margin-bottom: 14px; text-align: center; font-size: 13px;">
            <div style="font-weight: 700; color: var(--text-main); font-size: 14px;">🏷️ Precio: $${activePrice.toLocaleString("es-CL")} c/u</div>
            ${badgeHTML}
        </div>
        `;
    } else if (unitario) {
        container.innerHTML = `
        <div style="background: rgba(75, 55, 45, 0.04); border: 1px solid var(--border-color); border-radius: 12px; padding: 10px; margin-bottom: 14px; text-align: center; font-size: 13px;">
            <div style="font-weight: 700; color: var(--text-main); font-size: 14px;">Valor: $${unitario.toLocaleString("es-CL")}</div>
        </div>
        `;
    }
}

// Agregar producto al carro
function agregarProducto() {
    const p = productoActual;
    const cantidadVal = parseInt(document.getElementById("cantidadProducto").value) || 1;

    let nuevoProducto = {
        codigo: p.codigo,
        nombre: p.nombre,
        imagen: p.imagen,
        cantidad: cantidadVal,
        observacion: document.getElementById("obsProducto").value.trim(),
        medida: "",
        variante: "",
        unitario: p.unitario,
        mayor: p.mayor || p.unitario,
        precio: 0,
        tipo: ""
    };

    if (p.tipo === "medidas") {
        const data = document.getElementById("medidaSelect").value.split("|");
        nuevoProducto.medida = data[0];
        nuevoProducto.mayor = parseInt(data[1]);
        nuevoProducto.unitario = parseInt(data[2]);
    }

    if (p.tipo === "variantes") {
        const data = document.getElementById("varianteSelect").value.split("|");
        nuevoProducto.variante = data[0];
        nuevoProducto.unitario = parseInt(data[1]);
        nuevoProducto.mayor = parseInt(data[1]);
    }

    const normBase = obtenerCodigoBaseNormalizado(nuevoProducto);
    if (esItemAros(normBase)) {
        nuevoProducto.unitario = 750;
        nuevoProducto.mayor = 400;
    }

    // Agregar o acumular
    let existente = carrito.find(item => 
        item.codigo === nuevoProducto.codigo &&
        item.medida === nuevoProducto.medida &&
        item.variante === nuevoProducto.variante &&
        item.observacion === nuevoProducto.observacion
    );

    if (existente) {
        existente.cantidad += nuevoProducto.cantidad;
    } else {
        carrito.push(nuevoProducto);
    }

    recalcularPreciosCarrito(carrito);
    guardarCarrito();
    renderCarrito();
    
    if (sessionStorage.getItem("fromSites") === "true") {
        cerrarPopupSilencioso();
        mostrarToast();
        setTimeout(() => {
            const targetUrl = sessionStorage.getItem("referrerSites") || "https://sites.google.com/view/bendito-taller/p%C3%A1gina-principal";
            window.location.href = targetUrl;
        }, 1500);
    } else {
        cerrarPopup();
        mostrarToast();
    }
}

function cerrarPopup() {
    const popup = document.getElementById("popupProducto");
    if (!popup) return;
    
    popup.classList.remove("active");
    popup.classList.add("closing");
    
    setTimeout(() => {
        popup.remove();
        document.body.classList.remove("modal-open");
        
        // Limpiar query param de producto
        const url = new URL(window.location);
        url.searchParams.delete('producto');
        window.history.replaceState({}, document.title, url.pathname + url.search);

        // Si viene de Google Sites y cancela, redirigir de vuelta a Google Sites
        if (sessionStorage.getItem("fromSites") === "true") {
            const targetUrl = sessionStorage.getItem("referrerSites") || "https://sites.google.com/view/bendito-taller/p%C3%A1gina-principal";
            window.location.href = targetUrl;
        }
    }, 250);
}

// Cierra el modal de producto sin gatillar la redirección inmediata a Google Sites
function cerrarPopupSilencioso() {
    const popup = document.getElementById("popupProducto");
    if (popup) {
        popup.remove();
        document.body.classList.remove("modal-open");
    }
    
    const url = new URL(window.location);
    url.searchParams.delete('producto');
    window.history.replaceState({}, document.title, url.pathname + url.search);
}

let cartTimeout = null;
let justOpenedByHover = false;

function showCart() {
    clearTimeout(cartTimeout);
    const panel = document.getElementById("cartPanel");
    if (panel && panel.style.display !== "block") {
        panel.style.display = "block";
        justOpenedByHover = true;
        setTimeout(() => {
            justOpenedByHover = false;
        }, 300);
    }
}

function hideCart() {
    cartTimeout = setTimeout(() => {
        const panel = document.getElementById("cartPanel");
        if (panel) panel.style.display = "none";
    }, 300); // 300ms de retraso para dar tiempo a mover el cursor al panel
}

function toggleCart() {
    const panel = document.getElementById("cartPanel");
    if (panel) {
        if (justOpenedByHover) {
            justOpenedByHover = false;
            return;
        }
        panel.style.display = panel.style.display === "block" ? "none" : "block";
    }
}

function renderCarrito() {
    let html = "";
    let total = 0;

    recalcularPreciosCarrito(carrito);

    carrito.forEach((item, index) => {
        let subtotal = item.precio * item.cantidad;
        total += subtotal;

        let detalles = [];
        if (item.medida) detalles.push(item.medida);
        if (item.variante) detalles.push(item.variante);
        if (item.precio < item.unitario) detalles.push("Mayor");

        let detailsString = detalles.join(" | ");

        html += `
        <div class="cart-item">
            <img src="${item.imagen}" alt="${item.nombre}" onerror="this.src='https://via.placeholder.com/90?text=Sin+Foto'">
            <div class="item-info">
                <div class="item-title">${item.nombre}</div>
                <div class="item-detail">${detailsString}</div>
                ${item.observacion ? `<div class="item-detail" style="font-style: italic; color: #8e8076;">Obs: "${item.observacion}"</div>` : ""}
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button onclick="restarCantidad(${index})" style="border: none; background: #e5dacb; width: 24px; height: 24px; border-radius: 50%; cursor: pointer; font-weight: bold; color: #4b372d; font-size: 14px; display: flex; align-items: center; justify-content: center;">-</button>
                        <span style="font-weight: bold; font-size: 14px;">${item.cantidad}</span>
                        <button onclick="sumarCantidad(${index})" style="border: none; background: #e5dacb; width: 24px; height: 24px; border-radius: 50%; cursor: pointer; font-weight: bold; color: #4b372d; font-size: 14px; display: flex; align-items: center; justify-content: center;">+</button>
                        <button onclick="eliminarProducto(${index})" style="border: none; background: transparent; cursor: pointer; font-size: 16px; margin-left: 6px; padding: 4px; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='rgba(220, 53, 69, 0.1)'" onmouseout="this.style.backgroundColor='transparent'" title="Eliminar">🗑️</button>
                    </div>
                    <div class="item-price">$${subtotal.toLocaleString("es-CL")}</div>
                </div>
            </div>
        </div>
        `;
    });

    document.getElementById("cartItems").innerHTML = html || `<div style="text-align: center; color: var(--text-muted); padding: 30px 0; font-size: 15px;">Tu carrito está vacío 🛒</div>`;
    document.getElementById("cartTotal").innerHTML = `<span>Total:</span> <span>$${total.toLocaleString("es-CL")}</span>`;
    
    // Actualizar badges
    const totalItems = carrito.reduce((acc, i) => acc + i.cantidad, 0);
    document.getElementById("cartCount").textContent = `(${totalItems})`;
}

function sumarCantidad(index) {
    carrito[index].cantidad++;
    recalcularPreciosCarrito(carrito);
    guardarCarrito();
    renderCarrito();
}

function restarCantidad(index) {
    if (carrito[index].cantidad > 1) {
        carrito[index].cantidad--;
        recalcularPreciosCarrito(carrito);
        guardarCarrito();
        renderCarrito();
    }
}

function eliminarProducto(index) {
    if (confirm("¿Deseas eliminar este producto de tu pedido?")) {
        carrito.splice(index, 1);
        recalcularPreciosCarrito(carrito);
        guardarCarrito();
        renderCarrito();
    }
}

function vaciarCarrito() {
    if (carrito.length === 0) return;
    if (confirm("¿Vaciar todo tu pedido?")) {
        carrito = [];
        guardarCarrito();
        renderCarrito();
    }
}

function guardarCarrito() {
    localStorage.setItem("carrito", JSON.stringify(carrito));
}

function mostrarToast() {
    const toast = document.getElementById("toast");
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 2000);
}

function toggleMobileMenu() {
    const menu = document.getElementById("navMenu");
    const toggle = document.getElementById("menuToggle");
    menu.classList.toggle("show");
    toggle.classList.toggle("active");
}

// Leer URL params al cargar
function procesarParametrosURL() {
    const params = new URLSearchParams(window.location.search);
    let autoScroll = false;
    
    // Cargar búsqueda de URL si existe (soporta ?search= y ?buscar=)
    const searchVal = params.get("search") || params.get("buscar");
    if (searchVal) {
        busquedaActual = searchVal.trim().toLowerCase();
        const searchInput = document.getElementById("searchInput");
        if (searchInput) {
            searchInput.value = searchVal;
        }
    }
    
    // Cargar categoría de URL si existe
    const cat = params.get("category");
    if (cat && CATEGORIAS_MAP[cat]) {
        setCategory(cat);
        autoScroll = true;
    } else {
        renderCatalog();
    }
    
    // Cargar producto de URL si existe
    const prodId = params.get("producto");
    if (prodId && productos[prodId]) {
        abrirCompraModal(prodId);
        autoScroll = true;
    }
    
    // Auto-scroll y resaltado suave si viene con ancla de producto (#prod-xxx)
    if (window.location.hash) {
        setTimeout(() => {
            const targetCard = document.querySelector(window.location.hash);
            if (targetCard) {
                targetCard.scrollIntoView({ behavior: "smooth", block: "center" });
                targetCard.classList.add("product-card-highlight");
                setTimeout(() => targetCard.classList.remove("product-card-highlight"), 2500);
            } else if (autoScroll) {
                const section = document.getElementById("catalog-section");
                if (section) section.scrollIntoView({ behavior: "smooth" });
            }
        }, 250);
    } else if (autoScroll) {
        setTimeout(() => {
            const section = document.getElementById("catalog-section");
            if (section) {
                section.scrollIntoView({ behavior: "smooth" });
            }
        }, 150);
    }
}

// Carrusel de la página de inicio (Productos Destacados)
// El cliente puede agregar o remover imágenes de forma sencilla aquí:
const IMAGENES_CARROUSEL = [
    { src: "img/co43.webp", title: "Corazón multicapa Flores", subtitle: "encuentralo en Corazones" },
    { src: "img/Corona  Reno.webp", title: "Navideños", subtitle: "Corona Reno" },
    { src: "img/Comp8.webp", title: "Composición sirena", subtitle: "Encuentalo en deco" },
    { src: "img/altar12.webp", title: "ALTAR 12", subtitle: "Altar en capas" },
    { src: "img/Libromagico1.webp", title: "LIBRO ALICIA 3d", subtitle: "encuentalo en libros 3d" },
    { src: "img/ca20.webp", title: "CA20", subtitle: "Corazón alado 3 capas" },
    { src: "img/ca21.webp", title: "CA21", subtitle: "Corazón alado 3 capas" },
    { src: "img/comp9.webp", title: "COMP9", subtitle: "Composición multicapa" },
    { src: "img/comp12.webp", title: "COMP12", subtitle: "Tetera reloj" },
    { src: "img/setfiguritas10.webp", title: "SET FIGURITAS10", subtitle: "Set para pintar" },
    { src: "img/setfiguritas11.webp", title: "SET FIGURITAS11", subtitle: "Set para pintar" },
    { src: "img/Tienda vintage2.webp", title: "Tienda Vintage", subtitle: "ENCUENTRALO EN DECO" },
    { src: "img/co38.webp", title: "CO38", subtitle: "Corazón devoto en capas" },
    { src: "img/co42.webp", title: "Corazón multicapa Flores", subtitle: "encuentralo en Corazones" }
];

let carouselIndex = 0;
let carouselInterval = null;

function inicializarCarrusel() {
    const track = document.getElementById("carouselTrack");
    const dotsContainer = document.getElementById("carouselDots");
    if (!track || !dotsContainer) return;
    
    track.innerHTML = "";
    dotsContainer.innerHTML = "";
    
    IMAGENES_CARROUSEL.forEach((img, index) => {
        // Crear slide
        const slide = document.createElement("div");
        slide.className = `carousel-slide ${index === 0 ? "active" : ""}`;
        
        slide.innerHTML = `
            <img src="${img.src}" alt="${img.title}">
            <div class="carousel-overlay">
                <div class="carousel-caption">
                    <p>${img.title}</p>
                    <h3>${img.subtitle}</h3>
                </div>
            </div>
        `;
        track.appendChild(slide);
        
        // Crear dot
        const dot = document.createElement("button");
        dot.className = `carousel-dot ${index === 0 ? "active" : ""}`;
        dot.onclick = () => irASlide(index);
        dotsContainer.appendChild(dot);
    });
    
    iniciarAutoSlide();
}

function iniciarAutoSlide() {
    detenerAutoSlide();
    carouselInterval = setInterval(() => {
        moveCarousel(1);
    }, 4000); // Cambia cada 4 segundos
}

function detenerAutoSlide() {
    if (carouselInterval) {
        clearInterval(carouselInterval);
    }
}

function moveCarousel(direction) {
    const track = document.getElementById("carouselTrack");
    if (!track) return;
    const slides = track.querySelectorAll(".carousel-slide");
    if (slides.length === 0) return;
    
    carouselIndex = (carouselIndex + direction + slides.length) % slides.length;
    actualizarCarrusel();
    iniciarAutoSlide(); // Reiniciar timer
}

function irASlide(index) {
    carouselIndex = index;
    actualizarCarrusel();
    iniciarAutoSlide(); // Reiniciar timer
}

function actualizarCarrusel() {
    const track = document.getElementById("carouselTrack");
    const dotsContainer = document.getElementById("carouselDots");
    if (!track) return;
    
    track.style.transform = `translateX(-${carouselIndex * 100}%)`;
    
    // Actualizar clase active en slides
    const slides = track.querySelectorAll(".carousel-slide");
    slides.forEach((slide, index) => {
        if (index === carouselIndex) {
            slide.classList.add("active");
        } else {
            slide.classList.remove("active");
        }
    });
    
    // Actualizar dots
    if (dotsContainer) {
        const dots = dotsContainer.querySelectorAll(".carousel-dot");
        dots.forEach((dot, index) => {
            if (index === carouselIndex) {
                dot.classList.add("active");
            } else {
                dot.classList.remove("active");
            }
        });
    }
}

// ==========================================
// CARRUSEL 2: LO + NUEVO (Últimos 10 productos subidos)
// ==========================================
let carouselNuevosIndex = 0;
let carouselNuevosInterval = null;

function inicializarCarruselNuevos() {
    const track = document.getElementById("carouselNuevosTrack");
    const dotsContainer = document.getElementById("carouselNuevosDots");
    if (!track || !dotsContainer) return;
    
    track.innerHTML = "";
    dotsContainer.innerHTML = "";
    
    if (typeof productos === "undefined" || !productos) return;
    
    // Obtener sólo productos padres en orden cronológico inverso (.reverse())
    // y tomar exactamente los últimos 10 productos ingresados
    const parentKeys = Object.keys(productos).filter(key => !productos[key].parent).reverse();
    const ultimos10Keys = parentKeys.slice(0, 10);
    
    if (ultimos10Keys.length === 0) return;
    
    ultimos10Keys.forEach((key, index) => {
        const p = productos[key];
        const categorias = (typeof clasificarProducto === "function") ? clasificarProducto(key, p) : [];
        const catKey = (categorias && categorias.length > 0 && typeof CATEGORIAS_MAP !== "undefined" && CATEGORIAS_MAP[categorias[0]]) ? categorias[0] : "all";
        const catLabel = (typeof CATEGORIAS_MAP !== "undefined" && CATEGORIAS_MAP[catKey]) ? CATEGORIAS_MAP[catKey] : "Catálogo";

        const slide = document.createElement("div");
        slide.className = `carousel-slide ${index === 0 ? "active" : ""}`;
        slide.style.cursor = "pointer";
        slide.title = `Ver ${p.nombre || p.codigo} en categoría ${catLabel}`;
        slide.onclick = () => {
            if (catKey && catKey !== "all") {
                window.location.href = `catalogo.html?category=${encodeURIComponent(catKey)}#prod-${encodeURIComponent(key)}`;
            } else {
                window.location.href = "catalogo.html";
            }
        };
        
        const imgSrc = p.imagen || "img/logo_circulo.webp";
        const titulo = p.nombre || p.codigo || "Producto Nuevo";
        const subtitulo = p.descripcion ? p.descripcion : (p.unitario ? `$${Number(p.unitario).toLocaleString('es-CL')}` : "Ver producto");
        
        slide.innerHTML = `
            <img src="${imgSrc}" alt="${titulo}" loading="lazy">
            <div class="carousel-overlay">
                <div class="carousel-caption">
                    <p style="color: #ff9e7d; font-weight: 700; letter-spacing: 1.5px;">&#10024; RECI&Eacute;N INGRESADO &bull; ${catLabel.toUpperCase()}</p>
                    <h3>${titulo}</h3>
                    <p style="font-size: 13px; opacity: 0.95; text-transform: none;">${subtitulo}</p>
                </div>
            </div>
        `;
        track.appendChild(slide);
        
        // Crear dot
        const dot = document.createElement("button");
        dot.className = `carousel-dot ${index === 0 ? "active" : ""}`;
        dot.setAttribute("aria-label", `Slide nuevo ${index + 1}`);
        dot.onclick = () => irASlideNuevos(index);
        dotsContainer.appendChild(dot);
    });
    
    iniciarAutoSlideNuevos();
}

function iniciarAutoSlideNuevos() {
    detenerAutoSlideNuevos();
    carouselNuevosInterval = setInterval(() => {
        moveCarouselNuevos(1);
    }, 4500); // 4.5 segundos
}

function detenerAutoSlideNuevos() {
    if (carouselNuevosInterval) {
        clearInterval(carouselNuevosInterval);
    }
}

function moveCarouselNuevos(direction) {
    const track = document.getElementById("carouselNuevosTrack");
    if (!track) return;
    const slides = track.querySelectorAll(".carousel-slide");
    if (slides.length === 0) return;
    
    carouselNuevosIndex = (carouselNuevosIndex + direction + slides.length) % slides.length;
    actualizarCarruselNuevos();
    iniciarAutoSlideNuevos();
}

function irASlideNuevos(index) {
    carouselNuevosIndex = index;
    actualizarCarruselNuevos();
    iniciarAutoSlideNuevos();
}

function actualizarCarruselNuevos() {
    const track = document.getElementById("carouselNuevosTrack");
    const dotsContainer = document.getElementById("carouselNuevosDots");
    if (!track) return;
    
    track.style.transform = `translateX(-${carouselNuevosIndex * 100}%)`;
    
    const slides = track.querySelectorAll(".carousel-slide");
    slides.forEach((slide, index) => {
        if (index === carouselNuevosIndex) {
            slide.classList.add("active");
        } else {
            slide.classList.remove("active");
        }
    });
    
    if (dotsContainer) {
        const dots = dotsContainer.querySelectorAll(".carousel-dot");
        dots.forEach((dot, index) => {
            if (index === carouselNuevosIndex) {
                dot.classList.add("active");
            } else {
                dot.classList.remove("active");
            }
        });
    }
}

// Inicializar al cargar
window.addEventListener("DOMContentLoaded", () => {
    inicializarCategorias();
    renderCarrito();
    procesarParametrosURL();
    inicializarCarrusel();
    inicializarCarruselNuevos();
    
    // Asignar view-transition-name a las tarjetas de categorías al hacer click
    document.querySelectorAll(".category-card").forEach(card => {
        card.addEventListener("click", () => {
            card.style.viewTransitionName = "active-category-header";
        });
    });
});
