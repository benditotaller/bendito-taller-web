// Configuración del contacto de la tienda (número de WhatsApp)
const numeroWhatsapp = "56979295426";

// Mapeo de categorías amigables
const CATEGORIAS_MAP = {
    "corazones": "Corazones",
    "corazones-alados": "Corazones Alados",
    "nichos-y-altares": "Nichos y Altares",
    "mexicanos-y-calacas": "Mexicanos y Calacas",
    "grabados": "Grabados",
    "navidad": "Navidad",
    "deco": "Deco",
    "stencil": "Stencil",
    "mistico-y-mas": "Místico y Más",
    "otros-insumos": "Otros Insumos",
    "libros-3d": "Libros 3D",
    "pascua": "Pascua"
};

// Set de códigos intercambiables normalizados (lowercase, sin caracteres especiales) - Grupo original de Corazones/Cruces/Altares
const codigosIntercambiablesNorm = new Set([
    "bc4", "co120cm", "co130cm", "co1020cm", "co1030cm", "co11", 
    "co1220cm", "co1230cm", "co13", "co14", "co1520cm", "co1530cm", 
    "co16", "co1720cm", "co1730cm", "co18", "co19", "co220cm", 
    "co230cm", "co20", "co21", "co22", "co23", "co2420cm", "co2430cm", 
    "co2520cm", "co2530cm", "co26", "co2720cm", "co2730cm", "co28", 
    "co2920cm", "co2930cm", "co3", "co30", "co31", "co32", "co3320cm", 
    "co3330cm", "co3420cm", "co3430cm", "co3620cm", "co3630cm", 
    "co37", "co420cm", "co430cm", "co520cm", "co530cm", "co620cm", 
    "co630cm", "co720cm", "co730cm", "co820cm", "co830cm", "co920cm", 
    "co930cm", "cruz1", "cruz2", "setcorazonesmulticapa", "florcora1", 
    "florcora2", "florcora3", "bc1", "bc2", "bc3", "ca120cm", "ca130cm", 
    "ca1020cm", "ca1030cm", "ca11trio", "ca123mm", "ca1255mm", 
    "ca133mm", "ca1355mm", "ca14", "ca15", "ca1620cm", "ca1630cm", 
    "ca1720cm", "ca1730cm", "ca18", "ca220cm", "ca230cm", "ca420cm", 
    "ca430cm", "ca520cm", "ca530cm", "ca620cm", "ca630cm", "ca7", 
    "ca8", "ca9trio"
]);

