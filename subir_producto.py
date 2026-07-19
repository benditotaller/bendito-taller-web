# -*- coding: utf-8 -*-
import os
import sys
import sqlite3
import shutil
import re
import json
import unicodedata
import subprocess
import threading
import math
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# Intentar importar rembg para remover fondos
try:
    from rembg import remove, new_session
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

# Intentar importar Pillow para previsualización y compresión de imágenes
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageChops
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Mapeo de IDs de grupos combinables a nombres amigables en español
GROUP_NAMES_MAP = {
    "intercambiables": "Intercambiables (Corazones, Cruces, Altares originales)",
    "altares_nichos": "Altares y Nichos",
    "virgenes": "Vírgenes",
    "alebrijes_catrinas": "Alebrijes y Catrinas",
    "calaveras": "Calaveras",
    "composiciones_1_3": "Composiciones (1 a 3)",
    "fridas": "Fridas",
    "tienda_vintage": "Tienda Vintage",
    "grabados_gra": "Grabados (GRA)",
    "set_navideno": "Set Navideño",
    "casita_muneca_torre": "Casita de Muñecas / Torre",
    "composiciones_4_8_arabesco": "Composiciones (4 a 8) / Arabesco",
    "set_anillos": "Set de Anillos",
    "deco_infantil": "Deco Infantil",
    "animales": "Animales",
    "abejas_mariposas": "Abejas y Mariposas",
    "cuadros_c": "Cuadros (C)",
    "bienvenidos": "Letreros de Bienvenidos",
    "letreros": "Letreros",
    "colibri": "Colibríes",
    "eclipse": "Eclipses",
    "obras_3d": "Obras 3D",
    "corona_navidad_personajes": "Coronas Navideñas (Personajes)",
    "coronas_navidad_base": "Coronas Navideñas (Base/Especiales)",
    "cuadros_navidad": "Cuadros Navideños",
    "arboles_navidad_pino": "Pinos / Árboles de Navidad",
    "cajas_navidad": "Cajas Navideñas"
}

# Paleta de Colores "Bendito Taller"
COLOR_BG = "#fffcf8"       # Crema de fondo
COLOR_CARD = "#f5ece1"     # Arena suave para tarjetas
COLOR_TEXT = "#4b372d"     # Café oscuro
COLOR_BORDER = "#e5dacb"   # Borde beige claro
COLOR_ACCENT = "#7d8b63"   # Verde salvia
COLOR_ACCENT_HOVER = "#677351"
COLOR_DANGER = "#d9534f"   # Rojo suave
COLOR_DANGER_HOVER = "#b53f3a"
COLOR_WHITE = "#ffffff"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Bendito Taller - Gestión de Productos")
        self.root.geometry("1280x850")
        try:
            self.root.state('zoomed')  # Abrir maximizada por defecto en Windows
        except:
            pass
        self.root.configure(bg=COLOR_BG)
        self.root.minsize(850, 600)

        # Ruta del proyecto (soporta PyInstaller)
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self.imagen_procesada_ia = False
        self.imagen_ext_ia = ".webp"
        self.index_html_path = None
        self.tarjetas_web = []
        self.decoraciones = []
        self.fondos_css = {}
        self.cached_web_bg_img = None
        self.deco_animations = {}

        self.FUENTES_LIST = [
            "Cormorant Garamond (Serif de alta elegancia)",
            "Outfit (Sans-serif moderna)",
            "Petit Formal Script (Script elegante)",
            "Playfair Display (Serif de alto contraste)",
            "Merriweather (Serif clásica)",
            "Montserrat (Sans-serif limpia)",
            "Segoe UI (Estilo sistema)",
            "Great Vibes (Caligrafía clásica)",
            "Dancing Script (Cursiva casual)",
            "Parisienne (Cursiva fluida)",
            "Alex Brush (Cursiva artística)",
            "Cinzel (Serif romana clásica)",
            "Lora (Serif literaria)",
            "Inter (Sans-serif ultra-limpia)",
            "Roboto (Sans-serif estándar)",
            "Poppins (Sans-serif geométrica)",
            "Pinyon Script (Caligrafía fina)",
            "Sacramento (Script fino retro)"
        ]

        # Cargar configuración local
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.sales_db_path = None
        self.saved_target_dirs = []
        self.saved_git_path = None
        self.git_path = None
        self.custom_tags = {}
        
        self.cargar_configuracion()

        # Iniciar búsqueda de Git en segundo plano
        threading.Thread(target=self.inicializar_git_path, daemon=True).start()

        # Resolver directorios de destino
        self.target_dirs = []
        if self.saved_target_dirs:
            for d in self.saved_target_dirs:
                if os.path.exists(d) and os.path.isdir(d):
                    self.target_dirs.append(d)

        # Si no hay directorios válidos en la configuración, buscar los predeterminados
        if not self.target_dirs:
            self.target_dirs = [self.base_dir]
            user_home = os.path.expanduser("~")
            rutas_default = [
                r"D:\CARRITO BENDITO TALLER\GitHub\bendito-taller-carrito",
                r"D:\CARRITO BENDITO TALLER\GitHub\bendito-taller-web"
            ]
            for repo_name in ["bendito-taller-carrito", "bendito-taller-web"]:
                rutas_default.append(os.path.join(user_home, "Documents", "GitHub", repo_name))
                
            for path in rutas_default:
                if os.path.exists(path) and os.path.isdir(path):
                    path_abs = os.path.abspath(path)
                    if path_abs not in [os.path.abspath(d) for d in self.target_dirs]:
                        self.target_dirs.append(path)
            
            # Guardar la configuración inicial encontrada
            if len(self.target_dirs) > 1:
                self.guardar_configuracion()

        # Inicializar y resolver las rutas de archivos js/img
        self.productos_js_path = None
        self.cart_shared_js_path = None
        self.img_dir = None
        self.resolver_rutas_archivos()

        # Cargar base de datos existente
        self.productos_db = {}
        self.cargar_productos_db()

        # Cargar productos combinables existentes y mapear a sus grupos
        self.grupos_dict = {}
        self.combo_values = []
        self.display_to_code = {}
        self.obtener_productos_combinables()

        # --- VARIABLES PESTAÑA CREAR ---
        self.var_id = tk.StringVar()
        self.var_codigo = tk.StringVar()
        self.var_imagen_path = tk.StringVar()
        self.var_tipo = tk.StringVar(value="simple")
        self.var_es_combinable = tk.BooleanVar(value=False)
        self.var_filtro_combinables = tk.StringVar()
        self.combinables_widgets = [] # Lista de diccionarios {frame, var_grupo, combo}

        # Precios simples
        self.var_precio_mayor = tk.StringVar()
        self.var_precio_unitario = tk.StringVar()

        # Opciones/Medidas dinámicas
        self.opciones_widgets = [] # Lista de diccionarios {frame, medida_entry, mayor_entry, unitario_entry}

        # --- VARIABLES PESTAÑA MODIFICAR ---
        self.mod_var_id = tk.StringVar()
        self.mod_var_codigo = tk.StringVar()
        self.mod_var_imagen_path = tk.StringVar()
        self.mod_var_tipo = tk.StringVar(value="simple")
        self.mod_var_es_combinable = tk.BooleanVar(value=False)
        self.mod_combinables_widgets = []

        # Precios simples
        self.mod_var_precio_mayor = tk.StringVar()
        self.mod_var_precio_unitario = tk.StringVar()

        # Opciones/Medidas dinámicas
        self.mod_opciones_widgets = []

        # Variables de búsqueda
        self.var_busqueda = tk.StringVar()
        self.var_select_producto = tk.StringVar()

        # --- VARIABLES GESTOR DE VIDEOS ---
        self.var_nuevo_video_url = tk.StringVar()
        self.videos_list = []

        # --- VARIABLES PESTAÑA LEYENDAS ---
        self.var_leyenda_title = tk.StringVar()
        self.var_leyenda_subtitle = tk.StringVar()
        self.var_leyenda_bg_color = tk.StringVar(value="#E6BDB3")
        self.var_leyenda_bg_img = tk.StringVar()
        self.var_leyenda_title_size = tk.StringVar(value="38px")
        self.var_leyenda_title_color = tk.StringVar(value="#1c1c1c")
        self.var_leyenda_sub_size = tk.StringVar(value="22px")
        self.var_leyenda_sub_color = tk.StringVar(value="#1c1c1c")
        self.var_leyenda_seleccionada = tk.StringVar()
        self.var_leyenda_icon = tk.StringVar(value="")
        self.var_leyenda_icon_color = tk.StringVar(value="#00B8A6")
        self.var_leyenda_icon_size = tk.StringVar(value="40px")
        self.var_leyenda_font = tk.StringVar(value="Segoe UI (Sans-serif moderna)")
        self.var_leyenda_bold = tk.BooleanVar(value=False)
        self.var_leyenda_italic = tk.BooleanVar(value=False)
        self.var_leyenda_sub_bold = tk.BooleanVar(value=False)
        self.var_leyenda_sub_italic = tk.BooleanVar(value=False)

        self.var_leyenda_title.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_subtitle.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_bg_color.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_bg_img.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_title_size.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_title_color.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_sub_size.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_sub_color.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_icon.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_icon_color.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_icon_size.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_font.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_bold.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_italic.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_sub_bold.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())
        self.var_leyenda_sub_italic.trace_add("write", lambda *a: self.actualizar_previsualizacion_leyenda())

        self.setup_styles()
        self.build_ui()

        # Cargar lista para buscador
        self.actualizar_combo_buscar()

        # Binds para autogenerar ID y verificar duplicados (Pestaña Crear)
        self.var_codigo.trace_add("write", self.on_codigo_changed)
        self.var_id.trace_add("write", self.on_id_changed)

        # Rastrear cambios en las rutas de imágenes para actualizar la vista previa
        self.var_imagen_path.trace_add("write", lambda *a: self.actualizar_vista_previa_imagen())
        self.mod_var_imagen_path.trace_add("write", lambda *a: self.actualizar_vista_previa_imagen())

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Estilos generales para Combobox y otros widgets de ttk
        self.style.configure("TCombobox", 
                             fieldbackground=COLOR_WHITE,
                             background=COLOR_BORDER,
                             foreground=COLOR_TEXT,
                             bordercolor=COLOR_BORDER,
                             lightcolor=COLOR_BORDER,
                             darkcolor=COLOR_BORDER)
        self.root.option_add('*TCombobox*Listbox.background', COLOR_WHITE)
        self.root.option_add('*TCombobox*Listbox.foreground', COLOR_TEXT)
        self.root.option_add('*TCombobox*Listbox.selectBackground', COLOR_ACCENT)
        self.root.option_add('*TCombobox*Listbox.selectForeground', COLOR_WHITE)

    def cargar_productos_db(self):
        if not os.path.exists(self.productos_js_path):
            if self.solicitar_rutas_repositorios():
                if not os.path.exists(self.productos_js_path):
                    messagebox.showerror("Error", f"No se encontró el archivo productos.js en:\n{self.productos_js_path}")
                    return
            else:
                messagebox.showerror("Error", f"No se encontró el archivo productos.js en:\n{self.productos_js_path}")
                return
        
        try:
            with open(self.productos_js_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                json_str = content[start:end+1]
                self.productos_db = json.loads(json_str)
            else:
                messagebox.showerror("Error", "El formato de productos.js no es válido. No se encontró el objeto de productos.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer productos.js:\n{str(e)}")

    def obtener_productos_combinables(self):
        self.grupos_dict = {}
        self.combo_values = []
        self.display_to_group_id = {}
        
        if not os.path.exists(self.cart_shared_js_path):
            return
            
        try:
            with open(self.cart_shared_js_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 1. Parsear Set codigosIntercambiablesNorm
            set_match = re.search(r'const\s+codigosIntercambiablesNorm\s*=\s*new\s+Set\(\[\s*([\s\S]*?)\s*\]\);', content)
            if set_match:
                codes = [c.strip().strip('"').strip("'") for c in set_match.group(1).split(",") if c.strip()]
                for code in codes:
                    self.grupos_dict[code] = "intercambiables"
                    
            # 2. Parsear gruposCombinables
            m_array = re.search(r'const\s+gruposCombinables\s*=\s*\[([\s\S]*?)\];', content)
            if m_array:
                array_content = m_array.group(1)
                matches = re.finditer(r'\{\s*id:\s*["\']([^"\']+)["\'][\s\S]*?codigos:\s*\[([\s\S]*?)\]', array_content)
                for m in matches:
                    g_id = m.group(1)
                    if g_id not in GROUP_NAMES_MAP:
                        GROUP_NAMES_MAP[g_id] = g_id.replace("_", " ").title()
                    g_codes = [c.strip().strip('"').strip("'") for c in m.group(2).split(",") if c.strip()]
                    for code in g_codes:
                        self.grupos_dict[code] = g_id
        except Exception as e:
            print("Error al parsear productos combinables de cart-shared.js:", e)
            
        # Asociar con nombres descriptivos de productos.js
        for code, g_id in self.grupos_dict.items():
            name = self.obtener_nombre_de_producto(code)
            group_name = GROUP_NAMES_MAP.get(g_id, g_id.replace("_", " ").title())
            display = f"{name} ({group_name}) [{code}]"
            self.combo_values.append(display)
            self.display_to_code[display] = (code, g_id)
            
        self.combo_values.sort()

        # Agregar categorías especiales para selección rápida al inicio
        special_categories = [
            ("Categoría Corazones", "intercambiables"),
            ("Categoría Corazones Alados", "intercambiables"),
            ("Categoría Altares y Nichos", "altares_nichos")
        ]
        for name, g_id in reversed(special_categories):
            self.combo_values.insert(0, name)
            self.display_to_code[name] = (name, g_id)

    def resolver_ruta_imagen(self, path_str):
        if not path_str:
            return None
        
        path_str = path_str.strip()
        if not path_str:
            return None
            
        # Si es una ruta absoluta y existe, usarla
        if os.path.isabs(path_str) and os.path.exists(path_str):
            return path_str
            
        # Buscar en base_dir
        p = os.path.join(self.base_dir, path_str)
        if os.path.exists(p):
            return p
            
        # Buscar en target_dirs
        for d in self.target_dirs:
            p = os.path.join(d, path_str)
            if os.path.exists(p):
                return p
                
        return None

    def actualizar_vista_previa_imagen(self, *args):
        if not hasattr(self, 'lbl_image_preview') or not self.lbl_image_preview:
            return
            
        # Determinar de qué panel tomar la ruta
        # Si el panel de edición está activo (pack_info() o winfo_manager() indica que está visible)
        is_mod = False
        try:
            if self.edit_form_frame.winfo_manager():
                is_mod = True
        except:
            pass
            
        img_path_str = self.mod_var_imagen_path.get() if is_mod else self.var_imagen_path.get()
        
        # Si no hay imagen en el modo activo, intentar usar la del otro panel como respaldo
        if not img_path_str:
            img_path_str = self.var_imagen_path.get() if is_mod else self.mod_var_imagen_path.get()
            
        resolved_path = self.resolver_ruta_imagen(img_path_str)
        
        if resolved_path:
            try:
                img = Image.open(resolved_path)
                
                # Redimensionar manteniendo el aspect ratio (max 320x320)
                max_size = 320
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                self.preview_tk_img = ImageTk.PhotoImage(img)
                self.lbl_image_preview.config(image=self.preview_tk_img, text="")
                return
            except Exception as e:
                print(f"Error loading image preview: {e}")
                
        # Fallback si no hay imagen o hay error
        self.lbl_image_preview.config(image="", text="📷 Ninguna imagen seleccionada o cargada\n(La previsualización del producto aparecerá aquí)")

    def obtener_nombre_de_producto(self, code):
        if code in self.productos_db:
            p = self.productos_db[code]
            if "parent" in p:
                parent_id = p["parent"]
                preselect = p.get("preselect", "")
                parent_name = self.productos_db.get(parent_id, {}).get("nombre", parent_id)
                return f"{parent_name} ({preselect})"
            return p.get("nombre", code)
            
        code_clean = code.lower().replace("[^a-z0-9]", "")
        for key, p in self.productos_db.items():
            if key.lower().replace("[^a-z0-9]", "") == code_clean:
                if "parent" in p:
                    parent_id = p["parent"]
                    preselect = p.get("preselect", "")
                    parent_name = self.productos_db.get(parent_id, {}).get("nombre", parent_id)
                    return f"{parent_name} ({preselect})"
                return p.get("nombre", key)
        return code

    def obtener_display_name_para_grupo(self, pid, grupo_id):
        if grupo_id == "intercambiables":
            pid_norm = pid.lower()
            if pid_norm.startswith("ca") or pid_norm.startswith("bc1") or pid_norm.startswith("bc2") or pid_norm.startswith("bc3"):
                return "Categoría Corazones Alados"
            else:
                return "Categoría Corazones"
        elif grupo_id == "altares_nichos":
            return "Categoría Altares y Nichos"
        else:
            return GROUP_NAMES_MAP.get(grupo_id, grupo_id.replace("_", " ").title())

    def find_git_executable(self):
        if self.git_path:
            return self.git_path
        if self.saved_git_path and os.path.exists(self.saved_git_path):
            self.git_path = self.saved_git_path
            return self.git_path

        # 1. Intentar usar el git del PATH si está disponible
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            self.git_path = "git"
            self.guardar_configuracion()
            return "git"
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        # 2. Rutas comunes en Windows
        user_home = os.path.expanduser("~")
        common_paths = [
            r"C:\Program Files\Git\cmd\git.exe",
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\cmd\git.exe",
            os.path.join(user_home, r"AppData\Local\Programs\Git\cmd\git.exe")
        ]
        for p in common_paths:
            if os.path.exists(p):
                self.git_path = p
                self.guardar_configuracion()
                return p

        # 3. Intentar buscar en las carpetas de GitHub Desktop
        github_desktop_dir = os.path.join(user_home, r"AppData\Local\GitHubDesktop")
        if os.path.exists(github_desktop_dir):
            git_paths = []
            for root, dirs, files in os.walk(github_desktop_dir):
                if "git.exe" in files:
                    git_path = os.path.join(root, "git.exe")
                    if "\\cmd\\" in git_path:
                        git_paths.append(git_path)
            if git_paths:
                git_paths.sort(reverse=True)
                self.git_path = git_paths[0]
                self.guardar_configuracion()
                return self.git_path

        self.git_path = "git"
        return "git"

    def cargar_configuracion(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.sales_db_path = config.get("sales_db_path")
                    self.saved_target_dirs = config.get("target_dirs", [])
                    self.saved_git_path = config.get("git_path")
                    self.custom_tags = config.get("custom_tags", {})
            except Exception as e:
                print("Error al cargar config.json:", e)

    def guardar_configuracion(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({
                    "sales_db_path": self.sales_db_path,
                    "target_dirs": self.target_dirs,
                    "git_path": self.git_path,
                    "custom_tags": self.custom_tags
                }, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Error al guardar config.json:", e)

    def resolver_rutas_archivos(self):
        preferida = None
        max_mtime = 0
        for d in self.target_dirs:
            p_js = os.path.join(d, "productos.js")
            if os.path.exists(p_js) and os.path.getsize(p_js) > 2000: # Evitar archivos vacíos o dummy (menos de 2KB)
                mtime = os.path.getmtime(p_js)
                if mtime > max_mtime:
                    max_mtime = mtime
                    preferida = d

        if preferida:
            self.productos_js_path = os.path.join(preferida, "productos.js")
            self.cart_shared_js_path = os.path.join(preferida, "cart-shared.js")
            self.img_dir = os.path.join(preferida, "img")
        else:
            self.productos_js_path = os.path.join(self.base_dir, "productos.js")
            self.cart_shared_js_path = os.path.join(self.base_dir, "cart-shared.js")
            self.img_dir = os.path.join(self.base_dir, "img")

    def solicitar_rutas_repositorios(self):
        messagebox.showinfo(
            "Configuración de Repositorios",
            "No se encontraron automáticamente los directorios de los repositorios de GitHub.\n\n"
            "Por favor, selecciona la carpeta raíz de tu repositorio web o de carrito (donde se encuentra productos.js)."
        )
        folder = filedialog.askdirectory(title="Selecciona la carpeta del Repositorio (Bendito Taller)")
        if folder:
            folder_abs = os.path.abspath(folder)
            p_js = os.path.join(folder_abs, "productos.js")
            if os.path.exists(p_js):
                if folder_abs not in self.target_dirs:
                    self.target_dirs.append(folder_abs)
                
                # Intentar buscar un repositorio hermano (carrito o web)
                parent = os.path.dirname(folder_abs)
                for sibling in ["bendito-taller-carrito", "bendito-taller-web"]:
                    sibling_path = os.path.join(parent, sibling)
                    if os.path.exists(sibling_path) and os.path.isdir(sibling_path):
                        sib_abs = os.path.abspath(sibling_path)
                        if sib_abs not in self.target_dirs:
                            self.target_dirs.append(sib_abs)
                            
                self.guardar_configuracion()
                self.resolver_rutas_archivos()
                return True
            else:
                messagebox.showerror(
                    "Error",
                    f"La carpeta seleccionada no parece ser un repositorio válido porque no contiene el archivo 'productos.js'."
                )
        return False

    def inicializar_git_path(self):
        self.find_git_executable()

    def resolver_ruta_base_datos_ventas(self):
        # 1. Si ya se cargó desde la configuración y existe, usar esa
        if self.sales_db_path and os.path.exists(self.sales_db_path):
            return self.sales_db_path

        # 2. Buscar en ubicaciones comunes
        user_home = os.path.expanduser("~")
        search_roots = [
            os.path.dirname(self.base_dir),
            os.path.join(user_home, "Documents", "GitHub"),
            r"D:\\"
        ]
        for root in search_roots:
            if not os.path.exists(root) or not os.path.isdir(root):
                continue
            try:
                for name in os.listdir(root):
                    dir_path = os.path.join(root, name)
                    if os.path.isdir(dir_path) and "ventas" in name.lower() and "bendito" in name.lower():
                        db_candidate = os.path.join(dir_path, "data", "ventas_laser.db")
                        if os.path.exists(db_candidate):
                            self.sales_db_path = os.path.abspath(db_candidate)
                            self.guardar_configuracion()
                            return self.sales_db_path
            except Exception as e:
                print(f"Error buscando base de datos en {root}: {e}")
        return None

    def solicitar_ruta_ventas_db(self):
        messagebox.showinfo(
            "Configuración Necesaria",
            "No se encontró automáticamente la carpeta del programa de ventas 'ventas_bendito'.\n\n"
            "Por favor, selecciona la carpeta raíz del programa de ventas (ej: 'ventas_bendito 2.6') para poder sincronizar la base de datos."
        )
        folder = filedialog.askdirectory(title="Selecciona la carpeta de Ventas Bendito")
        if folder:
            db_candidate = os.path.join(folder, "data", "ventas_laser.db")
            if os.path.exists(db_candidate):
                self.sales_db_path = os.path.abspath(db_candidate)
                self.guardar_configuracion()
                messagebox.showinfo("Configuración Guardada", f"Base de datos de ventas vinculada con éxito:\n{self.sales_db_path}")
                return self.sales_db_path
            else:
                messagebox.showerror(
                    "Error",
                    f"No se encontró la base de datos en la carpeta seleccionada.\n"
                    f"Se esperaba encontrar el archivo:\n{os.path.join('data', 'ventas_laser.db')}"
                )
        return None

    def sincronizar_con_ventas_db(self, codigo_base, precios):
        db_path = self.resolver_ruta_base_datos_ventas()
        if not db_path:
            db_path = self.solicitar_ruta_ventas_db()
            if not db_path:
                print("No se configuró la base de datos de ventas. Sincronización omitida.")
                return False

        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            c.execute('''CREATE TABLE IF NOT EXISTS productos (
                        codigo TEXT PRIMARY KEY,
                        valor_unitario REAL,
                        valor_mayor REAL,
                        ruta_archivo TEXT)''')
            
            if precios["tipo"] == "simple":
                cod_db = codigo_base.upper().strip()
                unitario = float(precios["unitario"])
                mayor = float(precios["mayor"])
                
                c.execute("SELECT ruta_archivo FROM productos WHERE codigo=?", (cod_db,))
                row = c.fetchone()
                if row is not None:
                    c.execute("UPDATE productos SET valor_unitario=?, valor_mayor=? WHERE codigo=?",
                              (unitario, mayor, cod_db))
                else:
                    c.execute("INSERT INTO productos (codigo, valor_unitario, valor_mayor, ruta_archivo) VALUES (?, ?, ?, ?)",
                              (cod_db, unitario, mayor, ""))
            else:
                for opt in precios["opciones"]:
                    medida_val = opt["medida"].strip()
                    medida_limpia = medida_val.upper().replace(" ", "")
                    cod_db = f"{codigo_base.upper().strip()} {medida_limpia}"
                    unitario = float(opt["unitario"])
                    mayor = float(opt["mayor"])
                    
                    c.execute("SELECT ruta_archivo FROM productos WHERE codigo=?", (cod_db,))
                    row = c.fetchone()
                    if row is not None:
                        c.execute("UPDATE productos SET valor_unitario=?, valor_mayor=? WHERE codigo=?",
                                  (unitario, mayor, cod_db))
                    else:
                        c.execute("INSERT INTO productos (codigo, valor_unitario, valor_mayor, ruta_archivo) VALUES (?, ?, ?, ?)",
                                  (cod_db, unitario, mayor, ""))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print("Error al sincronizar con la base de datos de ventas:", e)
            messagebox.showwarning(
                "Advertencia de Sincronización",
                f"El producto se guardó para la web, pero hubo un problema al sincronizar con la base de datos de ventas:\n{str(e)}\n\n"
                f"No te preocupes, los cambios en la web se subirán a GitHub normalmente."
            )
            return False

    def normalize_string(self, text):
        normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        return re.sub(r'[^a-z0-9]', '', normalized.lower())

    def on_combo_keyrelease(self, event):
        value = event.widget.get().lower()
        if value == '':
            event.widget['values'] = self.combo_values
        else:
            data = []
            for item in self.combo_values:
                if value in item.lower():
                    data.append(item)
            event.widget['values'] = data

    def on_codigo_changed(self, *args):
        codigo = self.var_codigo.get()
        self.var_id.set(self.normalize_string(codigo))

    def on_id_changed(self, *args):
        pid = self.var_id.get().strip()
        if not pid:
            self.lbl_status_id.config(text="")
            self.btn_guardar.config(state="normal")
            self.lbl_auto_intercambiable.config(text="", fg=COLOR_TEXT)
            self.toggle_grupo_frame()
            return

        if pid in self.productos_db:
            prod = self.productos_db[pid]
            if "parent" in prod:
                det = f"(Hijo de: {prod['parent']})"
            else:
                det = f"({prod.get('nombre', 'Existente')})"
            self.lbl_status_id.config(text=f"⚠️ Este código ya existe {det}", fg=COLOR_DANGER)
        else:
            self.lbl_status_id.config(text="✓ Código disponible", fg="#2e7d32")

        # Detección automática para pre-seleccionar el grupo en el dropdown
        pid_norm = self.normalize_string(pid)
        grupo_auto = None
        if re.match(r"^co\d", pid_norm):
            grupo_auto = "Corazones"
        elif re.match(r"^ca\d", pid_norm):
            grupo_auto = "Corazones Alados"
        elif re.match(r"^cruz\d", pid_norm):
            grupo_auto = "Cruces"
        elif re.match(r"^(bc\d|florcora\d|setcorazones)", pid_norm):
            grupo_auto = "Corazones"

        if grupo_auto:
            self.var_es_combinable.set(True)
            self.toggle_grupo_frame()
            
            # Pre-seleccionar en el combobox de la primera fila
            if self.combinables_widgets:
                first_combo = self.combinables_widgets[0]
                first_combo["var_grupo"].set(grupo_auto)
            
            self.lbl_auto_intercambiable.config(
                text=f"✨ Prefijo detectado. Se ha pre-seleccionado el grupo '{grupo_auto}'.", 
                fg=COLOR_ACCENT
            )
        else:
            self.lbl_auto_intercambiable.config(text="", fg=COLOR_TEXT)
            self.toggle_grupo_frame()

    def build_ui(self):
        # Header principal de la App
        header_frame = tk.Frame(self.root, bg=COLOR_TEXT, height=60)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        lbl_title = tk.Label(header_frame, text="BENDITO TALLER - GESTIÓN DE PRODUCTOS", 
                             font=("Outfit", 14, "bold"), fg=COLOR_BG, bg=COLOR_TEXT)
        lbl_title.pack(pady=15, padx=20)

        # Crear Notebook para Pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # --- PESTAÑA 1: PRODUCTOS (CREAR Y MODIFICAR) ---
        self.tab_crear = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_crear, text="  Subir Productos  ")

        # Scrollbar y Canvas para Pestaña Productos
        self.canvas_crear = tk.Canvas(self.tab_crear, bg=COLOR_BG, highlightthickness=0)
        scrollbar_crear = ttk.Scrollbar(self.tab_crear, orient="vertical", command=self.canvas_crear.yview)
        
        self.scrollable_frame_crear = tk.Frame(self.canvas_crear, bg=COLOR_BG)
        self.scrollable_frame_crear.bind(
            "<Configure>",
            lambda e: self.update_scrollregion_and_reset(self.canvas_crear)
        )
        self.canvas_crear.create_window((0, 0), window=self.scrollable_frame_crear, anchor="nw")
        self.canvas_crear.configure(yscrollcommand=scrollbar_crear.set)

        self.canvas_crear.pack(side="left", fill="both", expand=True)
        scrollbar_crear.pack(side="right", fill="y")

        # Paneles lado a lado dentro de scrollable_frame_crear
        self.left_prod_panel = tk.Frame(self.scrollable_frame_crear, bg=COLOR_BG)
        self.left_prod_panel.pack(side="left", fill="both", expand=True, padx=(10, 15))
        
        self.prod_separator = tk.Frame(self.scrollable_frame_crear, bg=COLOR_BORDER, width=2)
        self.prod_separator.pack(side="left", fill="y", padx=15)
        
        self.right_prod_panel = tk.Frame(self.scrollable_frame_crear, bg=COLOR_BG)
        self.right_prod_panel.pack(side="left", fill="both", expand=True, padx=(15, 10))

        # --- PESTAÑA 3: BANNER ---
        self.tab_banners = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_banners, text="  Diseño de Tarjetas  ")

        # Scrollbar y Canvas para Pestaña Banners
        self.canvas_banners = tk.Canvas(self.tab_banners, bg=COLOR_BG, highlightthickness=0)
        scrollbar_banners = ttk.Scrollbar(self.tab_banners, orient="vertical", command=self.canvas_banners.yview)
        
        self.scrollable_frame_banners = tk.Frame(self.canvas_banners, bg=COLOR_BG)
        self.scrollable_frame_banners.bind(
            "<Configure>",
            lambda e: self.update_scrollregion_and_reset(self.canvas_banners)
        )
        self.canvas_banners.create_window((0, 0), window=self.scrollable_frame_banners, anchor="nw")
        self.canvas_banners.configure(yscrollcommand=scrollbar_banners.set)

        self.canvas_banners.pack(side="left", fill="both", expand=True)
        scrollbar_banners.pack(side="right", fill="y")

        # --- PESTAÑA 4: CARRUSEL Y BANNERS (FUSIONADA) ---
        self.tab_carrusel = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_carrusel, text="  Carrusel y Banners  ")

        # Scrollbar y Canvas para Pestaña Carrusel y Banners
        self.canvas_carrusel = tk.Canvas(self.tab_carrusel, bg=COLOR_BG, highlightthickness=0)
        scrollbar_carrusel = ttk.Scrollbar(self.tab_carrusel, orient="vertical", command=self.canvas_carrusel.yview)
        
        self.scrollable_frame_carrusel = tk.Frame(self.canvas_carrusel, bg=COLOR_BG)
        self.scrollable_frame_carrusel.bind(
            "<Configure>",
            lambda e: self.update_scrollregion_and_reset(self.canvas_carrusel)
        )
        self.canvas_carrusel.create_window((0, 0), window=self.scrollable_frame_carrusel, anchor="nw")
        self.canvas_carrusel.configure(yscrollcommand=scrollbar_carrusel.set)

        self.canvas_carrusel.pack(side="left", fill="both", expand=True)
        scrollbar_carrusel.pack(side="right", fill="y")

        # --- PESTAÑA 5: VIDEOS (NUEVA) ---
        self.tab_videos = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_videos, text="  Videos y Tutoriales  ")

        # Scrollbar y Canvas para Pestaña Videos
        self.canvas_videos = tk.Canvas(self.tab_videos, bg=COLOR_BG, highlightthickness=0)
        scrollbar_videos = ttk.Scrollbar(self.tab_videos, orient="vertical", command=self.canvas_videos.yview)
        
        self.scrollable_frame_videos = tk.Frame(self.canvas_videos, bg=COLOR_BG)
        self.scrollable_frame_videos.bind(
            "<Configure>",
            lambda e: self.update_scrollregion_and_reset(self.canvas_videos)
        )
        self.canvas_videos.create_window((0, 0), window=self.scrollable_frame_videos, anchor="nw")
        self.canvas_videos.configure(yscrollcommand=scrollbar_videos.set)

        self.canvas_videos.pack(side="left", fill="both", expand=True)
        scrollbar_videos.pack(side="right", fill="y")

        # --- PESTAÑA 6: PAGINA (NUEVA) ---
        self.tab_pagina = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.tab_pagina, text="  Página  ")

        # Binds de scroll de ratón y cambio de pestaña
        self.canvas_crear.bind_all("<MouseWheel>", self.on_mousewheel)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Construir contenido
        self.build_crear_tab_ui(self.left_prod_panel)
        self.build_modificar_tab_ui(self.right_prod_panel)
        self.build_banners_tab_ui(self.scrollable_frame_banners)
        self.build_carrusel_tab_ui(self.scrollable_frame_carrusel)
        self.build_videos_tab_ui(self.scrollable_frame_videos)
        self.build_pagina_tab_ui(self.tab_pagina)

    def update_scrollregion_and_reset(self, canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas_height = canvas.winfo_height()
        bbox = canvas.bbox("all")
        if bbox:
            content_height = bbox[3] - bbox[1]
            if content_height <= canvas_height:
                canvas.yview_moveto(0.0)

    def on_mousewheel(self, event):
        try:
            # Ignorar el scroll del fondo si el cursor está sobre un dropdown abierto o scrollbar
            widget_class = event.widget.winfo_class()
            if widget_class in ("Listbox", "Scrollbar", "TCombobox", "Combobox"):
                return
                
            selected = self.notebook.select()
            
            def scroll_if_needed(canvas):
                canvas_height = canvas.winfo_height()
                bbox = canvas.bbox("all")
                if bbox:
                    content_height = bbox[3] - bbox[1]
                    if content_height > canvas_height:
                        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                else:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

            if selected == str(self.tab_crear):
                scroll_if_needed(self.canvas_crear)
            elif selected == str(self.tab_banners):
                scroll_if_needed(self.canvas_banners)
            elif selected == str(self.tab_carrusel):
                scroll_if_needed(self.canvas_carrusel)
            elif selected == str(self.tab_videos):
                scroll_if_needed(self.canvas_videos)
        except Exception as e:
            pass

    def build_crear_tab_ui(self, parent):
        # Contenedor principal de creación
        main_container = tk.Frame(parent, bg=COLOR_BG, padx=30, pady=20)
        main_container.pack(fill="both", expand=True)

        # ========================================================
        # SECCIÓN 1: DATOS BÁSICOS
        # ========================================================
        card_basicos = tk.LabelFrame(main_container, text=" Datos del Producto ", 
                                     font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                     bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        card_basicos.pack(fill="x", pady=10)

        # Nombre en pedido
        tk.Label(card_basicos, text="Nombre de producto:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        entry_codigo = tk.Entry(card_basicos, textvariable=self.var_codigo, font=("Segoe UI", 10),
                                relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE)
        entry_codigo.grid(row=0, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        entry_codigo.focus()

        # ID de producto (Autogenerado)
        tk.Label(card_basicos, text="Código ID (sistema):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        entry_id = tk.Entry(card_basicos, textvariable=self.var_id, font=("Segoe UI", 10),
                            relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE)
        entry_id.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        # Etiqueta de estado para ID duplicado
        self.lbl_status_id = tk.Label(card_basicos, text="", font=("Segoe UI", 9, "italic"), bg=COLOR_BG)
        self.lbl_status_id.grid(row=1, column=2, sticky="w", padx=10)

        # Imagen del producto
        tk.Label(card_basicos, text="Foto del Producto:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=3, column=0, sticky="w", pady=6)
        
        img_select_frame = tk.Frame(card_basicos, bg=COLOR_BG)
        img_select_frame.grid(row=3, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        entry_img = tk.Entry(img_select_frame, textvariable=self.var_imagen_path, font=("Segoe UI", 9),
                             state="readonly", relief="solid", bd=1, bg=COLOR_CARD)
        entry_img.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_browse = tk.Button(img_select_frame, text="Buscar Imagen...", command=self.seleccionar_imagen,
                               bg=COLOR_TEXT, fg=COLOR_BG, activebackground="#362720", 
                               activeforeground=COLOR_BG, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=10)
        btn_browse.pack(side="right")

        card_basicos.grid_columnconfigure(1, weight=1)

        # ========================================================
        # SECCIÓN 2: COMBINACIÓN Y GRUPOS
        # ========================================================
        card_grupo = tk.LabelFrame(main_container, text=" Lógica de Precios por Mayor / Combinación ", 
                                   font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                   bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        card_grupo.pack(fill="x", pady=10)

        # Checkbox para combinable
        chk_combinable = tk.Checkbutton(card_grupo, text="¿Es un producto combinable con otros para el precio por mayor?",
                                        variable=self.var_es_combinable, command=self.toggle_grupo_frame,
                                        font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, 
                                        activebackground=COLOR_BG, activeforeground=COLOR_TEXT, selectcolor=COLOR_WHITE)
        chk_combinable.pack(anchor="w")

        # Label para indicar combinación automática
        self.lbl_auto_intercambiable = tk.Label(card_grupo, text="", font=("Segoe UI", 9, "italic"), bg=COLOR_BG)
        self.lbl_auto_intercambiable.pack(anchor="w", pady=(5, 0))

        # Contenedor para el dropdown del grupo
        self.grupo_select_frame = tk.Frame(card_grupo, bg=COLOR_BG, pady=10)

        # Buscador/Filtro para combinaciones
        tk.Label(self.grupo_select_frame, text="Filtrar productos compatibles:", 
                 font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(anchor="w", pady=(0, 2))
        
        entry_filtro = tk.Entry(self.grupo_select_frame, textvariable=self.var_filtro_combinables, font=("Segoe UI", 10),
                                relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE)
        entry_filtro.pack(fill="x", pady=(0, 10))
        self.var_filtro_combinables.trace_add("write", self.on_filtro_combinables_changed)

        tk.Label(self.grupo_select_frame, text="Selecciona los productos con los que se combina:", 
                 font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(anchor="w", pady=(5, 5))

        # Contenedor para las filas dinámicas
        self.combinables_container = tk.Frame(self.grupo_select_frame, bg=COLOR_BG)
        self.combinables_container.pack(fill="x")

        # Botón para agregar otra combinación
        self.btn_add_combinable = tk.Button(self.grupo_select_frame, text="+ Agregar otra categoría compatible", 
                                            command=self.agregar_fila_combinable,
                                            bg=COLOR_TEXT, fg=COLOR_BG, activebackground="#362720", 
                                            activeforeground=COLOR_BG, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=12, pady=6)
        self.btn_add_combinable.pack(anchor="w", pady=10)

        # ========================================================
        # SECCIÓN 3: PRECIOS Y VARIANTES
        # ========================================================
        self.card_precios = tk.LabelFrame(main_container, text=" Precios y Formatos ", 
                                          font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                          bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        self.card_precios.pack(fill="x", pady=10)

        # Selector de Tipo (Simple vs Medidas)
        type_selector_frame = tk.Frame(self.card_precios, bg=COLOR_BG, pady=5)
        type_selector_frame.pack(fill="x")

        tk.Label(type_selector_frame, text="Tipo de Formato:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).pack(side="left", padx=(0, 20))

        rb_simple = tk.Radiobutton(type_selector_frame, text="Producto Único / Simple", variable=self.var_tipo, 
                                   value="simple", command=self.on_tipo_changed, font=("Segoe UI", 10),
                                   fg=COLOR_TEXT, bg=COLOR_BG, activebackground=COLOR_BG, selectcolor=COLOR_WHITE)
        rb_simple.pack(side="left", padx=10)

        rb_medidas = tk.Radiobutton(type_selector_frame, text="Con Medidas u Opciones", variable=self.var_tipo, 
                                    value="medidas", command=self.on_tipo_changed, font=("Segoe UI", 10),
                                    fg=COLOR_TEXT, bg=COLOR_BG, activebackground=COLOR_BG, selectcolor=COLOR_WHITE)
        rb_medidas.pack(side="left", padx=10)

        # Frame contenedor para controles de precio según tipo
        self.precios_content_frame = tk.Frame(self.card_precios, bg=COLOR_BG, pady=10)
        self.precios_content_frame.pack(fill="x")

        # Cargar interfaz inicial para tipo simple
        self.mostrar_campos_precio_simple()

        # ========================================================
        # BOTÓN GUARDAR Y ACCIONES
        # ========================================================
        btn_frame = tk.Frame(main_container, bg=COLOR_BG, pady=15)
        btn_frame.pack(fill="x")

        self.btn_guardar = tk.Button(btn_frame, text="💾 Guardar Producto", command=self.guardar_producto,
                                bg=COLOR_ACCENT, fg=COLOR_WHITE, activebackground=COLOR_ACCENT_HOVER, 
                                activeforeground=COLOR_WHITE, font=("Segoe UI", 11, "bold"), relief="flat", bd=0, padx=25, pady=12)
        self.btn_guardar.pack(side="left", padx=(0, 15))

        btn_cancelar = tk.Button(btn_frame, text="✕ Limpiar Campos", command=self.limpiar_formulario,
                                  bg=COLOR_CARD, fg=COLOR_TEXT, activebackground=COLOR_BORDER, 
                                  activeforeground=COLOR_TEXT, font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=15, pady=10)
        btn_cancelar.pack(side="left")

    def toggle_grupo_frame(self):
        if self.var_es_combinable.get():
            self.grupo_select_frame.pack(fill="x")
            if not self.combinables_widgets:
                self.agregar_fila_combinable()
        else:
            self.grupo_select_frame.pack_forget()

    def agregar_fila_combinable(self):
        row_frame = tk.Frame(self.combinables_container, bg=COLOR_BG, pady=4)
        row_frame.pack(fill="x")

        var_grupo = tk.StringVar()

        filtro = self.var_filtro_combinables.get().lower()
        valores_combo = self.combo_values
        if filtro:
            valores_combo = [item for item in self.combo_values if filtro in item.lower()]

        combo = ttk.Combobox(row_frame, values=valores_combo, textvariable=var_grupo, 
                             state="normal", font=("Segoe UI", 10))
        combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        combo.bind("<KeyRelease>", self.on_combo_keyrelease)

        if valores_combo:
            combo.current(0)

        # Botón para remover fila
        btn_remove = tk.Button(row_frame, text="✕", command=lambda: self.remover_fila_combinable(row_frame),
                               bg=COLOR_CARD, fg=COLOR_DANGER, activebackground=COLOR_BORDER,
                               activeforeground=COLOR_DANGER, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=6)
        btn_remove.pack(side="right")

        self.combinables_widgets.append({
            "frame": row_frame,
            "var_grupo": var_grupo,
            "combo": combo
        })

    def remover_fila_combinable(self, frame_to_remove):
        if len(self.combinables_widgets) <= 1:
            messagebox.showwarning("Advertencia", "Si el producto es combinable, debe tener al menos una combinación.")
            return

        for item in self.combinables_widgets:
            if item["frame"] == frame_to_remove:
                item["frame"].destroy()
                self.combinables_widgets.remove(item)
                break

    def on_filtro_combinables_changed(self, *args):
        filtro = self.var_filtro_combinables.get().lower()
        if not filtro:
            valores_combo = self.combo_values
        else:
            valores_combo = [item for item in self.combo_values if filtro in item.lower()]

        for item in self.combinables_widgets:
            item["combo"]['values'] = valores_combo

    def toggle_grupo_frame_mod(self):
        if self.mod_var_es_combinable.get():
            self.mod_grupo_select_frame.pack(fill="x")
            if not self.mod_combinables_widgets:
                self.agregar_fila_combinable_mod()
        else:
            self.mod_grupo_select_frame.pack_forget()

    def agregar_fila_combinable_mod(self):
        row_frame = tk.Frame(self.mod_combinables_container, bg=COLOR_BG, pady=4)
        row_frame.pack(fill="x")

        var_grupo = tk.StringVar()

        combo = ttk.Combobox(row_frame, values=self.combo_values, textvariable=var_grupo, 
                             state="normal", font=("Segoe UI", 10))
        combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        combo.bind("<KeyRelease>", self.on_combo_keyrelease)

        if self.combo_values:
            combo.current(0)

        # Botón para remover fila
        btn_remove = tk.Button(row_frame, text="✕", command=lambda: self.remover_fila_combinable_mod(row_frame),
                               bg=COLOR_CARD, fg=COLOR_DANGER, activebackground=COLOR_BORDER,
                               activeforeground=COLOR_DANGER, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=6)
        btn_remove.pack(side="right")

        self.mod_combinables_widgets.append({
            "frame": row_frame,
            "var_grupo": var_grupo,
            "combo": combo
        })

    def remover_fila_combinable_mod(self, frame_to_remove):
        if len(self.mod_combinables_widgets) <= 1:
            messagebox.showwarning("Advertencia", "Si el producto es combinable, debe tener al menos una combinación.")
            return

        for item in self.mod_combinables_widgets:
            if item["frame"] == frame_to_remove:
                item["frame"].destroy()
                self.mod_combinables_widgets.remove(item)
                break

    def on_tipo_changed(self):
        for child in self.precios_content_frame.winfo_children():
            child.destroy()
        self.opciones_widgets.clear()

        tipo = self.var_tipo.get()
        if tipo == "simple":
            self.mostrar_campos_precio_simple()
        else:
            self.mostrar_campos_precio_medidas()

    def mostrar_campos_precio_simple(self):
        lbl_info = tk.Label(self.precios_content_frame, text="Ingresa los valores numéricos correspondientes:",
                            font=("Segoe UI", 9, "italic"), bg=COLOR_BG, fg="#7f6c60")
        lbl_info.pack(anchor="w", pady=(0, 10))

        form_frame = tk.Frame(self.precios_content_frame, bg=COLOR_BG)
        form_frame.pack(fill="x")

        # Precio Unitario
        tk.Label(form_frame, text="Precio Unitario ($):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        entry_unitario = tk.Entry(form_frame, textvariable=self.var_precio_unitario, font=("Segoe UI", 10),
                                  relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE, width=20)
        entry_unitario.grid(row=0, column=1, sticky="w", pady=6, padx=(10, 30))

        # Precio Mayorista
        tk.Label(form_frame, text="Precio Mayorista ($):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=2, sticky="w", pady=6)
        entry_mayor = tk.Entry(form_frame, textvariable=self.var_precio_mayor, font=("Segoe UI", 10),
                               relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE, width=20)
        entry_mayor.grid(row=0, column=3, sticky="w", pady=6, padx=(10, 0))

    def mostrar_campos_precio_medidas(self):
        lbl_info = tk.Label(self.precios_content_frame, 
                            text="Ingresa las medidas del producto (ej: '20 cm', '30 cm', '3 mm') y sus respectivos precios:",
                            font=("Segoe UI", 9, "italic"), bg=COLOR_BG, fg="#7f6c60")
        lbl_info.pack(anchor="w", pady=(0, 10))

        # Cabecera de la tabla
        self.table_header = tk.Frame(self.precios_content_frame, bg=COLOR_BG)
        self.table_header.pack(fill="x")

        tk.Label(self.table_header, text="Medida / Opción", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, width=22, anchor="w").grid(row=0, column=0, padx=5, pady=2)
        tk.Label(self.table_header, text="Precio Mayor ($)", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, width=16, anchor="w").grid(row=0, column=1, padx=5, pady=2)
        tk.Label(self.table_header, text="Precio Unitario ($)", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, width=16, anchor="w").grid(row=0, column=2, padx=5, pady=2)
        
        # Contenedor para las filas dinámicas
        self.rows_container = tk.Frame(self.precios_content_frame, bg=COLOR_BG)
        self.rows_container.pack(fill="x")

        # Botón para agregar una nueva fila
        btn_add_opt = tk.Button(self.precios_content_frame, text="+ Agregar Medida / Opción", command=self.agregar_fila_opcion,
                                bg=COLOR_TEXT, fg=COLOR_BG, activebackground="#362720", 
                                activeforeground=COLOR_BG, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=12, pady=6)
        btn_add_opt.pack(anchor="w", pady=10)

        # Agregar las primeras dos filas por defecto
        self.agregar_fila_opcion()
        self.agregar_fila_opcion()
        
        if len(self.opciones_widgets) >= 2:
            self.opciones_widgets[0]["medida_entry"].insert(0, "20 cm")
            self.opciones_widgets[1]["medida_entry"].insert(0, "30 cm")

    def agregar_fila_opcion(self):
        row_frame = tk.Frame(self.rows_container, bg=COLOR_BG, pady=4)
        row_frame.pack(fill="x")

        entry_medida = tk.Entry(row_frame, font=("Segoe UI", 10), relief="solid", bd=1, bg=COLOR_WHITE, width=22)
        entry_medida.grid(row=0, column=0, padx=5)

        entry_mayor = tk.Entry(row_frame, font=("Segoe UI", 10), relief="solid", bd=1, bg=COLOR_WHITE, width=16)
        entry_mayor.grid(row=0, column=1, padx=5)

        entry_unitario = tk.Entry(row_frame, font=("Segoe UI", 10), relief="solid", bd=1, bg=COLOR_WHITE, width=16)
        entry_unitario.grid(row=0, column=2, padx=5)

        # Botón para remover fila
        btn_remove = tk.Button(row_frame, text="✕", command=lambda: self.remover_fila_opcion(row_frame),
                               bg=COLOR_CARD, fg=COLOR_DANGER, activebackground=COLOR_BORDER,
                               activeforeground=COLOR_DANGER, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=6)
        btn_remove.grid(row=0, column=3, padx=10)

        self.opciones_widgets.append({
            "frame": row_frame,
            "medida_entry": entry_medida,
            "mayor_entry": entry_mayor,
            "unitario_entry": entry_unitario
        })

    def remover_fila_opcion(self, frame_to_remove):
        if len(self.opciones_widgets) <= 1:
            messagebox.showwarning("Advertencia", "Un producto con medidas debe tener al menos una opción.")
            return

        for item in self.opciones_widgets:
            if item["frame"] == frame_to_remove:
                item["frame"].destroy()
                self.opciones_widgets.remove(item)
                break

    def seleccionar_imagen(self):
        pid = self.var_id.get().strip()
        if not pid:
            messagebox.showwarning("Falta Información", "Por favor ingresa primero el 'Nombre de producto' para generar el Código ID (sistema) antes de seleccionar la imagen.")
            return

        file_path = filedialog.askopenfilename(
            title="Seleccionar foto del producto",
            filetypes=[("Archivos de Imagen", "*.jpg *.jpeg *.png *.webp"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            BackgroundRemoverDialog(self.root, file_path, pid, self.target_dirs, self.var_imagen_path, is_modification=False)

    def limpiar_formulario(self):
        if messagebox.askyesno("Confirmar", "¿Seguro que deseas limpiar todos los campos del formulario?"):
            self.var_id.set("")
            self.var_codigo.set("")
            self.var_imagen_path.set("")
            self.var_tipo.set("simple")
            self.var_es_combinable.set(False)
            self.var_precio_mayor.set("")
            self.var_precio_unitario.set("")
            self.var_filtro_combinables.set("")
            self.lbl_auto_intercambiable.config(text="")
            
            for item in self.combinables_widgets:
                item["frame"].destroy()
            self.combinables_widgets.clear()

            self.toggle_grupo_frame()
            self.on_tipo_changed()

    def validar_datos(self):
        pid = self.var_id.get().strip()
        if not pid:
            messagebox.showerror("Error de Validación", "El campo 'Código ID' es requerido.")
            return False
        
        if not re.match("^[a-z0-9]+$", pid):
            messagebox.showerror("Error de Validación", "El Código ID sólo puede contener letras minúsculas y números (sin espacios ni acentos).")
            return False

        codigo = self.var_codigo.get().strip()
        if not codigo:
            messagebox.showerror("Error de Validación", "El campo 'Nombre de producto' es requerido.")
            return False

        imagen = self.var_imagen_path.get().strip()
        if not imagen or not os.path.exists(imagen):
            messagebox.showerror("Error de Validación", "Debes seleccionar una imagen válida del producto.")
            return False

        tipo = self.var_tipo.get()
        if tipo == "simple":
            try:
                unitario = int(self.var_precio_unitario.get().strip())
                mayor = int(self.var_precio_mayor.get().strip())
                if unitario <= 0 or mayor <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Error de Validación", "Los precios Mayorista y Unitario deben ser números enteros positivos mayores a cero.")
                return False
        else:
            if not self.opciones_widgets:
                messagebox.showerror("Error de Validación", "Debes ingresar al menos una Medida/Opción.")
                return False

            for idx, item in enumerate(self.opciones_widgets):
                medida = item["medida_entry"].get().strip()
                if not medida:
                    messagebox.showerror("Error de Validación", f"El campo 'Medida' en la fila {idx + 1} está vacío.")
                    return False
                
                try:
                    mayor = int(item["mayor_entry"].get().strip())
                    unitario = int(item["unitario_entry"].get().strip())
                    if unitario <= 0 or mayor <= 0:
                        raise ValueError()
                except ValueError:
                    messagebox.showerror("Error de Validación", f"Los precios en la fila {idx + 1} ('{medida}') deben ser números enteros positivos.")
                    return False

        if self.var_es_combinable.get():
            if not self.combinables_widgets:
                messagebox.showerror("Error de Validación", "Has marcado el producto como combinable pero no has agregado ninguna combinación.")
                return False
            for idx, item in enumerate(self.combinables_widgets):
                display_name = item["var_grupo"].get().strip()
                if not display_name:
                    messagebox.showerror("Error de Validación", f"El campo de combinación en la fila {idx + 1} está vacío.")
                    return False

        return True

    def guardar_producto(self):
        if not self.validar_datos():
            return

        nombre = self.var_codigo.get().strip()
        pid = self.var_id.get().strip()
        codigo = self.var_codigo.get().strip()
        src_imagen = self.var_imagen_path.get().strip()
        tipo = self.var_tipo.get()
        es_combinable = self.var_es_combinable.get()

        grupos_a_actualizar = set()
        if es_combinable:
            for idx, item in enumerate(self.combinables_widgets):
                display_name = item["var_grupo"].get().strip()
                grupo_id = None
                if display_name in self.display_to_code:
                    selected_code, grupo_id = self.display_to_code[display_name]
                else:
                    matched = False
                    for disp, (code, g_id) in self.display_to_code.items():
                        if disp.lower() == display_name.lower() or code.lower() == display_name.lower():
                            selected_code, grupo_id = code, g_id
                            matched = True
                            break
                    if not matched:
                        all_group_ids = set(self.grupos_dict.values())
                        if display_name in GROUP_NAMES_MAP or display_name in all_group_ids:
                            grupo_id = display_name
                        else:
                            messagebox.showerror("Error de Combinación", f"El producto o categoría '{display_name}' en la fila {idx + 1} no es válido.\nPor favor, selecciona un producto de la lista.")
                            return
                if grupo_id:
                    grupos_a_actualizar.add(grupo_id)

        if self.imagen_procesada_ia:
            ext = self.imagen_ext_ia
            dest_filename = f"{pid}{ext}"
            expected_img = f"img/{dest_filename}"
            if src_imagen != expected_img:
                for d in self.target_dirs:
                    old_path = os.path.join(d, src_imagen)
                    new_path = os.path.join(d, expected_img)
                    if os.path.exists(old_path) and old_path != new_path:
                        try:
                            shutil.move(old_path, new_path)
                        except Exception as e:
                            print(f"Error al renombrar imagen IA en {d}:", e)
                self.var_imagen_path.set(expected_img)
                src_imagen = expected_img
        else:
            _, ext = os.path.splitext(src_imagen.lower())
            dest_filename = f"{pid}.webp"

            for d in self.target_dirs:
                i_dir = os.path.join(d, "img")
                if not os.path.exists(i_dir):
                    os.makedirs(i_dir)
                dest_imagen_path = os.path.join(i_dir, dest_filename)
                
                if os.path.exists(src_imagen) and os.path.exists(dest_imagen_path) and os.path.samefile(src_imagen, dest_imagen_path):
                    continue

                success_img = False
                if HAS_PIL:
                    try:
                        img = Image.open(src_imagen)
                        max_w_h = 800
                        if img.width > max_w_h or img.height > max_w_h:
                            img.thumbnail((max_w_h, max_w_h), Image.Resampling.LANCZOS)
                        
                        img.save(dest_imagen_path, "WEBP", quality=80)
                        success_img = True
                    except Exception as e:
                        print(f"Error de Pillow al guardar imagen en {d}, intentando copia directa:", e)
                
                if not success_img:
                    try:
                        shutil.copy(src_imagen, dest_imagen_path)
                    except Exception as e:
                        print(f"Error al copiar imagen en {d}:", e)

        js_image_path = f"img/{dest_filename}"

        nuevo_producto = {
            "codigo": codigo,
            "nombre": nombre,
            "imagen": js_image_path,
            "tipo": tipo
        }

        productos_hijos = {}

        if tipo == "simple":
            nuevo_producto["unitario"] = int(self.var_precio_unitario.get().strip())
            nuevo_producto["mayor"] = int(self.var_precio_mayor.get().strip())
        else:
            nuevo_producto["opciones"] = []
            for item in self.opciones_widgets:
                medida_val = item["medida_entry"].get().strip()
                mayor_val = int(item["mayor_entry"].get().strip())
                unitario_val = int(item["unitario_entry"].get().strip())
                
                nuevo_producto["opciones"].append({
                    "medida": medida_val,
                    "mayor": mayor_val,
                    "unitario": unitario_val
                })

                medida_limpia = self.normalize_string(medida_val)
                child_id = f"{pid}{medida_limpia}"
                productos_hijos[child_id] = {
                    "parent": pid,
                    "preselect": medida_val
                }

        try:
            self.actualizar_productos_js(pid, nuevo_producto, productos_hijos)
            self.productos_db[pid] = nuevo_producto
            for cid, cdata in productos_hijos.items():
                self.productos_db[cid] = cdata
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Error al reescribir productos.js:\n{str(e)}")
            return

        cart_shared_modificado = False
        if es_combinable and grupos_a_actualizar:
            try:
                for grupo_id in grupos_a_actualizar:
                    codigos_a_agregar = []
                    if grupo_id == "intercambiables":
                        if tipo == "medidas":
                            for child_id in productos_hijos.keys():
                                codigos_a_agregar.append(child_id)
                        else:
                            codigos_a_agregar.append(pid)
                    else:
                        codigos_a_agregar.append(pid)

                    self.actualizar_cart_shared_js(grupo_id, codigos_a_agregar)
                cart_shared_modificado = True
            except Exception as e:
                messagebox.showerror("Advertencia", f"El producto se creó con éxito, pero no se pudo actualizar cart-shared.js automáticamente:\n{str(e)}")

        # Sincronizar con la base de datos de ventas local
        precios_sinc = {"tipo": tipo}
        if tipo == "simple":
            precios_sinc["unitario"] = int(self.var_precio_unitario.get().strip())
            precios_sinc["mayor"] = int(self.var_precio_mayor.get().strip())
        else:
            precios_sinc["opciones"] = []
            for item in self.opciones_widgets:
                precios_sinc["opciones"].append({
                    "medida": item["medida_entry"].get().strip(),
                    "unitario": int(item["unitario_entry"].get().strip()),
                    "mayor": int(item["mayor_entry"].get().strip())
                })
        self.sincronizar_con_ventas_db(codigo, precios_sinc)

        self.obtener_productos_combinables()
        self.actualizar_combo_buscar()
        self.subir_a_github_async(nombre, pid, dest_filename, cart_shared_modificado, es_modificacion=False)

    def limpiar_despues_de_guardar(self):
        self.var_id.set("")
        self.var_codigo.set("")
        self.var_imagen_path.set("")
        self.var_precio_unitario.set("")
        self.var_precio_mayor.set("")
        self.var_es_combinable.set(False)
        self.var_filtro_combinables.set("")
        self.lbl_auto_intercambiable.config(text="")

        for item in self.combinables_widgets:
            item["frame"].destroy()
        self.combinables_widgets.clear()

        self.obtener_productos_combinables()
        self.toggle_grupo_frame()
        self.on_tipo_changed()

    # ========================================================
    # MÉTODOS DE LA PESTAÑA MODIFICAR
    # ========================================================
    def build_modificar_tab_ui(self, parent):
        main_container = tk.Frame(parent, bg=COLOR_BG, padx=30, pady=20)
        main_container.pack(fill="both", expand=True)

        # ========================================================
        # BUSCADOR
        # ========================================================
        search_card = tk.LabelFrame(main_container, text=" Modificar Producto Existente ", 
                                    font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                    bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        search_card.pack(fill="x", pady=10)

        # Filtrar
        tk.Label(search_card, text="Filtrar por nombre/código:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        
        entry_filtrar = tk.Entry(search_card, textvariable=self.var_busqueda, font=("Segoe UI", 10),
                                 relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE)
        entry_filtrar.grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 0))
        self.var_busqueda.trace_add("write", self.on_busqueda_changed)

        # Seleccionar
        tk.Label(search_card, text="Seleccionar producto:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        
        self.combo_buscar = ttk.Combobox(search_card, textvariable=self.var_select_producto, font=("Segoe UI", 10), state="readonly")
        self.combo_buscar.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))
        self.combo_buscar.bind("<<ComboboxSelected>>", self.on_product_to_edit_selected)

        search_card.grid_columnconfigure(1, weight=1)

        # Placeholder
        self.lbl_select_placeholder = tk.Label(main_container, text="🔍 Por favor, busca y selecciona un producto arriba para comenzar a editar.",
                                               font=("Segoe UI", 12, "italic"), fg="#7f6c60", bg=COLOR_BG, pady=40)
        self.lbl_select_placeholder.pack(fill="x")

        # Edit Form Frame (inicialmente oculto)
        self.edit_form_frame = tk.Frame(main_container, bg=COLOR_BG)

        # Card de Vista Previa de Imagen del Producto
        self.preview_image_card = tk.LabelFrame(main_container, text=" Vista Previa de Imagen del Producto ", 
                                                font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                                bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        self.preview_image_card.pack(fill="both", expand=True, pady=10)
        
        self.lbl_image_preview = tk.Label(self.preview_image_card, text="📷 Ninguna imagen seleccionada o cargada\n(La previsualización del producto aparecerá aquí)", 
                                          font=("Segoe UI", 10, "italic"), fg="#7f6c60", bg=COLOR_BG, justify="center")
        self.lbl_image_preview.pack(fill="both", expand=True, pady=10)

        # --- SECCIONES INTERNAS DE EDIT FORM FRAME ---
        # SECCIÓN 1: DATOS BÁSICOS
        card_basicos = tk.LabelFrame(self.edit_form_frame, text=" Datos del Producto (Modificación) ", 
                                     font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                     bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        card_basicos.pack(fill="x", pady=10)

        # Nombre en pedido
        tk.Label(card_basicos, text="Nombre de producto:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        entry_codigo = tk.Entry(card_basicos, textvariable=self.mod_var_codigo, font=("Segoe UI", 10),
                                relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE)
        entry_codigo.grid(row=0, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))

        # ID de producto (Deshabilitado en edición)
        tk.Label(card_basicos, text="Código ID (sistema):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        self.mod_entry_id = tk.Entry(card_basicos, textvariable=self.mod_var_id, font=("Segoe UI", 10),
                                    state="disabled", relief="solid", bd=1, highlightthickness=0, bg=COLOR_CARD)
        self.mod_entry_id.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))

        # Imagen del producto
        tk.Label(card_basicos, text="Foto del Producto:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=3, column=0, sticky="w", pady=6)
        
        img_select_frame = tk.Frame(card_basicos, bg=COLOR_BG)
        img_select_frame.grid(row=3, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        entry_img = tk.Entry(img_select_frame, textvariable=self.mod_var_imagen_path, font=("Segoe UI", 9),
                             state="readonly", relief="solid", bd=1, bg=COLOR_CARD)
        entry_img.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_browse = tk.Button(img_select_frame, text="Cambiar Imagen...", command=self.seleccionar_imagen_mod,
                               bg=COLOR_TEXT, fg=COLOR_BG, activebackground="#362720", 
                               activeforeground=COLOR_BG, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=10)
        btn_browse.pack(side="right")

        card_basicos.grid_columnconfigure(1, weight=1)

        # ========================================================
        # SECCIÓN 2: COMBINACIÓN Y GRUPOS (Modificación)
        # ========================================================
        card_grupo = tk.LabelFrame(self.edit_form_frame, text=" Lógica de Precios por Mayor / Combinación ", 
                                   font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                   bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        card_grupo.pack(fill="x", pady=10)

        # Checkbox para combinable
        chk_combinable = tk.Checkbutton(card_grupo, text="¿Es un producto combinable con otros para el precio por mayor?",
                                        variable=self.mod_var_es_combinable, command=self.toggle_grupo_frame_mod,
                                        font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, 
                                        activebackground=COLOR_BG, activeforeground=COLOR_TEXT, selectcolor=COLOR_WHITE)
        chk_combinable.pack(anchor="w")

        # Contenedor para el dropdown del grupo
        self.mod_grupo_select_frame = tk.Frame(card_grupo, bg=COLOR_BG, pady=10)

        tk.Label(self.mod_grupo_select_frame, text="Selecciona los productos con los que se combina:", 
                 font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(anchor="w", pady=(0, 5))

        # Contenedor para las filas dinámicas
        self.mod_combinables_container = tk.Frame(self.mod_grupo_select_frame, bg=COLOR_BG)
        self.mod_combinables_container.pack(fill="x")

        # Botón para agregar otra combinación
        self.mod_btn_add_combinable = tk.Button(self.mod_grupo_select_frame, text="+ Agregar otro producto compatible", 
                                            command=self.agregar_fila_combinable_mod,
                                            bg=COLOR_TEXT, fg=COLOR_BG, activebackground="#362720", 
                                            activeforeground=COLOR_BG, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=12, pady=6)
        self.mod_btn_add_combinable.pack(anchor="w", pady=10)

        # SECCIÓN 3: PRECIOS Y VARIANTES
        self.mod_card_precios = tk.LabelFrame(self.edit_form_frame, text=" Precios y Formatos ", 
                                          font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                          bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        self.mod_card_precios.pack(fill="x", pady=10)

        # Selector de Tipo (Simple vs Medidas)
        type_selector_frame = tk.Frame(self.mod_card_precios, bg=COLOR_BG, pady=5)
        type_selector_frame.pack(fill="x")

        tk.Label(type_selector_frame, text="Tipo de Formato:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).pack(side="left", padx=(0, 20))

        rb_simple = tk.Radiobutton(type_selector_frame, text="Producto Único / Simple", variable=self.mod_var_tipo, 
                                   value="simple", command=self.on_tipo_changed_mod, font=("Segoe UI", 10),
                                   fg=COLOR_TEXT, bg=COLOR_BG, activebackground=COLOR_BG, selectcolor=COLOR_WHITE)
        rb_simple.pack(side="left", padx=10)

        rb_medidas = tk.Radiobutton(type_selector_frame, text="Con Medidas u Opciones", variable=self.mod_var_tipo, 
                                    value="medidas", command=self.on_tipo_changed_mod, font=("Segoe UI", 10),
                                    fg=COLOR_TEXT, bg=COLOR_BG, activebackground=COLOR_BG, selectcolor=COLOR_WHITE)
        rb_medidas.pack(side="left", padx=10)

        # Frame contenedor para controles de precio según tipo
        self.mod_precios_content_frame = tk.Frame(self.mod_card_precios, bg=COLOR_BG, pady=10)
        self.mod_precios_content_frame.pack(fill="x")

        # Cargar interfaz inicial para tipo simple
        self.mostrar_campos_precio_simple_mod()

        # BOTONES
        btn_frame = tk.Frame(self.edit_form_frame, bg=COLOR_BG, pady=15)
        btn_frame.pack(fill="x")

        self.mod_btn_guardar = tk.Button(btn_frame, text="💾 Guardar Cambios", command=self.guardar_producto_mod,
                                bg=COLOR_ACCENT, fg=COLOR_WHITE, activebackground=COLOR_ACCENT_HOVER, 
                                activeforeground=COLOR_WHITE, font=("Segoe UI", 11, "bold"), relief="flat", bd=0, padx=25, pady=12)
        self.mod_btn_guardar.pack(side="left", padx=(0, 15))

        self.mod_btn_eliminar = tk.Button(btn_frame, text="🗑️ Eliminar Producto", command=self.eliminar_producto,
                                bg=COLOR_DANGER, fg=COLOR_WHITE, activebackground=COLOR_DANGER_HOVER, 
                                activeforeground=COLOR_WHITE, font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=15, pady=10)
        self.mod_btn_eliminar.pack(side="left", padx=(0, 15))

        btn_cancelar = tk.Button(btn_frame, text="✕ Cancelar Edición", command=lambda: self.limpiar_formulario_mod(confirm=True),
                                  bg=COLOR_CARD, fg=COLOR_TEXT, activebackground=COLOR_BORDER, 
                                  activeforeground=COLOR_TEXT, font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=15, pady=10)
        btn_cancelar.pack(side="left")

    def actualizar_combo_buscar(self):
        self.buscar_combo_values = []
        self.display_to_id_buscar = {}
        
        for pid, p in self.productos_db.items():
            if "parent" not in p:
                nombre = p.get("nombre", pid)
                display = f"{nombre} [{pid}]"
                self.buscar_combo_values.append(display)
                self.display_to_id_buscar[display] = pid
                
        self.buscar_combo_values.sort()
        if hasattr(self, 'combo_buscar'):
            self.combo_buscar['values'] = self.buscar_combo_values

    def on_busqueda_changed(self, *args):
        val = self.var_busqueda.get().lower()
        if not val:
            self.combo_buscar['values'] = self.buscar_combo_values
        else:
            filtered = [item for item in self.buscar_combo_values if val in item.lower()]
            self.combo_buscar['values'] = filtered

    def on_product_to_edit_selected(self, event):
        display = self.var_select_producto.get()
        pid = self.display_to_id_buscar.get(display)
        if pid:
            self.cargar_producto_edicion(pid)

    def cargar_producto_edicion(self, pid):
        if pid not in self.productos_db:
            return

        p = self.productos_db[pid]
        
        # 1. Habilitar ID temporalmente para asignarle el valor
        self.mod_entry_id.config(state="normal")
        self.mod_var_id.set(pid)
        self.mod_entry_id.config(state="disabled")

        # 2. Asignar resto de variables básicas
        self.mod_var_codigo.set(p.get("codigo", p.get("nombre", pid)))
        self.mod_var_imagen_path.set(p.get("imagen", ""))
        self.mod_var_tipo.set(p.get("tipo", "simple"))

        # 3. Disparar el cambio de interfaz de precios
        self.on_tipo_changed_mod()

        # 4. Rellenar precios
        if self.mod_var_tipo.get() == "simple":
            self.mod_var_precio_unitario.set(str(p.get("unitario", "")))
            self.mod_var_precio_mayor.set(str(p.get("mayor", "")))
        else:
            # Eliminar filas antiguas
            for item in self.mod_opciones_widgets:
                item["frame"].destroy()
            self.mod_opciones_widgets.clear()

            # Rellenar opciones nuevas
            for option in p.get("opciones", []):
                self.agregar_fila_opcion_mod()
                self.mod_opciones_widgets[-1]["medida_entry"].insert(0, option.get("medida", ""))
                self.mod_opciones_widgets[-1]["mayor_entry"].insert(0, str(option.get("mayor", "")))
                self.mod_opciones_widgets[-1]["unitario_entry"].insert(0, str(option.get("unitario", "")))

        # 5. Escanear combinables
        grupos_encontrados = []
        if pid in self.grupos_dict:
            grupos_encontrados.append(self.grupos_dict[pid])
        
        # Buscar posibles códigos de hijos de medidas
        hijos_ids = [k for k, v in self.productos_db.items() if isinstance(v, dict) and v.get("parent") == pid]
        for hid in hijos_ids:
            if hid in self.grupos_dict:
                g_id = self.grupos_dict[hid]
                if g_id not in grupos_encontrados:
                    grupos_encontrados.append(g_id)

        # Destruir widgets antiguos de combinación
        for item in self.mod_combinables_widgets:
            item["frame"].destroy()
        self.mod_combinables_widgets.clear()

        if grupos_encontrados:
            self.mod_var_es_combinable.set(True)
            self.toggle_grupo_frame_mod()
            
            # Limpiar fila vacía por defecto que agrega automáticamente toggle_grupo_frame_mod
            for item in self.mod_combinables_widgets:
                item["frame"].destroy()
            self.mod_combinables_widgets.clear()
            
            for grupo_id in grupos_encontrados:
                self.agregar_fila_combinable_mod()
                display_name = self.obtener_display_name_para_grupo(pid, grupo_id)
                self.mod_combinables_widgets[-1]["var_grupo"].set(display_name)
        else:
            self.mod_var_es_combinable.set(False)
            self.toggle_grupo_frame_mod()

        # 6. Mostrar el formulario de edición y ocultar placeholder
        self.lbl_select_placeholder.pack_forget()
        self.edit_form_frame.pack(fill="both", expand=True)

    def on_tipo_changed_mod(self):
        for child in self.mod_precios_content_frame.winfo_children():
            child.destroy()
        self.mod_opciones_widgets.clear()

        tipo = self.mod_var_tipo.get()
        if tipo == "simple":
            self.mostrar_campos_precio_simple_mod()
        else:
            self.mostrar_campos_precio_medidas_mod()

    def mostrar_campos_precio_simple_mod(self):
        lbl_info = tk.Label(self.mod_precios_content_frame, text="Ingresa los valores numéricos correspondientes:",
                            font=("Segoe UI", 9, "italic"), bg=COLOR_BG, fg="#7f6c60")
        lbl_info.pack(anchor="w", pady=(0, 10))

        form_frame = tk.Frame(self.mod_precios_content_frame, bg=COLOR_BG)
        form_frame.pack(fill="x")

        # Precio Unitario
        tk.Label(form_frame, text="Precio Unitario ($):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        entry_unitario = tk.Entry(form_frame, textvariable=self.mod_var_precio_unitario, font=("Segoe UI", 10),
                                  relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE, width=20)
        entry_unitario.grid(row=0, column=1, sticky="w", pady=6, padx=(10, 30))

        # Precio Mayorista
        tk.Label(form_frame, text="Precio Mayorista ($):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=2, sticky="w", pady=6)
        entry_mayor = tk.Entry(form_frame, textvariable=self.mod_var_precio_mayor, font=("Segoe UI", 10),
                               relief="solid", bd=1, highlightthickness=0, bg=COLOR_WHITE, width=20)
        entry_mayor.grid(row=0, column=3, sticky="w", pady=6, padx=(10, 0))

    def mostrar_campos_precio_medidas_mod(self):
        lbl_info = tk.Label(self.mod_precios_content_frame, 
                            text="Ingresa las medidas del producto (ej: '20 cm', '30 cm', '3 mm') y sus respectivos precios:",
                            font=("Segoe UI", 9, "italic"), bg=COLOR_BG, fg="#7f6c60")
        lbl_info.pack(anchor="w", pady=(0, 10))

        # Cabecera de la tabla
        self.mod_table_header = tk.Frame(self.mod_precios_content_frame, bg=COLOR_BG)
        self.mod_table_header.pack(fill="x")

        tk.Label(self.mod_table_header, text="Medida / Opción", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, width=22, anchor="w").grid(row=0, column=0, padx=5, pady=2)
        tk.Label(self.mod_table_header, text="Precio Mayor ($)", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, width=16, anchor="w").grid(row=0, column=1, padx=5, pady=2)
        tk.Label(self.mod_table_header, text="Precio Unitario ($)", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG, width=16, anchor="w").grid(row=0, column=2, padx=5, pady=2)
        
        # Contenedor para las filas dinámicas
        self.mod_rows_container = tk.Frame(self.mod_precios_content_frame, bg=COLOR_BG)
        self.mod_rows_container.pack(fill="x")

        # Botón para agregar una nueva fila
        btn_add_opt = tk.Button(self.mod_precios_content_frame, text="+ Agregar Medida / Opción", command=self.agregar_fila_opcion_mod,
                                bg=COLOR_TEXT, fg=COLOR_BG, activebackground="#362720", 
                                activeforeground=COLOR_BG, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=12, pady=6)
        btn_add_opt.pack(anchor="w", pady=10)

    def agregar_fila_opcion_mod(self):
        row_frame = tk.Frame(self.mod_rows_container, bg=COLOR_BG, pady=4)
        row_frame.pack(fill="x")

        entry_medida = tk.Entry(row_frame, font=("Segoe UI", 10), relief="solid", bd=1, bg=COLOR_WHITE, width=22)
        entry_medida.grid(row=0, column=0, padx=5)

        entry_mayor = tk.Entry(row_frame, font=("Segoe UI", 10), relief="solid", bd=1, bg=COLOR_WHITE, width=16)
        entry_mayor.grid(row=0, column=1, padx=5)

        entry_unitario = tk.Entry(row_frame, font=("Segoe UI", 10), relief="solid", bd=1, bg=COLOR_WHITE, width=16)
        entry_unitario.grid(row=0, column=2, padx=5)

        # Botón para remover fila
        btn_remove = tk.Button(row_frame, text="✕", command=lambda: self.remover_fila_opcion_mod(row_frame),
                               bg=COLOR_CARD, fg=COLOR_DANGER, activebackground=COLOR_BORDER,
                               activeforeground=COLOR_DANGER, font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=6)
        btn_remove.grid(row=0, column=3, padx=10)

        self.mod_opciones_widgets.append({
            "frame": row_frame,
            "medida_entry": entry_medida,
            "mayor_entry": entry_mayor,
            "unitario_entry": entry_unitario
        })

    def remover_fila_opcion_mod(self, frame_to_remove):
        if len(self.mod_opciones_widgets) <= 1:
            messagebox.showwarning("Advertencia", "Un producto con medidas debe tener al menos una opción.")
            return

        for item in self.mod_opciones_widgets:
            if item["frame"] == frame_to_remove:
                item["frame"].destroy()
                self.mod_opciones_widgets.remove(item)
                break

    def seleccionar_imagen_mod(self):
        pid = self.mod_var_id.get().strip()
        if not pid:
            messagebox.showwarning("Falta Información", "Por favor selecciona primero un producto para editar antes de cambiar la imagen.")
            return

        file_path = filedialog.askopenfilename(
            title="Seleccionar foto del producto",
            filetypes=[("Archivos de Imagen", "*.jpg *.jpeg *.png *.webp"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            BackgroundRemoverDialog(self.root, file_path, pid, self.target_dirs, self.mod_var_imagen_path, is_modification=True)

    def limpiar_formulario_mod(self, confirm=True):
        if confirm:
            if not messagebox.askyesno("Confirmar", "¿Seguro que deseas cancelar la edición y limpiar los campos?"):
                return
        
        self.var_busqueda.set("")
        self.var_select_producto.set("")
        self.mod_var_id.set("")
        self.mod_var_codigo.set("")
        self.mod_var_imagen_path.set("")
        self.mod_var_tipo.set("simple")
        self.mod_var_es_combinable.set(False)
        self.mod_var_precio_unitario.set("")
        self.mod_var_precio_mayor.set("")

        for item in self.mod_combinables_widgets:
            item["frame"].destroy()
        self.mod_combinables_widgets.clear()

        # Ocultar formulario de edición y mostrar placeholder
        self.edit_form_frame.pack_forget()
        self.lbl_select_placeholder.pack(fill="x", pady=40)

    def validar_datos_mod(self):
        pid = self.mod_var_id.get().strip()
        if not pid:
            messagebox.showerror("Error de Validación", "El campo 'Código ID' es requerido.")
            return False

        codigo = self.mod_var_codigo.get().strip()
        if not codigo:
            messagebox.showerror("Error de Validación", "El campo 'Nombre de producto' es requerido.")
            return False

        imagen = self.mod_var_imagen_path.get().strip()
        if not imagen:
            messagebox.showerror("Error de Validación", "Debes seleccionar una imagen para el producto.")
            return False
            
        if imagen.startswith("img/"):
            # Imagen existente del proyecto, validar que exista en el subdirectorio img
            full_img_path = os.path.join(self.base_dir, imagen)
            if not os.path.exists(full_img_path):
                messagebox.showerror("Error de Validación", f"La imagen existente '{imagen}' no se encuentra en la carpeta del proyecto.")
                return False
        else:
            # Imagen local nueva
            if not os.path.exists(imagen):
                messagebox.showerror("Error de Validación", f"La imagen seleccionada no existe en tu computadora:\n{imagen}")
                return False

        tipo = self.mod_var_tipo.get()
        if tipo == "simple":
            try:
                unitario = int(self.mod_var_precio_unitario.get().strip())
                mayor = int(self.mod_var_precio_mayor.get().strip())
                if unitario <= 0 or mayor <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Error de Validación", "Los precios Mayorista y Unitario deben ser números enteros positivos mayores a cero.")
                return False
        else:
            if not self.mod_opciones_widgets:
                messagebox.showerror("Error de Validación", "Debes ingresar al menos una Medida/Opción.")
                return False

            for idx, item in enumerate(self.mod_opciones_widgets):
                medida = item["medida_entry"].get().strip()
                if not medida:
                    messagebox.showerror("Error de Validación", f"El campo 'Medida' en la fila {idx + 1} está vacío.")
                    return False
                
                try:
                    mayor = int(item["mayor_entry"].get().strip())
                    unitario = int(item["unitario_entry"].get().strip())
                    if unitario <= 0 or mayor <= 0:
                        raise ValueError()
                except ValueError:
                    messagebox.showerror("Error de Validación", f"Los precios en la fila {idx + 1} ('{medida}') deben ser números enteros positivos.")
                    return False

        if self.mod_var_es_combinable.get():
            if not self.mod_combinables_widgets:
                messagebox.showerror("Error de Validación", "Has marcado el producto como combinable pero no has agregado ninguna combinación.")
                return False
            for idx, item in enumerate(self.mod_combinables_widgets):
                display_name = item["var_grupo"].get().strip()
                if not display_name:
                    messagebox.showerror("Error de Validación", f"El campo de combinación en la fila {idx + 1} está vacío.")
                    return False

        return True

    def limpiar_codigos_de_cart_shared_js(self, codes_to_remove):
        for d in self.target_dirs:
            c_js = os.path.join(d, "cart-shared.js")
            if not os.path.exists(c_js):
                continue
            
            with open(c_js, "r", encoding="utf-8") as f:
                content = f.read()

            # 1. Limpiar de Set codigosIntercambiablesNorm
            pattern = r'(const\s+codigosIntercambiablesNorm\s*=\s*new\s+Set\(\[\s*)([\s\S]*?)(\s*\]\);)'
            match = re.search(pattern, content)
            if match:
                prefix = match.group(1)
                items_str = match.group(2)
                suffix = match.group(3)

                existing_items = [c.strip().strip('"').strip("'") for c in items_str.split(",") if c.strip()]
                new_items = [item for item in existing_items if item not in codes_to_remove]

                if len(new_items) != len(existing_items):
                    lines = []
                    for i in range(0, len(new_items), 6):
                        chunk = new_items[i:i+6]
                        line = ", ".join(f'"{item}"' for item in chunk)
                        lines.append("    " + line)
                    
                    new_items_str = ",\n".join(lines)
                    new_block = prefix + "\n" + new_items_str + "\n" + suffix
                    content = content.replace(match.group(0), new_block)

            # 2. Limpiar de gruposCombinables en gruposCombinables
            m_array = re.search(r'const\s+gruposCombinables\s*=\s*\[([\s\S]*?)\];', content)
            if m_array:
                array_content = m_array.group(1)
                matches = list(re.finditer(r'\{\s*id:\s*["\']([^"\']+)["\'][\s\S]*?codigos:\s*\[([\s\S]*?)\]', array_content))
                for m in matches:
                    g_id = m.group(1)
                    codigos_str = m.group(2)
                    
                    existing_codes = [c.strip().strip('"').strip("'") for c in codigos_str.split(",") if c.strip()]
                    new_codes = [c for c in existing_codes if c not in codes_to_remove]
                    
                    if len(new_codes) != len(existing_codes):
                        group_pattern = rf'({{\s*id:\s*["\']{g_id}["\'][\s\S]*?codigos:\s*\[)([^\]]*?)(\s*\])'
                        g_match = re.search(group_pattern, content)
                        if g_match:
                            g_prefix = g_match.group(1)
                            g_suffix = g_match.group(3)
                            indent = "            "
                            new_codigos_str = "\n" + ",\n".join(f'{indent}"{c}"' for c in new_codes) + "\n        "
                            new_group_block = g_prefix + new_codigos_str + g_suffix
                            content = content.replace(g_match.group(0), new_group_block)

            with open(c_js, "w", encoding="utf-8") as f:
                f.write(content)

    def guardar_producto_mod(self):
        if not self.validar_datos_mod():
            return

        nombre = self.mod_var_codigo.get().strip()
        pid = self.mod_var_id.get().strip()
        codigo = self.mod_var_codigo.get().strip()
        src_imagen = self.mod_var_imagen_path.get().strip()
        tipo = self.mod_var_tipo.get()
        es_combinable = self.mod_var_es_combinable.get()

        grupos_a_actualizar = set()
        if es_combinable:
            for idx, item in enumerate(self.mod_combinables_widgets):
                display_name = item["var_grupo"].get().strip()
                grupo_id = None
                if display_name in self.display_to_code:
                    selected_code, grupo_id = self.display_to_code[display_name]
                else:
                    matched = False
                    for disp, (code, g_id) in self.display_to_code.items():
                        if disp.lower() == display_name.lower() or code.lower() == display_name.lower():
                            selected_code, grupo_id = code, g_id
                            matched = True
                            break
                    if not matched:
                        all_group_ids = set(self.grupos_dict.values())
                        if display_name in GROUP_NAMES_MAP or display_name in all_group_ids:
                            grupo_id = display_name
                        else:
                            messagebox.showerror("Error de Combinación", f"El producto o categoría '{display_name}' en la fila {idx + 1} no es válido.\nPor favor, selecciona un producto de la lista.")
                            return
                if grupo_id:
                    grupos_a_actualizar.add(grupo_id)

        old_children_ids = [k for k, v in self.productos_db.items() if isinstance(v, dict) and v.get("parent") == pid]
        all_old_codes = [pid] + old_children_ids

        # 2. Limpiar de cart-shared.js los códigos viejos antes de guardar
        try:
            self.limpiar_codigos_de_cart_shared_js(all_old_codes)
        except Exception as e:
            print("Error al limpiar códigos antiguos de cart-shared.js:", e)

        # 3. Procesar imagen si es nueva
        if self.imagen_procesada_ia:
            ext = self.imagen_ext_ia
            dest_filename = f"{pid}{ext}"
            expected_img = f"img/{dest_filename}"
            if src_imagen != expected_img:
                for d in self.target_dirs:
                    old_path = os.path.join(d, src_imagen)
                    new_path = os.path.join(d, expected_img)
                    if os.path.exists(old_path) and old_path != new_path:
                        try:
                            shutil.move(old_path, new_path)
                        except Exception as e:
                            print(f"Error al renombrar imagen IA en {d}:", e)
                self.mod_var_imagen_path.set(expected_img)
                src_imagen = expected_img
            js_image_path = expected_img
        else:
            img_is_new = not src_imagen.startswith("img/")
            dest_filename = f"{pid}.webp"

            if img_is_new:
                _, ext = os.path.splitext(src_imagen.lower())
                for d in self.target_dirs:
                    i_dir = os.path.join(d, "img")
                    if not os.path.exists(i_dir):
                        os.makedirs(i_dir)
                    dest_imagen_path = os.path.join(i_dir, dest_filename)
                    
                    if os.path.exists(src_imagen) and os.path.exists(dest_imagen_path) and os.path.samefile(src_imagen, dest_imagen_path):
                        continue

                    success_img = False
                    if HAS_PIL:
                        try:
                            img = Image.open(src_imagen)
                            max_w_h = 800
                            if img.width > max_w_h or img.height > max_w_h:
                                img.thumbnail((max_w_h, max_w_h), Image.Resampling.LANCZOS)
                            
                            img.save(dest_imagen_path, "WEBP", quality=80)
                            success_img = True
                        except Exception as e:
                            print(f"Error de Pillow en {d}, intentando copia directa:", e)
                    
                    if not success_img:
                        try:
                            shutil.copy(src_imagen, dest_imagen_path)
                        except Exception as e:
                            print(f"Error al copiar imagen en {d}:", e)
                js_image_path = f"img/{dest_filename}"
            else:
                js_image_path = src_imagen

            # Asegurar que la imagen del producto existe en todos los repositorios de destino
            for d in self.target_dirs:
                i_dir = os.path.join(d, "img")
                dest_imagen_path = os.path.join(i_dir, dest_filename)
                src_lookup = None
                for od in self.target_dirs:
                    potential_src = os.path.join(od, js_image_path)
                    if os.path.exists(potential_src):
                        src_lookup = potential_src
                        break
                if src_lookup and not os.path.exists(dest_imagen_path):
                    try:
                        if not os.path.exists(i_dir):
                            os.makedirs(i_dir)
                        shutil.copy(src_lookup, dest_imagen_path)
                    except Exception as e:
                        print(f"Error al sincronizar imagen existente a {d}:", e)

        # 4. Crear el objeto del producto principal
        nuevo_producto = {
            "codigo": codigo,
            "nombre": nombre,
            "imagen": js_image_path,
            "tipo": tipo
        }

        productos_hijos = {}

        if tipo == "simple":
            nuevo_producto["unitario"] = int(self.mod_var_precio_unitario.get().strip())
            nuevo_producto["mayor"] = int(self.mod_var_precio_mayor.get().strip())
        else:
            nuevo_producto["opciones"] = []
            for item in self.mod_opciones_widgets:
                medida_val = item["medida_entry"].get().strip()
                mayor_val = int(item["mayor_entry"].get().strip())
                unitario_val = int(item["unitario_entry"].get().strip())
                
                nuevo_producto["opciones"].append({
                    "medida": medida_val,
                    "mayor": mayor_val,
                    "unitario": unitario_val
                })

                medida_limpia = self.normalize_string(medida_val)
                child_id = f"{pid}{medida_limpia}"
                productos_hijos[child_id] = {
                    "parent": pid,
                    "preselect": medida_val
                }

        # 5. Modificar productos.js
        try:
            self.actualizar_productos_js(pid, nuevo_producto, productos_hijos)
            # Actualizar base de datos en memoria local
            for hk in old_children_ids:
                if hk in self.productos_db:
                    del self.productos_db[hk]
            self.productos_db[pid] = nuevo_producto
            for cid, cdata in productos_hijos.items():
                self.productos_db[cid] = cdata
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Error al reescribir productos.js:\n{str(e)}")
            return

        # 6. Re-agregar a cart-shared.js de forma automática si pertenecía a algún grupo
        cart_shared_modificado = False
        if es_combinable and grupos_a_actualizar:
            try:
                for grupo_id in grupos_a_actualizar:
                    codigos_a_agregar = []
                    if grupo_id == "intercambiables":
                        if tipo == "medidas":
                            for child_id in productos_hijos.keys():
                                codigos_a_agregar.append(child_id)
                        else:
                            codigos_a_agregar.append(pid)
                    else:
                        codigos_a_agregar.append(pid)

                    self.actualizar_cart_shared_js(grupo_id, codigos_a_agregar)
                cart_shared_modificado = True
            except Exception as e:
                messagebox.showerror("Advertencia", f"El producto se modificó con éxito, pero no se pudo actualizar cart-shared.js automáticamente:\n{str(e)}")

        # Sincronizar con la base de datos de ventas local
        precios_sinc = {"tipo": tipo}
        if tipo == "simple":
            precios_sinc["unitario"] = int(self.mod_var_precio_unitario.get().strip())
            precios_sinc["mayor"] = int(self.mod_var_precio_mayor.get().strip())
        else:
            precios_sinc["opciones"] = []
            for item in self.mod_opciones_widgets:
                precios_sinc["opciones"].append({
                    "medida": item["medida_entry"].get().strip(),
                    "unitario": int(item["unitario_entry"].get().strip()),
                    "mayor": int(item["mayor_entry"].get().strip())
                })
        self.sincronizar_con_ventas_db(codigo, precios_sinc)

        self.obtener_productos_combinables()
        self.actualizar_combo_buscar()
        self.subir_a_github_async(nombre, pid, os.path.basename(js_image_path), cart_shared_modificado, es_modificacion=True)

    def eliminar_producto(self):
        pid = self.mod_var_id.get().strip()
        if not pid or pid not in self.productos_db:
            messagebox.showerror("Error", "No hay ningún producto seleccionado para eliminar.")
            return

        nombre = self.mod_var_codigo.get().strip()
        
        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar Eliminación", 
                                   f"⚠️ ¿Seguro que deseas eliminar permanentemente el producto '{nombre}' ({pid})?\n\n"
                                   f"Esto borrará sus datos en productos.js, sus combinaciones en cart-shared.js y su imagen del proyecto."):
            return

        # 1. Obtener códigos a eliminar (padre e hijos)
        old_children_ids = [k for k, v in self.productos_db.items() if isinstance(v, dict) and v.get("parent") == pid]
        all_codes = [pid] + old_children_ids

        # 2. Eliminar de cart-shared.js
        try:
            self.limpiar_codigos_de_cart_shared_js(all_codes)
        except Exception as e:
            print("Error al limpiar de cart-shared.js:", e)

        # 3. Eliminar imagen física (Se conserva el archivo para evitar romper imágenes compartidas con el carrusel u otras secciones)
        p = self.productos_db[pid]
        img_path = p.get("imagen")
        image_filename = ""
        if img_path and img_path.startswith("img/"):
            image_filename = os.path.basename(img_path)

        # 4. Eliminar de productos.js
        try:
            self.eliminar_producto_de_js(pid, old_children_ids)
            
            # Eliminar localmente de productos_db
            if pid in self.productos_db:
                del self.productos_db[pid]
            for hk in old_children_ids:
                if hk in self.productos_db:
                    del self.productos_db[hk]
        except Exception as e:
            messagebox.showerror("Error al Eliminar", f"No se pudo completar la eliminación en productos.js:\n{str(e)}")
            return

        # 5. Refrescar datos
        self.obtener_productos_combinables()
        self.actualizar_combo_buscar()
        
        # 6. Subir cambios a GitHub asíncronamente
        self.subir_a_github_async_eliminar(nombre, pid, image_filename)

    def eliminar_producto_de_js(self, pid, child_ids):
        for d in self.target_dirs:
            p_js = os.path.join(d, "productos.js")
            if not os.path.exists(p_js):
                continue
            with open(p_js, "r", encoding="utf-8") as f:
                content = f.read()

            start = content.find("{")
            end = content.rfind("}")
            json_str = content[start:end+1]
            try:
                data = json.loads(json_str)
            except:
                data = {}

            if pid in data:
                del data[pid]
            for cid in child_ids:
                if cid in data:
                    del data[cid]

            new_json_str = json.dumps(data, indent=4, ensure_ascii=False)
            new_content = f"const productos = {new_json_str};\n"

            with open(p_js, "w", encoding="utf-8") as f:
                f.write(new_content)

    def subir_a_github_async_eliminar(self, nombre, pid, image_filename):
        # MODO LOCAL DESACTIVADO: Ahora se sincroniza con GitHub

        loading_popup = tk.Toplevel(self.root)
        loading_popup.title("Eliminando de Internet...")
        loading_popup.geometry("400x160")
        loading_popup.configure(bg=COLOR_BG)
        loading_popup.resizable(False, False)
        
        loading_popup.transient(self.root)
        loading_popup.grab_set()
        
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 80
        loading_popup.geometry(f"+{x}+{y}")
        
        lbl_msg = tk.Label(
            loading_popup, 
            text="🗑️ Eliminando y subiendo a GitHub...", 
            font=("Segoe UI", 12, "bold"), 
            fg=COLOR_TEXT, 
            bg=COLOR_BG
        )
        lbl_msg.pack(pady=(25, 10))
        
        lbl_sub = tk.Label(
            loading_popup, 
            text="Conectando con servidores de GitHub. Por favor espera...", 
            font=("Segoe UI", 9, "italic"), 
            fg="#7f6c60", 
            bg=COLOR_BG
        )
        lbl_sub.pack()
        
        def run_git():
            git_exe = self.find_git_executable()
            success_count = 0
            errors = []
            
            for d in self.target_dirs:
                if not os.path.exists(os.path.join(d, ".git")):
                    continue
                try:
                    files_to_commit = ["productos.js", "cart-shared.js"]
                    if image_filename:
                        img_path_rel = f"img/{image_filename}"
                        if not os.path.exists(os.path.join(d, img_path_rel)):
                            subprocess.run([git_exe, "rm", img_path_rel], cwd=d, capture_output=True)
                        else:
                            subprocess.run([git_exe, "add", img_path_rel], cwd=d, capture_output=True)
                    
                    subprocess.run([git_exe, "add"] + files_to_commit, cwd=d, check=True, capture_output=True)
                    
                    commit_msg = f"Eliminar producto: {nombre} ({pid})"
                    subprocess.run([git_exe, "commit", "-m", commit_msg], cwd=d, check=True, capture_output=True)
                    
                    # git pull --rebase para evitar rechazos si la rama remota está más avanzada
                    subprocess.run([git_exe, "pull", "--rebase"], cwd=d, check=True, capture_output=True)
                    
                    subprocess.run([git_exe, "push"], cwd=d, check=True, capture_output=True)
                    success_count += 1
                except subprocess.CalledProcessError as e:
                    err_out = e.stderr.decode("utf-8", errors="ignore") if e.stderr else str(e)
                    errors.append(f"{os.path.basename(d)}: {err_out.strip()}")
                except Exception as e:
                    errors.append(f"{os.path.basename(d)}: {str(e)}")
            
            if errors:
                err_msg = "\n".join(errors)
                if success_count > 0:
                    err_msg = f"Se eliminó en algunos repositorios, pero falló en otros:\n\n{err_msg}"
                self.root.after(0, lambda: self.on_delete_error(loading_popup, nombre, err_msg))
            else:
                self.root.after(0, lambda: self.on_delete_success(loading_popup, nombre))

        threading.Thread(target=run_git, daemon=True).start()

    def on_delete_success(self, popup, nombre):
        popup.destroy()
        messagebox.showinfo(
            "¡Éxito!",
            f"✓ ¡El producto '{nombre}' ha sido eliminado de la base de datos y de Internet con éxito!\n\n"
            f"Los cambios ya están publicados en la página web."
        )
        self.limpiar_formulario_mod(confirm=False)

    def on_delete_error(self, popup, nombre, err_msg):
        popup.destroy()
        messagebox.showwarning(
            "Guardado Localmente",
            f"El producto '{nombre}' se eliminó en tu computadora, pero no se pudieron subir los cambios a Internet.\n\n"
            f"Detalles del error:\n{err_msg}\n\n"
            f"No te preocupes, puedes abrir GitHub Desktop más tarde para subir los cambios manualmente."
        )
        self.limpiar_formulario_mod(confirm=False)

    # ========================================================
    # MÉTODOS COMPARTIDOS Y GIT
    # ========================================================
    def subir_a_github_async(self, nombre, pid, image_filename, cart_shared_modified, es_modificacion=False):
        # MODO LOCAL DESACTIVADO: Ahora se sincroniza con GitHub

        loading_popup = tk.Toplevel(self.root)
        loading_popup.title("Subiendo a Internet...")
        loading_popup.geometry("400x160")
        loading_popup.configure(bg=COLOR_BG)
        loading_popup.resizable(False, False)
        
        loading_popup.transient(self.root)
        loading_popup.grab_set()
        
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 80
        loading_popup.geometry(f"+{x}+{y}")
        
        lbl_msg = tk.Label(
            loading_popup, 
            text="🚀 Subiendo cambios a GitHub...", 
            font=("Segoe UI", 12, "bold"), 
            fg=COLOR_TEXT, 
            bg=COLOR_BG
        )
        lbl_msg.pack(pady=(25, 10))
        
        lbl_sub = tk.Label(
            loading_popup, 
            text="Conectando con servidores de GitHub. Por favor espera...", 
            font=("Segoe UI", 9, "italic"), 
            fg="#7f6c60", 
            bg=COLOR_BG
        )
        lbl_sub.pack()
        
        def run_git():
            git_exe = self.find_git_executable()
            success_count = 0
            errors = []
            
            for d in self.target_dirs:
                if not os.path.exists(os.path.join(d, ".git")):
                    continue
                try:
                    files_to_add = ["productos.js"]
                    img_path_rel = f"img/{image_filename}"
                    if os.path.exists(os.path.join(d, img_path_rel)):
                        files_to_add.append(img_path_rel)
                    if cart_shared_modified:
                        files_to_add.append("cart-shared.js")
                    
                    # git add
                    subprocess.run([git_exe, "add"] + files_to_add, cwd=d, check=True, capture_output=True)
                    
                    # git commit
                    verb = "Modificar" if es_modificacion else "Agregar"
                    commit_msg = f"{verb} producto: {nombre} ({pid})"
                    subprocess.run([git_exe, "commit", "-m", commit_msg], cwd=d, check=True, capture_output=True)
                    
                    # git pull --rebase para evitar rechazos si la rama remota está más avanzada
                    subprocess.run([git_exe, "pull", "--rebase"], cwd=d, check=True, capture_output=True)
                    
                    # git push
                    subprocess.run([git_exe, "push"], cwd=d, check=True, capture_output=True)
                    success_count += 1
                except subprocess.CalledProcessError as e:
                    err_out = e.stderr.decode("utf-8", errors="ignore") if e.stderr else str(e)
                    errors.append(f"{os.path.basename(d)}: {err_out.strip()}")
                except Exception as e:
                    errors.append(f"{os.path.basename(d)}: {str(e)}")
            
            if errors:
                err_msg = "\n".join(errors)
                if success_count > 0:
                    err_msg = f"Se subió con éxito a algunos repositorios, pero falló en otros:\n\n{err_msg}"
                self.root.after(0, lambda: self.on_upload_error(loading_popup, nombre, err_msg, es_modificacion))
            else:
                self.root.after(0, lambda: self.on_upload_success(loading_popup, nombre, es_modificacion))

        threading.Thread(target=run_git, daemon=True).start()

    def on_upload_success(self, popup, nombre, es_modificacion):
        popup.destroy()
        verb = "modificado" if es_modificacion else "guardado"
        messagebox.showinfo(
            "¡Éxito!",
            f"✓ ¡El producto '{nombre}' ha sido {verb} y publicado en Internet con éxito!\n\n"
            f"Ya está disponible en la página web."
        )
        if es_modificacion:
            self.limpiar_formulario_mod(confirm=False)
        else:
            self.limpiar_despues_de_guardar()

    def on_upload_error(self, popup, nombre, err_msg, es_modificacion):
        popup.destroy()
        verb = "modificó" if es_modificacion else "guardó"
        messagebox.showwarning(
            "Guardado Localmente",
            f"El producto '{nombre}' se {verb} en tu computadora, pero no se pudo subir automáticamente a Internet.\n\n"
            f"Detalles del error:\n{err_msg}\n\n"
            f"No te preocupes, puedes abrir GitHub Desktop más tarde para subir los cambios manualmente."
        )
        if es_modificacion:
            self.limpiar_formulario_mod(confirm=False)
        else:
            self.limpiar_despues_de_guardar()

    def actualizar_productos_js(self, pid, nuevo_prod, hijos):
        for d in self.target_dirs:
            p_js = os.path.join(d, "productos.js")
            if not os.path.exists(p_js):
                # Si no existe, podemos crear uno vacío básico
                with open(p_js, "w", encoding="utf-8") as f:
                    f.write("const productos = {};\n")

            with open(p_js, "r", encoding="utf-8") as f:
                content = f.read()

            start = content.find("{")
            end = content.rfind("}")
            json_str = content[start:end+1]
            try:
                data = json.loads(json_str)
            except:
                data = {}

            hijos_a_eliminar = [k for k, v in data.items() if isinstance(v, dict) and v.get("parent") == pid]
            for hk in hijos_a_eliminar:
                if hk in data:
                    del data[hk]

            data[pid] = nuevo_prod
            for cid, cdata in hijos.items():
                data[cid] = cdata

            new_json_str = json.dumps(data, indent=4, ensure_ascii=False)
            new_content = f"const productos = {new_json_str};\n"

            with open(p_js, "w", encoding="utf-8") as f:
                f.write(new_content)

    def actualizar_cart_shared_js(self, grupo_id, codigos):
        for d in self.target_dirs:
            c_js = os.path.join(d, "cart-shared.js")
            if not os.path.exists(c_js):
                continue
            
            with open(c_js, "r", encoding="utf-8") as f:
                content = f.read()

            if grupo_id == "intercambiables":
                pattern = r'(const\s+codigosIntercambiablesNorm\s*=\s*new\s+Set\(\[\s*)([\s\S]*?)(\s*\]\);)'
                match = re.search(pattern, content)
                if match:
                    prefix = match.group(1)
                    items_str = match.group(2)
                    suffix = match.group(3)

                    existing_items = [c.strip().strip('"').strip("'") for c in items_str.split(",") if c.strip()]
                    
                    added = False
                    for code in codigos:
                        if code not in existing_items:
                            existing_items.append(code)
                            added = True
                    
                    if added:
                        lines = []
                        for i in range(0, len(existing_items), 6):
                            chunk = existing_items[i:i+6]
                            line = ", ".join(f'"{item}"' for item in chunk)
                            lines.append("    " + line)
                        
                        new_items_str = ",\n".join(lines)
                        new_block = prefix + "\n" + new_items_str + "\n" + suffix
                        content = content.replace(match.group(0), new_block)
            else:
                pattern = rf'({{\s*id:\s*["\']{grupo_id}["\'][\s\S]*?codigos:\s*\[)([^\]]*?)(\s*\])'
                match = re.search(pattern, content)
                if match:
                    prefix = match.group(1)
                    codigos_str = match.group(2)
                    suffix = match.group(3)

                    existing_codes = [c.strip().strip('"').strip("'") for c in codigos_str.split(",") if c.strip()]
                    
                    added = False
                    for code in codigos:
                        if code not in existing_codes:
                            existing_codes.append(code)
                            added = True
                    
                    if added:
                        indent = "            "
                        new_codigos_str = "\n" + ",\n".join(f'{indent}"{c}"' for c in existing_codes) + "\n        "
                        new_block = prefix + new_codigos_str + suffix
                        content = content.replace(match.group(0), new_block)

            with open(c_js, "w", encoding="utf-8") as f:
                f.write(content)

    # ========================================================
    # FASE 3: DISEÑADOR DE BANNERS / TARJETAS
    # ========================================================
    def build_banners_tab_ui(self, parent):
        # Contenedor principal de la pestaña
        self.banners_container = tk.Frame(parent, bg=COLOR_BG, padx=20, pady=15)
        self.banners_container.pack(fill="both", expand=True)
        
        # Panel 1: Selección y Edición
        panel_edit = tk.Frame(self.banners_container, bg=COLOR_BG)
        panel_edit.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Separador Vertical 1
        sep1 = tk.Frame(self.banners_container, bg=COLOR_BORDER, width=2)
        sep1.pack(side="left", fill="y", padx=10)
        
        # Panel 3: Previsualización (Columna Central)
        panel_preview = tk.Frame(self.banners_container, bg=COLOR_BG)
        panel_preview.pack(side="left", fill="both", padx=10)
        
        # Separador Vertical 2
        sep2 = tk.Frame(self.banners_container, bg=COLOR_BORDER, width=2)
        sep2.pack(side="left", fill="y", padx=10)
        
        # Panel 2: Creación y Eliminación
        panel_create = tk.Frame(self.banners_container, bg=COLOR_BG)
        panel_create.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        # --- PANEL 1: EDICIÓN ---
        # LabelFrame de Selección
        card_sel = tk.LabelFrame(panel_edit, text=" Seleccionar Tarjeta ", 
                                 font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                 bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=12)
        card_sel.pack(fill="x", pady=(0, 8))
        
        tk.Label(card_sel, text="Elegir Tarjeta actual:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        
        self.var_banner_seleccionado = tk.StringVar()
        self.combo_banners = ttk.Combobox(card_sel, textvariable=self.var_banner_seleccionado, 
                                          state="readonly", font=("Segoe UI", 10))
        self.combo_banners.grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 0))
        self.combo_banners.bind("<<ComboboxSelected>>", self.seleccionar_tarjeta)
        
        # LabelFrame de Edición
        self.card_edit = tk.LabelFrame(panel_edit, text=" Editar Propiedades de Tarjeta ", 
                                       font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                       bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=12)
        self.card_edit.pack(fill="x", pady=8)
        
        # Título
        tk.Label(self.card_edit, text="Título (Mayúsculas):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        self.var_banner_title = tk.StringVar()
        self.entry_banner_title = tk.Entry(self.card_edit, textvariable=self.var_banner_title, font=("Segoe UI", 10),
                                           relief="solid", bd=1, bg=COLOR_WHITE)
        self.entry_banner_title.grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 0))
        self.var_banner_title.trace_add("write", lambda *a: self.actualizar_previsualizacion())
        
        # Subtítulo
        tk.Label(self.card_edit, text="Subtítulo:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        self.var_banner_subtitle = tk.StringVar()
        self.entry_banner_subtitle = tk.Entry(self.card_edit, textvariable=self.var_banner_subtitle, font=("Segoe UI", 10),
                                              relief="solid", bd=1, bg=COLOR_WHITE)
        self.entry_banner_subtitle.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))
        self.var_banner_subtitle.trace_add("write", lambda *a: self.actualizar_previsualizacion())
        
        # Etiqueta Flotante eliminada de aquí (movida a su propio recuadro)
        # Imagen de Fondo
        tk.Label(self.card_edit, text="Fondo de Imagen:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=3, column=0, sticky="w", pady=6)
        self.var_banner_bg_img = tk.StringVar()
        self.combo_banner_bg_img = ttk.Combobox(self.card_edit, textvariable=self.var_banner_bg_img, 
                                                state="readonly", font=("Segoe UI", 10))
        self.combo_banner_bg_img.grid(row=3, column=1, sticky="ew", pady=6, padx=(10, 0))
        self.combo_banner_bg_img.bind("<<ComboboxSelected>>", lambda e: self.actualizar_previsualizacion())
        
        # Estilo Letra
        tk.Label(self.card_edit, text="Estilo Letra:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=4, column=0, sticky="w", pady=6)
        self.var_banner_font = tk.StringVar(value="Merriweather (Serif clásica)")
        self.combo_banner_font = ttk.Combobox(self.card_edit, textvariable=self.var_banner_font,
                                              state="readonly", font=("Segoe UI", 10),
                                              values=self.FUENTES_LIST)
        self.combo_banner_font.grid(row=4, column=1, sticky="ew", pady=6, padx=(10, 0))
        self.combo_banner_font.bind("<<ComboboxSelected>>", lambda e: self.actualizar_previsualizacion())
        
        # Tamaño Letra Título (Movable Slider)
        tk.Label(self.card_edit, text="Tam. Título (px):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=5, column=0, sticky="w", pady=6)
        self.scale_banner_title_size = tk.Scale(self.card_edit, from_=10, to=48, orient="horizontal",
                                                bg=COLOR_BG, fg=COLOR_TEXT, highlightthickness=0,
                                                command=lambda val: self.actualizar_previsualizacion())
        self.scale_banner_title_size.set(24)
        self.scale_banner_title_size.grid(row=5, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        # Color Título
        tk.Label(self.card_edit, text="Color Título:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=6, column=0, sticky="w", pady=6)
        self.var_banner_title_color = tk.StringVar(value="#ffffff")
        frame_t_col = tk.Frame(self.card_edit, bg=COLOR_BG)
        frame_t_col.grid(row=6, column=1, sticky="w", pady=6, padx=(10, 0))
        entry_t_col = tk.Entry(frame_t_col, textvariable=self.var_banner_title_color, width=10, font=("Segoe UI", 10),
                               relief="solid", bd=1, bg=COLOR_WHITE)
        entry_t_col.pack(side="left", padx=(0, 5))
        self.var_banner_title_color.trace_add("write", lambda *a: self.actualizar_previsualizacion())
        btn_t_col = tk.Button(frame_t_col, text="🎨", bg=COLOR_WHITE, relief="flat", cursor="hand2",
                              command=self.elegir_color_banner_title)
        btn_t_col.pack(side="left")
        
        # Grosor Borde Título (Movable Slider)
        tk.Label(self.card_edit, text="Grosor Borde Tít. (px):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=7, column=0, sticky="w", pady=6)
        self.scale_banner_title_stroke_width = tk.Scale(self.card_edit, from_=0, to=8, resolution=0.5, orient="horizontal",
                                                        bg=COLOR_BG, fg=COLOR_TEXT, highlightthickness=0,
                                                        command=lambda val: self.actualizar_previsualizacion())
        self.scale_banner_title_stroke_width.set(2.5)
        self.scale_banner_title_stroke_width.grid(row=7, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        # Color Borde Título
        tk.Label(self.card_edit, text="Color Borde Tít.:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=8, column=0, sticky="w", pady=6)
        self.var_banner_title_stroke_color = tk.StringVar(value="#ffffff")
        frame_ts_col = tk.Frame(self.card_edit, bg=COLOR_BG)
        frame_ts_col.grid(row=8, column=1, sticky="w", pady=6, padx=(10, 0))
        entry_ts_col = tk.Entry(frame_ts_col, textvariable=self.var_banner_title_stroke_color, width=10, font=("Segoe UI", 10),
                                relief="solid", bd=1, bg=COLOR_WHITE)
        entry_ts_col.pack(side="left", padx=(0, 5))
        self.var_banner_title_stroke_color.trace_add("write", lambda *a: self.actualizar_previsualizacion())
        btn_ts_col = tk.Button(frame_ts_col, text="🎨", bg=COLOR_WHITE, relief="flat", cursor="hand2",
                               command=self.elegir_color_banner_title_stroke)
        btn_ts_col.pack(side="left")

        # Tamaño Letra Subtítulo (Movable Slider)
        tk.Label(self.card_edit, text="Tam. Subtítulo (px):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=9, column=0, sticky="w", pady=6)
        self.scale_banner_sub_size = tk.Scale(self.card_edit, from_=8, to=36, orient="horizontal",
                                              bg=COLOR_BG, fg=COLOR_TEXT, highlightthickness=0,
                                              command=lambda val: self.actualizar_previsualizacion())
        self.scale_banner_sub_size.set(14)
        self.scale_banner_sub_size.grid(row=9, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        # Color Subtítulo
        tk.Label(self.card_edit, text="Color Subtítulo:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=10, column=0, sticky="w", pady=6)
        self.var_banner_sub_color = tk.StringVar(value="#e5dacb")
        frame_s_col = tk.Frame(self.card_edit, bg=COLOR_BG)
        frame_s_col.grid(row=10, column=1, sticky="w", pady=6, padx=(10, 0))
        entry_s_col = tk.Entry(frame_s_col, textvariable=self.var_banner_sub_color, width=10, font=("Segoe UI", 10),
                               relief="solid", bd=1, bg=COLOR_WHITE)
        entry_s_col.pack(side="left", padx=(0, 5))
        self.var_banner_sub_color.trace_add("write", lambda *a: self.actualizar_previsualizacion())
        btn_s_col = tk.Button(frame_s_col, text="🎨", bg=COLOR_WHITE, relief="flat", cursor="hand2",
                              command=self.elegir_color_banner_sub)
        btn_s_col.pack(side="left")
        
        # Posición Línea (Divider vertical offset)
        tk.Label(self.card_edit, text="Posición Línea (px):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=11, column=0, sticky="w", pady=6)
        self.scale_banner_divider_top = tk.Scale(self.card_edit, from_=-40, to=40, orient="horizontal",
                                                 bg=COLOR_BG, fg=COLOR_TEXT, highlightthickness=0,
                                                 command=lambda val: self.actualizar_previsualizacion())
        self.scale_banner_divider_top.set(0)
        self.scale_banner_divider_top.grid(row=11, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        # Color Línea (Divider)
        tk.Label(self.card_edit, text="Color Línea:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=12, column=0, sticky="w", pady=6)
        self.var_banner_divider_color = tk.StringVar(value="#FFBF00")
        frame_d_col = tk.Frame(self.card_edit, bg=COLOR_BG)
        frame_d_col.grid(row=12, column=1, sticky="w", pady=6, padx=(10, 0))
        entry_d_col = tk.Entry(frame_d_col, textvariable=self.var_banner_divider_color, width=10, font=("Segoe UI", 10),
                               relief="solid", bd=1, bg=COLOR_WHITE)
        entry_d_col.pack(side="left", padx=(0, 5))
        self.var_banner_divider_color.trace_add("write", lambda *a: self.actualizar_previsualizacion())
        btn_d_col = tk.Button(frame_d_col, text="🎨", bg=COLOR_WHITE, relief="flat", cursor="hand2",
                              command=self.elegir_color_banner_divider)
        btn_d_col.pack(side="left")
        
        # Imagen Separador (Divider image)
        tk.Label(self.card_edit, text="Imagen Separador:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=13, column=0, sticky="w", pady=6)
                 
        frame_d_img = tk.Frame(self.card_edit, bg=COLOR_BG)
        frame_d_img.grid(row=13, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        self.var_banner_divider_img = tk.StringVar(value="Ninguno (Línea Sólida)")
        self.combo_banner_divider_img = ttk.Combobox(frame_d_img, textvariable=self.var_banner_divider_img, 
                                                     state="readonly", font=("Segoe UI", 9))
        self.combo_banner_divider_img.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.combo_banner_divider_img.bind("<<ComboboxSelected>>", lambda e: self.actualizar_previsualizacion())
        
        btn_divider_browse = tk.Button(frame_d_img, text="📁", bg=COLOR_WHITE, relief="flat", cursor="hand2",
                                       command=self.buscar_y_copiar_divider_img)
        btn_divider_browse.pack(side="left")
        
        # Variables para fondos base y de madera
        self.var_card_bg_base = tk.StringVar(value="img/fondo_rayas.png")
        self.var_card_bg_wood = tk.StringVar(value="img/fondo_letra.png")
        
        # --- PANEL 2: CREACIÓN ---
        card_create = tk.LabelFrame(panel_create, text=" Crear Nueva Tarjeta de Categoría ", 
                                    font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                    bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        card_create.pack(fill="x", pady=(0, 10))
        
        # Inicializar variables de Clase CSS y Enlace en segundo plano
        self.var_new_card_class = tk.StringVar()
        self.var_new_card_href = tk.StringVar()
        
        # Título
        tk.Label(card_create, text="Título:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        self.var_new_card_title = tk.StringVar()
        self.var_new_card_title.trace_add("write", self.autogenerar_campos_nueva_tarjeta)
        entry_new_title = tk.Entry(card_create, textvariable=self.var_new_card_title, font=("Segoe UI", 10),
                                   relief="solid", bd=1, bg=COLOR_WHITE)
        entry_new_title.grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        # Subtítulo
        tk.Label(card_create, text="Subtítulo:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        self.var_new_card_subtitle = tk.StringVar()
        entry_new_sub = tk.Entry(card_create, textvariable=self.var_new_card_subtitle, font=("Segoe UI", 10),
                                 relief="solid", bd=1, bg=COLOR_WHITE)
        entry_new_sub.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        # Fondo
        tk.Label(card_create, text="Fondo Inicial:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=2, column=0, sticky="w", pady=6)
        self.var_new_card_bg = tk.StringVar()
        self.combo_new_card_bg = ttk.Combobox(card_create, textvariable=self.var_new_card_bg, 
                                              state="readonly", font=("Segoe UI", 10))
        self.combo_new_card_bg.grid(row=2, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        # Botones de Acción
        btn_prev_banner = tk.Button(card_create, text="👁️ Previsualizar Nueva Tarjeta", 
                                    font=("Segoe UI", 10, "bold"), fg=COLOR_BG, bg=COLOR_TEXT, 
                                    activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                                    relief="flat", cursor="hand2", padx=10, pady=6,
                                    command=self.previsualizar_nueva_tarjeta)
        btn_prev_banner.grid(row=3, column=0, sticky="ew", pady=(12, 0), padx=(0, 5))
        
        btn_crear_banner = tk.Button(card_create, text="➕ Crear y Añadir Tarjeta", 
                                     font=("Segoe UI", 10, "bold"), fg=COLOR_BG, bg="#2e7d32", 
                                     activebackground=COLOR_BG, activeforeground="#2e7d32",
                                     relief="flat", cursor="hand2", padx=10, pady=6,
                                     command=self.crear_tarjeta)
        btn_crear_banner.grid(row=3, column=1, sticky="ew", pady=(12, 0), padx=(5, 0))
         
        # LabelFrame de Fondos de Tarjeta (debajo de Crear Nueva Tarjeta de Categoría)
        self.card_bg_edit = tk.LabelFrame(panel_create, text=" Editar Fondos de Tarjeta ", 
                                          font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                          bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=12)
        self.card_bg_edit.pack(fill="x", pady=(10, 0))
        
        # Fondo Base info/editable
        tk.Label(self.card_bg_edit, text="Fondo Base (Detrás):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=4)
                 
        frame_base_bg = tk.Frame(self.card_bg_edit, bg=COLOR_BG)
        frame_base_bg.grid(row=0, column=1, sticky="ew", pady=4, padx=(10, 0))
        
        self.combo_card_bg_base = ttk.Combobox(frame_base_bg, textvariable=self.var_card_bg_base, state="readonly", font=("Segoe UI", 9))
        self.combo_card_bg_base.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.combo_card_bg_base.bind("<<ComboboxSelected>>", lambda e: self.actualizar_previsualizacion())
        
        btn_base_browse = tk.Button(frame_base_bg, text="📁", bg=COLOR_WHITE, relief="flat", cursor="hand2",
                                    command=self.buscar_y_copiar_base_bg)
        btn_base_browse.pack(side="left")
                 
        # Silueta Madera info/editable
        tk.Label(self.card_bg_edit, text="Silueta Madera:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=1, column=0, sticky="w", pady=4)
                 
        frame_wood_bg = tk.Frame(self.card_bg_edit, bg=COLOR_BG)
        frame_wood_bg.grid(row=1, column=1, sticky="ew", pady=4, padx=(10, 0))
        
        self.combo_card_bg_wood = ttk.Combobox(frame_wood_bg, textvariable=self.var_card_bg_wood, state="readonly", font=("Segoe UI", 9))
        self.combo_card_bg_wood.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.combo_card_bg_wood.bind("<<ComboboxSelected>>", lambda e: self.actualizar_previsualizacion())
        
        btn_wood_browse = tk.Button(frame_wood_bg, text="📁", bg=COLOR_WHITE, relief="flat", cursor="hand2",
                                    command=self.buscar_y_copiar_wood_bg)
        btn_wood_browse.pack(side="left")
                 
        # Barra deslizante para el tamaño de fondo_letra.png
        tk.Label(self.card_bg_edit, text="Escala Madera (%):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=2, column=0, sticky="w", pady=6)
        self.scale_banner_wood_size = tk.Scale(self.card_bg_edit, from_=30, to=180, orient="horizontal",
                                               bg=COLOR_BG, fg=COLOR_TEXT, highlightthickness=0,
                                               command=lambda val: self.actualizar_previsualizacion())
        self.scale_banner_wood_size.set(100)
        self.scale_banner_wood_size.grid(row=2, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        self.card_bg_edit.grid_columnconfigure(1, weight=1)
        
        # --- NUEVO PANEL: Etiquetas Flotantes ---
        self.card_tag_edit = tk.LabelFrame(panel_create, text=" Etiquetas Flotantes ", 
                                          font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                          bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=12)
        self.card_tag_edit.pack(fill="x", pady=(10, 0))
        
        tk.Label(self.card_tag_edit, text="Etiqueta Flotante:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=4)
                 
        frame_tag_bg = tk.Frame(self.card_tag_edit, bg=COLOR_BG)
        frame_tag_bg.grid(row=0, column=1, sticky="ew", pady=4, padx=(10, 0))
        
        self.var_banner_badge = tk.StringVar()
        
        # Llenar con etiquetas predeterminadas y personalizadas
        tag_values = ["Ninguno", "Nuevos Diseños", "Oferta Especial"]
        if hasattr(self, "custom_tags"):
            tag_values.extend(self.custom_tags.keys())
            
        self.combo_banner_badge = ttk.Combobox(frame_tag_bg, textvariable=self.var_banner_badge, 
                                               values=tag_values,
                                               state="readonly", font=("Segoe UI", 9))
        self.combo_banner_badge.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.combo_banner_badge.bind("<<ComboboxSelected>>", lambda e: self.actualizar_previsualizacion())
        
        btn_add_tag = tk.Button(frame_tag_bg, text="➕", bg=COLOR_WHITE, relief="flat", cursor="hand2",
                                command=self.buscar_y_agregar_etiqueta)
        btn_add_tag.pack(side="left")
        self.card_tag_edit.grid_columnconfigure(1, weight=1)
        
        card_sel.grid_columnconfigure(1, weight=1)
        self.card_edit.grid_columnconfigure(1, weight=1)
        card_create.grid_columnconfigure(1, weight=1)
        
        # --- PANEL 3: PREVISUALIZACIÓN ---
        lbl_prev_title = tk.Label(panel_preview, text="VISTA PREVIA (VISTA WEB)", 
                                  font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, bg=COLOR_BG)
        lbl_prev_title.pack(pady=(0, 10))
        
        # Canvas de Previsualización (416x274 - Proporción exacta de la tarjeta web)
        self.canvas_prev = tk.Canvas(panel_preview, width=416, height=274, bg="#dfdfdf", bd=1, relief="solid")
        self.canvas_prev.pack(pady=10)
        
        # Botones de Acción en Panel 3 (Debajo del Canvas de Previsualización)
        actions_frame = tk.Frame(panel_preview, bg=COLOR_BG)
        actions_frame.pack(fill="x", pady=(10, 0))
        
        self.btn_guardar_banner = tk.Button(actions_frame, text="💾 Guardar Cambios en Tarjeta", 
                                            font=("Segoe UI", 10, "bold"), fg=COLOR_BG, bg=COLOR_TEXT, 
                                            activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                                            relief="flat", cursor="hand2", pady=8,
                                            command=self.guardar_tarjeta)
        self.btn_guardar_banner.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        self.btn_aplicar_todas = tk.Button(actions_frame, text="⚡ Aplicar Formato a Todas las Tarjetas", 
                                           font=("Segoe UI", 10, "bold"), fg=COLOR_WHITE, bg="#b08257", 
                                           activebackground=COLOR_BG, activeforeground="#b08257",
                                           relief="flat", cursor="hand2", pady=8,
                                           command=self.aplicar_formato_todas_tarjetas)
        self.btn_aplicar_todas.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.btn_restablecer_pred = tk.Button(actions_frame, text="🔄 Restablecer", 
                                              font=("Segoe UI", 10, "bold"), fg=COLOR_WHITE, bg="#31708f", 
                                              activebackground=COLOR_BG, activeforeground="#31708f",
                                              relief="flat", cursor="hand2", pady=8,
                                              command=self.restablecer_tarjeta_predefinida)
        self.btn_restablecer_pred.grid(row=2, column=0, sticky="ew", padx=(0, 2), pady=(5, 0))
        
        self.btn_fijar_pred = tk.Button(actions_frame, text="💾 Fijar Predefinido", 
                                        font=("Segoe UI", 10, "bold"), fg=COLOR_WHITE, bg="#777777", 
                                        activebackground=COLOR_BG, activeforeground="#777777",
                                        relief="flat", cursor="hand2", pady=8,
                                        command=self.fijar_tarjeta_predefinida)
        self.btn_fijar_pred.grid(row=2, column=1, sticky="ew", padx=(2, 0), pady=(5, 0))
        
        self.btn_eliminar_banner = tk.Button(actions_frame, text="🗑️ Eliminar Tarjeta Seleccionada", 
                                             font=("Segoe UI", 10, "bold"), fg=COLOR_BG, bg="#d9534f", 
                                             activebackground=COLOR_BG, activeforeground="#d9534f",
                                             relief="flat", cursor="hand2", pady=8,
                                             command=self.eliminar_tarjeta)
        self.btn_eliminar_banner.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)
        
        # Cargar los datos iniciales
        self.root.after(100, self.cargar_tarjetas_y_fondos)

    def autogenerar_campos_nueva_tarjeta(self, *args):
        titulo = self.var_new_card_title.get()
        # Normalizar caracteres con acentos y pasar a minúsculas
        normalized = unicodedata.normalize('NFKD', titulo).encode('ascii', 'ignore').decode('utf-8').lower()
        # Convertir espacios y caracteres especiales en guiones (formato slug)
        slug = re.sub(r'[^a-z0-9]+', '-', normalized).strip('-')
        
        if slug:
            self.var_new_card_class.set(f"card-{slug}")
            self.var_new_card_href.set(f"catalogo.html?category={slug}")
        else:
            self.var_new_card_class.set("")
            self.var_new_card_href.set("")

    def cargar_tarjetas_y_fondos(self):
        # 1. Leer index.html y parsear las tarjetas
        self.tarjetas_web = self.cargar_tarjetas_index()
        # 2. Leer styles.css y parsear las imágenes de fondo
        self.fondos_css = self.cargar_fondos_css()
        # 3. Cargar decoraciones flotantes del HTML
        self.cargar_decoraciones_html()
        
        if not self.tarjetas_web:
            return
            
        # Llenar el combobox de selección de tarjetas
        combo_values = [f"{t['title']} ({t['class']})" for t in self.tarjetas_web]
        self.combo_banners["values"] = combo_values
        
        # Buscar imágenes de fondo disponibles en la carpeta img/ de la web
        self.img_folder = None
        for d in self.target_dirs:
            p = os.path.join(d, "img")
            if os.path.exists(p):
                self.img_folder = p
                break
                
        if self.img_folder:
            fondos_files = [f"img/{f}" for f in os.listdir(self.img_folder) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
            fondos_files.sort()
            self.combo_banner_bg_img["values"] = fondos_files
            self.combo_new_card_bg["values"] = fondos_files
            try:
                self.combo_card_bg_base["values"] = fondos_files
                self.combo_card_bg_wood["values"] = fondos_files
                self.combo_banner_divider_img["values"] = ["Ninguno (Línea Sólida)"] + fondos_files
            except AttributeError:
                pass
            if fondos_files:
                self.var_new_card_bg.set(fondos_files[0])
                
        # Dejar la selección vacía por defecto
        self.combo_banners.set("Seleccionar Tarjeta...")
        self.var_banner_title.set("")
        self.var_banner_subtitle.set("")
        self.var_banner_badge.set("Ninguno")
        self.var_banner_bg_img.set("")
        try:
            self.var_banner_font.set("Outfit (Sans-serif moderna)")
            self.scale_banner_title_size.set(24)
            self.var_banner_title_color.set("#ffffff")
            self.scale_banner_sub_size.set(14)
            self.var_banner_sub_color.set("#e5dacb")
        except AttributeError:
            pass
        self.actualizar_previsualizacion()
        
        self.inicializar_tarjetas_predefinidas()
        self.cargar_leyendas_y_actualizar()
        self.cargar_videos_y_actualizar()
        self.actualizar_decoraciones_canvas()
        self.root.after(100, self.animar_decoraciones_loop)

    def cargar_decoraciones_html(self):
        self.decoraciones = []
        if not self.index_html_path or not os.path.exists(self.index_html_path):
            return
            
        try:
            with open(self.index_html_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Buscar contenedor de fondo
            back_match = re.search(r'<div\s+id="floating-decorations-container-back"[^>]*>([\s\S]*?)<\/div>', content)
            if back_match:
                self.parsear_imagenes_decorativas(back_match.group(1), "back")
                
            # Buscar contenedor del frente
            front_match = re.search(r'<div\s+id="floating-decorations-container-front"[^>]*>([\s\S]*?)<\/div>', content)
            if front_match:
                self.parsear_imagenes_decorativas(front_match.group(1), "front")
                
            # Buscar contenedor antiguo (por compatibilidad hacia atrás)
            old_match = re.search(r'<div\s+id="floating-decorations-container"[^>]*>([\s\S]*?)<\/div>', content)
            if old_match:
                self.parsear_imagenes_decorativas(old_match.group(1), "front")
                
        except Exception as e:
            print("Error al cargar decoraciones del HTML:", e)

    def parsear_imagenes_decorativas(self, html_content, default_layer):
        img_matches = re.finditer(r'<img\s+([^>]*class="[^"]*floating-deco[^"]*"[^>]*)>', html_content)
        for m in img_matches:
            attrs = m.group(1)
            src_match = re.search(r'src="([^"]+)"', attrs)
            style_match = re.search(r'style="([^"]+)"', attrs)
            if src_match and style_match:
                src = src_match.group(1)
                style = style_match.group(1)
                
                left_match = re.search(r'left:\s*([\d\.]+)px', style)
                top_match = re.search(r'top:\s*([\d\.]+)px', style)
                width_match = re.search(r'width:\s*([\d\.]+)px', style)
                height_match = re.search(r'height:\s*([^;]+)px', style)
                opacity_match = re.search(r'opacity:\s*([\d\.]+)', style)
                rotate_match = re.search(r'transform:\s*rotate\(([-\d\.]+)deg\)', style)
                
                left = int(float(left_match.group(1))) if left_match else 100
                top = int(float(top_match.group(1))) if top_match else 100
                width = int(float(width_match.group(1))) if width_match else 100
                
                height = -1
                if height_match:
                    h_val = height_match.group(1).strip()
                    if h_val != "auto":
                        try:
                            height = int(float(h_val))
                        except:
                            pass
                            
                opacity = float(opacity_match.group(1)) if opacity_match else 1.0
                angle = int(float(rotate_match.group(1))) if rotate_match else 0
                
                self.decoraciones.append({
                    "src": src,
                    "x_real": left,
                    "y_real": top,
                    "real_w": width,
                    "real_h": height,
                    "layer": default_layer,
                    "opacity": opacity,
                    "angle": angle
                })

    def cargar_tarjetas_index(self):
        self.index_html_path = None
        for d in self.target_dirs:
            path = os.path.join(d, "index.html")
            if os.path.exists(path):
                self.index_html_path = path
                break
        
        if not self.index_html_path:
            self.index_html_path = os.path.join(self.base_dir, "index.html")
            
        if not os.path.exists(self.index_html_path):
            return []
            
        try:
            with open(self.index_html_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Regex para encontrar todas las category-cards en index.html
            pattern = r'(<a\s+href="([^"]+)"\s+class="category-card\s+([^"]+)"[^>]*>[\s\S]*?<\/a>)'
            matches = re.finditer(pattern, content)
            
            tarjetas = []
            for m in matches:
                full_html = m.group(1)
                href = m.group(2)
                card_class = m.group(3).strip()
                
                # Buscar tag
                tag_match = re.search(r'<div\s+class="card-tag(?:\s+[^"]*)?">([\s\S]*?)<\/div>', full_html)
                tag = tag_match.group(1).replace("<br>", " ").replace("<br/>", " ").strip() if tag_match else ""
                
                # Buscar h2 data-text
                title_match = re.search(r'<h2\s+data-text="([^"]+)"', full_html)
                title = title_match.group(1) if title_match else ""
                
                # Buscar subtitle
                sub_match = re.search(r'<span\s+class="subtitle"[^>]*>([\s\S]*?)<\/span>', full_html)
                subtitle = sub_match.group(1).strip() if sub_match else ""
                h2_match = re.search(r'<h2\s+data-text="[^"]*"\s*([^>]*)>', full_html)
                h2_attrs = h2_match.group(1) if h2_match else ""
                title_font = self.extraer_estilo_inline(h2_attrs, "font-family")
                title_size = self.extraer_estilo_inline(h2_attrs, "font-size")
                title_color = self.extraer_estilo_inline(h2_attrs, "--title-color")
                if not title_color:
                    title_color = self.extraer_estilo_inline(h2_attrs, "color")
                
                title_stroke_color = self.extraer_estilo_inline(h2_attrs, "--title-stroke-color")
                title_stroke_width = self.extraer_estilo_inline(h2_attrs, "--title-stroke-width")
                
                # Buscar subtitle style
                sub_tag_match = re.search(r'<span\s+class="subtitle"\s*([^>]*)>', full_html)
                sub_attrs = sub_tag_match.group(1) if sub_tag_match else ""
                sub_font = self.extraer_estilo_inline(sub_attrs, "font-family")
                sub_size = self.extraer_estilo_inline(sub_attrs, "font-size")
                sub_color = self.extraer_estilo_inline(sub_attrs, "color")
                
                tarjetas.append({
                    "href": href,
                    "class": card_class,
                    "tag": tag,
                    "title": title,
                    "subtitle": subtitle,
                    "title_font": title_font,
                    "title_size": title_size,
                    "title_color": title_color,
                    "title_stroke_color": title_stroke_color,
                    "title_stroke_width": title_stroke_width,
                    "sub_font": sub_font,
                    "sub_size": sub_size,
                    "sub_color": sub_color,
                    "full_html": full_html
                })
            return tarjetas
        except Exception as e:
            print("Error al cargar tarjetas de index.html:", e)
            return []

    def cargar_fondos_css(self):
        self.styles_css_path = None
        for d in self.target_dirs:
            path = os.path.join(d, "styles.css")
            if os.path.exists(path):
                self.styles_css_path = path
                break
        
        if not self.styles_css_path:
            self.styles_css_path = os.path.join(self.base_dir, "styles.css")
            
        if not os.path.exists(self.styles_css_path):
            return {}
            
        try:
            with open(self.styles_css_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            pattern = r'\.([a-zA-Z0-9_-]+)\s+\.card-content::after\s*\{[^}]*?background-image:\s*url\(["\']?([^"\')]+)["\']?\)'
            matches = re.finditer(pattern, content)
            
            fondos = {}
            for m in matches:
                card_class = m.group(1).strip()
                img_path = m.group(2).strip()
                fondos[card_class] = img_path
            return fondos
        except Exception as e:
            print("Error al cargar fondos de styles.css:", e)
            return {}

    def seleccionar_tarjeta(self, event=None):
        idx = self.combo_banners.current()
        if idx == -1:
            return
            
        tarjeta = self.tarjetas_web[idx]
        self.var_banner_title.set(tarjeta["title"])
        self.var_banner_subtitle.set(tarjeta["subtitle"])
        
        # Badge
        tag = tarjeta["tag"]
        if "oferta" in tag.lower():
            self.var_banner_badge.set("Oferta Especial")
        elif "nuevos" in tag.lower():
            self.var_banner_badge.set("Nuevos Diseños")
        else:
            self.var_banner_badge.set("Ninguno")
            
        # Fondo
        card_class = tarjeta["class"]
        fondo_rel = self.fondos_css.get(card_class, "")
        self.var_banner_bg_img.set(fondo_rel)
        
        # Cargar estilos de la tarjeta seleccionada
        title_font = tarjeta.get("title_font", "")
        title_size = tarjeta.get("title_size", "")
        title_color = tarjeta.get("title_color", "")
        title_stroke_color = tarjeta.get("title_stroke_color", "")
        title_stroke_width = tarjeta.get("title_stroke_width", "")
        sub_font = tarjeta.get("sub_font", "")
        sub_size = tarjeta.get("sub_size", "")
        sub_color = tarjeta.get("sub_color", "")
        
        font_family_val = "Merriweather (Serif clásica)"
        if title_font:
            font_family_val = self.get_font_combobox_val(title_font)
        self.var_banner_font.set(font_family_val)
        
        try:
            t_size_num = int(re.search(r'\d+', title_size).group(0))
        except:
            t_size_num = 40
        try:
            self.scale_banner_title_size.set(t_size_num)
        except AttributeError:
            pass
            
        try:
            s_size_num = int(re.search(r'\d+', sub_size).group(0))
        except:
            s_size_num = 14
        try:
            self.scale_banner_sub_size.set(s_size_num)
        except AttributeError:
            pass
            
        self.var_banner_title_color.set(title_color if title_color else "#4b372d")
        self.var_banner_sub_color.set(sub_color if sub_color else "#4b372d")
        
        # Cargar grosor y color de borde
        try:
            ts_width_val = float(re.search(r'[\d\.]+', title_stroke_width).group(0))
        except:
            ts_width_val = 2.5
        try:
            self.scale_banner_title_stroke_width.set(ts_width_val)
        except AttributeError:
            pass
            
        self.var_banner_title_stroke_color.set(title_stroke_color if title_stroke_color else "#ffffff")
        
        # Cargar escala de madera
        scale_match = re.search(r'style="[^"]*--badge-scale\s*:\s*([^;"]+)', tarjeta["full_html"])
        if scale_match:
            try:
                scale_val = float(scale_match.group(1).strip())
                scale_percent = int(scale_val * 100)
            except:
                scale_percent = 100
        else:
            scale_percent = 100
            
        try:
            self.scale_banner_wood_size.set(scale_percent)
        except AttributeError:
            pass
            
        # Cargar Fondo Base (Detrás)
        card_bg_tag = re.search(r'<div\s+class="card-bg"\s*([^>]*)>', tarjeta["full_html"])
        base_bg_val = "img/fondo_rayas.png"
        if card_bg_tag:
            attrs = card_bg_tag.group(1)
            url_match = re.search(r'background-image:\s*url\([\'"]?([^\'"\)]+)[\'"]?\)', attrs)
            if url_match:
                base_bg_val = url_match.group(1).replace('\\', '/')
        self.var_card_bg_base.set(base_bg_val)
        
        # Cargar Silueta Madera
        wood_match = re.search(r'--wood-image:\s*url\([\'"]?([^\'"\)]+)[\'"]?\)', tarjeta["full_html"])
        if wood_match:
            wood_img_val = wood_match.group(1).replace('\\', '/')
        else:
            wood_img_val = "img/fondo_letra.png"
        self.var_card_bg_wood.set(wood_img_val)
        
        # Cargar offset de la línea (divider)
        divider_top_match = re.search(r'--divider-top\s*:\s*(\d+)px', tarjeta["full_html"])
        if divider_top_match:
            try:
                div_top_val = int(divider_top_match.group(1))
                divider_offset = div_top_val - 56
            except:
                divider_offset = 0
        else:
            divider_offset = 0
            
        try:
            self.scale_banner_divider_top.set(divider_offset)
        except AttributeError:
            pass
            
        # Cargar color de la línea (divider)
        divider_color_match = re.search(r'--divider-color\s*:\s*([^;"]+)', tarjeta["full_html"])
        if divider_color_match:
            div_color = divider_color_match.group(1).strip()
            if div_color == "transparent":
                div_color = "#FFBF00"  # Fallback to gold
        else:
            div_color = "#FFBF00"
            
        self.var_banner_divider_color.set(div_color)
        
        # Cargar imagen de la línea (divider)
        divider_img_match = re.search(r'--divider-image\s*:\s*url\([\'"]?([^\'"\)]+)[\'"]?\)', tarjeta["full_html"])
        if divider_img_match:
            div_img_val = divider_img_match.group(1).replace('\\', '/')
            if div_img_val == "none":
                div_img_val = "Ninguno (Línea Sólida)"
        else:
            div_img_val = "Ninguno (Línea Sólida)"
            
        self.var_banner_divider_img.set(div_img_val)
            
        self.actualizar_previsualizacion()
        
    def elegir_color_banner_title(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="Elegir Color de Título", initialcolor=self.var_banner_title_color.get())[1]
        if color:
            self.var_banner_title_color.set(color)
            self.actualizar_previsualizacion()
            
    def elegir_color_banner_title_stroke(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="Elegir Color de Borde de Título", initialcolor=self.var_banner_title_stroke_color.get())[1]
        if color:
            self.var_banner_title_stroke_color.set(color)
            self.actualizar_previsualizacion()
    def elegir_color_banner_sub(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="Elegir Color de Subtítulo", initialcolor=self.var_banner_sub_color.get())[1]
        if color:
            self.var_banner_sub_color.set(color)
            self.actualizar_previsualizacion()

    def inicializar_tarjetas_predefinidas(self):
        import json
        self.predefinidas_json_path = None
        for d in self.target_dirs:
            path = os.path.join(d, "tarjetas_predefinidas.json")
            self.predefinidas_json_path = path
            break
        if not self.predefinidas_json_path:
            self.predefinidas_json_path = os.path.join(self.base_dir, "tarjetas_predefinidas.json")
            
        if not os.path.exists(self.predefinidas_json_path):
            datos = {}
            for t in self.tarjetas_web:
                card_class = t["class"]
                title_font = t.get("title_font", "")
                title_size = t.get("title_size", "")
                title_color = t.get("title_color", "")
                sub_font = t.get("sub_font", "")
                sub_size = t.get("sub_size", "")
                sub_color = t.get("sub_color", "")
                
                try:
                    t_size_num = int(re.search(r'\d+', title_size).group(0))
                except:
                    t_size_num = 40
                try:
                    s_size_num = int(re.search(r'\d+', sub_size).group(0))
                except:
                    s_size_num = 14
                    
                scale_match = re.search(r'style="[^"]*--badge-scale\s*:\s*([^;"]+)', t["full_html"])
                try:
                    scale_val = float(scale_match.group(1).strip())
                    scale_percent = int(scale_val * 100)
                except:
                    scale_percent = 100
                    
                # Divider top
                divider_top_match = re.search(r'--divider-top\s*:\s*(\d+)px', t["full_html"])
                div_offset_val = 0
                if divider_top_match:
                    try:
                        div_offset_val = int(divider_top_match.group(1)) - 56
                    except:
                        pass
                        
                # Divider color
                divider_color_match = re.search(r'--divider-color\s*:\s*([^;"]+)', t["full_html"])
                div_color_val = "#FFBF00"
                if divider_color_match:
                    div_color_val = divider_color_match.group(1).strip()
                    if div_color_val == "transparent":
                        div_color_val = "#FFBF00"
                        
                # Divider img
                divider_img_match = re.search(r'--divider-image\s*:\s*url\([\'"]?([^\'"\)]+)[\'"]?\)', t["full_html"])
                div_img_val = "Ninguno (Línea Sólida)"
                if divider_img_match:
                    div_img_val = divider_img_match.group(1).replace('\\', '/')
                    if div_img_val == "none":
                        div_img_val = "Ninguno (Línea Sólida)"
                        
                # Base BG
                card_bg_tag = re.search(r'<div\s+class="card-bg"\s*([^>]*)>', t["full_html"])
                base_bg_val = "img/fondo_rayas.png"
                if card_bg_tag:
                    attrs = card_bg_tag.group(1)
                    url_match = re.search(r'background-image:\s*url\([\'"]?([^\'"\)]+)[\'"]?\)', attrs)
                    if url_match:
                        base_bg_val = url_match.group(1).replace('\\', '/')
                        
                # Wood BG
                wood_match = re.search(r'--wood-image:\s*url\([\'"]?([^\'"\)]+)[\'"]?\)', t["full_html"])
                if wood_match:
                    wood_img_val = wood_match.group(1).replace('\\', '/')
                else:
                    wood_img_val = "img/fondo_letra.png"
                    
                datos[card_class] = {
                    "title": t["title"],
                    "subtitle": t["subtitle"],
                    "badge": t["tag"],
                    "bg_img": self.fondos_css.get(card_class, ""),
                    "font": title_font if title_font else "Merriweather (Serif clásica)",
                    "title_size": t_size_num,
                    "title_color": title_color if title_color else "#4b372d",
                    "sub_size": s_size_num,
                    "sub_color": sub_color if sub_color else "#4b372d",
                    "wood_scale": scale_percent,
                    "base_bg": base_bg_val,
                    "wood_bg": wood_img_val,
                    "divider_offset": div_offset_val,
                    "divider_color": div_color_val,
                    "divider_img": div_img_val
                }
            try:
                with open(self.predefinidas_json_path, "w", encoding="utf-8") as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print("Error al inicializar predefinidas:", e)

    def get_font_family_css(self, selected_font):
        if "Petit Formal Script" in selected_font:
            return "'Petit Formal Script', cursive"
        elif "Parisienne" in selected_font:
            return "'Parisienne', cursive"
        elif "Dancing Script" in selected_font:
            return "'Dancing Script', cursive"
        elif "Great Vibes" in selected_font:
            return "'Great Vibes', cursive"
        elif "Alex Brush" in selected_font:
            return "'Alex Brush', cursive"
        elif "Pinyon Script" in selected_font:
            return "'Pinyon Script', cursive"
        elif "Sacramento" in selected_font:
            return "'Sacramento', cursive"
        elif "Playfair Display" in selected_font:
            return "'Playfair Display', Georgia, serif"
        elif "Merriweather" in selected_font:
            return "'Merriweather', Georgia, serif"
        elif "Cormorant Garamond" in selected_font:
            return "'Cormorant Garamond', Georgia, serif"
        elif "Cinzel" in selected_font:
            return "'Cinzel', Georgia, serif"
        elif "Lora" in selected_font:
            return "'Lora', Georgia, serif"
        elif "Montserrat" in selected_font:
            return "'Montserrat', sans-serif"
        elif "Outfit" in selected_font:
            return "'Outfit', sans-serif"
        elif "Inter" in selected_font:
            return "'Inter', sans-serif"
        elif "Roboto" in selected_font:
            return "'Roboto', sans-serif"
        elif "Poppins" in selected_font:
            return "'Poppins', sans-serif"
        return ""

    def get_font_combobox_val(self, font_name):
        if not font_name:
            return "Outfit (Sans-serif moderna)"
        for f in self.FUENTES_LIST:
            clean_name = f.split(" (")[0]
            if clean_name in font_name:
                return f
        return "Outfit (Sans-serif moderna)"

    def buscar_y_copiar_base_bg(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen de fondo base",
            filetypes=[("Archivos de Imagen", "*.jpg *.jpeg *.png *.webp"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            filename = os.path.basename(file_path)
            for d in self.target_dirs:
                dest = os.path.join(d, "img", filename)
                try:
                    import shutil
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(file_path, dest)
                except Exception as e:
                    print(f"Error copying base background: {e}")
            self.actualizar_listas_de_fondos_solo()
            self.var_card_bg_base.set(f"img/{filename}")
            self.actualizar_previsualizacion()
            
    def buscar_y_copiar_wood_bg(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar silueta de madera",
            filetypes=[("Archivos de Imagen", "*.jpg *.jpeg *.png *.webp"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            filename = os.path.basename(file_path)
            for d in self.target_dirs:
                dest = os.path.join(d, "img", filename)
                try:
                    import shutil
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(file_path, dest)
                except Exception as e:
                    print(f"Error copying wood background: {e}")
            self.actualizar_listas_de_fondos_solo()
            self.var_card_bg_wood.set(f"img/{filename}")
            self.actualizar_previsualizacion()
            
    def buscar_y_agregar_etiqueta(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen de etiqueta",
            filetypes=[("Archivos de Imagen", "*.png *.gif *.webp *.jpg"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            import tkinter.simpledialog as simpledialog
            tag_name = simpledialog.askstring("Nombre de la Etiqueta", "Ingresa un nombre para esta nueva etiqueta:")
            if not tag_name or tag_name.strip() == "":
                return
            tag_name = tag_name.strip()
            
            filename = os.path.basename(file_path)
            for d in self.target_dirs:
                dest = os.path.join(d, "img", filename)
                try:
                    import shutil
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(file_path, dest)
                except Exception as e:
                    print(f"Error copying tag image: {e}")
            
            # Guardar en config
            if not hasattr(self, "custom_tags"):
                self.custom_tags = {}
            self.custom_tags[tag_name] = filename
            self.guardar_configuracion()
            
            # Actualizar combo
            tag_values = ["Ninguno", "Nuevos Diseños", "Oferta Especial"] + list(self.custom_tags.keys())
            self.combo_banner_badge["values"] = tag_values
            self.var_banner_badge.set(tag_name)
            self.actualizar_previsualizacion()
 
    def buscar_y_copiar_divider_img(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen de separador",
            filetypes=[("Archivos de Imagen", "*.jpg *.jpeg *.png *.webp"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            filename = os.path.basename(file_path)
            for d in self.target_dirs:
                dest = os.path.join(d, "img", filename)
                try:
                    import shutil
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(file_path, dest)
                except Exception as e:
                    print(f"Error copying divider image: {e}")
            self.actualizar_listas_de_fondos_solo()
            self.var_banner_divider_img.set(f"img/{filename}")
            self.actualizar_previsualizacion()
            
    def actualizar_listas_de_fondos_solo(self):
        fondos_files = []
        for d in self.target_dirs:
            img_dir = os.path.join(d, "img")
            if os.path.exists(img_dir):
                for f in os.listdir(img_dir):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        rel_path = f"img/{f}"
                        if rel_path not in fondos_files:
                            fondos_files.append(rel_path)
                            
        # También en base_dir
        img_dir_base = os.path.join(self.base_dir, "img")
        if os.path.exists(img_dir_base):
            for f in os.listdir(img_dir_base):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    rel_path = f"img/{f}"
                    if rel_path not in fondos_files:
                        fondos_files.append(rel_path)
                        
        fondos_files.sort()
        
        self.combo_banner_bg_img["values"] = fondos_files
        self.combo_new_card_bg["values"] = fondos_files
        try:
            self.combo_card_bg_base["values"] = fondos_files
            self.combo_card_bg_wood["values"] = fondos_files
            self.combo_banner_divider_img["values"] = ["Ninguno (Línea Sólida)"] + fondos_files
        except AttributeError:
            pass
            
    def elegir_color_banner_divider(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="Elegir Color de la Línea", initialcolor=self.var_banner_divider_color.get())[1]
        if color:
            self.var_banner_divider_color.set(color)
            self.actualizar_previsualizacion()

    def fijar_tarjeta_predefinida(self):
        idx = self.combo_banners.current()
        if idx == -1:
            messagebox.showerror("Error", "Selecciona una tarjeta primero.")
            return
            
        tarjeta = self.tarjetas_web[idx]
        card_class = tarjeta["class"]
        
        import json
        datos = {}
        if os.path.exists(self.predefinidas_json_path):
            try:
                with open(self.predefinidas_json_path, "r", encoding="utf-8") as f:
                    datos = json.load(f)
            except:
                pass
                
        badge_type = self.var_banner_badge.get()
        if badge_type == "Ninguno":
            badge_val = ""
        else:
            badge_val = badge_type
            
        datos[card_class] = {
            "title": self.var_banner_title.get().strip(),
            "subtitle": self.var_banner_subtitle.get().strip(),
            "badge": badge_val,
            "bg_img": self.var_banner_bg_img.get().strip(),
            "font": self.var_banner_font.get(),
            "title_size": self.scale_banner_title_size.get(),
            "title_color": self.var_banner_title_color.get().strip(),
            "title_stroke_color": self.var_banner_title_stroke_color.get().strip(),
            "title_stroke_width": self.scale_banner_title_stroke_width.get(),
            "sub_size": self.scale_banner_sub_size.get(),
            "sub_color": self.var_banner_sub_color.get().strip(),
            "wood_scale": self.scale_banner_wood_size.get(),
            "base_bg": self.var_card_bg_base.get().strip(),
            "wood_bg": self.var_card_bg_wood.get().strip(),
            "divider_offset": self.scale_banner_divider_top.get(),
            "divider_color": self.var_banner_divider_color.get().strip(),
            "divider_img": self.var_banner_divider_img.get().strip()
        }
        
        try:
            with open(self.predefinidas_json_path, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Éxito", "El formato actual ha sido fijado como predefinido para esta tarjeta.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def restablecer_tarjeta_predefinida(self):
        idx = self.combo_banners.current()
        if idx == -1:
            messagebox.showerror("Error", "Selecciona una tarjeta primero.")
            return
            
        tarjeta = self.tarjetas_web[idx]
        card_class = tarjeta["class"]
        
        import json
        if not os.path.exists(self.predefinidas_json_path):
            messagebox.showerror("Error", "No existe un archivo de tarjetas predefinidas.")
            return
            
        try:
            with open(self.predefinidas_json_path, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo predefinido:\n{e}")
            return
            
        if card_class not in datos:
            messagebox.showerror("Error", "No hay datos predefinidos para esta tarjeta.")
            return
            
        pred = datos[card_class]
        self.var_banner_title.set(pred.get("title", ""))
        self.var_banner_subtitle.set(pred.get("subtitle", ""))
        
        badge = pred.get("badge", "")
        if "oferta" in badge.lower():
            self.var_banner_badge.set("Oferta Especial")
        elif "nuevos" in badge.lower():
            self.var_banner_badge.set("Nuevos Diseños")
        else:
            self.var_banner_badge.set("Ninguno")
            
        self.var_banner_bg_img.set(pred.get("bg_img", ""))
        self.var_banner_font.set(pred.get("font", "Outfit (Sans-serif moderna)"))
        self.scale_banner_title_size.set(pred.get("title_size", 24))
        self.var_banner_title_color.set(pred.get("title_color", "#ffffff"))
        
        try:
            self.scale_banner_title_stroke_width.set(pred.get("title_stroke_width", 2.5))
        except AttributeError:
            pass
        self.var_banner_title_stroke_color.set(pred.get("title_stroke_color", "#ffffff"))
        
        self.scale_banner_sub_size.set(pred.get("sub_size", 14))
        self.var_banner_sub_color.set(pred.get("sub_color", "#4b372d"))
        try:
            self.scale_banner_wood_size.set(pred.get("wood_scale", 100))
        except AttributeError:
            pass
            
        self.var_card_bg_base.set(pred.get("base_bg", "img/fondo_rayas.png"))
        self.var_card_bg_wood.set(pred.get("wood_bg", "img/fondo_letra.png"))
        
        try:
            self.scale_banner_divider_top.set(pred.get("divider_offset", 0))
        except AttributeError:
            pass
            
        self.var_banner_divider_color.set(pred.get("divider_color", "#FFBF00"))
        self.var_banner_divider_img.set(pred.get("divider_img", "Ninguno (Línea Sólida)"))
        
        self.actualizar_previsualizacion()
        messagebox.showinfo("Restablecido", "Se han cargado los valores predefinidos en la interfaz. Haz clic en Guardar para aplicarlos a la web.")

    def aplicar_formato_todas_tarjetas(self):
        if not self.tarjetas_web:
            messagebox.showerror("Error", "No hay tarjetas cargadas.")
            return
            
        if not messagebox.askyesno("Confirmar", "¿Estás seguro de que deseas aplicar el mismo formato (Tipografía, Colores y Tamaños) a TODAS las tarjetas principales?"):
            return
            
        try:
            selected_font = self.var_banner_font.get()
            new_font_family_css = self.get_font_family_css(selected_font)
                
            try:
                wood_scale = self.scale_banner_wood_size.get() / 100.0
            except AttributeError:
                wood_scale = 1.0
                
            t_size = f"{self.scale_banner_title_size.get()}px"
            t_color = self.var_banner_title_color.get().strip() or "#ffffff"
            
            try:
                ts_color = self.var_banner_title_stroke_color.get().strip() or "#ffffff"
            except AttributeError:
                ts_color = "#ffffff"
                
            try:
                ts_width = f"{self.scale_banner_title_stroke_width.get()}px"
            except AttributeError:
                ts_width = "2.5px"
                
            s_size = f"{self.scale_banner_sub_size.get()}px"
            s_color = self.var_banner_sub_color.get().strip() or "#e5dacb"
            
            h2_styles = [
                f"font-size: {t_size};",
                f"color: {ts_color};",
                f"--title-color: {t_color};",
                f"--title-stroke-color: {ts_color};",
                f"--title-stroke-width: {ts_width};"
            ]
            if new_font_family_css:
                h2_styles.append(f"font-family: {new_font_family_css};")
            h2_style_str = " ".join(h2_styles)
            
            span_styles = [f"font-size: {s_size};", f"color: {s_color};"]
            if new_font_family_css:
                span_styles.append(f"font-family: {new_font_family_css};")
            span_style_str = " ".join(span_styles)
            
            with open(self.index_html_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            for t in self.tarjetas_web:
                card_class = t["class"]
                tag_name = t.get("tag", "")
                tag_html = ""
                if "oferta" in tag_name.lower():
                    tag_html = '\n                        <div class="card-tag tag-ofertas">Oferta<br>Especial</div>'
                elif "nuevos" in tag_name.lower():
                    tag_html = '\n                        <div class="card-tag tag-nuevos">Nuevos<br>Diseños</div>'
                elif hasattr(self, "custom_tags") and tag_name in self.custom_tags:
                    custom_img = self.custom_tags[tag_name]
                    tag_html = f'\n                        <div class="card-tag card-tag-custom" style="background-image: url(\'img/{custom_img}\');"></div>'
                    
                # 1. Conservar escala y wood image
                scale_match = re.search(r'--badge-scale\s*:\s*([^;"]+)', t["full_html"])
                wood_scale_val = f"{wood_scale:.2f}"
                if scale_match:
                    wood_scale_val = scale_match.group(1).strip()
                    
                wood_img_match = re.search(r'--wood-image\s*:\s*url\([\'"]?([^\'"\)]+)[\'"]?\)', t["full_html"])
                style_parts = [f"--badge-scale: {wood_scale_val};"]
                if wood_img_match:
                    style_parts.append(f"--wood-image: url('{wood_img_match.group(1)}');")
                style_str = " ".join(style_parts)
                
                # 2. Conservar fondo base
                bg_base_match = re.search(r'class="card-bg"\s+style="background-image:\s*url\([\'"]?([^\'"\)]+)[\'"]?\)', t["full_html"])
                if bg_base_match:
                    card_bg_html = f'<div class="card-bg" style="background-image: url(\'{bg_base_match.group(1)}\');"></div>'
                else:
                    card_bg_html = '<div class="card-bg"></div>'
                    
                # 3. Conservar divisor
                divider_match = re.search(r'<div\s+class="divider"\s+style="([^"]+)"', t["full_html"])
                if divider_match:
                    divider_style_str = divider_match.group(1).strip()
                else:
                    divider_style_str = f"--divider-top: 56px; --divider-color: #FFBF00; --divider-image: none; --divider-width: 60px; --divider-height: 2px;"
                    
                new_card_html = f'''<a href="{t["href"]}" class="category-card {card_class}" style="{style_str}">{tag_html}
                        <div class="card-inner">
                            {card_bg_html}
                            <div class="card-overlay"></div>
                            <div class="card-content">
                                <h2 data-text="{t["title"].upper()}" style="{h2_style_str}">{t["title"].upper()}</h2>
                                <span class="subtitle" style="{span_style_str}">{t["subtitle"]}</span>
                                <div class="divider" style="{divider_style_str}"></div>
                                <span class="explore">Explorar colección <span class="arrow">→</span></span>
                            </div>
                        </div>
                    </a>'''
                    
                content = content.replace(t["full_html"], new_card_html)
                
            with open(self.index_html_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            self.cargar_tarjetas_y_fondos()
            messagebox.showinfo("Éxito", "El formato tipográfico ha sido aplicado a todas las tarjetas principales en index.html.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar los cambios en todas las tarjetas:\n{e}")

    def actualizar_previsualizacion(self):
        if not HAS_PIL:
            return
            
        # 1. Obtener imagen de fondo base
        base_bg_rel = self.var_card_bg_base.get().replace('\\', '/')
        rayas_path = None
        for d in self.target_dirs:
            p = os.path.join(d, base_bg_rel)
            if os.path.exists(p):
                rayas_path = p
                break
        if not rayas_path:
            rayas_path = os.path.join(self.base_dir, base_bg_rel)
            
        if os.path.exists(rayas_path):
            try:
                with Image.open(rayas_path) as temp_img:
                    temp_img.load()
                    base_img = temp_img.convert("RGBA")
            except:
                base_img = Image.new("RGBA", (416, 274), (245, 240, 235, 255))
        else:
            base_img = Image.new("RGBA", (416, 274), (245, 240, 235, 255))
            
        base_img = self.resize_cover(base_img, (416, 274))
        
        # Overlay café oscuro semitransparente
        overlay = Image.new("RGBA", (416, 274), (75, 55, 45, 60))
        base_img = Image.alpha_composite(base_img, overlay)
        
        # 2. Cargar y escalar silueta de madera
        wood_bg_rel = self.var_card_bg_wood.get().replace('\\', '/')
        letra_path = None
        for d in self.target_dirs:
            p = os.path.join(d, wood_bg_rel)
            if os.path.exists(p):
                letra_path = p
                break
        if not letra_path:
            letra_path = os.path.join(self.base_dir, wood_bg_rel)
            
        try:
            scale_percent = self.scale_banner_wood_size.get()
        except AttributeError:
            scale_percent = 100
            
        new_w = int(345 * (scale_percent / 100.0))
        new_h = int(224 * (scale_percent / 100.0))
        
        new_w = max(10, min(new_w, 800))
        new_h = max(10, min(new_h, 600))
        
        if os.path.exists(letra_path):
            try:
                with Image.open(letra_path) as temp_img:
                    temp_img.load()
                    wood_img = temp_img.convert("RGBA")
                wood_img = wood_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Cargar el fondo de la categoría seleccionado
                fondo_rel = self.var_banner_bg_img.get()
                fondo_abs = None
                for d in self.target_dirs:
                    p = os.path.join(d, fondo_rel)
                    if os.path.exists(p):
                        fondo_abs = p
                        break
                        
                if fondo_abs and os.path.exists(fondo_abs):
                    try:
                        with Image.open(fondo_abs) as temp_img:
                            temp_img.load()
                            cat_img = temp_img.convert("RGBA")
                        cat_img = self.resize_cover(cat_img, (new_w, new_h))
                        
                        orig_alpha = wood_img.getchannel('A')
                        from PIL import ImageChops
                        multiplied = ImageChops.multiply(wood_img, cat_img)
                        wood_img = Image.blend(wood_img, multiplied, 0.35)
                        wood_img.putalpha(orig_alpha)
                    except Exception as e:
                        print("Error mezclando textura de categoría:", e)
                        
                cx, cy = 208, 137
                px = cx - (new_w // 2)
                py = cy - (new_h // 2)
                base_img.paste(wood_img, (px, py), wood_img)
            except Exception as e:
                print("Error dibujando silueta de madera:", e)
                
        draw = ImageDraw.Draw(base_img)
        
        # Cargar fuentes del sistema
        try:
            selected_font = self.var_banner_font.get()
        except AttributeError:
            selected_font = "Merriweather (Serif clásica)"
            
        if any(f in selected_font for f in ["Petit Formal Script", "Parisienne", "Dancing Script", "Great Vibes", "Alex Brush", "Pinyon Script", "Sacramento"]):
            title_font_type = "script"
        elif any(f in selected_font for f in ["Merriweather", "Playfair Display", "Cormorant Garamond", "Cinzel", "Lora"]):
            title_font_type = "serif"
        else:
            title_font_type = "sans"
            
        try:
            t_size = self.scale_banner_title_size.get()
        except AttributeError:
            t_size = 24
            
        try:
            s_size = self.scale_banner_sub_size.get()
        except AttributeError:
            s_size = 14
            
        font_title = self.get_pillow_font(title_font_type, t_size, bold=True)
        font_sub = self.get_pillow_font(title_font_type, s_size, bold=False)
        
        title_text = self.var_banner_title.get().upper()
        sub_text = self.var_banner_subtitle.get()
        
        # Colores
        try:
            t_color_str = self.var_banner_title_color.get().strip() or "#ffffff"
        except AttributeError:
            t_color_str = "#ffffff"
            
        try:
            s_color_str = self.var_banner_sub_color.get().strip() or "#e5dacb"
        except AttributeError:
            s_color_str = "#e5dacb"
        
        def hex_to_rgba(hex_str, default=(255, 255, 255, 255)):
            hex_str = hex_str.lstrip('#')
            if len(hex_str) == 6:
                try:
                    r = int(hex_str[0:2], 16)
                    g = int(hex_str[2:4], 16)
                    b = int(hex_str[4:6], 16)
                    return (r, g, b, 255)
                except:
                    pass
            elif len(hex_str) == 3:
                try:
                    r = int(hex_str[0]*2, 16)
                    g = int(hex_str[1]*2, 16)
                    b = int(hex_str[2]*2, 16)
                    return (r, g, b, 255)
                except:
                    pass
            return default
            
        t_rgba = hex_to_rgba(t_color_str, (75, 55, 45, 255))
        s_rgba = hex_to_rgba(s_color_str, (229, 218, 203, 255))
        
        try:
            ts_width = float(self.scale_banner_title_stroke_width.get())
        except AttributeError:
            ts_width = 2.5
            
        try:
            ts_color_str = self.var_banner_title_stroke_color.get().strip() or "#ffffff"
        except AttributeError:
            ts_color_str = "#ffffff"
            
        ts_rgba = hex_to_rgba(ts_color_str, (255, 255, 255, 255))
        
        cw, ch = 208, 137
        
        # Título outlined (Relleno: t_rgba, Borde: ts_rgba)
        self.draw_outlined_text(draw, (cw, ch), title_text, font_title, t_rgba, ts_rgba, int(round(ts_width)), anchor="mm")
        
        # Subtítulo (Calculado como top: calc(50% + 28px) en la web -> 137 + 28 = 165px)
        draw.text((cw, 165), sub_text, font=font_sub, fill=s_rgba, anchor="mt")
        
        # Divisor Dinámico
        try:
            divider_offset = self.scale_banner_divider_top.get()
        except AttributeError:
            divider_offset = 0
            
        divider_color_str = self.var_banner_divider_color.get().strip() or "#FFBF00"
        divider_img_rel = self.var_banner_divider_img.get().strip().replace('\\', '/')
        
        y_divider = 193 + divider_offset
        
        if divider_img_rel and divider_img_rel != "Ninguno (Línea Sólida)":
            div_img_path = None
            for d in self.target_dirs:
                p = os.path.join(d, divider_img_rel)
                if os.path.exists(p):
                    div_img_path = p
                    break
            if not div_img_path:
                div_img_path = os.path.join(self.base_dir, divider_img_rel)
                
            if os.path.exists(div_img_path):
                try:
                    div_img = Image.open(div_img_path).convert("RGBA")
                    orig_w, orig_h = div_img.size
                    new_div_w = 100
                    new_div_h = max(2, int(orig_h * (100.0 / orig_w)))
                    div_img = div_img.resize((new_div_w, new_div_h), Image.Resampling.LANCZOS)
                    
                    px = 208 - (new_div_w // 2)
                    py = y_divider - (new_div_h // 2)
                    base_img.paste(div_img, (px, py), div_img)
                except Exception as e:
                    print("Error dibujando imagen separador en preview:", e)
        else:
            # Dibujar línea sólida
            draw.line([(208 - 30, y_divider), (208 + 30, y_divider)], fill=divider_color_str, width=2)
        
        # Etiqueta flotante
        badge_type = self.var_banner_badge.get()
        if badge_type != "Ninguno":
            tag_filename = None
            if badge_type == "Nuevos Diseños":
                tag_filename = "tag_nuevos_disenos.png"
            elif badge_type == "Oferta Especial":
                tag_filename = "tag_ofertas_especiales.png"
            elif hasattr(self, "custom_tags") and badge_type in self.custom_tags:
                tag_filename = self.custom_tags[badge_type]
                
            if tag_filename:
                tag_path = None
                for d in self.target_dirs:
                    p = os.path.join(d, "img", tag_filename)
                    if os.path.exists(p):
                        tag_path = p
                        break
                if not tag_path:
                    tag_path = os.path.join(self.base_dir, "img", tag_filename)
                
                success_tag = False
                if os.path.exists(tag_path):
                    try:
                        tag_img = Image.open(tag_path).convert("RGBA")
                        tag_w, tag_h = 50, 77
                        tag_img = tag_img.resize((tag_w, tag_h), Image.Resampling.LANCZOS)
                        rotated_badge = tag_img.rotate(10, resample=Image.Resampling.BICUBIC, expand=True)
                        base_img.paste(rotated_badge, (20, 0), rotated_badge)
                        success_tag = True
                    except Exception as e:
                        print(f"Error al cargar {tag_filename} para previsualización:", e)
                
                if not success_tag:
                    # Fallback a dibujar el badge rojo con el texto
                    badge_w, badge_h = 100, 48
                    badge_img = Image.new("RGBA", (badge_w, badge_h), (0, 0, 0, 0))
                    b_draw = ImageDraw.Draw(badge_img)
                    b_draw.rounded_rectangle([0, 0, badge_w, badge_h], radius=7, fill=(217, 83, 79, 255), outline=(255, 255, 255, 38), width=1)
                    badge_font = self.get_pillow_font("sans", 11, bold=True)
                    words = badge_type.split()
                    lines = [words[0][:10].upper()] if len(words) == 1 else [words[0][:10].upper(), words[1][:10].upper()]
                    y_offset = (badge_h - len(lines) * 12) // 2
                    for line in lines:
                        ltw = b_draw.textlength(line, font=badge_font)
                        ltx = (badge_w - ltw) // 2
                        b_draw.text((ltx, y_offset), line, font=badge_font, fill=(255, 255, 255, 255))
                        y_offset += 13
                    rotated_badge = badge_img.rotate(12, resample=Image.Resampling.BICUBIC, expand=True)
                    base_img.paste(rotated_badge, (12, 12), rotated_badge)
            
        # Aplicar esquinas redondeadas de 24px (border-radius) fundiendo sobre el color de fondo de la app (#fcfaf7)
        try:
            final_canvas = Image.new("RGBA", (416, 274), (252, 250, 247, 255))
            card_mask = Image.new("L", (416, 274), 0)
            mask_draw = ImageDraw.Draw(card_mask)
            mask_draw.rounded_rectangle([0, 0, 416, 274], radius=24, fill=255)
            rounded_card = Image.new("RGBA", (416, 274), (0, 0, 0, 0))
            rounded_card.paste(base_img, (0, 0), card_mask)
            final_canvas.paste(rounded_card, (0, 0), rounded_card)
            base_img = final_canvas
        except Exception as e:
            print("Error aplicando bordes redondeados a la previsualización:", e)
            
        self.tk_banner_img = ImageTk.PhotoImage(base_img)
        self.canvas_prev.delete("all")
        self.canvas_prev.create_image(0, 0, image=self.tk_banner_img, anchor="nw")

    def get_pillow_font(self, font_type, size, bold=False, italic=False):
        font_paths = []
        if sys.platform == "win32":
            windir = os.environ.get("windir", "C:\\Windows")
            if font_type == "serif":
                if bold and italic:
                    font_paths = [
                        os.path.join(windir, "Fonts", "georgiaz.ttf"),
                        os.path.join(windir, "Fonts", "timesbi.ttf")
                    ]
                elif bold:
                    font_paths = [
                        os.path.join(windir, "Fonts", "georgiab.ttf"),
                        os.path.join(windir, "Fonts", "timesbd.ttf")
                    ]
                elif italic:
                    font_paths = [
                        os.path.join(windir, "Fonts", "georgiai.ttf"),
                        os.path.join(windir, "Fonts", "timesi.ttf")
                    ]
                else:
                    font_paths = [
                        os.path.join(windir, "Fonts", "georgia.ttf"),
                        os.path.join(windir, "Fonts", "times.ttf")
                    ]
            elif font_type == "script":
                font_paths = [
                    os.path.join(windir, "Fonts", "lhandw.ttf"),
                    os.path.join(windir, "Fonts", "Gabriola.ttf"),
                    os.path.join(windir, "Fonts", "segoepr.ttf")
                ]
            else:
                if bold and italic:
                    font_paths = [
                        os.path.join(windir, "Fonts", "segoeuiz.ttf"),
                        os.path.join(windir, "Fonts", "arialbi.ttf")
                    ]
                elif bold:
                    font_paths = [
                        os.path.join(windir, "Fonts", "segoeuib.ttf"),
                        os.path.join(windir, "Fonts", "arialbd.ttf")
                    ]
                elif italic:
                    font_paths = [
                        os.path.join(windir, "Fonts", "segoeuii.ttf"),
                        os.path.join(windir, "Fonts", "ariali.ttf")
                    ]
                else:
                    font_paths = [
                        os.path.join(windir, "Fonts", "segoeui.ttf"),
                        os.path.join(windir, "Fonts", "arial.ttf")
                    ]
                
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except:
                    pass
        return ImageFont.load_default()

    def resize_cover(self, img, target_size):
        tw, th = target_size
        src_ratio = img.width / img.height
        target_ratio = tw / th
        if src_ratio > target_ratio:
            # Mas ancho que el ratio objetivo: ajustar al alto y cortar bordes laterales
            new_w = int(th * src_ratio)
            img_resized = img.resize((new_w, th), Image.Resampling.LANCZOS)
            left = (new_w - tw) // 2
            return img_resized.crop((left, 0, left + tw, th))
        else:
            # Mas alto o igual que el ratio objetivo: ajustar al ancho y cortar bordes superior/inferior
            new_h = int(tw / src_ratio)
            img_resized = img.resize((tw, new_h), Image.Resampling.LANCZOS)
            top = (new_h - th) // 2
            return img_resized.crop((0, top, tw, top + th))

    def draw_outlined_text(self, draw, position, text, font, fill_color, outline_color, outline_width=2, anchor="mm"):
        # Usamos los parametros nativos stroke_width y stroke_fill de Pillow para un borde suave vectorial
        draw.text(position, text, font=font, fill=fill_color, stroke_width=outline_width, stroke_fill=outline_color, anchor=anchor)

    def guardar_tarjeta(self):
        idx = self.combo_banners.current()
        if idx == -1:
            messagebox.showerror("Error", "Por favor, selecciona una tarjeta de la lista para modificar.")
            return
            
        tarjeta = self.tarjetas_web[idx]
        card_class = tarjeta["class"]
        
        new_title = self.var_banner_title.get().strip()
        new_subtitle = self.var_banner_subtitle.get().strip()
        badge_type = self.var_banner_badge.get()
        new_bg = self.var_banner_bg_img.get().replace('\\', '/')
        
        if not new_title or not new_subtitle:
            messagebox.showerror("Error", "El título y subtítulo no pueden estar vacíos.")
            return
            
        if badge_type == "Nuevos Diseños":
            tag_html = '\n                        <div class="card-tag tag-nuevos">Nuevos<br>Diseños</div>'
        elif badge_type == "Oferta Especial":
            tag_html = '\n                        <div class="card-tag tag-ofertas">Oferta<br>Especial</div>'
        elif hasattr(self, "custom_tags") and badge_type in self.custom_tags:
            custom_img = self.custom_tags[badge_type]
            tag_html = f'\n                        <div class="card-tag card-tag-custom" style="background-image: url(\'img/{custom_img}\');"></div>'
        else:
            tag_html = ""
            
        # Obtener tipografía y estilos
        try:
            selected_font = self.var_banner_font.get()
        except AttributeError:
            selected_font = "Merriweather (Serif clásica)"
            
        new_font_family_css = self.get_font_family_css(selected_font)
            
        try:
            t_size = f"{self.scale_banner_title_size.get()}px"
        except AttributeError:
            t_size = "24px"
            
        try:
            t_color = self.var_banner_title_color.get().strip() or "#ffffff"
        except AttributeError:
            t_color = "#ffffff"
            
        try:
            s_size = f"{self.scale_banner_sub_size.get()}px"
        except AttributeError:
            s_size = "14px"
            
        try:
            s_color = self.var_banner_sub_color.get().strip() or "#e5dacb"
        except AttributeError:
            s_color = "#e5dacb"
            
        try:
            ts_color = self.var_banner_title_stroke_color.get().strip() or "#ffffff"
        except AttributeError:
            ts_color = "#ffffff"
            
        try:
            ts_width = f"{self.scale_banner_title_stroke_width.get()}px"
        except AttributeError:
            ts_width = "2.5px"
            
        h2_styles = [
            f"font-size: {t_size};",
            f"color: {ts_color};",
            f"--title-color: {t_color};",
            f"--title-stroke-color: {ts_color};",
            f"--title-stroke-width: {ts_width};"
        ]
        if new_font_family_css:
            h2_styles.append(f"font-family: {new_font_family_css};")
        h2_style_str = " ".join(h2_styles)
        
        span_styles = [f"font-size: {s_size};", f"color: {s_color};"]
        if new_font_family_css:
            span_styles.append(f"font-family: {new_font_family_css};")
        span_style_str = " ".join(span_styles)
        
        try:
            wood_scale = self.scale_banner_wood_size.get() / 100.0
        except AttributeError:
            wood_scale = 1.0
            
        bg_base = self.var_card_bg_base.get().strip().replace('\\', '/')
        if bg_base and bg_base != "img/fondo_rayas.png":
            card_bg_html = f'<div class="card-bg" style="background-image: url(\'{bg_base}\');"></div>'
        else:
            card_bg_html = '<div class="card-bg"></div>'
            
        bg_wood = self.var_card_bg_wood.get().strip().replace('\\', '/')
        style_parts = [f"--badge-scale: {wood_scale:.2f};"]
        if bg_wood and bg_wood != "img/fondo_letra.png":
            style_parts.append(f"--wood-image: url('{bg_wood}');")
        style_str = " ".join(style_parts)
        
        # Divider style
        try:
            divider_offset = self.scale_banner_divider_top.get()
        except AttributeError:
            divider_offset = 0
        divider_top = 56 + divider_offset
        
        divider_color = self.var_banner_divider_color.get().strip() or "#FFBF00"
        divider_img = self.var_banner_divider_img.get().strip().replace('\\', '/')
        
        divider_style_parts = [f"--divider-top: {divider_top}px;"]
        if divider_img and divider_img != "Ninguno (Línea Sólida)":
            divider_style_parts.append(f"--divider-color: transparent;")
            divider_style_parts.append(f"--divider-image: url('{divider_img}');")
            divider_style_parts.append(f"--divider-width: 100px;")
            divider_style_parts.append(f"--divider-height: 12px;")
        else:
            divider_style_parts.append(f"--divider-color: {divider_color};")
            divider_style_parts.append(f"--divider-image: none;")
            divider_style_parts.append(f"--divider-width: 60px;")
            divider_style_parts.append(f"--divider-height: 2px;")
            
        divider_style_str = " ".join(divider_style_parts)
        
        new_html = f'''<a href="{tarjeta["href"]}" class="category-card {card_class}" style="{style_str}">{tag_html}
                        <div class="card-inner">
                            {card_bg_html}
                            <div class="card-overlay"></div>
                            <div class="card-content">
                                <h2 data-text="{new_title.upper()}" style="{h2_style_str}">{new_title.upper()}</h2>
                                <span class="subtitle" style="{span_style_str}">{new_subtitle}</span>
                                <div class="divider" style="{divider_style_str}"></div>
                                <span class="explore">Explorar colección <span class="arrow">→</span></span>
                            </div>
                        </div>
                    </a>'''
                    
        try:
            with open(self.index_html_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            content = content.replace(tarjeta["full_html"], new_html)
            
            with open(self.index_html_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            old_bg = self.fondos_css.get(card_class, "")
            if old_bg != new_bg and new_bg:
                with open(self.styles_css_path, "r", encoding="utf-8") as f:
                    css_content = f.read()
                    
                rule_pattern = rf'\.{card_class}\s+\.card-content::after\s*\{{[^}}]*?background-image:\s*url\([^)]+\);\s*\}}'
                new_rule = f".{card_class} .card-content::after {{\n    background-image: url('{new_bg}');\n}}"
                
                if re.search(rule_pattern, css_content):
                    css_content = re.sub(rule_pattern, new_rule, css_content)
                else:
                    css_content += f"\n\n/* Fondo dinámico añadido */\n{new_rule}\n"
                    
                with open(self.styles_css_path, "w", encoding="utf-8") as f:
                    f.write(css_content)
                    
            self.cargar_tarjetas_y_fondos()
            self.combo_banners.current(idx)
            self.seleccionar_tarjeta()
            
            # Subir a GitHub en segundo plano
            threading.Thread(target=self.subir_tarjetas_git, args=(card_class,), daemon=True).start()
            
            messagebox.showinfo("Éxito", "Tarjeta actualizada correctamente en el código del sitio web.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la tarjeta:\n{e}")

    def crear_tarjeta(self):
        new_class = self.var_new_card_class.get().strip()
        new_href = self.var_new_card_href.get().strip()
        new_title = self.var_new_card_title.get().strip()
        new_subtitle = self.var_new_card_subtitle.get().strip()
        new_bg = self.var_new_card_bg.get().replace('\\', '/')
        
        if not new_class or not new_href or not new_title or not new_subtitle:
            messagebox.showerror("Error", "Todos los campos de la nueva tarjeta son obligatorios.")
            return
            
        # Obtener tipografía y estilos seleccionados en la UI
        try:
            selected_font = self.var_banner_font.get()
        except AttributeError:
            selected_font = "Merriweather (Serif clásica)"
            
        new_font_family_css = self.get_font_family_css(selected_font)
            
        try:
            t_size = f"{self.scale_banner_title_size.get()}px"
        except AttributeError:
            t_size = "24px"
            
        try:
            t_color = self.var_banner_title_color.get().strip() or "#ffffff"
        except AttributeError:
            t_color = "#ffffff"
            
        try:
            s_size = f"{self.scale_banner_sub_size.get()}px"
        except AttributeError:
            s_size = "14px"
            
        try:
            s_color = self.var_banner_sub_color.get().strip() or "#e5dacb"
        except AttributeError:
            s_color = "#e5dacb"
            
        h2_styles = [f"font-size: {t_size};", "color: #ffffff;", f"--title-color: {t_color};"]
        if new_font_family_css:
            h2_styles.append(f"font-family: {new_font_family_css};")
        h2_style_str = " ".join(h2_styles)
        
        span_styles = [f"font-size: {s_size};", f"color: {s_color};"]
        if new_font_family_css:
            span_styles.append(f"font-family: {new_font_family_css};")
        span_style_str = " ".join(span_styles)
 
        try:
            wood_scale = self.scale_banner_wood_size.get() / 100.0
        except AttributeError:
            wood_scale = 1.0
            
        bg_base = self.var_card_bg_base.get().strip().replace('\\', '/')
        if bg_base and bg_base != "img/fondo_rayas.png":
            card_bg_html = f'<div class="card-bg" style="background-image: url(\'{bg_base}\');"></div>'
        else:
            card_bg_html = '<div class="card-bg"></div>'
            
        bg_wood = self.var_card_bg_wood.get().strip().replace('\\', '/')
        style_parts = [f"--badge-scale: {wood_scale:.2f};"]
        if bg_wood and bg_wood != "img/fondo_letra.png":
            style_parts.append(f"--wood-image: url('{bg_wood}');")
        style_str = " ".join(style_parts)
        
        # Divider style
        try:
            divider_offset = self.scale_banner_divider_top.get()
        except AttributeError:
            divider_offset = 0
        divider_top = 56 + divider_offset
        
        divider_color = self.var_banner_divider_color.get().strip() or "#FFBF00"
        divider_img = self.var_banner_divider_img.get().strip().replace('\\', '/')
        
        divider_style_parts = [f"--divider-top: {divider_top}px;"]
        if divider_img and divider_img != "Ninguno (Línea Sólida)":
            divider_style_parts.append(f"--divider-color: transparent;")
            divider_style_parts.append(f"--divider-image: url('{divider_img}');")
            divider_style_parts.append(f"--divider-width: 100px;")
            divider_style_parts.append(f"--divider-height: 12px;")
        else:
            divider_style_parts.append(f"--divider-color: {divider_color};")
            divider_style_parts.append(f"--divider-image: none;")
            divider_style_parts.append(f"--divider-width: 60px;")
            divider_style_parts.append(f"--divider-height: 2px;")
            
        divider_style_str = " ".join(divider_style_parts)
        
        new_html = f'''                    <a href="{new_href}" class="category-card {new_class}" style="{style_str}">
                        <div class="card-inner">
                            {card_bg_html}
                            <div class="card-overlay"></div>
                            <div class="card-content">
                                <h2 data-text="{new_title.upper()}" style="{h2_style_str}">{new_title.upper()}</h2>
                                <span class="subtitle" style="{span_style_str}">{new_subtitle}</span>
                                <div class="divider" style="{divider_style_str}"></div>
                                <span class="explore">Explorar colección <span class="arrow">→</span></span>
                            </div>
                        </div>
                    </a>\n'''
                    
        try:
            with open(self.index_html_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            grid_pattern = r'(<div\s+class="categories-grid"[^>]*>[\s\S]*?<\/a>\s*)(<\/div>)'
            matches = list(re.finditer(grid_pattern, content))
            if not matches:
                messagebox.showerror("Error", "No se encontró el contenedor de rejilla de categorías en index.html.")
                return
                
            # Tomar el último bloque de rejilla de categorías (el que está al final de la página)
            last_match = matches[-1]
            prefix = last_match.group(1)
            suffix = last_match.group(2)
            
            new_grid_content = prefix + new_html + "                " + suffix
            
            # Reemplazar el bloque en su posición exacta al final
            start_pos = last_match.start()
            end_pos = last_match.end()
            content = content[:start_pos] + new_grid_content + content[end_pos:]
            
            with open(self.index_html_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            new_css_rule = f"\n\n.{new_class} .card-content::after {{\n    background-image: url('{new_bg}');\n}}"
            with open(self.styles_css_path, "a", encoding="utf-8") as f:
                f.write(new_css_rule)
                
            self.var_new_card_class.set("")
            self.var_new_card_href.set("")
            self.var_new_card_title.set("")
            self.var_new_card_subtitle.set("")
            
            self.cargar_tarjetas_y_fondos()
            self.combo_banners.current(len(self.tarjetas_web) - 1)
            self.seleccionar_tarjeta()
            
            threading.Thread(target=self.subir_tarjetas_git, args=(new_class,), daemon=True).start()
            
            messagebox.showinfo("Éxito", f"Nueva tarjeta '{new_title}' agregada al sitio web.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la tarjeta:\n{e}")

    def subir_tarjetas_git(self, card_name):
        # Git sync activado
        git_exe = self.find_git_executable()
        repo_dir = os.path.dirname(self.index_html_path)
        try:
            subprocess.run([git_exe, "add", "index.html", "styles.css"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            commit_msg = f"Actualizar tarjeta principal: {card_name}"
            subprocess.run([git_exe, "commit", "-m", commit_msg], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            subprocess.run([git_exe, "pull", "--rebase"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            subprocess.run([git_exe, "push"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        except Exception as e:
            print("Error en git push de tarjetas:", e)

    def previsualizar_nueva_tarjeta(self):
        if not HAS_PIL:
            return
            
        # 1. Obtener imagen de fondo base
        base_bg_rel = self.var_card_bg_base.get().replace('\\', '/')
        rayas_path = None
        for d in self.target_dirs:
            p = os.path.join(d, base_bg_rel)
            if os.path.exists(p):
                rayas_path = p
                break
        if not rayas_path:
            rayas_path = os.path.join(self.base_dir, base_bg_rel)
            
        if os.path.exists(rayas_path):
            try:
                with Image.open(rayas_path) as temp_img:
                    temp_img.load()
                    base_img = temp_img.convert("RGBA")
            except:
                base_img = Image.new("RGBA", (416, 274), (245, 240, 235, 255))
        else:
            base_img = Image.new("RGBA", (416, 274), (245, 240, 235, 255))
            
        base_img = self.resize_cover(base_img, (416, 274))
        
        # Overlay café oscuro semitransparente
        overlay = Image.new("RGBA", (416, 274), (75, 55, 45, 60))
        base_img = Image.alpha_composite(base_img, overlay)
        
        # 2. Cargar y escalar silueta de madera
        wood_bg_rel = self.var_card_bg_wood.get().replace('\\', '/')
        letra_path = None
        for d in self.target_dirs:
            p = os.path.join(d, wood_bg_rel)
            if os.path.exists(p):
                letra_path = p
                break
        if not letra_path:
            letra_path = os.path.join(self.base_dir, wood_bg_rel)
            
        try:
            scale_percent = self.scale_banner_wood_size.get()
        except AttributeError:
            scale_percent = 100
            
        new_w = int(345 * (scale_percent / 100.0))
        new_h = int(224 * (scale_percent / 100.0))
        
        new_w = max(10, min(new_w, 800))
        new_h = max(10, min(new_h, 600))
        
        if os.path.exists(letra_path):
            try:
                with Image.open(letra_path) as temp_img:
                    temp_img.load()
                    wood_img = temp_img.convert("RGBA")
                wood_img = wood_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Cargar el fondo de la categoría seleccionado
                fondo_rel = self.var_new_card_bg.get()
                fondo_abs = None
                for d in self.target_dirs:
                    p = os.path.join(d, fondo_rel)
                    if os.path.exists(p):
                        fondo_abs = p
                        break
                        
                if fondo_abs and os.path.exists(fondo_abs):
                    try:
                        with Image.open(fondo_abs) as temp_img:
                            temp_img.load()
                            cat_img = temp_img.convert("RGBA")
                        cat_img = self.resize_cover(cat_img, (new_w, new_h))
                        
                        orig_alpha = wood_img.getchannel('A')
                        from PIL import ImageChops
                        multiplied = ImageChops.multiply(wood_img, cat_img)
                        wood_img = Image.blend(wood_img, multiplied, 0.35)
                        wood_img.putalpha(orig_alpha)
                    except Exception as e:
                        print("Error mezclando textura de categoría:", e)
                        
                cx, cy = 208, 137
                px = cx - (new_w // 2)
                py = cy - (new_h // 2)
                base_img.paste(wood_img, (px, py), wood_img)
            except Exception as e:
                print("Error dibujando silueta de madera:", e)
                
        draw = ImageDraw.Draw(base_img)
        
        # Cargar fuentes del sistema
        try:
            selected_font = self.var_banner_font.get()
        except AttributeError:
            selected_font = "Merriweather (Serif clásica)"
            
        if any(f in selected_font for f in ["Petit Formal Script", "Parisienne", "Dancing Script", "Great Vibes", "Alex Brush", "Pinyon Script", "Sacramento"]):
            title_font_type = "script"
        elif any(f in selected_font for f in ["Merriweather", "Playfair Display", "Cormorant Garamond", "Cinzel", "Lora"]):
            title_font_type = "serif"
        else:
            title_font_type = "sans"
            
        try:
            t_size = self.scale_banner_title_size.get()
        except AttributeError:
            t_size = 24
            
        try:
            s_size = self.scale_banner_sub_size.get()
        except AttributeError:
            s_size = 14
            
        font_title = self.get_pillow_font(title_font_type, t_size, bold=True)
        font_sub = self.get_pillow_font(title_font_type, s_size, bold=False)
        
        title_text = self.var_new_card_title.get().upper().strip()
        sub_text = self.var_new_card_subtitle.get().strip()
        
        if not title_text:
            title_text = "NUEVA TARJETA"
            
        # Colores
        try:
            t_color_str = self.var_banner_title_color.get().strip() or "#ffffff"
        except AttributeError:
            t_color_str = "#ffffff"
            
        try:
            s_color_str = self.var_banner_sub_color.get().strip() or "#e5dacb"
        except AttributeError:
            s_color_str = "#e5dacb"
        
        def hex_to_rgba(hex_str, default=(255, 255, 255, 255)):
            hex_str = hex_str.lstrip('#')
            if len(hex_str) == 6:
                try:
                    r = int(hex_str[0:2], 16)
                    g = int(hex_str[2:4], 16)
                    b = int(hex_str[4:6], 16)
                    return (r, g, b, 255)
                except:
                    pass
            elif len(hex_str) == 3:
                try:
                    r = int(hex_str[0]*2, 16)
                    g = int(hex_str[1]*2, 16)
                    b = int(hex_str[2]*2, 16)
                    return (r, g, b, 255)
                except:
                    pass
            return default
            
        t_rgba = hex_to_rgba(t_color_str, (75, 55, 45, 255))
        s_rgba = hex_to_rgba(s_color_str, (229, 218, 203, 255))
        
        try:
            ts_width = float(self.scale_banner_title_stroke_width.get())
        except AttributeError:
            ts_width = 2.5
            
        try:
            ts_color_str = self.var_banner_title_stroke_color.get().strip() or "#ffffff"
        except AttributeError:
            ts_color_str = "#ffffff"
            
        ts_rgba = hex_to_rgba(ts_color_str, (255, 255, 255, 255))
        
        cw, ch = 208, 137
        
        # Título outlined (Relleno: t_rgba, Borde: ts_rgba)
        self.draw_outlined_text(draw, (cw, ch), title_text, font_title, t_rgba, ts_rgba, int(round(ts_width)), anchor="mm")
        
        # Subtítulo (Calculado como top: calc(50% + 28px) en la web -> 137 + 28 = 165px)
        draw.text((cw, 165), sub_text, font=font_sub, fill=s_rgba, anchor="mt")
        
        # Divisor Dinámico
        try:
            divider_offset = self.scale_banner_divider_top.get()
        except AttributeError:
            divider_offset = 0
            
        divider_color_str = self.var_banner_divider_color.get().strip() or "#FFBF00"
        divider_img_rel = self.var_banner_divider_img.get().strip().replace('\\', '/')
        
        y_divider = 193 + divider_offset
        
        if divider_img_rel and divider_img_rel != "Ninguno (Línea Sólida)":
            div_img_path = None
            for d in self.target_dirs:
                p = os.path.join(d, divider_img_rel)
                if os.path.exists(p):
                    div_img_path = p
                    break
            if not div_img_path:
                div_img_path = os.path.join(self.base_dir, divider_img_rel)
                
            if os.path.exists(div_img_path):
                try:
                    div_img = Image.open(div_img_path).convert("RGBA")
                    orig_w, orig_h = div_img.size
                    new_div_w = 100
                    new_div_h = max(2, int(orig_h * (100.0 / orig_w)))
                    div_img = div_img.resize((new_div_w, new_div_h), Image.Resampling.LANCZOS)
                    
                    px = 208 - (new_div_w // 2)
                    py = y_divider - (new_div_h // 2)
                    base_img.paste(div_img, (px, py), div_img)
                except Exception as e:
                    print("Error dibujando imagen separador en preview:", e)
        else:
            # Dibujar línea sólida
            draw.line([(208 - 30, y_divider), (208 + 30, y_divider)], fill=divider_color_str, width=2)
        
        # Aplicar esquinas redondeadas de 24px (border-radius) fundiendo sobre el color de fondo de la app (#fcfaf7)
        try:
            final_canvas = Image.new("RGBA", (416, 274), (252, 250, 247, 255))
            card_mask = Image.new("L", (416, 274), 0)
            mask_draw = ImageDraw.Draw(card_mask)
            mask_draw.rounded_rectangle([0, 0, 416, 274], radius=24, fill=255)
            rounded_card = Image.new("RGBA", (416, 274), (0, 0, 0, 0))
            rounded_card.paste(base_img, (0, 0), card_mask)
            final_canvas.paste(rounded_card, (0, 0), rounded_card)
            base_img = final_canvas
        except Exception as e:
            print("Error aplicando bordes redondeados a la previsualización:", e)
            
        self.tk_banner_img = ImageTk.PhotoImage(base_img)
        self.canvas_prev.delete("all")
        self.canvas_prev.create_image(0, 0, image=self.tk_banner_img, anchor="nw")

    def eliminar_tarjeta(self):
        idx = self.combo_banners.current()
        if idx == -1:
            messagebox.showerror("Error", "Por favor, selecciona una tarjeta de la lista para eliminar.")
            return
            
        tarjeta = self.tarjetas_web[idx]
        card_class = tarjeta["class"]
        title = tarjeta["title"]
        
        if not messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar la tarjeta '{title}'?"):
            return
            
        try:
            # 1. Leer index.html y eliminar el bloque HTML
            with open(self.index_html_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            content = content.replace(tarjeta["full_html"], "")
            
            with open(self.index_html_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            # 2. Leer styles.css y eliminar la regla de fondo
            if os.path.exists(self.styles_css_path):
                with open(self.styles_css_path, "r", encoding="utf-8") as f:
                    css_content = f.read()
                    
                rule_pattern = rf'\.{card_class}\s+\.card-content::after\s*\{{[^}}]*?background-image:\s*url\([^)]+\);\s*\}}'
                css_content = re.sub(rule_pattern, "", css_content)
                
                with open(self.styles_css_path, "w", encoding="utf-8") as f:
                    f.write(css_content)
                    
            # 3. Recargar combobox y seleccionar la primera
            self.cargar_tarjetas_y_fondos()
            
            # Sincronizar en segundo plano con Git
            threading.Thread(target=self.subir_tarjetas_git, args=(card_class,), daemon=True).start()
            
            messagebox.showinfo("Éxito", f"La tarjeta '{title}' se eliminó correctamente del sitio web.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar la tarjeta:\n{e}")

    # ========================================================
    # FASE 4: GESTOR DE CARRUSEL (SLIDES DE INICIO)
    # ========================================================
    # ========================================================
    # FASE 5: MODIFICADOR DE BANNERS DE LEYENDA (NUEVA PESTAÑA)
    # ========================================================
    def build_leyendas_tab_ui(self, parent):
        # Contenedor principal de la pestaña (acoplado a right_panel)
        self.leyendas_container = tk.Frame(parent, bg=COLOR_BG)
        self.leyendas_container.pack(fill="both", expand=True)
        
        # Panel 1: Selección y Edición de Leyenda
        panel_edit = tk.Frame(self.leyendas_container, bg=COLOR_BG)
        panel_edit.pack(fill="both", expand=True)
        
        # --- PANEL 1: EDICIÓN ---
        # LabelFrame de Selección
        leyenda_sel = tk.LabelFrame(panel_edit, text=" Seleccionar Banner de Leyenda ", 
                                     font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                     bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=12)
        leyenda_sel.pack(fill="x", pady=(0, 8))
        
        tk.Label(leyenda_sel, text="Elegir Banner actual:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        
        self.combo_leyendas = ttk.Combobox(leyenda_sel, textvariable=self.var_leyenda_seleccionada, 
                                           state="readonly", font=("Segoe UI", 10))
        self.combo_leyendas.grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 0))
        self.combo_leyendas.bind("<<ComboboxSelected>>", self.seleccionar_leyenda)
        
        # LabelFrame de Edición
        self.leyenda_edit = tk.LabelFrame(panel_edit, text=" Editar Propiedades de Leyenda ", 
                                          font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                          bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=12)
        self.leyenda_edit.pack(fill="x", pady=8)
        
        # Texto Principal
        tk.Label(self.leyenda_edit, text="Texto Principal:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        self.entry_leyenda_title = tk.Entry(self.leyenda_edit, textvariable=self.var_leyenda_title, font=("Segoe UI", 10),
                                            relief="solid", bd=1, bg=COLOR_WHITE)
        self.entry_leyenda_title.grid(row=0, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        # Tamaño Letra Principal
        tk.Label(self.leyenda_edit, text="Tamaño Principal:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        self.combo_leyenda_title_size = ttk.Combobox(self.leyenda_edit, textvariable=self.var_leyenda_title_size, 
                                                     values=["20px", "24px", "28px", "32px", "38px", "42px", "48px", "54px"],
                                                     font=("Segoe UI", 10))
        self.combo_leyenda_title_size.grid(row=1, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        # Color Letra Principal
        tk.Label(self.leyenda_edit, text="Color Principal:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=2, column=0, sticky="w", pady=6)
        
        frame_color_title = tk.Frame(self.leyenda_edit, bg=COLOR_BG)
        frame_color_title.grid(row=2, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        self.btn_title_color = tk.Button(frame_color_title, text="🎨 Elegir Color", font=("Segoe UI", 9, "bold"),
                                         fg=COLOR_BG, bg=COLOR_TEXT, relief="flat", cursor="hand2",
                                         command=self.elegir_color_titulo)
        self.btn_title_color.pack(side="left")
        self.lbl_title_color_indicator = tk.Label(frame_color_title, text="   ", bg="#1c1c1c", width=4, relief="solid", bd=1)
        self.lbl_title_color_indicator.pack(side="left", padx=10)
        self.entry_title_color = tk.Entry(frame_color_title, textvariable=self.var_leyenda_title_color, font=("Segoe UI", 9),
                                          relief="solid", bd=1, bg=COLOR_WHITE, width=10)
        self.entry_title_color.pack(side="left")
 
        # Texto Secundario (Opcional)
        tk.Label(self.leyenda_edit, text="Texto Secundario:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=3, column=0, sticky="w", pady=6)
        self.entry_leyenda_subtitle = tk.Entry(self.leyenda_edit, textvariable=self.var_leyenda_subtitle, font=("Segoe UI", 10),
                                               relief="solid", bd=1, bg=COLOR_WHITE)
        self.entry_leyenda_subtitle.grid(row=3, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        # Tamaño Letra Secundario
        tk.Label(self.leyenda_edit, text="Tamaño Secundario:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=4, column=0, sticky="w", pady=6)
        self.combo_leyenda_sub_size = ttk.Combobox(self.leyenda_edit, textvariable=self.var_leyenda_sub_size, 
                                                   values=["14px", "16px", "18px", "20px", "22px", "24px", "28px", "32px", "38px", "42px", "48px", "54px"],
                                                   font=("Segoe UI", 10))
        self.combo_leyenda_sub_size.grid(row=4, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        # Color Letra Secundario
        tk.Label(self.leyenda_edit, text="Color Secundario:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=5, column=0, sticky="w", pady=6)
        
        frame_color_sub = tk.Frame(self.leyenda_edit, bg=COLOR_BG)
        frame_color_sub.grid(row=5, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        self.btn_sub_color = tk.Button(frame_color_sub, text="🎨 Elegir Color", font=("Segoe UI", 9, "bold"),
                                       fg=COLOR_BG, bg=COLOR_TEXT, relief="flat", cursor="hand2",
                                       command=self.elegir_color_sub)
        self.btn_sub_color.pack(side="left")
        self.lbl_sub_color_indicator = tk.Label(frame_color_sub, text="   ", bg="#1c1c1c", width=4, relief="solid", bd=1)
        self.lbl_sub_color_indicator.pack(side="left", padx=10)
        self.entry_sub_color = tk.Entry(frame_color_sub, textvariable=self.var_leyenda_sub_color, font=("Segoe UI", 9),
                                        relief="solid", bd=1, bg=COLOR_WHITE, width=10)
        self.entry_sub_color.pack(side="left")
        
        # Color de Fondo del Banner
        tk.Label(self.leyenda_edit, text="Fondo (Color):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=6, column=0, sticky="w", pady=6)
        
        frame_color_bg = tk.Frame(self.leyenda_edit, bg=COLOR_BG)
        frame_color_bg.grid(row=6, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        self.btn_bg_color = tk.Button(frame_color_bg, text="🎨 Elegir Fondo", font=("Segoe UI", 9, "bold"),
                                      fg=COLOR_BG, bg=COLOR_TEXT, relief="flat", cursor="hand2",
                                      command=self.elegir_color_bg)
        self.btn_bg_color.pack(side="left")
        self.lbl_bg_color_indicator = tk.Label(frame_color_bg, text="   ", bg="#E6BDB3", width=4, relief="solid", bd=1)
        self.lbl_bg_color_indicator.pack(side="left", padx=10)
        self.entry_bg_color = tk.Entry(frame_color_bg, textvariable=self.var_leyenda_bg_color, font=("Segoe UI", 9),
                                       relief="solid", bd=1, bg=COLOR_WHITE, width=10)
        self.entry_bg_color.pack(side="left")
        
        # Imagen de Fondo (Opcional)
        tk.Label(self.leyenda_edit, text="Fondo (Imagen):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=7, column=0, sticky="w", pady=6)
        self.combo_leyenda_bg_img = ttk.Combobox(self.leyenda_edit, textvariable=self.var_leyenda_bg_img, 
                                                 state="readonly", font=("Segoe UI", 10))
        self.combo_leyenda_bg_img.grid(row=7, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        self.combo_leyenda_bg_img.bind("<<ComboboxSelected>>", self.on_bg_img_selected)
        
        # Tipo de Letra
        tk.Label(self.leyenda_edit, text="Estilo Letra:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=8, column=0, sticky="w", pady=6)
        self.combo_leyenda_font = ttk.Combobox(self.leyenda_edit, textvariable=self.var_leyenda_font, 
                                               state="readonly", font=("Segoe UI", 10),
                                               values=self.FUENTES_LIST)
        self.combo_leyenda_font.grid(row=8, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        # Formato (Negritas / Cursivas)
        frame_font_styles = tk.Frame(self.leyenda_edit, bg=COLOR_BG)
        frame_font_styles.grid(row=9, column=1, columnspan=2, sticky="w", pady=6, padx=(10, 0))
        
        # Principal
        tk.Label(frame_font_styles, text="Principal:", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(side="left", padx=(0, 5))
        chk_bold = tk.Checkbutton(frame_font_styles, text="N", variable=self.var_leyenda_bold,
                                  font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG,
                                  activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                                  selectcolor=COLOR_WHITE)
        chk_bold.pack(side="left", padx=(0, 5))
        
        chk_italic = tk.Checkbutton(frame_font_styles, text="C", variable=self.var_leyenda_italic,
                                    font=("Segoe UI", 9, "italic"), fg=COLOR_TEXT, bg=COLOR_BG,
                                    activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                                    selectcolor=COLOR_WHITE)
        chk_italic.pack(side="left", padx=(0, 20))

        # Secundario
        tk.Label(frame_font_styles, text="Secundario:", font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(side="left", padx=(0, 5))
        chk_sub_bold = tk.Checkbutton(frame_font_styles, text="N", variable=self.var_leyenda_sub_bold,
                                      font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT, bg=COLOR_BG,
                                      activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                                      selectcolor=COLOR_WHITE)
        chk_sub_bold.pack(side="left", padx=(0, 5))
        
        chk_sub_italic = tk.Checkbutton(frame_font_styles, text="C", variable=self.var_leyenda_sub_italic,
                                        font=("Segoe UI", 9, "italic"), fg=COLOR_TEXT, bg=COLOR_BG,
                                        activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                                        selectcolor=COLOR_WHITE)
        chk_sub_italic.pack(side="left")
        
        # Frame de Controles de Icono (se muestra/oculta dinámicamente)
        self.frame_icon_controls = tk.Frame(self.leyenda_edit, bg=COLOR_BG)
        
        # Icono (Emoji / Texto)
        tk.Label(self.frame_icon_controls, text="Icono (o 'logos'):", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        self.entry_leyenda_icon = tk.Entry(self.frame_icon_controls, textvariable=self.var_leyenda_icon, font=("Segoe UI", 10),
                                           relief="solid", bd=1, bg=COLOR_WHITE)
        self.entry_leyenda_icon.grid(row=0, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        # Tamaño de Icono
        tk.Label(self.frame_icon_controls, text="Tamaño Icono:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        self.combo_leyenda_icon_size = ttk.Combobox(self.frame_icon_controls, textvariable=self.var_leyenda_icon_size, 
                                                    values=["30px", "36px", "40px", "46px", "50px"],
                                                    font=("Segoe UI", 10))
        self.combo_leyenda_icon_size.grid(row=1, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        # Color de Icono
        tk.Label(self.frame_icon_controls, text="Color Icono:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=2, column=0, sticky="w", pady=6)
        
        frame_color_icon = tk.Frame(self.frame_icon_controls, bg=COLOR_BG)
        frame_color_icon.grid(row=2, column=1, columnspan=2, sticky="ew", pady=6, padx=(10, 0))
        
        self.btn_icon_color = tk.Button(frame_color_icon, text="🎨 Elegir Color", font=("Segoe UI", 9, "bold"),
                                        fg=COLOR_BG, bg=COLOR_TEXT, relief="flat", cursor="hand2",
                                        command=self.elegir_color_icono)
        self.btn_icon_color.pack(side="left")
        self.lbl_icon_color_indicator = tk.Label(frame_color_icon, text="   ", bg="#00B8A6", width=4, relief="solid", bd=1)
        self.lbl_icon_color_indicator.pack(side="left", padx=10)
        self.entry_icon_color = tk.Entry(frame_color_icon, textvariable=self.var_leyenda_icon_color, font=("Segoe UI", 9),
                                         relief="solid", bd=1, bg=COLOR_WHITE, width=10)
        self.entry_icon_color.pack(side="left")
        self.frame_icon_controls.grid_columnconfigure(1, weight=1)
        
        # Botón Guardar Cambios en Banner
        self.btn_guardar_leyenda = tk.Button(panel_edit, text="💾 Guardar Cambios en Banner", 
                                             font=("Segoe UI", 11, "bold"), fg=COLOR_BG, bg=COLOR_TEXT, 
                                             activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                                             relief="flat", cursor="hand2", padx=20, pady=8,
                                             command=self.guardar_leyenda)
        self.btn_guardar_leyenda.pack(fill="x", pady=(10, 0))
        
        # Configurar grillas
        leyenda_sel.grid_columnconfigure(1, weight=1)
        self.leyenda_edit.grid_columnconfigure(1, weight=1)

    def elegir_color_bg(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="Elegir Color de Fondo", initialcolor=self.var_leyenda_bg_color.get())
        if color[1]:
            self.var_leyenda_bg_color.set(color[1])
            self.var_leyenda_bg_img.set("")
            self.actualizar_previsualizacion_leyenda()

    def elegir_color_titulo(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="Elegir Color de Título", initialcolor=self.var_leyenda_title_color.get())
        if color[1]:
            self.var_leyenda_title_color.set(color[1])
            self.actualizar_previsualizacion_leyenda()

    def elegir_color_sub(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="Elegir Color de Texto", initialcolor=self.var_leyenda_sub_color.get())
        if color[1]:
            self.var_leyenda_sub_color.set(color[1])
            self.actualizar_previsualizacion_leyenda()

    def elegir_color_icono(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="Elegir Color de Icono", initialcolor=self.var_leyenda_icon_color.get())
        if color[1]:
            self.var_leyenda_icon_color.set(color[1])
            self.actualizar_previsualizacion_leyenda()

    def on_bg_img_selected(self, event=None):
        val = self.var_leyenda_bg_img.get()
        if val == "(Ninguna - Usar Color Sólido)":
            self.var_leyenda_bg_img.set("")
        self.actualizar_previsualizacion_leyenda()

    def extraer_estilo_inline(self, attrs_str, property_name):
        style_match = re.search(r'style="([^"]*)"', attrs_str)
        if not style_match:
            return None
        style_str = style_match.group(1)
        prop_match = re.search(rf'{property_name}\s*:\s*([^;]+)', style_str)
        if prop_match:
            return prop_match.group(1).strip()
        return None

    def cargar_fondos_css_cards(self):
        if not os.path.exists(self.styles_css_path):
            return {}
        try:
            with open(self.styles_css_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            pattern = r'\.feature-card:nth-child\((\d+)\)::before\s*\{[^}]*?background-image:\s*url\(["\']?([^"\')]+)["\']?\)'
            matches = re.finditer(pattern, content)
            
            fondos = {}
            for m in matches:
                idx = int(m.group(1))
                img_path = m.group(2).strip()
                fondos[idx] = img_path
            return fondos
        except Exception as e:
            print("Error al cargar fondos de feature cards desde styles.css:", e)
            return {}

    def cargar_leyendas(self):
        self.leyendas_web = []
        if not os.path.exists(self.index_html_path):
            return
        try:
            with open(self.index_html_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 1. Parsear Banners
            pattern_banner = r'(<div\s+class="dots-banner-container"[^>]*>[\s\S]*?<\/div>\s*<\/div>)'
            matches_banner = re.finditer(pattern_banner, content)
            
            for m in matches_banner:
                full_html = m.group(1)
                
                h3_match = re.search(r'<h3\s+class="dots-banner-title"([^>]*)>([\s\S]*?)<\/h3>', full_html)
                title = h3_match.group(2).strip() if h3_match else ""
                h3_attrs = h3_match.group(1) if h3_match else ""
                
                p_match = re.search(r'<p\s+class="dots-banner-text"([^>]*)>([\s\S]*?)<\/p>', full_html)
                subtitle = p_match.group(2).strip() if p_match else ""
                p_attrs = p_match.group(1) if p_match else ""
                
                container_match = re.search(r'<div\s+class="dots-banner-container"([^>]*)>', full_html)
                container_attrs = container_match.group(1) if container_match else ""
                
                bg_color = self.extraer_estilo_inline(container_attrs, "background-color") or "#E6BDB3"
                bg_img = self.extraer_estilo_inline(container_attrs, "background-image") or ""
                if bg_img and "url(" in bg_img:
                    bg_img = bg_img.replace("url(", "").replace(")", "").replace("'", "").replace('"', '').strip()
                
                title_color = self.extraer_estilo_inline(h3_attrs, "color") or "#1c1c1c"
                title_size = self.extraer_estilo_inline(h3_attrs, "font-size") or "38px"
                font_family = self.extraer_estilo_inline(h3_attrs, "font-family") or ""
                font_weight = self.extraer_estilo_inline(h3_attrs, "font-weight") or ""
                font_style = self.extraer_estilo_inline(h3_attrs, "font-style") or ""
                
                if "Petit Formal Script" in font_family:
                    font_family_val = "Petit Formal Script (Script elegante)"
                elif "Parisienne" in font_family:
                    font_family_val = "Parisienne (Cursiva fluida)"
                elif "Dancing Script" in font_family:
                    font_family_val = "Dancing Script (Cursiva casual)"
                elif "Great Vibes" in font_family:
                    font_family_val = "Great Vibes (Caligrafía clásica)"
                elif "Playfair Display" in font_family:
                    font_family_val = "Playfair Display (Serif de alto contraste)"
                elif "Merriweather" in font_family:
                    font_family_val = "Merriweather (Serif clásica)"
                elif "Cormorant Garamond" in font_family:
                    font_family_val = "Cormorant Garamond (Serif de alta elegancia)"
                elif "Montserrat" in font_family:
                    font_family_val = "Montserrat (Sans-serif limpia)"
                elif "Outfit" in font_family:
                    font_family_val = "Outfit (Sans-serif moderna)"
                elif "Segoe UI" in font_family:
                    font_family_val = "Segoe UI (Estilo sistema)"
                else:
                    font_family_val = "Petit Formal Script (Script elegante)"
                    
                is_bold = "bold" in font_weight or font_weight in ("700", "900")
                is_italic = "italic" in font_style
                
                sub_color = self.extraer_estilo_inline(p_attrs, "color") or "#1c1c1c"
                sub_size = self.extraer_estilo_inline(p_attrs, "font-size") or "22px"
                sub_font_weight = self.extraer_estilo_inline(p_attrs, "font-weight") or ""
                sub_font_style = self.extraer_estilo_inline(p_attrs, "font-style") or ""
                sub_is_bold = "bold" in sub_font_weight or sub_font_weight in ("700", "900")
                sub_is_italic = "italic" in sub_font_style
                
                self.leyendas_web.append({
                    "type": "banner",
                    "full_html": full_html,
                    "title": title,
                    "subtitle": subtitle,
                    "bg_color": bg_color,
                    "bg_img": bg_img,
                    "title_color": title_color,
                    "title_size": title_size,
                    "sub_color": sub_color,
                    "sub_size": sub_size,
                    "container_attrs": container_attrs,
                    "h3_attrs": h3_attrs,
                    "p_attrs": p_attrs,
                    "font_family": font_family_val,
                    "bold": is_bold,
                    "italic": is_italic,
                    "sub_bold": sub_is_bold,
                    "sub_italic": sub_is_italic,
                    "icon": "",
                    "icon_color": "#00B8A6",
                    "icon_size": "40px",
                    "card_index": 0
                })
                
            # 2. Parsear Cuadros de Características (feature-card)
            pattern_card = r'(<div\s+class="feature-card"\s+id="feature-card-(\d+)"[^>]*>[\s\S]*?<\/div>\s*(?=<div\s+class="feature-card"|<\/section>))'
            matches_card = re.finditer(pattern_card, content)
            
            for m in matches_card:
                full_html = m.group(1)
                card_index = int(m.group(2))
                
                icon_match = re.search(r'<div\s+class="feature-icon"([^>]*)>([\s\S]*?)<\/div>', full_html)
                icon = icon_match.group(2).strip() if icon_match else ""
                if not icon_match and "shipping-logos-container" in full_html:
                    icon = "logos"
                icon_attrs = icon_match.group(1) if icon_match else ""
                
                h3_match = re.search(r'<h3\s+class="feature-title"([^>]*)>([\s\S]*?)<\/h3>', full_html)
                title = h3_match.group(2).strip() if h3_match else ""
                h3_attrs = h3_match.group(1) if h3_match else ""
                
                p_match = re.search(r'<p\s+class="feature-desc"([^>]*)>([\s\S]*?)<\/p>', full_html)
                subtitle = p_match.group(2).strip() if p_match else ""
                p_attrs = p_match.group(1) if p_match else ""
                
                container_match = re.search(r'<div\s+class="feature-card"[^>]*>', full_html)
                container_attrs = container_match.group(0) if container_match else ""
                
                bg_color = self.extraer_estilo_inline(container_attrs, "background-color") or "#ffffff"
                bg_img = self.fondos_css_cards.get(card_index, "")
                
                title_color = self.extraer_estilo_inline(h3_attrs, "color") or "#1c1c1c"
                title_size = self.extraer_estilo_inline(h3_attrs, "font-size") or "18px"
                font_family = self.extraer_estilo_inline(h3_attrs, "font-family") or ""
                font_weight = self.extraer_estilo_inline(h3_attrs, "font-weight") or ""
                font_style = self.extraer_estilo_inline(h3_attrs, "font-style") or ""
                
                if "Petit Formal Script" in font_family:
                    font_family_val = "Petit Formal Script (Script elegante)"
                elif "Parisienne" in font_family:
                    font_family_val = "Parisienne (Cursiva fluida)"
                elif "Dancing Script" in font_family:
                    font_family_val = "Dancing Script (Cursiva casual)"
                elif "Great Vibes" in font_family:
                    font_family_val = "Great Vibes (Caligrafía clásica)"
                elif "Playfair Display" in font_family:
                    font_family_val = "Playfair Display (Serif de alto contraste)"
                elif "Merriweather" in font_family:
                    font_family_val = "Merriweather (Serif clásica)"
                elif "Cormorant Garamond" in font_family:
                    font_family_val = "Cormorant Garamond (Serif de alta elegancia)"
                elif "Montserrat" in font_family:
                    font_family_val = "Montserrat (Sans-serif limpia)"
                elif "Outfit" in font_family:
                    font_family_val = "Outfit (Sans-serif moderna)"
                elif "Segoe UI" in font_family:
                    font_family_val = "Segoe UI (Estilo sistema)"
                else:
                    font_family_val = "Segoe UI (Estilo sistema)"
                    
                is_bold = "bold" in font_weight or font_weight in ("700", "900")
                is_italic = "italic" in font_style
                
                sub_color = self.extraer_estilo_inline(p_attrs, "color") or "#5a5a5a"
                sub_size = self.extraer_estilo_inline(p_attrs, "font-size") or "14px"
                sub_font_weight = self.extraer_estilo_inline(p_attrs, "font-weight") or ""
                sub_font_style = self.extraer_estilo_inline(p_attrs, "font-style") or ""
                sub_is_bold = "bold" in sub_font_weight or sub_font_weight in ("700", "900")
                sub_is_italic = "italic" in sub_font_style
                
                icon_color = self.extraer_estilo_inline(icon_attrs, "color") or "#00B8A6"
                icon_size = self.extraer_estilo_inline(icon_attrs, "font-size") or "40px"
                
                self.leyendas_web.append({
                    "type": "card",
                    "full_html": full_html,
                    "title": title,
                    "subtitle": subtitle,
                    "bg_color": bg_color,
                    "bg_img": bg_img,
                    "title_color": title_color,
                    "title_size": title_size,
                    "sub_color": sub_color,
                    "sub_size": sub_size,
                    "container_attrs": container_attrs,
                    "h3_attrs": h3_attrs,
                    "p_attrs": p_attrs,
                    "font_family": font_family_val,
                    "bold": is_bold,
                    "italic": is_italic,
                    "sub_bold": sub_is_bold,
                    "sub_italic": sub_is_italic,
                    "icon": icon,
                    "icon_color": icon_color,
                    "icon_size": icon_size,
                    "card_index": card_index
                })
        except Exception as e:
            print("Error al cargar leyendas de index.html:", e)

    def cargar_leyendas_y_actualizar(self):
        self.fondos_css_cards = self.cargar_fondos_css_cards()
        self.cargar_leyendas()
        combo_values = []
        for i, ley in enumerate(self.leyendas_web):
            type_label = "Banner" if ley["type"] == "banner" else "Cuadro"
            trunc_title = ley["title"][:40] + "..." if len(ley["title"]) > 40 else ley["title"]
            combo_values.append(f"{type_label} {i+1 if ley['type'] == 'banner' else ley['card_index']}: {trunc_title}")
        self.combo_leyendas["values"] = combo_values
        
        if self.img_folder:
            fondos_files = [f"img/{f}" for f in os.listdir(self.img_folder) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
            fondos_files.sort()
            self.combo_leyenda_bg_img["values"] = ["(Ninguna - Usar Color Sólido)"] + fondos_files
            
        self.combo_leyendas.set("Seleccionar Banner o Cuadro...")
        self.var_leyenda_title.set("")
        self.var_leyenda_subtitle.set("")
        self.var_leyenda_bg_color.set("#E6BDB3")
        self.var_leyenda_bg_img.set("")
        self.var_leyenda_title_size.set("38px")
        self.var_leyenda_title_color.set("#1c1c1c")
        self.var_leyenda_sub_size.set("22px")
        self.var_leyenda_sub_color.set("#1c1c1c")
        self.var_leyenda_icon.set("")
        self.var_leyenda_icon_color.set("#00B8A6")
        self.var_leyenda_icon_size.set("40px")
        self.actualizar_previsualizacion_leyenda()

    def seleccionar_leyenda(self, event=None):
        idx = self.combo_leyendas.current()
        if idx == -1:
            return
        ley = self.leyendas_web[idx]
        
        self.var_leyenda_title.set(ley["title"])
        self.var_leyenda_subtitle.set(ley["subtitle"])
        self.var_leyenda_bg_color.set(ley["bg_color"])
        self.var_leyenda_bg_img.set(ley["bg_img"])
        self.var_leyenda_title_size.set(ley["title_size"])
        self.var_leyenda_title_color.set(ley["title_color"])
        self.var_leyenda_sub_size.set(ley["sub_size"])
        self.var_leyenda_sub_color.set(ley["sub_color"])
        self.var_leyenda_icon.set(ley["icon"])
        self.var_leyenda_icon_color.set(ley["icon_color"])
        self.var_leyenda_icon_size.set(ley["icon_size"])
        self.var_leyenda_font.set(ley.get("font_family", "Segoe UI (Sans-serif moderna)"))
        self.var_leyenda_bold.set(ley.get("bold", False))
        self.var_leyenda_italic.set(ley.get("italic", False))
        self.var_leyenda_sub_bold.set(ley.get("sub_bold", False))
        self.var_leyenda_sub_italic.set(ley.get("sub_italic", False))
        
        if ley["type"] == "card":
            self.frame_icon_controls.grid(row=10, column=0, columnspan=3, sticky="ew", pady=6)
        else:
            self.frame_icon_controls.grid_forget()
            
        self.actualizar_previsualizacion_leyenda()

    def actualizar_previsualizacion_leyenda(self):
        if not HAS_PIL:
            return
            
        idx = self.combo_leyendas.current()
        ley = self.leyendas_web[idx] if idx != -1 else {"type": "banner"}
        
        bg_color_str = self.var_leyenda_bg_color.get().strip() or "#E6BDB3"
        bg_img_path = self.var_leyenda_bg_img.get().strip()
        
        try:
            self.lbl_title_color_indicator.config(bg=self.var_leyenda_title_color.get().strip() or "#1c1c1c")
        except:
            pass
        try:
            self.lbl_sub_color_indicator.config(bg=self.var_leyenda_sub_color.get().strip() or "#1c1c1c")
        except:
            pass
        try:
            self.lbl_bg_color_indicator.config(bg=bg_color_str)
        except:
            pass
        try:
            self.lbl_icon_color_indicator.config(bg=self.var_leyenda_icon_color.get().strip() or "#00B8A6")
        except:
            pass
            
        fondo_abs = None
        if bg_img_path:
            for d in self.target_dirs:
                p = os.path.join(d, bg_img_path)
                if os.path.exists(p):
                    fondo_abs = p
                    break
                    
        if fondo_abs:
            try:
                base_img = Image.open(fondo_abs).convert("RGBA")
                bw, bh = base_img.size
                aspect_src = bw / bh
                aspect_dest = 416 / 150
                if aspect_src > aspect_dest:
                    new_w = int(bh * aspect_dest)
                    left = (bw - new_w) // 2
                    base_img = base_img.crop((left, 0, left + new_w, bh))
                else:
                    new_h = int(bw / aspect_dest)
                    top = (bh - new_h) // 2
                    base_img = base_img.crop((0, top, bw, top + new_h))
                base_img = base_img.resize((416, 150), Image.Resampling.LANCZOS)
            except:
                base_img = Image.new("RGBA", (416, 150), bg_color_str)
        else:
            try:
                base_img = Image.new("RGBA", (416, 150), bg_color_str)
            except:
                base_img = Image.new("RGBA", (416, 150), "#E6BDB3")
                
        draw = ImageDraw.Draw(base_img)
        
        title_text = self.var_leyenda_title.get()
        sub_text = self.var_leyenda_subtitle.get()
        
        title_color = self.var_leyenda_title_color.get().strip() or "#1c1c1c"
        sub_color = self.var_leyenda_sub_color.get().strip() or "#1c1c1c"
        
        try:
            t_size = int(re.search(r'\d+', self.var_leyenda_title_size.get()).group(0))
        except:
            t_size = 38
        try:
            s_size = int(re.search(r'\d+', self.var_leyenda_sub_size.get()).group(0))
        except:
            s_size = 22
            
        scaled_t_size = max(8, int(t_size * 0.45))
        scaled_s_size = max(8, int(s_size * 0.45))
        
        is_card = ley["type"] == "card"
        selected_font = self.var_leyenda_font.get()
        if any(f in selected_font for f in ["Petit Formal Script", "Parisienne", "Dancing Script", "Great Vibes", "Alex Brush", "Pinyon Script", "Sacramento"]):
            title_font_type = "script"
        elif any(f in selected_font for f in ["Merriweather", "Playfair Display", "Cormorant Garamond", "Cinzel", "Lora"]):
            title_font_type = "serif"
        else:
            title_font_type = "sans"
            
        is_bold = self.var_leyenda_bold.get()
        is_italic = self.var_leyenda_italic.get()
        sub_is_bold = self.var_leyenda_sub_bold.get()
        sub_is_italic = self.var_leyenda_sub_italic.get()
        
        sub_font_type = title_font_type
        
        font_title = self.get_pillow_font(title_font_type, scaled_t_size, bold=is_bold, italic=is_italic)
        font_sub = self.get_pillow_font(sub_font_type, scaled_s_size, bold=sub_is_bold, italic=sub_is_italic)
        
        cw, ch = 208, 75
        
        if is_card:
            icon_val = self.var_leyenda_icon.get().strip()
            icon_color = self.var_leyenda_icon_color.get().strip() or "#00B8A6"
            
            try:
                i_size = int(re.search(r'\d+', self.var_leyenda_icon_size.get()).group(0))
            except:
                i_size = 40
            scaled_i_size = max(8, int(i_size * 0.45))
            font_icon = self.get_pillow_font("sans", scaled_i_size, bold=True)
            
            y_cursor = 15
            
            if icon_val == "logos":
                draw.rounded_rectangle([cw - 70, y_cursor, cw + 70, y_cursor + 24], radius=4, fill=(255, 255, 255, 180), outline=(200, 200, 200, 255))
                logos_font = self.get_pillow_font("sans", 9, bold=True)
                lw = draw.textlength("🚚 Starken / Blue", font=logos_font)
                draw.text((cw - (lw / 2), y_cursor + 6), "🚚 Starken / Blue", font=logos_font, fill=(75, 55, 45, 255))
                y_cursor += 36
            elif icon_val:
                iw = draw.textlength(icon_val, font=font_icon)
                draw.text((cw - (iw / 2), y_cursor), icon_val, font=font_icon, fill=icon_color)
                y_cursor += scaled_i_size + 8
                
            tw = draw.textlength(title_text, font=font_title)
            if tw > 380:
                words = title_text.split()
                line1, line2 = "", ""
                for word in words:
                    if draw.textlength(line1 + " " + word, font=font_title) < 360:
                        line1 += " " + word
                    else:
                        line2 += " " + word
                line1 = line1.strip()
                line2 = line2.strip()
                
                l1w = draw.textlength(line1, font=font_title)
                draw.text((cw - (l1w / 2), y_cursor), line1, font=font_title, fill=title_color)
                y_cursor += scaled_t_size + 4
                
                if line2:
                    l2w = draw.textlength(line2, font=font_title)
                    draw.text((cw - (l2w / 2), y_cursor), line2, font=font_title, fill=title_color)
                    y_cursor += scaled_t_size + 8
            else:
                draw.text((cw - (tw / 2), y_cursor), title_text, font=font_title, fill=title_color)
                y_cursor += scaled_t_size + 8
                
            if sub_text:
                sw = draw.textlength(sub_text, font=font_sub)
                if sw > 380:
                    words = sub_text.split()
                    line1, line2 = "", ""
                    for word in words:
                        if draw.textlength(line1 + " " + word, font=font_sub) < 360:
                            line1 += " " + word
                        else:
                            line2 += " " + word
                    line1 = line1.strip()
                    line2 = line2.strip()
                    
                    l1w = draw.textlength(line1, font=font_sub)
                    draw.text((cw - (l1w / 2), y_cursor), line1, font=font_sub, fill=sub_color)
                    y_cursor += scaled_s_size + 4
                    
                    if line2:
                        l2w = draw.textlength(line2, font=font_sub)
                        draw.text((cw - (l2w / 2), y_cursor), line2, font=font_sub, fill=sub_color)
                else:
                    draw.text((cw - (sw / 2), y_cursor), sub_text, font=font_sub, fill=sub_color)
        else:
            if sub_text:
                tw = draw.textlength(title_text, font=font_title)
                tx = cw - (tw / 2)
                ty = ch - 25
                draw.text((tx, ty), title_text, font=font_title, fill=title_color)
                
                sw = draw.textlength(sub_text, font=font_sub)
                sx = cw - (sw / 2)
                sy = ch + 15
                draw.text((sx, sy), sub_text, font=font_sub, fill=sub_color)
            else:
                tw = draw.textlength(title_text, font=font_title)
                tx = cw - (tw / 2)
                ty = ch - (scaled_t_size // 2)
                draw.text((tx, ty), title_text, font=font_title, fill=title_color)
                
        self.tk_leyenda_img = ImageTk.PhotoImage(base_img)
        if hasattr(self, 'lbl_compartido_prev_title'):
            self.lbl_compartido_prev_title.config(text="VISTA PREVIA COMPARTIDA: BANNER DE LEYENDA / CUADRO")
        self.canvas_leyendas_prev.delete("all")
        # Centrar la imagen de leyenda (416x150) dentro del canvas compartido (500x320)
        self.canvas_leyendas_prev.create_image(42, 85, image=self.tk_leyenda_img, anchor="nw")

    def guardar_leyenda(self):
        idx = self.combo_leyendas.current()
        if idx == -1:
            messagebox.showerror("Error", "Por favor, selecciona un banner o cuadro de la lista para modificar.")
            return
            
        leyenda = self.leyendas_web[idx]
        is_card = leyenda["type"] == "card"
        
        new_title = self.var_leyenda_title.get().strip()
        new_subtitle = self.var_leyenda_subtitle.get().strip()
        new_bg_color = self.var_leyenda_bg_color.get().strip()
        new_bg_img = self.var_leyenda_bg_img.get().strip().replace('\\', '/').replace('\\', '/')
        new_title_size = self.var_leyenda_title_size.get().strip()
        new_title_color = self.var_leyenda_title_color.get().strip()
        new_sub_size = self.var_leyenda_sub_size.get().strip()
        new_sub_color = self.var_leyenda_sub_color.get().strip()
        new_icon = self.var_leyenda_icon.get().strip()
        new_icon_color = self.var_leyenda_icon_color.get().strip()
        new_icon_size = self.var_leyenda_icon_size.get().strip()
        
        if not new_title:
            messagebox.showerror("Error", "El título no puede estar vacío.")
            return
            
        selected_font = self.var_leyenda_font.get()
        new_font_family_css = self.get_font_family_css(selected_font)
            
        new_bold = self.var_leyenda_bold.get()
        new_italic = self.var_leyenda_italic.get()
            
        # Reconstruir estilos inline del contenedor
        container_styles = []
        if is_card:
            if new_bg_color:
                container_styles.append(f"background-color: {new_bg_color};")
            container_style_str = " ".join(container_styles)
            
            # Icono o logos de transporte
            if new_icon == "logos":
                icon_html = '''<div class="shipping-logos-container">
                <div class="shipping-logos-row">
                    <img src="img/logo_starken.png" alt="Starken" class="shipping-logo">
                    <img src="img/Logo-Blue.png" alt="Blue Express" class="shipping-logo">
                </div>
                <div class="shipping-logos-row">
                    <img src="img/correos-chile-logo1.png" alt="Correos de Chile" class="shipping-logo correos-logo">
                </div>
            </div>'''
            elif new_icon:
                icon_style_str = f"font-size: {new_icon_size}; color: {new_icon_color};"
                icon_html = f'<div class="feature-icon" style="{icon_style_str}">{new_icon}</div>'
            else:
                icon_html = ""
                
            title_styles = [f"font-size: {new_title_size};", f"color: {new_title_color};"]
            if new_font_family_css:
                title_styles.append(f"font-family: {new_font_family_css};")
            title_styles.append("font-weight: bold;" if new_bold else "font-weight: normal;")
            title_styles.append("font-style: italic;" if new_italic else "font-style: normal;")
            title_style_str = " ".join(title_styles)
            
            new_sub_bold = self.var_leyenda_sub_bold.get()
            new_sub_italic = self.var_leyenda_sub_italic.get()
            
            desc_styles = [f"font-size: {new_sub_size};", f"color: {new_sub_color};"]
            if new_font_family_css:
                desc_styles.append(f"font-family: {new_font_family_css};")
            desc_styles.append("font-weight: bold;" if new_sub_bold else "font-weight: normal;")
            desc_styles.append("font-style: italic;" if new_sub_italic else "font-style: normal;")
            desc_style_str = " ".join(desc_styles)
            
            new_html = f'''<div class="feature-card" id="feature-card-{leyenda["card_index"]}" style="{container_style_str}">
            {icon_html}
            <h3 class="feature-title" style="{title_style_str}">{new_title}</h3>
            <p class="feature-desc" style="{desc_style_str}">{new_subtitle}</p>
        </div>'''
        else:
            # Banner
            new_sub_bold = self.var_leyenda_sub_bold.get()
            new_sub_italic = self.var_leyenda_sub_italic.get()
            
            if new_bg_img:
                container_styles.append(f"background-image: url('{new_bg_img}'); background-size: cover; background-position: center;")
            else:
                container_styles.append(f"background-color: {new_bg_color};")
            container_style_str = " ".join(container_styles)
            
            h3_styles = [f"font-size: {new_title_size};", f"color: {new_title_color};"]
            if new_font_family_css:
                h3_styles.append(f"font-family: {new_font_family_css};")
            h3_styles.append("font-weight: bold;" if new_bold else "font-weight: normal;")
            h3_styles.append("font-style: italic;" if new_italic else "font-style: normal;")
            if "margin: 0;" in leyenda["h3_attrs"] or "margin:0" in leyenda["h3_attrs"] or idx > 0:
                h3_styles.append("margin: 0;")
            if "line-height: 1.4;" in leyenda["h3_attrs"]:
                h3_styles.append("line-height: 1.4;")
            h3_style_str = " ".join(h3_styles)
            
            p_styles = [f"font-size: {new_sub_size};", f"color: {new_sub_color};"]
            if new_font_family_css:
                p_styles.append(f"font-family: {new_font_family_css};")
            p_styles.append("font-weight: bold;" if new_sub_bold else "font-weight: normal;")
            p_styles.append("font-style: italic;" if new_sub_italic else "font-style: normal;")
            p_style_str = " ".join(p_styles)
            
            if new_subtitle:
                p_html = f'\n                            <p class="dots-banner-text" style="{p_style_str}">{new_subtitle}</p>'
            else:
                p_html = ""
                
            content_class = "dots-banner-content"
            if "instagram-banner-content" in leyenda["full_html"]:
                content_class = "dots-banner-content instagram-banner-content"
                
            new_html = f'''<div class="dots-banner-container" style="{container_style_str}">
                        <div class="{content_class}">
                            <h3 class="dots-banner-title" style="{h3_style_str}">{new_title}</h3>{p_html}
                        </div>
                    </div>'''
                            
        try:
            with open(self.index_html_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            content = content.replace(leyenda["full_html"], new_html)
            
            with open(self.index_html_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            # Si es una tarjeta, sincronizar catalogo.html y actualizar styles.css
            if is_card:
                # 1. Leer index.html modificado para extraer la sección features-section entera
                with open(self.index_html_path, "r", encoding="utf-8") as f_idx:
                    idx_content = f_idx.read()
                
                sec_match = re.search(r'<section\s+class="features-section">[\s\S]*?<\/section>', idx_content)
                if sec_match:
                    features_section_html = sec_match.group(0)
                    
                    # 2. Sincronizar catalogo.html si existe
                    for d in self.target_dirs:
                        cat_path = os.path.join(d, "catalogo.html")
                        if os.path.exists(cat_path):
                            with open(cat_path, "r", encoding="utf-8") as f_cat:
                                cat_content = f_cat.read()
                            cat_content = re.sub(r'<section\s+class="features-section">[\s\S]*?<\/section>', features_section_html, cat_content)
                            with open(cat_path, "w", encoding="utf-8") as f_cat:
                                f_cat.write(cat_content)
                            try:
                                subprocess.run(["git", "add", "catalogo.html"], cwd=d, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                            except:
                                pass
                
                # 3. Actualizar styles.css si el fondo de imagen cambió
                old_bg = self.fondos_css_cards.get(leyenda["card_index"], "")
                if old_bg != new_bg_img and new_bg_img:
                    with open(self.styles_css_path, "r", encoding="utf-8") as f_css:
                        css_content = f_css.read()
                        
                    rule_pattern = rf'\.feature-card:nth-child\({leyenda["card_index"]}\)::before\s*\{{[^}}]*?background-image:\s*url\([^)]+\);\s*\}}'
                    new_rule = f".feature-card:nth-child({leyenda['card_index']})::before {{\n    background-image: url('{new_bg_img}');\n}}"
                    
                    if re.search(rule_pattern, css_content):
                        css_content = re.sub(rule_pattern, new_rule, css_content)
                    else:
                        css_content += f"\n\n/* Fondo dinámico de tarjeta añadido */\n{new_rule}\n"
                        
                    with open(self.styles_css_path, "w", encoding="utf-8") as f_css:
                        f_css.write(css_content)
                    try:
                        subprocess.run(["git", "add", "styles.css"], cwd=os.path.dirname(self.styles_css_path), check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                    except:
                        pass
            
            try:
                repo_dir = os.path.dirname(self.index_html_path)
                git_exe = "git"
                subprocess.run([git_exe, "add", "index.html"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            except:
                pass
                
            messagebox.showinfo("Éxito", "Banner o cuadro guardado correctamente.")
            self.cargar_leyendas_y_actualizar()
            self.combo_leyendas.current(idx)
            self.seleccionar_leyenda()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el banner o cuadro: {e}")

    # ========================================================
    # FASE 6: GESTOR DE VIDEOS Y TUTORIALES (NUEVA PESTAÑA)
    # ========================================================
    def build_videos_tab_ui(self, parent):
        self.videos_container = tk.Frame(parent, bg=COLOR_BG, padx=20, pady=15)
        self.videos_container.pack(fill="both", expand=True)
        
        # Panel Izquierdo: Controles
        panel_left = tk.Frame(self.videos_container, bg=COLOR_BG)
        panel_left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Separador Vertical 1
        sep = tk.Frame(self.videos_container, bg=COLOR_BORDER, width=2)
        sep.pack(side="left", fill="y", padx=10)
        
        # Panel Central: Listbox de Videos
        panel_middle = tk.Frame(self.videos_container, bg=COLOR_BG)
        panel_middle.pack(side="left", fill="both", expand=True, padx=10)
        
        # Separador Vertical 2
        sep2 = tk.Frame(self.videos_container, bg=COLOR_BORDER, width=2)
        sep2.pack(side="left", fill="y", padx=10)
        
        # Panel Derecho: Previsualización de Video
        panel_preview_video = tk.Frame(self.videos_container, bg=COLOR_BG)
        panel_preview_video.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        # --- PANEL IZQUIERDO: AGREGAR ---
        frame_agregar = tk.LabelFrame(panel_left, text=" Agregar Nuevo Video / Tutorial ", 
                                      font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                      bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=12)
        frame_agregar.pack(fill="x", pady=(0, 10))
        
        tk.Label(frame_agregar, text="Dirección de YouTube o Instagram:", font=("Segoe UI", 10, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_BG).pack(anchor="w", pady=4)
        
        self.entry_video_url = tk.Entry(frame_agregar, textvariable=self.var_nuevo_video_url, font=("Segoe UI", 10),
                                        relief="solid", bd=1, bg=COLOR_WHITE)
        self.entry_video_url.pack(fill="x", pady=6)
        
        btn_add = tk.Button(frame_agregar, text="➕ Agregar Video a la Lista", font=("Segoe UI", 10, "bold"),
                            fg=COLOR_BG, bg=COLOR_TEXT, relief="flat", cursor="hand2", pady=6,
                            command=self.agregar_video)
        btn_add.pack(fill="x", pady=(8, 0))
        
        # --- PANEL IZQUIERDO: ORDENAR ---
        frame_orden = tk.LabelFrame(panel_left, text=" Controles de Orden y Acciones ", 
                                    font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                    bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=12)
        frame_orden.pack(fill="x", pady=10)
        
        btn_up = tk.Button(frame_orden, text="▲ Subir Video (Subir en Lista)", font=("Segoe UI", 10, "bold"),
                           fg=COLOR_TEXT, bg=COLOR_BG, activebackground=COLOR_BORDER,
                           relief="solid", bd=1, cursor="hand2", pady=6,
                           command=self.subir_video)
        btn_up.pack(fill="x", pady=4)
        
        btn_down = tk.Button(frame_orden, text="▼ Bajar Video (Bajar en Lista)", font=("Segoe UI", 10, "bold"),
                             fg=COLOR_TEXT, bg=COLOR_BG, activebackground=COLOR_BORDER,
                             relief="solid", bd=1, cursor="hand2", pady=6,
                             command=self.bajar_video)
        btn_down.pack(fill="x", pady=4)
        
        btn_del = tk.Button(frame_orden, text="❌ Eliminar Video de la Lista", font=("Segoe UI", 10, "bold"),
                            fg=COLOR_WHITE, bg="#D9534F", activebackground="#C9302C",
                            relief="flat", cursor="hand2", pady=6,
                            command=self.eliminar_video)
        btn_del.pack(fill="x", pady=(12, 0))
        
        # --- PANEL CENTRAL: LISTA ---
        frame_lista = tk.LabelFrame(panel_middle, text=" Videos Guardados (En Orden de Aparición) ", 
                                    font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                    bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=12)
        frame_lista.pack(fill="both", expand=True)
        
        # Listbox y Scrollbar
        frame_listbox = tk.Frame(frame_lista, bg=COLOR_BG)
        frame_listbox.pack(fill="both", expand=True)
        
        self.listbox_videos = tk.Listbox(frame_listbox, font=("Segoe UI", 10), bg=COLOR_WHITE,
                                         selectbackground=COLOR_TEXT, selectforeground=COLOR_BG,
                                         relief="solid", bd=1, highlightthickness=0)
        scrollbar_listbox = ttk.Scrollbar(frame_listbox, orient="vertical", command=self.listbox_videos.yview)
        self.listbox_videos.configure(yscrollcommand=scrollbar_listbox.set)
        
        self.listbox_videos.pack(side="left", fill="both", expand=True)
        scrollbar_listbox.pack(side="right", fill="y")
        self.listbox_videos.bind("<<ListboxSelect>>", self.seleccionar_video)
        
        # Botón Guardar Cambios en Videos
        btn_save_videos = tk.Button(panel_middle, text="💾 Guardar Cambios en Videos", font=("Segoe UI", 11, "bold"),
                                    fg=COLOR_BG, bg=COLOR_TEXT, activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                                    relief="flat", cursor="hand2", pady=8,
                                    command=self.guardar_videos)
        btn_save_videos.pack(fill="x", pady=(10, 0))
        
        # --- PANEL DERECHO: PREVISUALIZACIÓN DE VIDEO ---
        lbl_prev_video_title = tk.Label(panel_preview_video, text="VISTA PREVIA DE VIDEO", 
                                        font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, bg=COLOR_BG)
        lbl_prev_video_title.pack(pady=(0, 10))
        
        # Canvas de Previsualización (400x250 - proporción 16:9 ideal)
        self.canvas_video_prev = tk.Canvas(panel_preview_video, width=400, height=250, bg="#faf6f0", bd=1, relief="solid")
        self.canvas_video_prev.pack(pady=5)
        
        # Hacer que hacer clic en el canvas también reproduzca el video
        self.canvas_video_prev.bind("<Button-1>", lambda e: self.reproducir_video_actual())
        
        # Botón para reproducir el video en el navegador
        self.btn_reproducir_video = tk.Button(panel_preview_video, text="▶️ Reproducir / Ver Video en Navegador", 
                                              font=("Segoe UI", 10, "bold"), fg=COLOR_BG, bg=COLOR_ACCENT, 
                                              activebackground=COLOR_ACCENT_HOVER, activeforeground=COLOR_BG,
                                              relief="flat", cursor="hand2", pady=8,
                                              command=self.reproducir_video_actual)
        self.btn_reproducir_video.pack(fill="x", pady=10)

    def cargar_videos_y_actualizar(self):
        self.videos_list = []
        videos_html_path = None
        for d in self.target_dirs:
            p = os.path.join(d, "videos.html")
            if os.path.exists(p):
                videos_html_path = p
                break
                
        if not videos_html_path:
            return
            
        try:
            with open(videos_html_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            pattern = r'<iframe\s+[^>]*src="([^"]+)"[^>]*>'
            self.videos_list = re.findall(pattern, content)
            
            self.listbox_videos.delete(0, tk.END)
            for url in self.videos_list:
                self.listbox_videos.insert(tk.END, url)
        except Exception as e:
            print("Error al cargar videos:", e)
            
        if hasattr(self, "canvas_video_prev"):
            self.mostrar_placeholder_video("Selecciona un video de la lista para previsualizar")

    def seleccionar_video(self, event=None):
        self.actualizar_previsualizacion_video()

    def actualizar_previsualizacion_video(self):
        if not HAS_PIL:
            return
            
        sel = self.listbox_videos.curselection()
        if not sel:
            self.mostrar_placeholder_video("Selecciona un video de la lista para previsualizar")
            return
            
        url = self.listbox_videos.get(sel[0])
        
        # Extraer ID de YouTube
        yt_match = re.search(r"youtube\.com/embed/([^/?#\s]+)", url)
        if yt_match:
            video_id = yt_match.group(1)
            self.mostrar_placeholder_video("Cargando miniatura de YouTube...")
            threading.Thread(target=self.descargar_miniatura_youtube_async, args=(video_id, url), daemon=True).start()
        else:
            # Si es Instagram u otro, mostrar placeholder correspondiente
            is_instagram = "instagram.com" in url
            title = "Video de Instagram" if is_instagram else "Video / Tutorial"
            self.mostrar_placeholder_video(f"{title}\nHaga clic para abrir en el navegador", is_instagram=is_instagram)

    def descargar_miniatura_youtube_async(self, video_id, original_url):
        import urllib.request
        thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        temp_img_path = os.path.join(self.base_dir, f"temp_yt_{video_id}.jpg")
        try:
            req = urllib.request.Request(thumb_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                with open(temp_img_path, "wb") as out_file:
                    out_file.write(response.read())
            
            # Dibujar miniatura en el hilo principal
            self.root.after(0, lambda: self.dibujar_miniatura_youtube(temp_img_path, original_url))
        except Exception as e:
            print("Error descargando miniatura de YouTube:", e)
            self.root.after(0, lambda: self.mostrar_placeholder_video("Reproducir Video (YouTube)\nHaga clic para ver", is_youtube=True))

    def dibujar_miniatura_youtube(self, img_path, original_url):
        try:
            if not os.path.exists(img_path):
                return
            
            base_img = Image.open(img_path).convert("RGBA")
            base_img = base_img.resize((400, 250), Image.Resampling.LANCZOS)
            
            # Dibujar botón de Play
            overlay = Image.new("RGBA", (400, 250), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            cx, cy = 200, 125
            r = 35
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 180), outline=(255, 255, 255, 220), width=2)
            
            p1 = (cx - 10, cy - 15)
            p2 = (cx - 10, cy + 15)
            p3 = (cx + 18, cy)
            draw.polygon([p1, p2, p3], fill=(217, 83, 79, 230))
            
            final_img = Image.alpha_composite(base_img, overlay)
            
            self.tk_video_img = ImageTk.PhotoImage(final_img)
            self.canvas_video_prev.delete("all")
            self.canvas_video_prev.create_image(0, 0, image=self.tk_video_img, anchor="nw")
            
            try:
                os.remove(img_path)
            except:
                pass
        except Exception as e:
            print("Error dibujando miniatura de YouTube:", e)

    def mostrar_placeholder_video(self, text, is_instagram=False, is_youtube=False):
        try:
            img = Image.new("RGBA", (400, 250), (245, 236, 225, 255))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([10, 10, 390, 240], radius=10, fill=None, outline=(229, 218, 203, 255), width=2)
            
            cx, cy = 200, 100
            r = 30
            if is_instagram:
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(225, 48, 108, 180), outline=(225, 48, 108, 220), width=2)
                p1, p2, p3 = (cx - 8, cy - 12), (cx - 8, cy + 12), (cx + 14, cy)
                draw.polygon([p1, p2, p3], fill=(255, 255, 255, 255))
            elif is_youtube:
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 0, 0, 180), outline=(255, 0, 0, 220), width=2)
                p1, p2, p3 = (cx - 8, cy - 12), (cx - 8, cy + 12), (cx + 14, cy)
                draw.polygon([p1, p2, p3], fill=(255, 255, 255, 255))
            else:
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(75, 55, 45, 180), outline=(75, 55, 45, 220), width=2)
                p1, p2, p3 = (cx - 8, cy - 12), (cx - 8, cy + 12), (cx + 14, cy)
                draw.polygon([p1, p2, p3], fill=(255, 252, 248, 255))
                
            font = self.get_pillow_font("sans", 12, bold=True)
            
            lines = text.split("\n")
            y_offset = 150
            for line in lines:
                lw = draw.textlength(line, font=font)
                draw.text((200 - (lw / 2), y_offset), line, font=font, fill=(75, 55, 45, 255))
                y_offset += 20
                
            self.tk_video_img = ImageTk.PhotoImage(img)
            self.canvas_video_prev.delete("all")
            self.canvas_video_prev.create_image(0, 0, image=self.tk_video_img, anchor="nw")
        except Exception as e:
            print("Error mostrando placeholder de video:", e)

    def reproducir_video_actual(self):
        sel = self.listbox_videos.curselection()
        if not sel:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un video de la lista para reproducir.")
            return
            
        url = self.listbox_videos.get(sel[0]).strip()
        
        import webbrowser
        try:
            if "youtube.com/embed/" in url:
                video_id = url.split("youtube.com/embed/")[-1].split("?")[0]
                watch_url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(watch_url)
            elif "instagram.com/p/" in url:
                post_id = url.split("instagram.com/p/")[-1].split("/")[0]
                insta_url = f"https://www.instagram.com/p/{post_id}/"
                webbrowser.open(insta_url)
            else:
                webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el video en el navegador:\n{e}")

    def agregar_video(self):
        url = self.var_nuevo_video_url.get().strip()
        if not url:
            messagebox.showerror("Error", "Por favor, ingresa una dirección de YouTube o Instagram.")
            return
            
        norm_url = self.normalizar_link_video(url)
        
        if norm_url in self.videos_list:
            messagebox.showwarning("Advertencia", "Este video ya está en la lista.")
            return
            
        self.videos_list.append(norm_url)
        self.listbox_videos.insert(tk.END, norm_url)
        self.var_nuevo_video_url.set("")
        messagebox.showinfo("Éxito", "Video agregado a la lista.")

    def normalizar_link_video(self, url):
        url = url.strip()
        yt_watch_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|youtube\.com/embed/)([^&\s?#]+)', url)
        if yt_watch_match:
            video_id = yt_watch_match.group(1)
            return f"https://www.youtube.com/embed/{video_id}"
            
        insta_match = re.search(r'instagram\.com/(?:reel|p)/([^/\s?#]+)', url)
        if insta_match:
            post_id = insta_match.group(1)
            return f"https://www.instagram.com/p/{post_id}/embed/"
            
        return url

    def eliminar_video(self):
        sel = self.listbox_videos.curselection()
        if not sel:
            messagebox.showerror("Error", "Selecciona un video de la lista para eliminar.")
            return
        idx = sel[0]
        self.listbox_videos.delete(idx)
        del self.videos_list[idx]
        messagebox.showinfo("Éxito", "Video eliminado de la lista.")

    def subir_video(self):
        sel = self.listbox_videos.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == 0:
            return
            
        self.videos_list[idx], self.videos_list[idx-1] = self.videos_list[idx-1], self.videos_list[idx]
        
        val = self.listbox_videos.get(idx)
        self.listbox_videos.delete(idx)
        self.listbox_videos.insert(idx-1, val)
        self.listbox_videos.select_set(idx-1)

    def bajar_video(self):
        sel = self.listbox_videos.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == len(self.videos_list) - 1:
            return
            
        self.videos_list[idx], self.videos_list[idx+1] = self.videos_list[idx+1], self.videos_list[idx]
        
        val = self.listbox_videos.get(idx)
        self.listbox_videos.delete(idx)
        self.listbox_videos.insert(idx+1, val)
        self.listbox_videos.select_set(idx+1)

    def guardar_videos(self):
        videos_html_path = None
        for d in self.target_dirs:
            p = os.path.join(d, "videos.html")
            if os.path.exists(p):
                videos_html_path = p
                break
                
        if not videos_html_path:
            messagebox.showerror("Error", "No se encontró el archivo videos.html")
            return
            
        try:
            cards_html = []
            for i, url in enumerate(self.videos_list):
                card = f'''            <!-- Video {i+1} -->
            <div class="video-card">
                <div class="video-container">
                    <iframe src="{url}" frameborder="0" allowfullscreen></iframe>
                </div>
            </div>'''
                cards_html.append(card)
                
            new_cards_block = "\n".join(cards_html)
            
            with open(videos_html_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            pattern = r'<div\s+class="videos-grid"[^>]*>([\s\S]*?)<\/div>\s*<\/main>'
            grid_match = re.search(pattern, content)
            if not grid_match:
                messagebox.showerror("Error", "No se encontró el grid de videos en videos.html")
                return
                
            old_grid_content = grid_match.group(1)
            new_grid_content = f"\n{new_cards_block}\n        "
            content = content.replace(old_grid_content, new_grid_content)
            
            with open(videos_html_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            # Guardar en index.html (primeros 2 videos)
            index_html_path = None
            for d in self.target_dirs:
                p = os.path.join(d, "index.html")
                if os.path.exists(p):
                    index_html_path = p
                    break
                    
            if index_html_path:
                with open(index_html_path, "r", encoding="utf-8") as f:
                    index_content = f.read()
                    
                idx_cards_html = []
                for i, url in enumerate(self.videos_list[:2]):
                    card = f'''                <!-- Video {i+1} -->
                <div class="video-card">
                    <div class="video-container">
                        <iframe src="{url}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                    </div>
                </div>'''
                    idx_cards_html.append(card)
                new_idx_cards_block = "\n".join(idx_cards_html)
                
                pattern_idx = r'<!-- FEATURED VIDEOS -->[\s\S]*?<div\s+class="videos-grid"[^>]*>([\s\S]*?)<\/div>\s*<div\s+style="text-align:\s*center;'
                idx_grid_match = re.search(pattern_idx, index_content)
                if idx_grid_match:
                    old_idx_grid = idx_grid_match.group(1)
                    new_idx_grid = f"\n{new_idx_cards_block}\n            "
                    index_content = index_content.replace(old_idx_grid, new_idx_grid)
                    
                    with open(index_html_path, "w", encoding="utf-8") as f:
                        f.write(index_content)
                        
            try:
                subprocess.run(["git", "add", "videos.html", "index.html"], cwd=os.path.dirname(videos_html_path), check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            except:
                pass
                
            messagebox.showinfo("Éxito", "Lista de videos guardada y sincronizada correctamente.")
            self.cargar_videos_y_actualizar()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la lista de videos: {e}")



    def build_carrusel_tab_ui(self, parent):
        # Contenedor principal
        self.carrusel_container = tk.Frame(parent, bg=COLOR_BG, padx=20, pady=15)
        self.carrusel_container.pack(fill="both", expand=True)
        
        # Panel Izquierdo: Controles de Carrusel (Sin expandir para evitar sobreancho)
        left_panel = tk.Frame(self.carrusel_container, bg=COLOR_BG)
        left_panel.pack(side="left", fill="both", expand=False, padx=(0, 10))
        
        # Separador Vertical 1
        sep_vert1 = tk.Frame(self.carrusel_container, bg=COLOR_BORDER, width=2)
        sep_vert1.pack(side="left", fill="y", padx=10)
        
        # Panel Central: Previsualización Compartida
        middle_panel = tk.Frame(self.carrusel_container, bg=COLOR_BG)
        middle_panel.pack(side="left", fill="both", padx=10)
        
        # Separador Vertical 2
        sep_vert2 = tk.Frame(self.carrusel_container, bg=COLOR_BORDER, width=2)
        sep_vert2.pack(side="left", fill="y", padx=10)
        
        # Panel Derecho: Controles de Banners de Leyenda
        right_panel = tk.Frame(self.carrusel_container, bg=COLOR_BG)
        right_panel.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        # --- PANEL IZQUIERDO (CARRUSEL) ---
        # LabelFrame de Selección/Lista
        slide_list_frame = tk.LabelFrame(left_panel, text=" Diapositivas del Carrusel ", 
                                         font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                         bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=10)
        slide_list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Listbox y scrollbar para los slides (con ancho fijo de 30)
        list_scroll = ttk.Scrollbar(slide_list_frame, orient="vertical")
        self.listbox_carrusel = tk.Listbox(slide_list_frame, font=("Segoe UI", 10), 
                                           yscrollcommand=list_scroll.set, bd=1, relief="solid",
                                           highlightthickness=0, selectbackground=COLOR_TEXT, selectforeground=COLOR_BG,
                                           exportselection=False, width=30)
        list_scroll.config(command=self.listbox_carrusel.yview)
        
        self.listbox_carrusel.pack(side="left", fill="both", expand=True)
        list_scroll.pack(side="right", fill="y")
        self.listbox_carrusel.bind("<<ListboxSelect>>", self.seleccionar_slide)
        
        # Botones de Orden (Arriba / Abajo)
        order_frame = tk.Frame(slide_list_frame, bg=COLOR_BG)
        order_frame.pack(side="right", fill="y", padx=(10, 0))
        
        btn_up = tk.Button(order_frame, text="⬆️ Subir", font=("Segoe UI", 10, "bold"),
                           fg=COLOR_BG, bg=COLOR_TEXT, activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                           relief="flat", cursor="hand2", command=self.mover_slide_arriba)
                           
        btn_up.pack(fill="x", pady=5)
        
        btn_down = tk.Button(order_frame, text="⬇️ Bajar", font=("Segoe UI", 10, "bold"),
                             fg=COLOR_BG, bg=COLOR_TEXT, activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                             relief="flat", cursor="hand2", command=self.mover_slide_abajo)
        btn_down.pack(fill="x", pady=5)
        
        # LabelFrame de Formulario / Edición
        self.slide_edit_frame = tk.LabelFrame(left_panel, text=" Propiedades de Diapositiva ", 
                                              font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, 
                                              bg=COLOR_BG, bd=2, relief="groove", padx=15, pady=15)
        self.slide_edit_frame.pack(fill="x", pady=10)
        
        # Título
        tk.Label(self.slide_edit_frame, text="Título:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        self.var_slide_title = tk.StringVar()
        self.entry_slide_title = tk.Entry(self.slide_edit_frame, textvariable=self.var_slide_title, font=("Segoe UI", 10),
                                          relief="solid", bd=1, bg=COLOR_WHITE, exportselection=False)
        self.entry_slide_title.grid(row=0, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        # Subtítulo
        tk.Label(self.slide_edit_frame, text="Subtítulo:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        self.var_slide_subtitle = tk.StringVar()
        self.entry_slide_subtitle = tk.Entry(self.slide_edit_frame, textvariable=self.var_slide_subtitle, font=("Segoe UI", 10),
                                             relief="solid", bd=1, bg=COLOR_WHITE, exportselection=False)
        self.entry_slide_subtitle.grid(row=1, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        # Imagen
        tk.Label(self.slide_edit_frame, text="Imagen:", font=("Segoe UI", 10, "bold"), 
                 fg=COLOR_TEXT, bg=COLOR_BG).grid(row=2, column=0, sticky="w", pady=6)
        self.var_slide_image = tk.StringVar()
        self.combo_slide_image = ttk.Combobox(self.slide_edit_frame, textvariable=self.var_slide_image, 
                                              state="readonly", font=("Segoe UI", 10))
        self.combo_slide_image.grid(row=2, column=1, sticky="ew", pady=6, padx=(10, 0))
        
        self.slide_edit_frame.grid_columnconfigure(1, weight=1)
        
        # Botones de Acción
        # Botones de Acción (Reorganizados en Grid 2x2 para ser compactos)
        action_buttons_frame = tk.Frame(left_panel, bg=COLOR_BG)
        action_buttons_frame.pack(fill="x", pady=10)
        action_buttons_frame.columnconfigure(0, weight=1)
        action_buttons_frame.columnconfigure(1, weight=1)
        
        btn_prev = tk.Button(action_buttons_frame, text="👁️ Previsualizar Slide", 
                             font=("Segoe UI", 10, "bold"), fg=COLOR_BG, bg=COLOR_TEXT, 
                             activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                             relief="flat", cursor="hand2", padx=10, pady=8,
                             command=self.previsualizar_slide)
        btn_prev.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(0, 5))
        
        btn_save = tk.Button(action_buttons_frame, text="💾 Guardar Cambios", 
                             font=("Segoe UI", 10, "bold"), fg=COLOR_BG, bg="#1976d2", 
                             activebackground=COLOR_BG, activeforeground="#1976d2",
                             relief="flat", cursor="hand2", padx=10, pady=8,
                             command=self.guardar_slide)
        btn_save.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(0, 5))
        
        btn_add = tk.Button(action_buttons_frame, text="➕ Agregar Slide", 
                            font=("Segoe UI", 10, "bold"), fg=COLOR_BG, bg="#2e7d32", 
                            activebackground=COLOR_BG, activeforeground="#2e7d32",
                            relief="flat", cursor="hand2", padx=10, pady=8,
                            command=self.agregar_slide)
        btn_add.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(5, 0))
        
        btn_del = tk.Button(action_buttons_frame, text="🗑️ Eliminar Slide", 
                            font=("Segoe UI", 10, "bold"), fg=COLOR_BG, bg="#d9534f", 
                            activebackground=COLOR_BG, activeforeground="#d9534f",
                            relief="flat", cursor="hand2", padx=10, pady=8,
                            command=self.eliminar_slide)
        btn_del.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(5, 0))
        
        # --- PANEL DERECHO (BANNERS DE LEYENDA) ---
        self.build_leyendas_tab_ui(right_panel)
        
        # --- PANEL CENTRAL (PREVISUALIZACIÓN COMPARTIDA) ---
        self.lbl_compartido_prev_title = tk.Label(middle_panel, text="VISTA PREVIA COMPARTIDA\n(DIAPOSITIVA O LEYENDA)", 
                                                  font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT, bg=COLOR_BG,
                                                  wraplength=350, justify="center")
        self.lbl_compartido_prev_title.pack(pady=(0, 5))
        
        # Canvas de Previsualización Único (500x320)
        self.canvas_compartido_prev = tk.Canvas(middle_panel, width=500, height=320, bg="#faf6f0", bd=1, relief="solid")
        self.canvas_compartido_prev.pack(pady=10)
        
        # Definir alias para mantener compatibilidad
        self.canvas_carrusel_prev = self.canvas_compartido_prev
        self.canvas_leyendas_prev = self.canvas_compartido_prev
        
        # Iniciar datos
        self.root.after(150, self.cargar_carrusel_datos)
        
    def cargar_carrusel_datos(self, selected_idx=None):
        # Cargar slides
        self.slides_carrusel = self.cargar_carrusel_js()
        
        # Llenar listbox
        self.listbox_carrusel.delete(0, "end")
        for s in self.slides_carrusel:
            self.listbox_carrusel.insert("end", f"{s['title']} [{s['subtitle']}]")
            
        # Actualizar combos de imágenes
        fondos_files = []
        if hasattr(self, 'img_folder') and self.img_folder:
            fondos_files = [f"img/{f}" for f in os.listdir(self.img_folder) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
            fondos_files.sort()
            self.combo_slide_image["values"] = fondos_files
            
        if self.slides_carrusel:
            if selected_idx is not None and 0 <= selected_idx < len(self.slides_carrusel):
                self.listbox_carrusel.selection_clear(0, "end")
                self.listbox_carrusel.selection_set(selected_idx)
                self.listbox_carrusel.activate(selected_idx)
                self.listbox_carrusel.see(selected_idx)
                self.seleccionar_slide(None)
            else:
                # No seleccionar nada por defecto en el inicio o reinicio sin índice
                self.listbox_carrusel.selection_clear(0, "end")
                self.var_slide_title.set("")
                self.var_slide_subtitle.set("")
                self.var_slide_image.set("")
                self.previsualizar_slide()
            
    def seleccionar_slide(self, event):
        sel = self.listbox_carrusel.curselection()
        if not sel:
            return
        idx = sel[0]
        slide = self.slides_carrusel[idx]
        
        self.var_slide_title.set(slide["title"])
        self.var_slide_subtitle.set(slide["subtitle"])
        self.var_slide_image.set(slide["src"])
        
        # Previsualizar inmediatamente
        self.previsualizar_slide()
        
    def previsualizar_slide(self):
        if not HAS_PIL:
            return
            
        # 1. Obtener imagen de fondo
        img_rel = self.var_slide_image.get()
        
        # Si no hay ninguna diapositiva seleccionada ni rellenada, mostrar un placeholder
        if not img_rel and not self.var_slide_title.get() and not self.var_slide_subtitle.get():
            placeholder = Image.new("RGBA", (500, 320), "#faf6f0")
            draw = ImageDraw.Draw(placeholder)
            font_title = self.get_pillow_font("sans", 12, bold=True)
            text = "[ Ninguna diapositiva seleccionada ]"
            if hasattr(draw, "textbbox"):
                bbox = draw.textbbox((0, 0), text, font=font_title)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
            else:
                tw, th = draw.textsize(text, font=font_title)
            draw.text(((500 - tw)//2, (320 - th)//2), text, font=font_title, fill="#8c857b")
            
            self.tk_slide_img = ImageTk.PhotoImage(placeholder)
            if hasattr(self, 'lbl_compartido_prev_title'):
                self.lbl_compartido_prev_title.config(text="VISTA PREVIA COMPARTIDA: CARRUSEL")
            self.canvas_carrusel_prev.delete("all")
            self.canvas_carrusel_prev.create_image(0, 0, image=self.tk_slide_img, anchor="nw")
            return
        img_abs = None
        for d in self.target_dirs:
            p = os.path.join(d, img_rel)
            if os.path.exists(p):
                img_abs = p
                break
                
        if img_abs:
            try:
                base_img = Image.open(img_abs).convert("RGBA")
            except:
                base_img = Image.new("RGBA", (750, 480), (250, 246, 240, 255))
        else:
            base_img = Image.new("RGBA", (750, 480), (250, 246, 240, 255))
            
        # Redimensionar la imagen para que se ajuste completamente (object-fit: contain)
        base_w, base_h = base_img.size
        ratio_canvas = 750 / 480
        ratio_img = base_w / base_h
        
        canvas_bg = Image.new("RGBA", (750, 480), (250, 246, 240, 255))
        if ratio_img > ratio_canvas:
            # Ancho limitante
            new_w = 750
            new_h = int(750 / ratio_img)
        else:
            # Alto limitante
            new_h = 480
            new_w = int(480 * ratio_img)
            
        base_img_resized = base_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Centrar la imagen en el canvas
        x_offset = (750 - new_w) // 2
        y_offset = (480 - new_h) // 2
        canvas_bg.paste(base_img_resized, (x_offset, y_offset), base_img_resized if base_img_resized.mode == "RGBA" else None)
        
        # 2. Dibujar overlay degradado (marrón oscuro a transparente desde abajo)
        overlay = Image.new("RGBA", (750, 480), (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        # Dibujar gradiente en las últimas 200 filas de píxeles
        for y in range(480 - 200, 480):
            # Calcular la opacidad de 0 a 128 (marrón: 75, 55, 45)
            factor = (y - (480 - 200)) / 200.0
            alpha = int(128 * factor)
            draw_ov.line([(0, y), (750, y)], fill=(75, 55, 45, alpha))
            
        canvas_bg = Image.alpha_composite(canvas_bg, overlay)
        
        # 3. Dibujar textos en la parte inferior izquierda
        draw = ImageDraw.Draw(canvas_bg)
        
        font_title = self.get_pillow_font("serif", 36, bold=True)
        font_sub = self.get_pillow_font("sans", 16, bold=False)
        
        title_text = self.var_slide_title.get().strip()
        sub_text = self.var_slide_subtitle.get().strip()
        
        # Coordenada base del texto (bottom-left)
        text_x = 40
        text_y_title = 480 - 80
        text_y_sub = text_y_title - 30
        
        # Código del producto (título) en pequeño arriba
        draw.text((text_x, text_y_sub), title_text, font=font_sub, fill=(255, 252, 248, 255))
        # Descripción del producto (subtítulo) en grande abajo
        draw.text((text_x, text_y_title), sub_text, font=font_title, fill=(255, 252, 248, 255))
        
        # 4. Redimensionar al tamaño del canvas de visualización (500x320)
        display_img = canvas_bg.resize((500, 320), Image.Resampling.LANCZOS)
        
        # Mostrar
        self.tk_slide_img = ImageTk.PhotoImage(display_img)
        if hasattr(self, 'lbl_compartido_prev_title'):
            self.lbl_compartido_prev_title.config(text="VISTA PREVIA COMPARTIDA: DIAPOSITIVA DEL CARRUSEL")
        self.canvas_carrusel_prev.delete("all")
        self.canvas_carrusel_prev.create_image(0, 0, image=self.tk_slide_img, anchor="nw")
        
    def guardar_slide(self):
        sel = self.listbox_carrusel.curselection()
        if not sel:
            messagebox.showerror("Error", "Por favor, selecciona un slide de la lista para editar.")
            return
            
        idx = sel[0]
        title = self.var_slide_title.get().strip()
        subtitle = self.var_slide_subtitle.get().strip()
        src = self.var_slide_image.get()
        
        if not title or not subtitle or not src:
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return
            
        self.slides_carrusel[idx] = {
            "src": src,
            "title": title,
            "subtitle": subtitle
        }
        
        if self.guardar_carrusel_js(self.slides_carrusel):
            self.cargar_carrusel_datos(selected_idx=idx)
            messagebox.showinfo("Éxito", "Slide guardado y actualizado en la web.")
            
    def agregar_slide(self):
        title = self.var_slide_title.get().strip()
        subtitle = self.var_slide_subtitle.get().strip()
        src = self.var_slide_image.get()
        
        if not title or not subtitle or not src:
            messagebox.showerror("Error", "Completa todos los campos (Título, Subtítulo y Selecciona una Imagen) para poder agregar un nuevo slide.")
            return
            
        nuevo_slide = {
            "src": src,
            "title": title,
            "subtitle": subtitle
        }
        
        self.slides_carrusel.append(nuevo_slide)
        
        if self.guardar_carrusel_js(self.slides_carrusel):
            self.cargar_carrusel_datos(selected_idx=len(self.slides_carrusel) - 1)
            messagebox.showinfo("Éxito", "Nuevo slide añadido con éxito al final del carrusel.")
            
    def eliminar_slide(self):
        sel = self.listbox_carrusel.curselection()
        if not sel:
            messagebox.showerror("Error", "Selecciona el slide que deseas eliminar.")
            return
            
        idx = sel[0]
        slide = self.slides_carrusel[idx]
        
        if not messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas eliminar el slide '{slide['title']}'?"):
            return
            
        self.slides_carrusel.pop(idx)
        
        if self.guardar_carrusel_js(self.slides_carrusel):
            target_idx = max(0, idx - 1) if self.slides_carrusel else None
            self.cargar_carrusel_datos(selected_idx=target_idx)
            messagebox.showinfo("Éxito", "Slide eliminado correctamente del carrusel.")
            
    def mover_slide_arriba(self):
        sel = self.listbox_carrusel.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == 0:
            return # Ya está arriba
            
        # Intercambiar
        self.slides_carrusel[idx], self.slides_carrusel[idx - 1] = self.slides_carrusel[idx - 1], self.slides_carrusel[idx]
        
        if self.guardar_carrusel_js(self.slides_carrusel):
            self.cargar_carrusel_datos(selected_idx=idx - 1)
            
    def mover_slide_abajo(self):
        sel = self.listbox_carrusel.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == len(self.slides_carrusel) - 1:
            return # Ya está al final
            
        # Intercambiar
        self.slides_carrusel[idx], self.slides_carrusel[idx + 1] = self.slides_carrusel[idx + 1], self.slides_carrusel[idx]
        
        if self.guardar_carrusel_js(self.slides_carrusel):
            self.cargar_carrusel_datos(selected_idx=idx + 1)
            
    def subir_carrusel_git(self):
        # Git sync activado
        git_exe = self.find_git_executable()
        for repo_dir in self.target_dirs:
            if not os.path.exists(os.path.join(repo_dir, ".git")):
                continue
            try:
                subprocess.run([git_exe, "add", "script.js"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                subprocess.run([git_exe, "commit", "-m", "Actualizar carrusel"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                subprocess.run([git_exe, "pull", "--rebase"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                subprocess.run([git_exe, "push"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            except Exception as e:
                print("Error en git push de carrusel:", e)

    def cargar_carrusel_js(self):
        self.script_js_path = None
        for d in self.target_dirs:
            path = os.path.join(d, "script.js")
            if os.path.exists(path):
                self.script_js_path = path
                break
                
        if not self.script_js_path:
            self.script_js_path = os.path.join(self.base_dir, "script.js")
            
        if not os.path.exists(self.script_js_path):
            return []
            
        try:
            with open(self.script_js_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Buscar el bloque const IMAGENES_CARROUSEL = [ ... ];
            match = re.search(r'const\s+IMAGENES_CARROUSEL\s*=\s*\[([\s\S]*?)\]\s*;', content)
            if not match:
                return []
                
            array_str = match.group(1)
            # Extraer objetos { src: "...", title: "...", subtitle: "..." }
            obj_pattern = r'\{\s*src:\s*["\']([^"\']+)["\']\s*,\s*title:\s*["\']([^"\']*)["\']\s*,\s*subtitle:\s*["\']([^"\']*)["\']\s*\}'
            objs = re.findall(obj_pattern, array_str)
            
            slides = []
            for src, title, subtitle in objs:
                slides.append({
                    "src": src.replace('\\', '/'),
                    "title": title,
                    "subtitle": subtitle
                })
            return slides
        except Exception as e:
            print("Error al cargar carrusel de script.js:", e)
            return []
            
    def guardar_carrusel_js(self, slides):
        if not self.script_js_path:
            return False
            
        try:
            with open(self.script_js_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            lines = ["const IMAGENES_CARROUSEL = ["]
            for s in slides:
                src = s["src"].replace('\\', '/')
                title = s["title"]
                subtitle = s["subtitle"]
                lines.append(f'    {{ src: "{src}", title: "{title}", subtitle: "{subtitle}" }},')
                
            if len(lines) > 1:
                # Quitar la última coma del último elemento
                lines[-1] = lines[-1].rstrip(',')
            lines.append("];")
            
            new_block = "\n".join(lines)
            
            pattern = r'const\s+IMAGENES_CARROUSEL\s*=\s*\[([\s\S]*?)\]\s*;'
            content = re.sub(pattern, new_block, content)
            
            with open(self.script_js_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            # Sincronizar en segundo plano con Git
            threading.Thread(target=self.subir_carrusel_git, daemon=True).start()
            
            return True
        except Exception as e:
            print("Error al guardar carrusel en script.js:", e)
            return False

    def build_pagina_tab_ui(self, parent):
        # Un panel dividido: Izquierda (Canvas de previsualización), Derecha (Controles)
        frame_left = tk.Frame(parent, bg=COLOR_BG)
        frame_left.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        
        lbl_canvas_title = tk.Label(frame_left, text="Miniatura de la Página (1200px a escala ~33%)", 
                                    fg=COLOR_TEXT, bg=COLOR_BG, font=("Segoe UI", 10, "bold"))
        lbl_canvas_title.pack(anchor="c", pady=(0, 5))
        
        canvas_container = tk.Frame(frame_left, bg=COLOR_BG)
        canvas_container.pack(expand=True, fill="y")
        
        self.canvas_web = tk.Canvas(canvas_container, width=400, bg="#fcfaf7", highlightthickness=1, highlightbackground=COLOR_BORDER)
        scrollbar_web = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas_web.yview)
        
        self.canvas_web.configure(yscrollcommand=scrollbar_web.set)
        self.canvas_web.pack(side="left", fill="y", expand=False)
        scrollbar_web.pack(side="right", fill="y")
        
        # Bind de eventos del Canvas
        self.canvas_web.bind("<Button-1>", self.on_deco_click)
        self.canvas_web.bind("<B1-Motion>", self.on_deco_drag)
        self.canvas_web.bind("<ButtonRelease-1>", self.on_deco_release)
        self.canvas_web.bind("<MouseWheel>", lambda e: self.canvas_web.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        
        # Panel derecho: Controles y Acciones
        frame_right = tk.Frame(parent, bg=COLOR_BG, width=320)
        frame_right.pack(side="right", fill="both", padx=(10, 15), pady=15)
        frame_right.pack_propagate(False)
        
        lbl_ctrl_title = tk.Label(frame_right, text="Elementos Decorativos", 
                                  fg=COLOR_TEXT, bg=COLOR_BG, font=("Segoe UI", 12, "bold"))
        lbl_ctrl_title.pack(anchor="w", pady=(0, 15))
        
        frame_add = tk.LabelFrame(frame_right, text=" Añadir Decoración ", bg=COLOR_BG, fg=COLOR_TEXT, font=("Segoe UI", 9, "bold"), padx=10, pady=10)
        frame_add.pack(fill="x", pady=(0, 15))
        
        lbl_info_add = tk.Label(frame_add, text="Agrega una imagen PNG transparente y arrástrala en el lienzo para posicionarla.", 
                                fg="#7b6d66", bg=COLOR_BG, font=("Segoe UI", 8), wraplength=270, justify="left")
        lbl_info_add.pack(anchor="w", pady=(0, 10))
        
        self.btn_elegir_deco = tk.Button(frame_add, text="📁 Elegir Imagen Decorativa", bg=COLOR_ACCENT, fg=COLOR_WHITE,
                                         font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", command=self.buscar_y_agregar_deco)
        self.btn_elegir_deco.pack(fill="x", pady=5)
        
        self.frame_edit_deco = tk.LabelFrame(frame_right, text=" Modificar Selección ", bg=COLOR_BG, fg=COLOR_TEXT, font=("Segoe UI", 9, "bold"), padx=10, pady=10)
        self.frame_edit_deco.pack(fill="x", pady=(0, 15))
        
        self.lbl_deco_sel_info = tk.Label(self.frame_edit_deco, text="Ninguna decoración seleccionada", 
                                          fg="#7b6d66", bg=COLOR_BG, font=("Segoe UI", 9), justify="left")
        self.lbl_deco_sel_info.pack(anchor="w", pady=(0, 10))
        
        tk.Label(self.frame_edit_deco, text="Ancho en la Web (px):", fg=COLOR_TEXT, bg=COLOR_BG, font=("Segoe UI", 9)).pack(anchor="w")
        self.scale_deco_width = tk.Scale(self.frame_edit_deco, from_=20, to=4000, orient="horizontal", bg=COLOR_BG, fg=COLOR_TEXT,
                                         highlightthickness=0, troughcolor=COLOR_BORDER, activebackground=COLOR_ACCENT, command=self.on_deco_width_slider_change)
        self.scale_deco_width.set(100)
        self.scale_deco_width.pack(fill="x", pady=(0, 5))
        
        tk.Label(self.frame_edit_deco, text="Alto en la Web (px):", fg=COLOR_TEXT, bg=COLOR_BG, font=("Segoe UI", 9)).pack(anchor="w")
        self.scale_deco_height = tk.Scale(self.frame_edit_deco, from_=20, to=4000, orient="horizontal", bg=COLOR_BG, fg=COLOR_TEXT,
                                          highlightthickness=0, troughcolor=COLOR_BORDER, activebackground=COLOR_ACCENT, command=self.on_deco_height_slider_change)
        self.scale_deco_height.set(100)
        self.scale_deco_height.pack(fill="x", pady=(0, 5))
        
        self.var_deco_keep_aspect = tk.BooleanVar(value=True)
        self.chk_keep_aspect = tk.Checkbutton(self.frame_edit_deco, text="Mantener proporción", variable=self.var_deco_keep_aspect,
                                              bg=COLOR_BG, fg=COLOR_TEXT, activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                                              font=("Segoe UI", 9), command=self.on_keep_aspect_change)
        self.chk_keep_aspect.pack(anchor="w", pady=(0, 5))
        
        tk.Label(self.frame_edit_deco, text="Rotación (grados):", fg=COLOR_TEXT, bg=COLOR_BG, font=("Segoe UI", 9)).pack(anchor="w")
        self.scale_deco_angle = tk.Scale(self.frame_edit_deco, from_=0, to=360, orient="horizontal", bg=COLOR_BG, fg=COLOR_TEXT,
                                         highlightthickness=0, troughcolor=COLOR_BORDER, activebackground=COLOR_ACCENT, command=self.on_deco_angle_slider_change)
        self.scale_deco_angle.set(0)
        self.scale_deco_angle.pack(fill="x", pady=(0, 10))
        
        # Capa de Posición
        tk.Label(self.frame_edit_deco, text="Capa de Posición:", fg=COLOR_TEXT, bg=COLOR_BG, font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 2))
        self.var_deco_layer = tk.StringVar(value="front")
        frame_radio = tk.Frame(self.frame_edit_deco, bg=COLOR_BG)
        frame_radio.pack(fill="x", pady=(0, 10))
        self.radio_front = tk.Radiobutton(frame_radio, text="Al frente", variable=self.var_deco_layer, value="front", 
                                          bg=COLOR_BG, fg=COLOR_TEXT, activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                                          font=("Segoe UI", 9), command=self.on_deco_layer_change)
        self.radio_front.pack(side="left", padx=(0, 10))
        self.radio_back = tk.Radiobutton(frame_radio, text="Al fondo", variable=self.var_deco_layer, value="back",
                                         bg=COLOR_BG, fg=COLOR_TEXT, activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                                         font=("Segoe UI", 9), command=self.on_deco_layer_change)
        self.radio_back.pack(side="left")
        
        # Opacidad / Transparencia
        tk.Label(self.frame_edit_deco, text="Opacidad / Transparencia:", fg=COLOR_TEXT, bg=COLOR_BG, font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 2))
        self.scale_deco_opacity = tk.Scale(self.frame_edit_deco, from_=10, to=100, orient="horizontal", bg=COLOR_BG, fg=COLOR_TEXT,
                                           highlightthickness=0, troughcolor=COLOR_BORDER, activebackground=COLOR_ACCENT, command=self.on_deco_opacity_slider_change)
        self.scale_deco_opacity.set(100)
        self.scale_deco_opacity.pack(fill="x", pady=(0, 15))
        
        self.btn_eliminar_deco = tk.Button(self.frame_edit_deco, text="🗑️ Eliminar Selección", bg="#E57373", fg=COLOR_WHITE,
                                           font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", command=self.eliminar_deco_seleccionada)
        self.btn_eliminar_deco.pack(fill="x", pady=5)
        
        self.set_edit_panel_state("disabled")
        
        frame_save = tk.Frame(frame_right, bg=COLOR_BG)
        frame_save.pack(fill="x", side="bottom")
        
        self.btn_guardar_decoraciones = tk.Button(frame_save, text="💾 Aplicar Cambios a la Web", bg="#81C784", fg=COLOR_WHITE,
                                                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", pady=10, command=self.guardar_decoraciones_html)
        self.btn_guardar_decoraciones.pack(fill="x")

    def set_edit_panel_state(self, state):
        new_state = "normal" if state == "normal" else "disabled"
        def _set_state_rec(widget):
            # No deshabilitar el LabelFrame en sí para conservar legibilidad, sino a sus componentes
            if widget != self.frame_edit_deco:
                try:
                    widget.configure(state=new_state)
                except:
                    pass
            for child in widget.winfo_children():
                _set_state_rec(child)
        _set_state_rec(self.frame_edit_deco)

    def on_tab_changed(self, event):
        selected_tab = self.notebook.select()
        print(f"[DEBUG] Tab changed: selected_tab={selected_tab}, tab_pagina={self.tab_pagina}")
        if selected_tab == str(self.tab_pagina):
            print("[DEBUG] Switching to tab Página. Calling actualizar_decoraciones_canvas().")
            self.actualizar_decoraciones_canvas()

    def render_webpage_miniature(self):
        self.web_scale = 0.3333333333333333
        
        # 1. Agrupar las tarjetas en bloques de máximo 4
        chunks = [self.tarjetas_web[i:i+4] for i in range(0, len(self.tarjetas_web), 4)]
        
        # 2. Calcular la altura total real de forma dinámica
        # Empezamos con el Header (Navbar + Hero + Banner 1 + Carousel + Carousel margin)
        # 72 + 360 + 120 + 480 + 40 = 1072px
        current_y_1to1 = 1072
        
        # Diccionario para guardar las coordenadas de cada tarjeta en 1to1
        card_coords = {}
        
        # Lista para guardar los banners intermedios
        banners = []
        
        for chunk_idx, chunk in enumerate(chunks):
            # Calcular las coordenadas de cada tarjeta en este bloque
            for local_idx, t in enumerate(chunk):
                global_idx = chunk_idx * 4 + local_idx
                row = local_idx // 2
                col = local_idx % 2
                
                x1 = 124 + col * (464 + 24)
                y1 = current_y_1to1 + row * (280 + 24)
                x2 = x1 + 464
                y2 = y1 + 280
                
                card_coords[global_idx] = (x1, y1, x2, y2)
                
            rows = math.ceil(len(chunk) / 2.0)
            chunk_height = rows * 280 + (rows - 1) * 24
            current_y_1to1 += chunk_height
            
            # Si no es el último bloque, añadir banner intermedio
            if chunk_idx < len(chunks) - 1:
                margin_bottom = 24 if chunk_idx < len(chunks) - 2 else 12
                
                banner_y1 = current_y_1to1 + 24
                banner_y2 = banner_y1 + 120
                
                title_text = "Ventas al detalle y al por mayor"
                if chunk_idx == 1:
                    title_text = "Productos complementarios para tus proyectos"
                elif chunk_idx == 2:
                    title_text = "Si tienes alguna duda o deseas hacer un pedido..."
                    
                banners.append({
                    "y1": banner_y1,
                    "y2": banner_y2,
                    "title": title_text
                })
                
                current_y_1to1 += (24 + 120 + margin_bottom)
                
        # Añadir Features Section (height ~180px + margin-bottom 60px)
        features_y1 = current_y_1to1
        features_y2 = features_y1 + 180
        current_y_1to1 += (180 + 60)
        
        # Añadir Footer (height 200px)
        footer_y1 = current_y_1to1
        footer_y2 = footer_y1 + 200
        current_y_1to1 += 200
        
        # Altura y ancho finales a escala
        w_canvas = 400
        h_canvas = int(current_y_1to1 * self.web_scale)
        
        bg_color = (252, 250, 247, 255)
        img = Image.new("RGBA", (w_canvas, h_canvas), bg_color)
        draw = ImageDraw.Draw(img)
        
        # --- DIBUJAR ---
        
        # A. Navbar
        nav_h_scaled = int(72 * self.web_scale)
        draw.rectangle([(0, 0), (w_canvas, nav_h_scaled)], fill=(255, 255, 255, 255))
        draw.line([(0, nav_h_scaled), (w_canvas, nav_h_scaled)], fill=(225, 220, 215, 255), width=1)
        try:
            font_small = ImageFont.truetype("Segoe UI", 9)
            draw.text((15, 5), "BENDITO TALLER", fill=(40, 40, 40, 255), font=font_small)
            draw.text((320, 5), "🛒 Carrito", fill=(40, 40, 40, 255), font=font_small)
        except:
            pass
            
        # B. Hero Banner
        hero_y1 = nav_h_scaled
        hero_y2 = int((72 + 360) * self.web_scale)
        hero_bg_loaded = False
        for d in self.target_dirs:
            p = os.path.join(d, "img/fondo logo.png")
            if os.path.exists(p):
                try:
                    with Image.open(p) as temp_img:
                        temp_img.load()
                        hero_bg = temp_img.convert("RGBA")
                    hero_bg = self.resize_cover(hero_bg, (w_canvas, hero_y2 - hero_y1))
                    img.paste(hero_bg, (0, hero_y1), hero_bg)
                    hero_bg_loaded = True
                    break
                except:
                    pass
        if not hero_bg_loaded:
            draw.rectangle([(0, hero_y1), (w_canvas, hero_y2)], fill=(229, 218, 203, 255))
            
        # Logotipo
        logo_loaded = False
        for d in self.target_dirs:
            p = os.path.join(d, "img/logo_madera_sin_fondo.png")
            if os.path.exists(p):
                try:
                    with Image.open(p) as temp_img:
                        temp_img.load()
                        logo_img = temp_img.convert("RGBA")
                    logo_h = int((hero_y2 - hero_y1) * 0.8)
                    logo_w = int(logo_img.width * (logo_h / logo_img.height))
                    logo_img = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                    img.paste(logo_img, (w_canvas // 2 - logo_w // 2, hero_y1 + (hero_y2 - hero_y1) // 2 - logo_h // 2), logo_img)
                    logo_loaded = True
                    break
                except:
                    pass
                    
        # C. Dibujar Dots Banner 1
        banner1_y1 = hero_y2
        banner1_y2 = int((72 + 360 + 120) * self.web_scale)
        draw.rectangle([(0, banner1_y1), (w_canvas, banner1_y2)], fill=(230, 189, 179, 255))
        try:
            font_title = ImageFont.truetype("Segoe UI", 9, layout_engine=ImageFont.Layout.BASIC)
            draw.text((w_canvas // 2, banner1_y1 + 10), "Insumos en corte láser para tus proyectos", fill=(28, 28, 28, 255), font=font_title, anchor="mt")
        except:
            pass
            
        # D. Dibujar Carrusel
        carr_y1 = banner1_y2
        carr_y2 = int((72 + 360 + 120 + 480) * self.web_scale)
        draw.rectangle([(20, carr_y1 + 10), (w_canvas - 20, carr_y2)], fill=(245, 235, 225, 255), outline=(210, 200, 190, 255))
        try:
            font_small = ImageFont.truetype("Segoe UI", 9)
            draw.text((w_canvas // 2, carr_y1 + (carr_y2 - carr_y1) // 2), "[ Carrusel de Destacados ]", fill=(120, 110, 100, 255), font=font_small, anchor="mm")
        except:
            pass
            
        # E. Dibujar Tarjetas de Categoría
        for idx, t in enumerate(self.tarjetas_web):
            coords = card_coords[idx]
            cx1 = int(coords[0] * self.web_scale)
            cy1 = int(coords[1] * self.web_scale)
            cx2 = int(coords[2] * self.web_scale)
            cy2 = int(coords[3] * self.web_scale)
            
            card_w_scaled = cx2 - cx1
            card_h_scaled = cy2 - cy1
            
            card_bg_drawn = False
            base_bg_rel = "img/fondo_rayas.png"
            card_bg_tag = re.search(r'<div\s+class="card-bg"\s*([^>]*)>', t["full_html"])
            if card_bg_tag:
                attrs = card_bg_tag.group(1)
                url_match = re.search(r'background-image:\s*url\([\'"]?([^\'"\)]+)[\'"]?\)', attrs)
                if url_match:
                    base_bg_rel = url_match.group(1).replace('\\', '/')
            
            for d in self.target_dirs:
                p = os.path.join(d, base_bg_rel)
                if os.path.exists(p):
                    try:
                        with Image.open(p) as temp_img:
                            temp_img.load()
                            c_bg = temp_img.convert("RGBA")
                        c_bg = self.resize_cover(c_bg, (card_w_scaled, card_h_scaled))
                        
                        # Dibujar bordes redondeados
                        mask = Image.new("L", (card_w_scaled, card_h_scaled), 0)
                        mask_draw = ImageDraw.Draw(mask)
                        mask_draw.rounded_rectangle([(0, 0), (card_w_scaled, card_h_scaled)], radius=int(20 * self.web_scale), fill=255)
                        
                        img.paste(c_bg, (cx1, cy1), mask)
                        card_bg_drawn = True
                        break
                    except Exception as e:
                        print("Error rendering card background:", e)
                        
            if not card_bg_drawn:
                draw.rounded_rectangle([(cx1, cy1), (cx2, cy2)], radius=int(20 * self.web_scale), fill=(240, 235, 230, 255))
                
            # Silueta de Madera
            wood_w = int(345 * self.web_scale)
            wood_h = int(224 * self.web_scale)
            w_x1 = cx1 + (card_w_scaled - wood_w) // 2
            w_y1 = cy1 + (card_h_scaled - wood_h) // 2
            
            wood_bg_rel = "img/fondo_letra.png"
            wood_match = re.search(r'--wood-image:\s*url\([\'"]?([^\'"\)]+)[\'"]?\)', t["full_html"])
            if wood_match:
                wood_bg_rel = wood_match.group(1).replace('\\', '/')
                
            wood_drawn = False
            for d in self.target_dirs:
                p = os.path.join(d, wood_bg_rel)
                if os.path.exists(p):
                    try:
                        with Image.open(p) as temp_img:
                            temp_img.load()
                            w_img = temp_img.convert("RGBA")
                        w_img = w_img.resize((wood_w, wood_h), Image.Resampling.LANCZOS)
                        
                        cat_bg_img = self.fondos_css.get(t["class"], "")
                        if cat_bg_img:
                            cat_bg_abs = None
                            for d2 in self.target_dirs:
                                p2 = os.path.join(d2, cat_bg_img)
                                if os.path.exists(p2):
                                    cat_bg_abs = p2
                                    break
                            if cat_bg_abs:
                                with Image.open(cat_bg_abs) as temp_img:
                                    temp_img.load()
                                    c_texture = temp_img.convert("RGBA")
                                c_texture = self.resize_cover(c_texture, (wood_w, wood_h))
                                orig_alpha = w_img.getchannel('A')
                                multiplied = ImageChops.multiply(w_img, c_texture)
                                w_img = Image.blend(w_img, multiplied, 0.35)
                                w_img.putalpha(orig_alpha)
                                
                        img.paste(w_img, (w_x1, w_y1), w_img)
                        wood_drawn = True
                        break
                    except Exception as e:
                        print("Error rendering card wood preview:", e)
                        
            if not wood_drawn:
                draw.rectangle([(w_x1, w_y1), (w_x1 + wood_w, w_y1 + wood_h)], fill=(139, 90, 43, 255))
                
            # Texto
            try:
                font_card = ImageFont.truetype("Segoe UI", 7, layout_engine=ImageFont.Layout.BASIC)
                draw.text((cx1 + card_w_scaled // 2, cy1 + card_h_scaled // 2), t["title"].upper(), fill=(255, 255, 255, 255), font=font_card, anchor="mm")
            except:
                pass
                
        # F. Dibujar Banners Intermedios
        for b in banners:
            by1_scaled = int(b["y1"] * self.web_scale)
            by2_scaled = int(b["y2"] * self.web_scale)
            draw.rectangle([(0, by1_scaled), (w_canvas, by2_scaled)], fill=(230, 189, 179, 255))
            try:
                font_title = ImageFont.truetype("Segoe UI", 9, layout_engine=ImageFont.Layout.BASIC)
                draw.text((w_canvas // 2, by1_scaled + 10), b["title"], fill=(28, 28, 28, 255), font=font_title, anchor="mt")
            except:
                pass
                
        # G. Dibujar Features Section
        feat_y1_scaled = int(features_y1 * self.web_scale)
        feat_y2_scaled = int(features_y2 * self.web_scale)
        draw.rectangle([(0, feat_y1_scaled), (w_canvas, feat_y2_scaled)], fill=(252, 250, 247, 255))
        try:
            font_small = ImageFont.truetype("Segoe UI", 8)
            draw.text((w_canvas // 2, feat_y1_scaled + 20), "[ Sección de Características ]", fill=(150, 140, 130, 255), font=font_small, anchor="mm")
        except:
            pass
            
        # H. Dibujar Footer
        footer_y1_scaled = int(footer_y1 * self.web_scale)
        draw.rectangle([(0, footer_y1_scaled), (w_canvas, h_canvas)], fill=(30, 30, 30, 255))
        try:
            font_small = ImageFont.truetype("Segoe UI", 9)
            draw.text((w_canvas // 2, footer_y1_scaled + 30), "© Bendito Taller. Todos los derechos reservados.", fill=(180, 180, 180, 255), font=font_small, anchor="mm")
        except:
            pass
            
        return img

    def animar_decoraciones_loop(self):
        import time
        try:
            if hasattr(self, "deco_animations") and self.deco_animations:
                now = time.time() * 1000
                for item_id, anim in list(self.deco_animations.items()):
                    if self.canvas_web.winfo_exists() and item_id in self.canvas_web.find_all():
                        if "last_update" not in anim:
                            anim["last_update"] = now
                        
                        elapsed = now - anim["last_update"]
                        delay = anim.get("delay", 100)
                        if delay < 20:
                            delay = 100
                            
                        if elapsed >= delay:
                            frames = anim["frames"]
                            curr = (anim["current_frame"] + 1) % len(frames)
                            anim["current_frame"] = curr
                            photo = frames[curr]
                            self.canvas_web.itemconfig(item_id, image=photo)
                            anim["last_update"] = now
        except Exception as e:
            print("Error in animar_decoraciones_loop:", e)
            
        try:
            if self.root.winfo_exists():
                self.root.after(20, self.animar_decoraciones_loop)
        except:
            pass

    def actualizar_decoraciones_canvas(self, force_bg_rebuild=False):
        print("[DEBUG] Entering actualizar_decoraciones_canvas()")
        try:
            if not hasattr(self, "cached_web_bg_img") or self.cached_web_bg_img is None or force_bg_rebuild:
                self.cached_web_bg_img = self.render_webpage_miniature()
                print(f"[DEBUG] Rendered background image cache. Size: {self.cached_web_bg_img.size}")
                
            web_img = self.cached_web_bg_img
            self.tk_web_bg = ImageTk.PhotoImage(web_img)
            self.canvas_web.image = self.tk_web_bg # Referencia extra para evitar garbage collection
            
            self.canvas_web.delete("all")
            self.canvas_web.create_image(0, 0, image=self.tk_web_bg, anchor="nw")
            self.canvas_web.configure(scrollregion=(0, 0, 400, web_img.height))
            print(f"[DEBUG] Drew page background on canvas. Scrollregion set to height: {web_img.height}")
            
            self.deco_items = {}
            self.deco_photos = []
            self.deco_animations = {}
            
            for idx, d in enumerate(self.decoraciones):
                deco_path = None
                for target_d in self.target_dirs:
                    p = os.path.join(target_d, d["src"])
                    if os.path.exists(p):
                        deco_path = p
                        break
                if not deco_path:
                    deco_path = os.path.join(self.base_dir, d["src"])
                    
                print(f"[DEBUG] Loading deco image {idx}: {d['src']} from path: {deco_path}")
                if os.path.exists(deco_path):
                    try:
                        frames = []
                        duration = 100
                        is_anim = False
                        
                        with Image.open(deco_path) as temp_img:
                            is_anim = getattr(temp_img, "is_animated", False)
                            n_frames = getattr(temp_img, "n_frames", 1)
                            duration = temp_img.info.get("duration", 100)
                            if duration <= 0:
                                duration = 100
                            
                            # Si es animado, extraer todos los frames
                            if is_anim and n_frames > 1:
                                for frame_idx in range(n_frames):
                                    temp_img.seek(frame_idx)
                                    frame_img = temp_img.copy().convert("RGBA")
                                    
                                    scaled_w = int(d["real_w"] * self.web_scale)
                                    if d.get("real_h", -1) <= 0:
                                        d["real_h"] = int(frame_img.height * (d["real_w"] / frame_img.width))
                                    scaled_h = int(d["real_h"] * self.web_scale)
                                    scaled_w = max(5, scaled_w)
                                    scaled_h = max(5, scaled_h)
                                    
                                    frame_scaled = frame_img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
                                    
                                    # Aplicar rotación
                                    angle = d.get("angle", 0)
                                    if angle != 0:
                                        frame_scaled = frame_scaled.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)
                                        rot_w, rot_h = frame_scaled.size
                                        cx = int(d["x_real"] * self.web_scale) + int((scaled_w - rot_w) / 2)
                                        cy = int(d["y_real"] * self.web_scale) + int((scaled_h - rot_h) / 2)
                                    else:
                                        cx = int(d["x_real"] * self.web_scale)
                                        cy = int(d["y_real"] * self.web_scale)
                                        
                                    # Aplicar opacidad
                                    opacity = d.get("opacity", 1.0)
                                    if opacity < 1.0:
                                        r, g, b, a = frame_scaled.split()
                                        a = a.point(lambda p: int(p * opacity))
                                        frame_scaled = Image.merge("RGBA", (r, g, b, a))
                                        
                                    photo = ImageTk.PhotoImage(frame_scaled)
                                    frames.append(photo)
                            else:
                                # Estático
                                temp_img.load()
                                img_orig = temp_img.convert("RGBA")
                                scaled_w = int(d["real_w"] * self.web_scale)
                                if d.get("real_h", -1) <= 0:
                                    d["real_h"] = int(img_orig.height * (d["real_w"] / img_orig.width))
                                scaled_h = int(d["real_h"] * self.web_scale)
                                scaled_w = max(5, scaled_w)
                                scaled_h = max(5, scaled_h)
                                
                                img_scaled = img_orig.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
                                angle = d.get("angle", 0)
                                if angle != 0:
                                    img_scaled = img_scaled.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)
                                    rot_w, rot_h = img_scaled.size
                                    cx = int(d["x_real"] * self.web_scale) + int((scaled_w - rot_w) / 2)
                                    cy = int(d["y_real"] * self.web_scale) + int((scaled_h - rot_h) / 2)
                                else:
                                    cx = int(d["x_real"] * self.web_scale)
                                    cy = int(d["y_real"] * self.web_scale)
                                    
                                opacity = d.get("opacity", 1.0)
                                if opacity < 1.0:
                                    r, g, b, a = img_scaled.split()
                                    a = a.point(lambda p: int(p * opacity))
                                    img_scaled = Image.merge("RGBA", (r, g, b, a))
                                photo = ImageTk.PhotoImage(img_scaled)
                                frames.append(photo)
                                
                        # Colocar la imagen inicial en el canvas
                        item_id = self.canvas_web.create_image(cx, cy, image=frames[0], anchor="nw", tags="deco")
                        self.deco_items[item_id] = idx
                        
                        # Guardar referencias
                        for f in frames:
                            self.deco_photos.append((item_id, f))
                            
                        # Si es animado, registrar en el gestor de animaciones
                        if is_anim and len(frames) > 1:
                            self.deco_animations[item_id] = {
                                "frames": frames,
                                "current_frame": 0,
                                "delay": duration
                            }
                        print(f"[DEBUG] Placed deco item on canvas at cx={cx}, cy={cy} (real_w={d['real_w']})")
                    except Exception as e:
                        print(f"[DEBUG] Error loading deco {d['src']}: {e}")
                else:
                    print(f"[DEBUG] Warning: Deco path {deco_path} does not exist on disk!")
            
            # Re-asignar la selección basada en el índice persistente
            if hasattr(self, "deco_seleccionada_idx") and self.deco_seleccionada_idx is not None:
                found_id = None
                for item_id, idx in self.deco_items.items():
                    if idx == self.deco_seleccionada_idx:
                        found_id = item_id
                        break
                if found_id:
                    self.deco_seleccionada = found_id
                else:
                    if hasattr(self, "deco_seleccionada"):
                        del self.deco_seleccionada
            else:
                if hasattr(self, "deco_seleccionada"):
                    del self.deco_seleccionada

            self.canvas_web.image_refs = self.deco_photos # Referencia extra
            self.dibujar_borde_seleccion()
            print("[DEBUG] Canvas updating complete.")
        except Exception as e:
            print("[DEBUG] CRITICAL ERROR inside actualizar_decoraciones_canvas:", e)
            import traceback
            traceback.print_exc()

    def dibujar_borde_seleccion(self):
        self.canvas_web.delete("sel_border")
        self.canvas_web.delete("sel_handle")
        
        if hasattr(self, "deco_seleccionada") and self.deco_seleccionada in self.deco_items:
            # Forzar procesamiento de tareas pendientes en Tkinter para que bbox sea preciso
            try:
                self.canvas_web.update_idletasks()
            except:
                pass
                
            bbox = self.canvas_web.bbox(self.deco_seleccionada)
            idx = self.deco_items[self.deco_seleccionada]
            d = self.decoraciones[idx]
            
            if not bbox:
                # Calcular manualmente en base al factor de escala
                cx = int(d["x_real"] * self.web_scale)
                cy = int(d["y_real"] * self.web_scale)
                
                photo = None
                for pid, p in self.deco_photos:
                    if pid == self.deco_seleccionada:
                        photo = p
                        break
                if photo:
                    w = photo.width()
                    h = photo.height()
                else:
                    w = int(d["real_w"] * self.web_scale)
                    h = w
                bbox = (cx, cy, cx + w, cy + h)
                
            x1, y1, x2, y2 = bbox
            
            # Dibujar borde naranja
            self.canvas_web.create_rectangle(
                x1 - 2, y1 - 2, x2 + 2, y2 + 2,
                outline="#FF8A65", width=1.5, dash=(4, 2), tags="sel_border"
            )
            
            # Posiciones de los 8 tiradores
            handles = {
                "TL": (x1, y1),
                "TM": ((x1 + x2)/2, y1),
                "TR": (x2, y1),
                "MR": (x2, (y1 + y2)/2),
                "BR": (x2, y2),
                "BM": ((x1 + x2)/2, y2),
                "BL": (x1, y2),
                "ML": (x1, (y1 + y2)/2)
            }
            
            # Dibujar los tiradores (cuadrados naranjas con borde blanco)
            r = 4 # radio del tirador
            for h_name, (hx, hy) in handles.items():
                cursor_map = {
                    "TL": "size_nw_se",
                    "BR": "size_nw_se",
                    "TR": "size_ne_sw",
                    "BL": "size_ne_sw",
                    "TM": "size_ns",
                    "BM": "size_ns",
                    "ML": "size_we",
                    "MR": "size_we"
                }
                cursor = cursor_map.get(h_name, "hand2")
                
                handle_id = self.canvas_web.create_rectangle(
                    hx - r, hy - r, hx + r, hy + r,
                    fill="#FF8A65", outline="#FFFFFF", width=1,
                    tags=("sel_handle", f"handle_{h_name}")
                )
                
                # Vincular cambio de cursor al pasar por encima del tirador
                self.canvas_web.tag_bind(handle_id, "<Enter>", lambda e, c=cursor: self.canvas_web.configure(cursor=c))
                self.canvas_web.tag_bind(handle_id, "<Leave>", lambda e: self.canvas_web.configure(cursor="arrow"))

    def on_deco_click(self, event):
        cx = self.canvas_web.canvasx(event.x)
        cy = self.canvas_web.canvasy(event.y)
        
        # 1. Comprobar si se ha pulsado en un tirador
        clicked = self.canvas_web.find_withtag("current")
        handle_clicked = None
        for item in clicked:
            tags = self.canvas_web.gettags(item)
            for t in tags:
                if t.startswith("handle_"):
                    handle_clicked = t.split("_")[1]
                    break
            if handle_clicked:
                break
                
        if handle_clicked:
            # Iniciar redimensionamiento por tirador
            self.drag_mode = "resize"
            self.active_handle = handle_clicked
            
            idx = self.deco_items[self.deco_seleccionada]
            d = self.decoraciones[idx]
            
            coords = self.canvas_web.coords(self.deco_seleccionada)
            self.resize_start_x1 = coords[0]
            self.resize_start_y1 = coords[1]
            
            for item_id, photo in self.deco_photos:
                if item_id == self.deco_seleccionada:
                    self.resize_orig_w = photo.width()
                    self.resize_orig_h = photo.height()
                    break
                    
            self.resize_start_x2 = self.resize_start_x1 + self.resize_orig_w
            self.resize_start_y2 = self.resize_start_y1 + self.resize_orig_h
            
            self.drag_start_x = cx
            self.drag_start_y = cy
            return
            
        # 2. Selección normal del elemento
        deco_clicked = None
        for item in clicked:
            if item in self.deco_items:
                deco_clicked = item
                break
                
        if deco_clicked:
            self.deco_seleccionada = deco_clicked
            idx = self.deco_items[deco_clicked]
            self.deco_seleccionada_idx = idx
            d = self.decoraciones[idx]
            self.drag_mode = "move"
            
            self.set_edit_panel_state("normal")
            filename = os.path.basename(d["src"])
            self.lbl_deco_sel_info.configure(text=f"Elemento: {filename}\nPos: X={d['x_real']}px, Y={d['y_real']}px")
            
            self.block_slider_callback = True
            self.scale_deco_width.set(d["real_w"])
            
            # Obtener real_h si no está definido
            if d.get("real_h", -1) <= 0:
                deco_path = self.obtener_deco_path(d["src"])
                if deco_path:
                    try:
                        with Image.open(deco_path) as temp_img:
                            d["real_h"] = int(temp_img.height * (d["real_w"] / temp_img.width))
                    except:
                        d["real_h"] = d["real_w"]
                else:
                    d["real_h"] = d["real_w"]
            
            self.scale_deco_height.set(d["real_h"])
            self.scale_deco_angle.set(d.get("angle", 0))
            self.var_deco_layer.set(d.get("layer", "front"))
            self.scale_deco_opacity.set(int(d.get("opacity", 1.0) * 100))
            self.block_slider_callback = False
            
            coords = self.canvas_web.coords(deco_clicked)
            self.drag_offset_x = cx - coords[0]
            self.drag_offset_y = cy - coords[1]
            
            self.dibujar_borde_seleccion()
        else:
            if hasattr(self, "deco_seleccionada"):
                del self.deco_seleccionada
            if hasattr(self, "deco_seleccionada_idx"):
                self.deco_seleccionada_idx = None
            self.set_edit_panel_state("disabled")
            self.lbl_deco_sel_info.configure(text="Ninguna decoración seleccionada")
            self.canvas_web.delete("sel_border")
            self.canvas_web.delete("sel_handle")

    def on_deco_drag(self, event):
        if not hasattr(self, "deco_seleccionada") or self.deco_seleccionada not in self.deco_items:
            return
            
        cx = self.canvas_web.canvasx(event.x)
        cy = self.canvas_web.canvasy(event.y)
        
        idx = self.deco_items[self.deco_seleccionada]
        d = self.decoraciones[idx]
        
        if getattr(self, "drag_mode", "move") == "move":
            # Modo arrastrar elemento completo
            img_x = cx - self.drag_offset_x
            img_y = cy - self.drag_offset_y
            
            self.canvas_web.coords(self.deco_seleccionada, img_x, img_y)
            
            x_real = int(img_x / self.web_scale)
            y_real = int(img_y / self.web_scale)
            x_real = max(-500, min(x_real, 2000))
            y_real = max(0, min(y_real, 10000))
            
            d["x_real"] = x_real
            d["y_real"] = y_real
            
            filename = os.path.basename(d["src"])
            self.lbl_deco_sel_info.configure(text=f"Elemento: {filename}\nPos: X={x_real}px, Y={y_real}px")
            self.dibujar_borde_seleccion()
            
        elif getattr(self, "drag_mode", "move") == "resize":
            # Modo redimensionar por tirador
            x1 = self.resize_start_x1
            y1 = self.resize_start_y1
            x2 = self.resize_start_x2
            y2 = self.resize_start_y2
            
            aspect_ratio = self.resize_orig_h / self.resize_orig_w
            
            # Calcular desplazamiento
            dx = cx - self.drag_start_x
            dy = cy - self.drag_start_y
            
            h = self.active_handle
            
            x1_new, y1_new = x1, y1
            x2_new, y2_new = x2, y2
            
            if self.var_deco_keep_aspect.get():
                if h in ("BR", "MR"):
                    new_w = (x2 + dx) - x1
                    new_w = max(10, new_w)
                    new_h = new_w * aspect_ratio
                    x2_new = x1 + new_w
                    y2_new = y1 + new_h
                elif h == "BM":
                    new_h = (y2 + dy) - y1
                    new_h = max(10, new_h)
                    new_w = new_h / aspect_ratio
                    x2_new = x1 + new_w
                    y2_new = y1 + new_h
                elif h in ("TL", "ML"):
                    new_w = x2 - (x1 + dx)
                    new_w = max(10, new_w)
                    new_h = new_w * aspect_ratio
                    x1_new = x2 - new_w
                    y1_new = y2 - new_h
                elif h == "TM":
                    new_h = y2 - (y1 + dy)
                    new_h = max(10, new_h)
                    new_w = new_h / aspect_ratio
                    x1_new = x2 - new_w
                    y1_new = y2 - new_h
                elif h == "TR":
                    new_w = (x2 + dx) - x1
                    new_w = max(10, new_w)
                    new_h = new_w * aspect_ratio
                    x1_new = x1
                    y1_new = y2 - new_h
                    x2_new = x1 + new_w
                    y2_new = y2
                elif h == "BL":
                    new_w = x2 - (x1 + dx)
                    new_w = max(10, new_w)
                    new_h = new_w * aspect_ratio
                    x1_new = x2 - new_w
                    y1_new = y1
                    x2_new = x2
                    y2_new = y1 + new_h
            else:
                if h == "BR":
                    new_w = (x2 + dx) - x1
                    new_h = (y2 + dy) - y1
                elif h == "MR":
                    new_w = (x2 + dx) - x1
                    new_h = y2 - y1
                elif h == "BM":
                    new_w = x2 - x1
                    new_h = (y2 + dy) - y1
                elif h == "TR":
                    new_w = (x2 + dx) - x1
                    new_h = y2 - (y1 + dy)
                    y1_new = y1 + dy
                elif h == "TM":
                    new_w = x2 - x1
                    new_h = y2 - (y1 + dy)
                    y1_new = y1 + dy
                elif h == "TL":
                    new_w = x2 - (x1 + dx)
                    new_h = y2 - (y1 + dy)
                    x1_new = x1 + dx
                    y1_new = y1 + dy
                elif h == "ML":
                    new_w = x2 - (x1 + dx)
                    new_h = y2 - y1
                    x1_new = x1 + dx
                elif h == "BL":
                    new_w = x2 - (x1 + dx)
                    new_h = (y2 + dy) - y1
                    x1_new = x1 + dx
                
                new_w = max(10, new_w)
                new_h = max(10, new_h)
                x2_new = x1_new + new_w
                y2_new = y1_new + new_h
                
            real_w = int((x2_new - x1_new) / self.web_scale)
            real_w = max(20, min(real_w, 4000))
            
            real_h = int((y2_new - y1_new) / self.web_scale)
            real_h = max(20, min(real_h, 4000))
            
            d["real_w"] = real_w
            d["real_h"] = real_h
            d["x_real"] = int(x1_new / self.web_scale)
            d["y_real"] = int(y1_new / self.web_scale)
            
            self.block_slider_callback = True
            self.scale_deco_width.set(real_w)
            self.scale_deco_height.set(real_h)
            self.block_slider_callback = False
            
            self.canvas_web.coords(self.deco_seleccionada, x1_new, y1_new)
            self.actualizar_imagen_tirador_arrastre(idx, real_w, real_h)

    def on_deco_release(self, event):
        self.drag_mode = "move"
        self.dibujar_borde_seleccion()

    def actualizar_imagen_tirador_arrastre(self, idx, real_w, real_h=None):
        d = self.decoraciones[idx]
        if real_h is None:
            real_h = d.get("real_h", -1)
            
        deco_path = self.obtener_deco_path(d["src"])
        if deco_path and os.path.exists(deco_path):
            try:
                with Image.open(deco_path) as temp_img:
                    temp_img.load()
                    img_orig = temp_img.convert("RGBA")
                    
                scaled_w = int(real_w * self.web_scale)
                if real_h <= 0:
                    real_h = int(img_orig.height * (real_w / img_orig.width))
                    d["real_h"] = real_h
                    
                scaled_h = int(real_h * self.web_scale)
                scaled_w = max(5, scaled_w)
                scaled_h = max(5, scaled_h)
                
                img_scaled = img_orig.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
                
                # Aplicar rotación
                angle = d.get("angle", 0)
                if angle != 0:
                    img_scaled = img_scaled.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)
                    rot_w, rot_h = img_scaled.size
                    cx = int(d["x_real"] * self.web_scale) + int((scaled_w - rot_w) / 2)
                    cy = int(d["y_real"] * self.web_scale) + int((scaled_h - rot_h) / 2)
                    self.canvas_web.coords(self.deco_seleccionada, cx, cy)
                
                # Aplicar opacidad
                opacity = d.get("opacity", 1.0)
                if opacity < 1.0:
                    r, g, b, a = img_scaled.split()
                    a = a.point(lambda p: int(p * opacity))
                    img_scaled = Image.merge("RGBA", (r, g, b, a))
                    
                photo = ImageTk.PhotoImage(img_scaled)
                
                for i, (item_id, old_photo) in enumerate(self.deco_photos):
                    if item_id == self.deco_seleccionada:
                        self.deco_photos[i] = (item_id, photo)
                        break
                        
                self.canvas_web.itemconfig(self.deco_seleccionada, image=photo)
                self.dibujar_borde_seleccion()
                
                filename = os.path.basename(d["src"])
                self.lbl_deco_sel_info.configure(text=f"Elemento: {filename}\nPos: X={d['x_real']}px, Y={d['y_real']}px")
            except Exception as e:
                print("Error redimensionando imagen al arrastrar tirador:", e)

    def obtener_deco_path(self, src):
        for target_d in self.target_dirs:
            p = os.path.join(target_d, src)
            if os.path.exists(p):
                return p
        p = os.path.join(self.base_dir, src)
        if os.path.exists(p):
            return p
        return None

    def on_deco_width_slider_change(self, val):
        if getattr(self, "block_slider_callback", False):
            return
        if not hasattr(self, "deco_seleccionada") or self.deco_seleccionada not in self.deco_items:
            return
            
        self.block_slider_callback = True
        try:
            idx = self.deco_items[self.deco_seleccionada]
            new_w = int(val)
            self.decoraciones[idx]["real_w"] = new_w
            
            # Ajustar alto proporcionalmente si mantener proporción está activo
            if self.var_deco_keep_aspect.get():
                d = self.decoraciones[idx]
                deco_path = self.obtener_deco_path(d["src"])
                if deco_path:
                    try:
                        with Image.open(deco_path) as temp_img:
                            aspect = temp_img.height / temp_img.width
                            new_h = int(new_w * aspect)
                            d["real_h"] = new_h
                            self.scale_deco_height.set(new_h)
                    except:
                        pass
            self.actualizar_decoraciones_canvas()
        finally:
            self.block_slider_callback = False

    def on_deco_height_slider_change(self, val):
        if getattr(self, "block_slider_callback", False):
            return
        if not hasattr(self, "deco_seleccionada") or self.deco_seleccionada not in self.deco_items:
            return
            
        self.block_slider_callback = True
        try:
            idx = self.deco_items[self.deco_seleccionada]
            new_h = int(val)
            self.decoraciones[idx]["real_h"] = new_h
            
            # Ajustar ancho proporcionalmente si mantener proporción está activo
            if self.var_deco_keep_aspect.get():
                d = self.decoraciones[idx]
                deco_path = self.obtener_deco_path(d["src"])
                if deco_path:
                    try:
                        with Image.open(deco_path) as temp_img:
                            aspect = temp_img.width / temp_img.height
                            new_w = int(new_h * aspect)
                            d["real_w"] = new_w
                            self.scale_deco_width.set(new_w)
                    except:
                        pass
            self.actualizar_decoraciones_canvas()
        finally:
            self.block_slider_callback = False

    def on_deco_angle_slider_change(self, val):
        if getattr(self, "block_slider_callback", False):
            return
        if not hasattr(self, "deco_seleccionada") or self.deco_seleccionada not in self.deco_items:
            return
        self.block_slider_callback = True
        try:
            idx = self.deco_items[self.deco_seleccionada]
            self.decoraciones[idx]["angle"] = int(val)
            self.actualizar_decoraciones_canvas()
        finally:
            self.block_slider_callback = False

    def on_keep_aspect_change(self):
        pass

    def on_deco_layer_change(self):
        if getattr(self, "block_slider_callback", False):
            return
        if not hasattr(self, "deco_seleccionada") or self.deco_seleccionada not in self.deco_items:
            return
        self.block_slider_callback = True
        try:
            idx = self.deco_items[self.deco_seleccionada]
            self.decoraciones[idx]["layer"] = self.var_deco_layer.get()
        finally:
            self.block_slider_callback = False

    def on_deco_opacity_slider_change(self, val):
        if getattr(self, "block_slider_callback", False):
            return
        if not hasattr(self, "deco_seleccionada") or self.deco_seleccionada not in self.deco_items:
            return
        self.block_slider_callback = True
        try:
            idx = self.deco_items[self.deco_seleccionada]
            self.decoraciones[idx]["opacity"] = float(val) / 100.0
            self.actualizar_decoraciones_canvas()
        finally:
            self.block_slider_callback = False

    def buscar_y_agregar_deco(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen decorativa",
            filetypes=[("Archivos de Imagen", "*.jpg *.jpeg *.png *.webp *.gif"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            filename = os.path.basename(file_path)
            for d in self.target_dirs:
                dest = os.path.join(d, "img", filename)
                try:
                    import shutil
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(file_path, dest)
                except Exception as e:
                    print(f"Error copying decorative image: {e}")
            
            yview = self.canvas_web.yview()
            web_h = self.canvas_web.bbox("all")[3] if self.canvas_web.bbox("all") else 1000
            canvas_y_center = ((yview[0] + yview[1]) / 2.0) * web_h
            
            x_real = int(200 / self.web_scale)
            y_real = int(canvas_y_center / self.web_scale)
            
            self.decoraciones.append({
                "src": f"img/{filename}",
                "x_real": x_real,
                "y_real": y_real,
                "real_w": 120,
                "real_h": -1,
                "layer": "front",
                "opacity": 1.0,
                "angle": 0
            })
            
            last_idx = len(self.decoraciones) - 1
            self.deco_seleccionada_idx = last_idx
            
            self.actualizar_listas_de_fondos_solo()
            self.actualizar_decoraciones_canvas()
            
            self.set_edit_panel_state("normal")
            self.lbl_deco_sel_info.configure(text=f"Elemento: {filename}\nPos: X={x_real}px, Y={y_real}px")
            self.block_slider_callback = True
            self.scale_deco_width.set(120)
            
            # Recalcular altura inicial proporcional para setear la UI
            d = self.decoraciones[last_idx]
            self.scale_deco_height.set(d.get("real_h", 120))
            self.scale_deco_angle.set(0)
            
            self.var_deco_layer.set("front")
            self.scale_deco_opacity.set(100)
            self.block_slider_callback = False

    def eliminar_deco_seleccionada(self):
        if not hasattr(self, "deco_seleccionada") or self.deco_seleccionada not in self.deco_items:
            return
            
        idx = self.deco_items[self.deco_seleccionada]
        del self.decoraciones[idx]
        
        if hasattr(self, "deco_seleccionada"):
            del self.deco_seleccionada
        if hasattr(self, "deco_seleccionada_idx"):
            self.deco_seleccionada_idx = None
        self.set_edit_panel_state("disabled")
        self.lbl_deco_sel_info.configure(text="Ninguna decoración seleccionada")
        self.actualizar_decoraciones_canvas()

    def guardar_decoraciones_html(self):
        if not self.index_html_path or not os.path.exists(self.index_html_path):
            messagebox.showerror("Error", "No se encontró el archivo index.html")
            return
            
        try:
            with open(self.index_html_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Separar decoraciones de fondo y de frente
            decos_back = [d for d in self.decoraciones if d.get("layer", "front") == "back"]
            decos_front = [d for d in self.decoraciones if d.get("layer", "front") == "front"]
            
            # Generar HTML para fondo
            lines_back = []
            lines_back.append('<!-- START FLOATING DECORATIONS BACK -->')
            lines_back.append('<div id="floating-decorations-container-back" style="position: absolute; top: 0; left: 50%; width: 1200px; transform: translateX(-50%); height: 100%; pointer-events: none; z-index: 0; overflow: visible;">')
            for d in decos_back:
                opacity_style = f" opacity: {d['opacity']:.2f};" if d.get("opacity", 1.0) < 1.0 else ""
                rotate_style = f" transform: rotate({d.get('angle', 0)}deg);" if d.get("angle", 0) != 0 else ""
                h_val = f"{d['real_h']}px" if d.get("real_h", -1) > 0 else "auto"
                lines_back.append(f'    <img class="floating-deco" src="{d["src"]}" style="position: absolute; left: {d["x_real"]}px; top: {d["y_real"]}px; width: {d["real_w"]}px; height: {h_val}; pointer-events: none;{opacity_style}{rotate_style}">')
            lines_back.append('</div>')
            lines_back.append('<!-- END FLOATING DECORATIONS BACK -->')
            
            # Generar HTML para frente
            lines_front = []
            lines_front.append('<!-- START FLOATING DECORATIONS FRONT -->')
            lines_front.append('<div id="floating-decorations-container-front" style="position: absolute; top: 0; left: 50%; width: 1200px; transform: translateX(-50%); height: 100%; pointer-events: none; z-index: 9999; overflow: visible;">')
            for d in decos_front:
                opacity_style = f" opacity: {d['opacity']:.2f};" if d.get("opacity", 1.0) < 1.0 else ""
                rotate_style = f" transform: rotate({d.get('angle', 0)}deg);" if d.get("angle", 0) != 0 else ""
                h_val = f"{d['real_h']}px" if d.get("real_h", -1) > 0 else "auto"
                lines_front.append(f'    <img class="floating-deco" src="{d["src"]}" style="position: absolute; left: {d["x_real"]}px; top: {d["y_real"]}px; width: {d["real_w"]}px; height: {h_val}; pointer-events: none;{opacity_style}{rotate_style}">')
            lines_front.append('</div>')
            lines_front.append('<!-- END FLOATING DECORATIONS FRONT -->')
            
            # Eliminar bloques anteriores (incluyendo el antiguo "floating-decorations-container" si existiese)
            old_pattern = r'<!-- START FLOATING DECORATIONS -->[\s\S]*?<!-- END FLOATING DECORATIONS -->'
            content = re.sub(old_pattern, '', content)
            
            back_pattern = r'<!-- START FLOATING DECORATIONS BACK -->[\s\S]*?<!-- END FLOATING DECORATIONS BACK -->'
            front_pattern = r'<!-- START FLOATING DECORATIONS FRONT -->[\s\S]*?<!-- END FLOATING DECORATIONS FRONT -->'
            
            content = re.sub(back_pattern, '', content)
            content = re.sub(front_pattern, '', content)
            
            # Insertar los nuevos bloques justo al inicio de <body>
            body_match = re.search(r'<body[^>]*>', content)
            if body_match:
                insert_pos = body_match.end()
                new_blocks = "\n" + "\n".join(lines_back) + "\n" + "\n".join(lines_front) + "\n"
                content = content[:insert_pos] + new_blocks + content[insert_pos:]
            else:
                # Fallback por si acaso
                content = f"<body>\n" + "\n".join(lines_back) + "\n" + "\n".join(lines_front) + "\n" + content
                
            with open(self.index_html_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            threading.Thread(target=self.subir_decoraciones_git, daemon=True).start()
            messagebox.showinfo("Éxito", "Decoraciones guardadas y aplicadas a la página web correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar las decoraciones:\n{e}")

    def subir_decoraciones_git(self):
        # Git sync activado
        git_exe = self.find_git_executable()
        for repo_dir in self.target_dirs:
            if not os.path.exists(os.path.join(repo_dir, ".git")):
                continue
            try:
                subprocess.run([git_exe, "add", "index.html"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                subprocess.run([git_exe, "commit", "-m", "Actualizar decoraciones flotantes"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                subprocess.run([git_exe, "pull", "--rebase"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                subprocess.run([git_exe, "push"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            except Exception as e:
                print("Error en git push de decoraciones:", e)

class BackgroundRemoverDialog(tk.Toplevel):
    def __init__(self, parent, src_imagen, pid, target_dirs, target_var, is_modification=False):
        super().__init__(parent)
        self.parent = parent
        self.src_imagen = src_imagen
        self.pid = pid
        self.target_dirs = target_dirs
        self.target_var = target_var
        self.is_modification = is_modification
        
        self.title("Removedor de Fondos IA - Bendito Taller")
        self.geometry("620x720")
        self.configure(bg="#fffcf8")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Centrar ventana relativo al padre
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 310
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 360
        self.geometry(f"+{x}+{y}")
        
        # Sesiones precargadas para evitar descargas/cargas lentas reiteradas
        if not hasattr(self.parent, 'remover_sessions'):
            self.parent.remover_sessions = {}
        self.sessions = self.parent.remover_sessions
        
        self.create_widgets()
        
    def create_widgets(self):
        title_label = tk.Label(
            self, 
            text="Removedor de Fondos IA", 
            font=("Segoe UI", 18, "bold"), 
            bg="#fffcf8", 
            fg="#7d8b63"
        )
        title_label.pack(pady=15)
        
        subtitle_label = tk.Label(
            self, 
            text="Aplica remoción de fondo IA y sellos de agua a tu producto", 
            font=("Segoe UI", 10, "italic"), 
            bg="#fffcf8", 
            fg="#4b372d"
        )
        subtitle_label.pack(pady=3)

        img_info = tk.Label(
            self,
            text=f"Imagen original: {os.path.basename(self.src_imagen)}",
            font=("Segoe UI", 9, "bold"),
            bg="#fffcf8",
            fg="#4b372d"
        )
        img_info.pack(pady=5)

        model_frame = tk.Frame(self, bg="#fffcf8")
        model_frame.pack(pady=5)
        
        model_lbl = tk.Label(
            model_frame, 
            text="Modelo de IA:", 
            font=("Segoe UI", 10, "bold"), 
            bg="#fffcf8", 
            fg="#4b372d"
        )
        model_lbl.grid(row=0, column=0, padx=10)
        
        self.model_var = tk.StringVar(value="birefnet-hrsod (Ultra Precisión - Recomendado)")
        self.model_combo = ttk.Combobox(
            model_frame, 
            textvariable=self.model_var, 
            values=[
                "birefnet-hrsod (Ultra Precisión - Recomendado)",
                "u2net (Estándar - Rápido)",
                "isnet-general-use (Precisión General)",
                "silueta (Solo Siluetas)"
            ],
            width=38,
            state="readonly"
        )
        self.model_combo.grid(row=0, column=1, padx=5)

        watermark_frame = tk.Frame(self, bg="#fffcf8")
        watermark_frame.pack(pady=5)
        
        self.watermark_var = tk.BooleanVar(value=True)
        self.watermark_check = tk.Checkbutton(
            watermark_frame,
            text="Aplicar Sello de Agua (Bendito Taller) en la imagen",
            variable=self.watermark_var,
            font=("Segoe UI", 10, "bold"),
            bg="#fffcf8",
            fg="#4b372d",
            selectcolor="#ffffff",
            activebackground="#fffcf8",
            activeforeground="#4b372d",
            cursor="hand2",
            command=self.toggle_opacity_slider
        )
        self.watermark_check.pack(pady=3)

        controls_frame = tk.Frame(watermark_frame, bg="#fffcf8")
        controls_frame.pack(pady=5)

        self.opacity_var = tk.IntVar(value=90)
        self.opacity_scale = tk.Scale(
            controls_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.opacity_var,
            font=("Segoe UI", 9, "bold"),
            bg="#fffcf8",
            fg="#4b372d",
            highlightthickness=0,
            activebackground="#7d8b63",
            troughcolor="#e5dacb",
            length=220,
            label="Opacidad del Sello (%)"
        )
        self.opacity_scale.grid(row=0, column=0, padx=15, pady=2, sticky="w")

        self.size_var = tk.IntVar(value=45)
        self.size_scale = tk.Scale(
            controls_frame,
            from_=5,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.size_var,
            font=("Segoe UI", 9, "bold"),
            bg="#fffcf8",
            fg="#4b372d",
            highlightthickness=0,
            activebackground="#7d8b63",
            troughcolor="#e5dacb",
            length=220,
            label="Tamaño del Sello (%)"
        )
        self.size_scale.grid(row=1, column=0, padx=15, pady=5, sticky="w")

        pos_frame = tk.Frame(controls_frame, bg="#fffcf8")
        pos_frame.grid(row=0, column=1, rowspan=2, padx=15, sticky="ne")
        
        pos_lbl = tk.Label(
            pos_frame, 
            text="Posición del Sello:", 
            font=("Segoe UI", 9, "bold"), 
            bg="#fffcf8", 
            fg="#4b372d"
        )
        pos_lbl.pack(anchor="w", pady=2)
        
        self.positions_map = {
            (0, 0): "Esquina Superior Izquierda",
            (0, 1): "Arriba",
            (0, 2): "Esquina Superior Derecha",
            (1, 0): "Izquierda",
            (1, 1): "Centro",
            (1, 2): "Derecha",
            (2, 0): "Esquina Inferior Izquierda",
            (2, 1): "Abajo",
            (2, 2): "Esquina Inferior Derecha"
        }
        
        self.grid_buttons = {}
        self.pos_var = tk.StringVar(value="Centro")
        
        self.pos_grid = tk.Frame(pos_frame, bg="#fffcf8")
        self.pos_grid.pack(pady=2)
        
        for r in range(3):
            for c in range(3):
                btn = tk.Button(
                    self.pos_grid,
                    text="",
                    width=2,
                    height=1,
                    bg="#f5ece1",
                    activebackground="#7d8b63",
                    bd=1,
                    relief="solid",
                    cursor="hand2",
                    command=lambda row=r, col=c: self.select_position_grid(row, col)
                )
                btn.grid(row=r, column=c, padx=2, pady=2)
                self.grid_buttons[(r, c)] = btn
                
        self.update_grid_colors(1, 1)

        actions_container = tk.Frame(self, bg="#fffcf8", pady=10)
        actions_container.pack(fill="x", padx=30)

        self.btn_proceed = tk.Button(
            actions_container,
            text="✨ 1. PROCESAR CON IA (Sin Fondo)",
            font=("Segoe UI", 10, "bold"),
            bg="#7d8b63",
            fg="#ffffff",
            activebackground="#677351",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            height=2,
            cursor="hand2",
            command=self.start_processing
        )
        self.btn_proceed.pack(fill="x", pady=4)

        self.btn_original = tk.Button(
            actions_container,
            text="📷 2. USAR IMAGEN ORIGINAL (Sin IA)",
            font=("Segoe UI", 10, "bold"),
            bg="#4b372d",
            fg="#fffcf8",
            activebackground="#f5ece1",
            activeforeground="#4b372d",
            relief="flat",
            bd=0,
            height=2,
            cursor="hand2",
            command=self.use_original_image
        )
        self.btn_original.pack(fill="x", pady=4)

        self.btn_cancel = tk.Button(
            actions_container,
            text="✕ Cancelar",
            font=("Segoe UI", 9, "bold"),
            bg="#f5ece1",
            fg="#4b372d",
            activebackground="#e5dacb",
            activeforeground="#4b372d",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.destroy
        )
        self.btn_cancel.pack(fill="x", pady=4)

        self.progress_label = tk.Label(
            self,
            text="Listo para procesar",
            font=("Segoe UI", 9, "italic"),
            bg="#fffcf8",
            fg="#4b372d"
        )
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(
            self,
            orient="horizontal",
            length=480,
            mode="determinate"
        )
        self.progress_bar.pack(pady=5)
        
        self.details_label = tk.Label(
            self,
            text="",
            font=("Consolas", 9),
            bg="#fffcf8",
            fg="#4b372d",
            wraplength=500
        )
        self.details_label.pack(pady=5)

    def select_position_grid(self, r, c):
        if not self.watermark_var.get():
            return
        pos_name = self.positions_map[(r, c)]
        self.pos_var.set(pos_name)
        self.update_grid_colors(r, c)
        
    def update_grid_colors(self, active_r, active_c):
        for (r, c), btn in self.grid_buttons.items():
            if r == active_r and c == active_c:
                btn.configure(bg="#7d8b63")
            else:
                btn.configure(bg="#f5ece1")

    def toggle_opacity_slider(self):
        if self.watermark_var.get():
            self.opacity_scale.configure(state="normal", fg="#4b372d")
            self.size_scale.configure(state="normal", fg="#4b372d")
            for btn in self.grid_buttons.values():
                btn.configure(state="normal", bg="#f5ece1")
            for (r, c), name in self.positions_map.items():
                if name == self.pos_var.get():
                    self.grid_buttons[(r, c)].configure(bg="#7d8b63")
        else:
            self.opacity_scale.configure(state="disabled", fg="#e5dacb")
            self.size_scale.configure(state="disabled", fg="#e5dacb")
            for btn in self.grid_buttons.values():
                btn.configure(state="disabled", bg="#e5dacb")

    def start_processing(self):
        if not HAS_REMBG:
            messagebox.showerror("Error", "La librería 'rembg' no está disponible en este sistema.")
            return
            
        model_name = self.get_selected_model_name()
        watermark_enabled = self.watermark_var.get()
        opacity = self.opacity_var.get()
        size = self.size_var.get()
        position = self.pos_var.get()

        self.set_ui_state("disabled")
        self.progress_label.config(text="Procesando imagen con IA...", fg="#7d8b63")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        threading.Thread(
            target=self._run_ia_remover, 
            args=(model_name, watermark_enabled, opacity, size, position),
            daemon=True
        ).start()

    def set_ui_state(self, state):
        self.btn_proceed.configure(state=state)
        self.btn_original.configure(state=state)
        self.btn_cancel.configure(state=state)
        self.model_combo.configure(state="readonly" if state == "normal" else "disabled")
        self.watermark_check.configure(state=state)
        if state == "normal":
            self.toggle_opacity_slider()
        else:
            self.opacity_scale.configure(state="disabled")
            self.size_scale.configure(state="disabled")
            for btn in self.grid_buttons.values():
                btn.configure(state="disabled")

    def get_selected_model_name(self):
        val = self.model_var.get()
        if "birefnet-hrsod" in val:
            return "birefnet-hrsod"
        elif "u2net" in val:
            return "u2net"
        elif "isnet-general-use" in val:
            return "isnet-general-use"
        elif "silueta" in val:
            return "silueta"
        return "birefnet-hrsod"

    def get_session(self, model_name):
        if model_name not in self.sessions:
            self.after(0, lambda: self.progress_label.config(text=f"Cargando modelo de IA ({model_name})...", fg="#7d8b63"))
            self.sessions[model_name] = new_session(model_name)
        return self.sessions[model_name]

    def apply_watermark_logic(self, img, opacity_pct, size_pct, position):
        if opacity_pct <= 0:
            return img
            
        # Buscar el sello de agua dinámicamente en los directorios de destino
        watermark_path = None
        for d in self.target_dirs:
            candidate = os.path.join(d, "img", "SELLO DE AGUA.png")
            if os.path.exists(candidate):
                watermark_path = candidate
                break
        
        if not watermark_path:
            watermark_path = os.path.join(self.parent.base_dir, "img", "SELLO DE AGUA.png")

        if not os.path.exists(watermark_path):
            self.after(0, lambda: self.details_label.config(
                text="Advertencia: Sello de agua no encontrado en los repositorios.", fg="#d9534f"
            ))
            return img
        try:
            with Image.open(watermark_path) as wm:
                wm = wm.convert("RGBA")
                img = img.convert("RGBA")
                
                opacity_factor = opacity_pct / 100.0
                r, g, b, a = wm.split()
                a = a.point(lambda p: int(p * opacity_factor))
                wm = Image.merge("RGBA", (r, g, b, a))
                
                scale = (img.width * (size_pct / 100.0)) / wm.width
                new_w = int(wm.width * scale)
                new_h = int(wm.height * scale)
                
                if new_w > 0 and new_h > 0:
                    wm_resized = wm.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    margin = 25
                    
                    if position == "Centro":
                        x = (img.width - new_w) // 2
                        y = (img.height - new_h) // 2
                    elif position == "Arriba":
                        x = (img.width - new_w) // 2
                        y = margin
                    elif position == "Abajo":
                        x = (img.width - new_w) // 2
                        y = img.height - new_h - margin
                    elif position == "Izquierda":
                        x = margin
                        y = (img.height - new_h) // 2
                    elif position == "Derecha":
                        x = img.width - new_w - margin
                        y = (img.height - new_h) // 2
                    elif position == "Esquina Superior Izquierda":
                        x = margin
                        y = margin
                    elif position == "Esquina Superior Derecha":
                        x = img.width - new_w - margin
                        y = margin
                    elif position == "Esquina Inferior Izquierda":
                        x = margin
                        y = img.height - new_h - margin
                    elif position == "Esquina Inferior Derecha":
                        x = img.width - new_w - margin
                        y = img.height - new_h - margin
                    else:
                        x = (img.width - new_w) // 2
                        y = (img.height - new_h) // 2
                    
                    img.paste(wm_resized, (x, y), wm_resized)
        except Exception as e:
            print(f"Error applying watermark: {e}")
        return img

    def _run_ia_remover(self, model_name, watermark_enabled, opacity, size, position):
        try:
            session = self.get_session(model_name)
            
            with Image.open(self.src_imagen) as img:
                out_img = remove(img, session=session)
                if watermark_enabled:
                    out_img = self.apply_watermark_logic(out_img, opacity, size, position)
                
                # Redimensionar si supera 800px
                max_w_h = 800
                if out_img.width > max_w_h or out_img.height > max_w_h:
                    out_img.thumbnail((max_w_h, max_w_h), Image.Resampling.LANCZOS)
                
                # Guardar en repositorios
                filename = f"{self.pid}.webp"
                for d in self.target_dirs:
                    img_dir = os.path.join(d, "img")
                    if not os.path.exists(img_dir):
                        os.makedirs(img_dir)
                    dest_path = os.path.join(img_dir, filename)
                    out_img.save(dest_path, "WEBP", quality=80)
                    
            self.after(0, self._on_ia_success)
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _on_ia_success(self):
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate", value=100)
        self.progress_label.config(text="¡Remoción de fondo IA completada!", fg="#7d8b63")
        
        self.parent.imagen_procesada_ia = True
        self.parent.imagen_ext_ia = ".webp"
        self.target_var.set(f"img/{self.pid}.webp")
        
        messagebox.showinfo("Éxito", "Imagen procesada con éxito y guardada en los repositorios locales.")
        self.destroy()

    def use_original_image(self):
        filename = f"{self.pid}.webp"
        try:
            for d in self.target_dirs:
                img_dir = os.path.join(d, "img")
                if not os.path.exists(img_dir):
                    os.makedirs(img_dir)
                dest_path = os.path.join(img_dir, filename)
                img = Image.open(self.src_imagen)
                img.save(dest_path, "WEBP", quality=80)
                
            self.parent.imagen_procesada_ia = True
            self.parent.imagen_ext_ia = ".webp"
            self.target_var.set(f"img/{filename}")
            
            messagebox.showinfo("Éxito", "Imagen original copiada con éxito a los repositorios locales.")
            self.destroy()
        except Exception as e:
            self._on_error(str(e))

    def _on_error(self, err_msg):
        self.set_ui_state("normal")
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate", value=0)
        self.progress_label.config(text="Error al procesar", fg="#d9534f")
        self.details_label.config(text=f"Detalle: {err_msg}", fg="#d9534f")
        messagebox.showerror("Error", f"Ocurrió un error:\n{err_msg}")

if __name__ == "__main__":
    # Ajuste de DPI en Windows para evitar que se vea borroso
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    root = tk.Tk()
    app = App(root)
    root.mainloop()