// Configuración de grupos combinables nuevos
const gruposCombinables = [
    {
        id: "altares_nichos",
        min: 4,
        codigos: [
            "altarvirgencita", "altar1", "altar10", "altar11", "altar2", "altar3", "altar4",
            "altar5", "altar5simple", "altar6", "altar7", "altar8", "altar9",
            "nicho1", "nicho2", "nicho3", "nicho4"
        ]
    },
    {
        id: "virgenes",
        min: 4,
        codigos: ["virgen1", "virgen2", "virgen3", "virgen4"]
    },
    {
        id: "alebrijes_catrinas",
        min: 4,
        codigos: ["alebrije1", "alebrije2", "catrina1", "catrina2"]
    },
    {
        id: "calaveras",
        min: 4,
        codigos: ["cal1", "cal2", "cal3"]
    },
    {
        id: "composiciones_1_3",
        min: 4,
        codigos: ["comp1", "comp2", "comp3"]
    },
    {
        id: "fridas",
        min: 4,
        codigos: ["frida1", "frida2", "frida3", "frida4", "frida5"]
    },
    {
        id: "tienda_vintage",
        min: 4,
        codigos: ["tiendavintage1", "tiendavintage2"]
    },
    {
        id: "grabados_gra",
        min: 4,
        codigos: [
            "gra1", "gra2", "gra3", "gra4", "gra5", "gra6", "gra7", "gra8", "gra9", "gra10",
            "gra11", "gra12", "gra13", "gra14", "gra15", "gra16", "gra17", "gra18", "gra19"
        ]
    },
    {
        id: "set_navideno",
        min: 4,
        codigos: ["setnavideno1", "setnavideno2"]
    },
    {
        id: "casita_muneca_torre",
        min: 4,
        codigos: ["casitamunecas2", "torre"]
    },
    {
        id: "composiciones_4_8_arabesco",
        min: 4,
        codigos: ["arabescofloral1", "comp4", "comp5", "comp6", "comp7", "comp8"]
    },
    {
        id: "set_anillos",
        min: 4,
        codigos: ["setanillos1", "setanillos2", "setanillos3", "setanillos4", "setanillos5", "setanillos6", "setanillos7"]
    },
    {
        id: "deco_infantil",
        min: 4,
        codigos: ["decoinantil1", "decoinfantil2", "decoinantil3", "decoinantil4"]
    },
    {
        id: "animales",
        min: 4,
        codigos: ["chinita", "leopardo", "leopardo2", "tortugahawaiana", "zorrito"]
    },
    {
        id: "abejas_mariposas",
        min: 4,
        codigos: [
            "abejareina", "abejareina2", "marip1", "marip2", "marip3", "marip4", "marip5", "marip6", "banderinmexicano"
        ]
    },
    {
        id: "cuadros_c",
        min: 4,
        codigos: ["cuadroc1", "cuadroc2", "cuadroc3", "cuadroc4"]
    },
    {
        id: "bienvenidos",
        min: 4,
        codigos: ["bienve1", "bienve2", "bienve3", "bienve4"]
    },
    {
        id: "letreros",
        min: 4,
        codigos: ["letrerovintage", "letrero1", "letrero2", "letrero3", "letrero4"]
    },
    {
        id: "colibri",
        min: 4,
        codigos: ["colibricapas", "colibrigrabado"]
    },
    {
        id: "eclipse",
        min: 4,
        codigos: ["eclipse1", "eclipse2"]
    },
    {
        id: "obras_3d",
        min: 4,
        codigos: [
            "alicia3d", "circo", "halloween", "harrypotter3d", "libromagico1", "libromagico2",
            "narnia3d", "peter3d", "principito1", "principito2", "ratitapresumida", "snoopy1", "snoopy2", "vigendelvalle"
        ]
    },
    {
        id: "corona_navidad_personajes",
        min: 4,
        codigos: ["coronacascanueces", "coronaosito", "coronareno"]
    },
    {
        id: "coronas_navidad_base",
        min: 4,
        codigos: ["cascanuecescapas", "coronacasa", "coronaespecial", "coronasimple", "coronasimple2", "coronavillanavidena"]
    },
    {
        id: "cuadros_navidad",
        min: 4,
        codigos: ["cuadronavideno", "cuadronoel"]
    },
    {
        id: "arboles_navidad_pino",
        min: 3,
        codigos: ["arboldenavidad", "arbolnavideno", "pinohome"]
    },
    {
        id: "cajas_navidad",
        min: 6,
        codigos: ["cajagrinch", "cajasanta"]
    }
];

// Conjuntos de productos no combinables con reglas especiales
const noCombinables3 = new Set([
    "renomecedor", "duodeangeles", "munecodenieve", "tagnavideno", "cascanueces", "renos", "angel3", "caballovintage"
]);

const noCombinables6 = new Set([
    "colganteangelcorazon", "colgantecaballito", "colganteangelestrella", "renograbado", "angel1", "angel2"
]);

/* ==========================
   CLASIFICACIÓN DINÁMICA
   Clasifica los productos según su prefijo e ID para la navegación
========================== */
const PRODUCT_CATEGORY_MAPPING = {
    // 1. CORAZONES
    "florcora3": ["corazones"],
    "co37": ["corazones"],
    "co36": ["corazones"],
    "florcora2": ["corazones"],
    "florcora1": ["corazones"],
    "co34": ["corazones"],
    "co33": ["corazones"],
    "cruz1": ["corazones"],
    "cruz2": ["corazones"],
    "co31": ["corazones"],
    "bc4": ["corazones"],
    "co32": ["corazones"],
    "co30": ["corazones"],
    "co28": ["corazones"],
    "co27": ["corazones"],
    "co26": ["corazones"],
    "co25": ["corazones"],
    "co23": ["corazones"],
    "co2": ["corazones"],
    "co4": ["corazones"],
    "co5": ["corazones"],
    "co29": ["corazones"],
    "co7": ["corazones"],
    "co8": ["corazones"],
    "co9": ["corazones"],
    "co10": ["corazones"],
    "co6": ["corazones"],
    "co12": ["corazones"],
    "co13": ["corazones"],
    "co14": ["corazones"],
    "co15": ["corazones"],
    "co16": ["corazones"],
    "co11": ["corazones"],
    "co17": ["corazones"],
    "co22": ["corazones"],
    "setcorazonesmulticapa": ["corazones"],
    "co3": ["corazones"],
    "co1": ["corazones"],
    "co24": ["corazones"],
    "co20": ["corazones"],
    "co21": ["corazones"],
    "co18": ["corazones"],
    "co19": ["corazones"],

    // 2. CORAZONES ALADOS
    "ca18": ["corazones-alados"],
    "ca17": ["corazones-alados"],
    "ca16": ["corazones-alados"],
    "ca15": ["corazones-alados"],
    "ca14": ["corazones-alados"],
    "ca13": ["corazones-alados"],
    "ca12": ["corazones-alados"],
    "ca1": ["corazones-alados"],
    "ca2": ["corazones-alados"],
    "ca5": ["corazones-alados"],
    "ca6": ["corazones-alados"],
    "ca7": ["corazones-alados"],
    "ca9trio": ["corazones-alados"],
    "ca10": ["corazones-alados"],
    "bc1": ["corazones-alados"],
    "bc2": ["corazones-alados"],
    "bc3": ["corazones-alados"],
    "ca8": ["corazones-alados"],
    "ca11trio": ["corazones-alados"],
    "ca4": ["corazones-alados"],

    // 3. NICHOS Y ALTARES
    "altar11": ["nichos-y-altares"],
    "altar10": ["nichos-y-altares"],
    "nicho4": ["nichos-y-altares"],
    "altar9": ["nichos-y-altares"],
    "altarvirgencita": ["nichos-y-altares"],
    "altar7": ["nichos-y-altares"],
    "nicho3": ["nichos-y-altares"],
    "altar6": ["nichos-y-altares"],
    "altar5simple": ["nichos-y-altares"],
    "altar5": ["nichos-y-altares"],
    "nicho1": ["nichos-y-altares"],
    "altar4": ["nichos-y-altares"],
    "altar1": ["nichos-y-altares"],
    "altar2": ["nichos-y-altares"],
    "altar3": ["nichos-y-altares"],
    "nicho2": ["nichos-y-altares"],
    "altar8": ["nichos-y-altares"],

    // 4. MEXICANOS Y CALACAS
    "alebrije2": ["mexicanos-y-calacas"],
    "virgen4": ["mexicanos-y-calacas", "libros-3d"],
    "alebrije1": ["mexicanos-y-calacas"],
    "frida3": ["mexicanos-y-calacas"],
    "frida5": ["mexicanos-y-calacas"],
    "virgen3": ["mexicanos-y-calacas"],
    "virgen2": ["mexicanos-y-calacas", "libros-3d"],
    "frida4": ["mexicanos-y-calacas"],
    "frida1": ["mexicanos-y-calacas"],
    "frida2": ["mexicanos-y-calacas"],
    "virgen1": ["mexicanos-y-calacas"],
    "comp1": ["mexicanos-y-calacas"],
    "comp2": ["mexicanos-y-calacas"],
    "comp3": ["mexicanos-y-calacas"],
    "catrina1": ["mexicanos-y-calacas"],
    "catrina2": ["mexicanos-y-calacas"],
    "cal3": ["mexicanos-y-calacas"],
    "cal2": ["mexicanos-y-calacas"],
    "cal1": ["mexicanos-y-calacas"],

    // 5. GRABADOS
    "figuritas17": ["grabados"],
    "figuritas16": ["grabados"],
    "figuritas15": ["grabados"],
    "figuritas14": ["grabados"],
    "figuritas13": ["grabados"],
    "figuritas12": ["grabados"],
    "figuritas11": ["grabados"],
    "figuritas10": ["grabados"],
    "setfiguritas1": ["grabados"],
    "setfiguritas2": ["grabados"],
    "setfiguritas3": ["grabados"],
    "setfiguritas4": ["grabados"],
    "setfiguritas5": ["grabados"],
    "setfiguritas6": ["grabados"],
    "setfiguritas7": ["grabados"],
    "setfiguritas8": ["grabados"],
    "setfiguritas9": ["grabados"],
    "gra19": ["grabados"],
    "gra1": ["grabados"],
    "gra7": ["grabados"],
    "gra2": ["grabados"],
    "gra3": ["grabados"],
    "gra4": ["grabados"],
    "gra5": ["grabados"],
    "gra6": ["grabados"],
    "gra17": ["grabados"],
    "gra8": ["grabados"],
    "gra9": ["grabados"],
    "gra10": ["grabados"],
    "gra11": ["grabados"],
    "gra12": ["grabados"],
    "gra13": ["grabados"],
    "gra14": ["grabados"],
    "gra15": ["grabados"],
    "gra16": ["grabados"],
    "gra18": ["grabados"],

    // 6. NAVIDAD
    "setfigurasnav1": ["navidad"],
    "setnavideno2": ["navidad"],
    "setnavideno1": ["navidad"],
    "arbolnavideno": ["navidad"],
    "coronaosito": ["navidad"],
    "tiendavintage1": ["navidad", "deco"],
    "casitamunecas2": ["navidad"],
    "torre": ["navidad"],
    "renomecedor": ["navidad"],
    "cuadronoel": ["navidad"],
    "arboldenavidad": ["navidad"],
    "cuadronavideno": ["navidad"],
    "carruselnavideno": ["navidad"],
    "coronaespecial": ["navidad"],
    "coronavillanavidena": ["navidad"],
    "coronasimple": ["navidad"],
    "coronasimple2": ["navidad"],
    "coronacasa": ["navidad"],
    "coronacascanueces": ["navidad"],
    "coronareno": ["navidad"],
    "buzonnavidad": ["navidad"],
    "teatro": ["navidad"],
    "casademunecas1": ["navidad"],
    "duodeangeles": ["navidad"],
    "munecodenieve": ["navidad"],
    "homenavideno": ["navidad"],
    "tagnavideno": ["navidad"],
    "colganteangelcorazon": ["navidad"],
    "colganteangelestrella": ["navidad"],
    "cascanueces": ["navidad"],
    "pinohome": ["navidad"],
    "renos": ["navidad"],
    "estrellas": ["navidad"],
    "copos": ["navidad"],
    "renograbado": ["navidad"],
    "estrellasgrabadas5cm": ["navidad"],
    "angel1": ["navidad"],
    "angel2": ["navidad"],
    "renobase3mm": ["navidad"],
    "colgantecaballito": ["navidad"],
    "cajagrinch": ["navidad"],
    "cajasanta": ["navidad"],
    "gnomonavideno": ["navidad"],
    "sagradafambase": ["navidad"],
    "pesebre": ["navidad"],
    "angel3": ["navidad"],
    "cascanuecescapas": ["navidad"],
    "tiendavintage2": ["navidad", "deco"],

    // 7. DECO
    "arabescofloral1": ["deco"],
    "siluetataza1": ["deco"],
    "siluetatetera1": ["deco"],
    "rosetaswallartl": ["deco"],
    "rosetaswallartm": ["deco"],
    "comp8": ["deco"],
    "comp7": ["deco"],
    "comp4": ["deco"],
    "comp5": ["deco"],
    "comp6": ["deco"],
    "setanillos1": ["deco"],
    "setanillos2": ["deco"],
    "setanillos3": ["deco"],
    "setanillos4": ["deco"],
    "setanillos5": ["deco"],
    "setanillos7": ["deco"],
    "setanillos6": ["deco"],
    "decoinfantil4": ["deco"],
    "decoinfantil3": ["deco"],
    "decoinfantil2": ["deco"],
    "decoinfantil1": ["deco"],
    "decoinantil4": ["deco"],
    "decoinantil3": ["deco"],
    "decoinantil1": ["deco"],
    "repisa01": ["deco"],
    "farol1": ["deco"],
    "tag": ["deco"],
    "setaplicaciones5": ["deco"],
    "setaplicaciones4": ["deco"],
    "setaplicaciones3": ["deco"],
    "setmolduras": ["deco"],
    "setcostura": ["deco"],
    "aplicaciones1": ["deco"],
    "horadelte": ["deco"],
    "llavesycerrojos": ["deco"],
    "tazasyteteras": ["deco"],
    "aplicaciones2": ["deco"],
    "principito1": ["deco"],
    "zorrito": ["deco"],
    "leopardo": ["deco"],
    "leopardo2": ["deco"],
    "chinita": ["deco"],
    "tortugahawaiana": ["deco"],
    "abejareina2": ["deco"],
    "abejareina": ["deco"],
    "marip6": ["deco"],
    "marip4": ["deco"],
    "marip5": ["deco"],
    "marip3": ["deco"],
    "marip2": ["deco"],
    "marip1": ["deco"],
    "cuadroc4": ["deco"],
    "cuadroc1": ["deco"],
    "cuadroc2": ["deco"],
    "cuadroc3": ["deco"],
    "bienve1": ["deco"],
    "bienve2": ["deco"],
    "bienve4": ["deco"],
    "bienve3": ["deco"],
    "letrero3": ["deco"],
    "letrero4": ["deco"],
    "letrero1": ["deco"],
    "letrero2": ["deco"],
    "homebase": ["deco"],
    "letrerovintage": ["deco"],
    "colibrigrabado": ["deco"],
    "portallave1": ["deco"],
    "pajaro": ["deco"],
    "colibricapas": ["deco"],
    "colgantedecorativo1": ["deco"],
    "colibri": ["deco"],
    "guirnaldabosque": ["deco"],
    "banderin1": ["deco"],
    "banderin3": ["deco"],
    "banderin2": ["deco"],
    "decobanderin": ["deco"],
    "corarelicario": ["deco"],
    "sol1": ["deco"],
    "eclipse1": ["deco"],
    "eclipse2": ["deco"],
    "caballomecedor": ["deco"],
    "ranita": ["deco"],
    "buzon": ["deco"],
    "caballovintage": ["deco"],
    "cuadrocarrusel": ["deco"],
    "carrusel": ["deco"],
    "caballodemar": ["deco"],
    "portacel1": ["deco"],
    "siluetanina1": ["deco"],
    "p2": ["deco"],
    "p3": ["deco"],
    "p4": ["deco"],
    "p1": ["deco"],
    "arbolfamiliar": ["deco"],
    "memorialmascotas": ["deco"],
    "mascara1": ["deco"],
    "l001": ["deco"],
    "l002": ["deco"],

    // 8. STENCIL
    "st21": ["stencil"],
    "st22": ["stencil"],
    "st09": ["stencil"],
    "st20": ["stencil"],
    "st01": ["stencil"],
    "st02": ["stencil"],
    "st03": ["stencil"],
    "st04": ["stencil"],
    "st06": ["stencil"],
    "st08": ["stencil"],
    "st10": ["stencil"],
    "st12": ["stencil"],
    "st05": ["stencil"],
    "st14": ["stencil"],
    "st18": ["stencil"],

    // 9. MISTICO Y MAS
    "aros10": ["mistico-y-mas"],
    "aros9": ["mistico-y-mas"],
    "aros8": ["mistico-y-mas"],
    "aros7": ["mistico-y-mas"],
    "aros2": ["mistico-y-mas"],
    "aros3": ["mistico-y-mas"],
    "aros4": ["mistico-y-mas"],
    "aros5": ["mistico-y-mas"],
    "aros6": ["mistico-y-mas"],
    "colgante1": ["mistico-y-mas"],
    "colgante2": ["mistico-y-mas"],
    "colgante3": ["mistico-y-mas"],
    "colgante4": ["mistico-y-mas"],
    "aroscora3": ["mistico-y-mas"],
    "aroscora4": ["mistico-y-mas"],
    "arosfelino1": ["mistico-y-mas"],
    "aroscalaca": ["mistico-y-mas"],
    "arosmarip": ["mistico-y-mas"],
    "aroscora1": ["mistico-y-mas"],
    "aroscora2": ["mistico-y-mas"],
    "arosfrida": ["mistico-y-mas"],
    "uteroflor": ["mistico-y-mas"],
    "mujerlunar": ["mistico-y-mas"],
    "ganesha": ["mistico-y-mas"],
    "ojoturco": ["mistico-y-mas"],

    // 10. OTROS INSUMOS
    "laminapandeoroverde": ["otros-insumos"],
    "laminapandeororojo": ["otros-insumos"],
    "laminapandeorodorado": ["otros-insumos"],
    "laminapandeorocobre": ["otros-insumos"],
    "laminapandeoroplata": ["otros-insumos"],
    "transfermod01": ["otros-insumos"],
    "transfermod02": ["otros-insumos"],
    "transfermod03": ["otros-insumos"],
    "transfermod04": ["otros-insumos"],
    "transfermod05": ["otros-insumos"],
    "transfermod06": ["otros-insumos"],
    "transfermod07": ["otros-insumos"],
    "transfermod08": ["otros-insumos"],
    "transfermod09": ["otros-insumos"],
    "transfermod010": ["otros-insumos"],
    "transfermod10": ["otros-insumos"],
    "transfermod11": ["otros-insumos"],
    "foliadecorativamod01": ["otros-insumos"],
    "foliadecorativamod02": ["otros-insumos"],
    "foliadecorativamod03": ["otros-insumos"],
    "foliadecorativamod04": ["otros-insumos"],
    "foliadecorativamod05": ["otros-insumos"],
    "setde10pinceles": ["otros-insumos"],
    "brochadecerdasuave": ["otros-insumos"],
    "pincelesunitarios": ["otros-insumos"],

    // 11. LIBROS 3D
    "libromagico2": ["libros-3d"],
    "libromagico1": ["libros-3d"],
    "peter3d": ["libros-3d"],
    "alicia3d": ["libros-3d"],
    "snoopy1": ["libros-3d"],
    "snoopy2": ["libros-3d"],
    "narnia3d": ["libros-3d"],
    "ratitapresumida": ["libros-3d"],
    "harrypotter3d": ["libros-3d"],
    "vigendelvalle": ["libros-3d"],
    "halloween": ["libros-3d"],
    "circo": ["libros-3d"],
    "principito2": ["libros-3d"],
    "co38": ["corazones"],
    "co42": ["corazones"],
    "co35": ["corazones"],
    "altar12": ["nichos-y-altares"],
    "ca20": ["corazones-alados"],
    "ca21": ["corazones-alados"],
    "comp9": ["deco"],
    "comp12": ["deco"],
    "comp10": ["mexicanos-y-calacas"],
    "setfiguritas10": ["grabados"],
    "setfiguritas11": ["grabados"]
};

function clasificarProducto(id, p) {
    const idClean = id.toLowerCase().replace(/[^a-z0-9]/g, "");
    
    // 1. Intentar clasificar con el mapeo estático
    if (PRODUCT_CATEGORY_MAPPING[idClean]) {
        return PRODUCT_CATEGORY_MAPPING[idClean];
    }

    // 2. Fallback dinámico si no está mapeado
    const nombreClean = (p.nombre || "").toLowerCase();

    if (idClean.startsWith("aros")) {
        return ["mistico-y-mas"];
    }
    if (
        idClean.includes("navid") || 
        idClean.includes("santa") || 
        idClean.includes("grinch") || 
        idClean.includes("noel") || 
        idClean.includes("cascanueces") || 
        idClean.includes("reno") || 
        idClean.includes("pino") || 
        idClean.includes("nieve") || 
        idClean.includes("pesebre") ||
        idClean.startsWith("setnavideno") ||
        nombreClean.includes("navidad") ||
        nombreClean.includes("reno") ||
        nombreClean.includes("pino")
    ) {
        return ["navidad"];
    }
    if (idClean.startsWith("altar") || idClean.startsWith("nicho") || nombreClean.includes("altar") || nombreClean.includes("nicho")) {
        return ["nichos-y-altares"];
    }
    if (idClean.startsWith("co") && !idClean.startsWith("colibri") && !idClean.startsWith("comp") && !idClean.startsWith("corona") && !idClean.startsWith("copos")) {
        return ["corazones"];
    }
    if (idClean.includes("cora") || nombreClean.includes("corazón") || nombreClean.includes("corazon")) {
        if (idClean.includes("alado") || nombreClean.includes("alado")) {
            return ["corazones-alados"];
        }
        return ["corazones"];
    }
    if (
        idClean.startsWith("cal") || 
        idClean.includes("catrina") || 
        idClean.includes("alebrije") || 
        idClean.includes("frida") || 
        idClean.includes("mexican") || 
        nombreClean.includes("calaca") || 
        nombreClean.includes("catrina") || 
        nombreClean.includes("alebrije") || 
        nombreClean.includes("frida") || 
        nombreClean.includes("mexicano")
    ) {
        return ["mexicanos-y-calacas"];
    }
    if (idClean.startsWith("gra") && !idClean.startsWith("grabado")) {
        return ["grabados"];
    }
    if (idClean.includes("grabado") || nombreClean.includes("grabado")) {
        return ["grabados"];
    }
    if (idClean.startsWith("letrero") || idClean.startsWith("letra") || idClean.startsWith("bienve") || idClean.startsWith("l00") || nombreClean.includes("letrero") || nombreClean.includes("bienvenido") || nombreClean.includes("letra")) {
        return ["deco"];
    }
    if (idClean.startsWith("st") || idClean.includes("stencil") || nombreClean.includes("stencil")) {
        return ["stencil"];
    }
    if (
        idClean.startsWith("cruz") || 
        idClean.includes("virgen") || 
        idClean.includes("angel") || 
        idClean.includes("santisima") || 
        idClean.includes("ganesha") ||
        nombreClean.includes("cruz") || 
        nombreClean.includes("virgen") || 
        nombreClean.includes("ángel") || 
        nombreClean.includes("angel") ||
        nombreClean.includes("ganesha")
    ) {
        return ["mistico-y-mas"];
    }
    if (
        idClean.startsWith("cuadro") || 
        idClean.startsWith("deco") || 
        idClean.startsWith("tiendavintage") || 
        idClean.startsWith("colibri") || 
        idClean.startsWith("eclipse") || 
        idClean.startsWith("comp") || 
        idClean.startsWith("arabesco") ||
        idClean.startsWith("setanillos") ||
        idClean.startsWith("casitamunecas") ||
        idClean.startsWith("casademunecas") ||
        idClean.startsWith("torre") ||
        idClean.startsWith("rosetas") ||
        idClean.startsWith("carrusel") ||
        idClean.startsWith("farol") ||
        idClean.startsWith("repisa") ||
        idClean.startsWith("sol") ||
        ["leopardo", "leopardo2", "zorrito", "chinita", "tortugahawaiana", "caballodemar", "caballomecedor", "caballovintage", "alicia3d", "circo", "halloween", "harrypotter3d", "libromagico1", "libromagico2", "narnia3d", "peter3d", "principito1", "principito2", "ratitapresumida", "snoopy1", "snoopy2", "vigendelvalle", "abejareina", "abejareina2", "marip1", "marip2", "marip3", "marip4", "marip5", "marip6"].includes(idClean) ||
        nombreClean.includes("cuadro") ||
        nombreClean.includes("decoración") ||
        nombreClean.includes("deco") ||
        nombreClean.includes("colibrí") ||
        nombreClean.includes("eclipse")
    ) {
        return ["deco"];
    }

    if (
        idClean.includes("pascua") || 
        idClean.includes("conejo") || 
        idClean.includes("huevo") || 
        nombreClean.includes("pascua") ||
        nombreClean.includes("conejo") ||
        nombreClean.includes("huevo")
    ) {
        return ["pascua"];
    }

    return ["otros-insumos"];
}

/* ==========================
   HELPERS DE NORMALIZACIÓN
========================== */
function obtenerCodigoItemNormalizado(item) {
    if (!item || !item.codigo) return "";
    let raw = item.codigo;
    if (item.medida) {
        raw += "_" + item.medida;
    } else if (item.variante) {
        raw += "_" + item.variante;
    }
    return raw.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function obtenerCodigoBaseNormalizado(item) {
    if (!item || !item.codigo) return "";
    return item.codigo.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function esItemIntercambiable(itemNorm) {
    return codigosIntercambiablesNorm.has(itemNorm);
}

function esMedida30cm(itemNorm) {
    return itemNorm.includes("30cm");
}

function esMedida20cm(itemNorm) {
    return itemNorm.includes("20cm");
}

function esItemAros(normBase) {
    return normBase.startsWith("aros");
}

/* ==========================
   HELPERS DE GRUPOS Y CANTIDADES
========================== */
function obtenerGrupoDeItem(normBase) {
    return gruposCombinables.find(g => g.codigos.includes(normBase)) || null;
}

function obtenerCantidadArosEnCart() {
    const list = typeof carrito !== 'undefined' ? carrito : [];
    let total = 0;
    list.forEach(item => {
        const normBase = obtenerCodigoBaseNormalizado(item);
        if (esItemAros(normBase)) {
            total += item.cantidad;
        }
    });
    return total;
}

function obtenerCantidadGrupoEnCart(groupId) {
    const list = typeof carrito !== 'undefined' ? carrito : [];
    let total = 0;
    list.forEach(item => {
        const normBase = obtenerCodigoBaseNormalizado(item);
        const grp = obtenerGrupoDeItem(normBase);
        if (grp && grp.id === groupId) {
            total += item.cantidad;
        }
    });
    return total;
}

/* ==========================
   RECALCULAR PRECIOS DEL CARRITO
========================== */
function recalcularPreciosCarrito(cartArray) {
    const list = cartArray || (typeof carrito !== 'undefined' ? carrito : []);
    
    // 1. Contadores para los grupos combinables
    let totalIntercambiables30cm = 0;
    let totalIntercambiables20cm = 0;
    let totalIntercambiablesTodo = 0;
    const totalPorGrupo = {};
    gruposCombinables.forEach(g => {
        totalPorGrupo[g.id] = 0;
    });
    let totalAros = 0;

    // Primer paso: Contar cantidades acumuladas
    list.forEach(item => {
        const normFull = obtenerCodigoItemNormalizado(item);
        const normBase = obtenerCodigoBaseNormalizado(item);

        // Grupo original (Corazones/Cruces/Altares/Intercambiables)
        if (esItemIntercambiable(normFull)) {
            if (esMedida30cm(normFull)) {
                totalIntercambiables30cm += item.cantidad;
            } else if (esMedida20cm(normFull)) {
                totalIntercambiables20cm += item.cantidad;
            } else {
                totalIntercambiablesTodo += item.cantidad;
            }
        }

        // Grupos combinables nuevos
        const grp = obtenerGrupoDeItem(normBase);
        if (grp) {
            totalPorGrupo[grp.id] += item.cantidad;
        }

        // Aros
        if (esItemAros(normBase)) {
            totalAros += item.cantidad;
        }
    });

    // Segundo paso: Actualizar precios unitarios en caliente
    list.forEach(item => {
        const normFull = obtenerCodigoItemNormalizado(item);
        const normBase = obtenerCodigoBaseNormalizado(item);
        let aplicaMayorista = false;

        if (esItemAros(normBase)) {
            // Aros tienen lógica de 3 niveles
            item.unitario = 750;
            item.mayor = 400;
            if (totalAros >= 20) {
                item.precio = 400;
                item.tipo = "Por Mayor (20+)";
            } else if (totalAros >= 10) {
                item.precio = 500;
                item.tipo = "Por Mayor (10+)";
            } else {
                item.precio = 750;
                item.tipo = "Unitario";
            }
        } else if (esItemIntercambiable(normFull)) {
            if (esMedida30cm(normFull)) {
                aplicaMayorista = (totalIntercambiables30cm + totalIntercambiablesTodo) >= 4;
            } else if (esMedida20cm(normFull)) {
                aplicaMayorista = (totalIntercambiables20cm + totalIntercambiablesTodo) >= 4;
            } else {
                aplicaMayorista = (totalIntercambiables30cm + totalIntercambiables20cm + totalIntercambiablesTodo) >= 4;
            }
            item.precio = aplicaMayorista ? item.mayor : item.unitario;
            item.tipo = (aplicaMayorista && item.mayor < item.unitario) ? "Por Mayor" : "Unitario";
        } else {
            const grp = obtenerGrupoDeItem(normBase);
            if (grp) {
                // Pertenece a un grupo combinable nuevo
                aplicaMayorista = (totalPorGrupo[grp.id] >= grp.min);
            } else if (noCombinables3.has(normBase)) {
                aplicaMayorista = (item.cantidad >= 3);
            } else if (noCombinables6.has(normBase)) {
                aplicaMayorista = (item.cantidad >= 6);
            } else {
                // Regla por defecto para productos individuales
                aplicaMayorista = (item.cantidad >= 4);
            }

            item.precio = aplicaMayorista ? item.mayor : item.unitario;
            item.tipo = (aplicaMayorista && item.mayor < item.unitario) ? "Por Mayor" : "Unitario";
        }
    });
}
