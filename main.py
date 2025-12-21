import flet as ft
import uuid
import json
import urllib.request
import urllib.error

def main(page: ft.Page):
    # --- CONFIGURACIÓN BÁSICA ---
    page.title = "Vegan Green"
    page.theme_mode = "light"
    page.padding = 0 
    page.bgcolor = "#202020" 
    page.theme = ft.Theme(color_scheme_seed="#388E3C")

    # --- IMAGEN DE FONDO (USAMOS INTERNET PARA QUE NO FALLE) ---
    # Si usamos local y falla la carga, la app se queda blanca.
    # Usamos esta URL segura para probar que la app abre.
    FONDO_APP = "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?auto=format&fit=crop&w=640&q=80"
    IMAGEN_DEFAULT = "https://upload.wikimedia.org/wikipedia/commons/1/14/No_Image_Available.jpg"
    
    # --- FIREBASE ---
    # PEGA TU URL AQUI
    FIREBASE_URL = "" 
    USAR_NUBE = bool(FIREBASE_URL)

    # --- DATOS DE SEGURIDAD ---
    # Si todo falla, cargará esto:
    DATOS_INICIALES = {
        "recetas": [{"id": "1", "titulo": "Tarta de Higos", "desc": "Postre natural", "tag": "Dulce", "imagen": "https://images.unsplash.com/photo-1602351447937-745cb720612f?auto=format&fit=crop&w=500&q=60", "video": "", "contenido": "Ingredientes: Higos..."}],
        "restaurantes": [],
        "productos": []
    }

    # --- GESTIÓN DE DATOS ---
    def cargar_datos_nube(coleccion):
        if not USAR_NUBE: return []
        try:
            # Timeout de 3 segundos para que no congele la app si no hay internet
            url = f"{FIREBASE_URL}/{coleccion}.json"
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    d = json.loads(r.read().decode())
                    if d: return list(d.values()) if isinstance(d, dict) else [x for x in d if x]
            return []
        except: return []

    def guardar_datos_nube(coleccion, datos):
        if not USAR_NUBE: return
        try:
            req = urllib.request.Request(f"{FIREBASE_URL}/{coleccion}.json", data=json.dumps(datos).encode(), method='PUT')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=5): pass
        except: pass

    def cargar_seguro(key, default):
        # Esta función evita que la app muera si fallan los datos
        datos = []
        
        # 1. Intentar Nube
        if USAR_NUBE:
            datos = cargar_datos_nube(key.replace("mis_", ""))
            if datos:
                page.client_storage.set(key, datos)
                return datos
        
        # 2. Intentar Local
        try:
            datos = page.client_storage.get(key)
        except: pass # Si falla local, ignoramos
        
        # 3. Si no hay nada, usar Default
        if not datos: return default
        
        # 4. Sanear IDs
        try:
            for i in datos:
                if isinstance(i, dict) and "id" not in i: i["id"] = str(uuid.uuid4())
            return datos
        except: return default

    # Cargamos datos protegidos
    db = {
        "recetas": cargar_seguro("mis_recetas", DATOS_INICIALES["recetas"]),
        "restaurantes": cargar_seguro("mis_restaurantes", DATOS_INICIALES["restaurantes"]),
        "productos": cargar_seguro("mis_productos", DATOS_INICIALES["productos"])
    }
    
    estado = {"seccion": 0, "admin": False, "edit_id": None} 

    # --- INTERFAZ ---
    fondo_img = ft.Image(src=FONDO_APP, fit=ft.ImageFit.COVER, opacity=1.0, expand=True, error_content=ft.Container(bgcolor="#388E3C"))
    contenedor = ft.Container(expand=True, padding=10, alignment=ft.alignment.center)
    stack_main = ft.Stack(controls=[fondo_img, contenedor], expand=True)

    def sync(key):
        page.client_storage.set(f"mis_{key}", db[key])
        if USAR_NUBE: guardar_datos_nube(key, db[key])

    # --- LÓGICA ---
    def borrar(key, id_obj):
        db[key] = [x for x in db[key] if x.get("id") != id_obj]
        sync(key)
        mostrar(estado["seccion"])
        try: page.open(ft.SnackBar(ft.Text("Eliminado"), bgcolor="green"))
        except: pass

    def guardar_item(e):
        if not input_nombre.value: return
        
        # Imagen por defecto si está vacía
        img_val = input_img.value if input_img.value else IMAGEN_DEFAULT
        
        data = {"titulo": input_nombre.value, "desc": input_desc.value, "tag": input_tag.value, "imagen": img_val, "video": input_vid.value, "contenido": input_cont.value}
        key = ["", "recetas", "restaurantes", "productos"][estado["seccion"]]
        
        if estado["edit_id"]:
            for i, x in enumerate(db[key]):
                if x["id"] == estado["edit_id"]:
                    data["id"] = estado["edit_id"]
                    db[key][i] = data
                    break
        else:
            data["id"] = str(uuid.uuid4())
            db[key].append(data)
        
        sync(key)
        mostrar(estado["seccion"])
        try: page.open(ft.SnackBar(ft.Text("Guardado"), bgcolor="green"))
        except: pass

    # --- FORMULARIO ---
    txt_titulo = ft.Text("Nuevo", size=20, weight="bold", color="green")
    input_nombre = ft.TextField(label="Nombre", bgcolor="white", color="black")
    input_desc = ft.TextField(label="Descripción", bgcolor="white", color="black")
    input_tag = ft.TextField(label="Etiqueta", bgcolor="white", color="black")
    input_img = ft.TextField(label="URL Imagen", bgcolor="white", color="black")
    input_vid = ft.TextField(label="URL Enlace", bgcolor="white", color="black")
    input_cont = ft.TextField(label="Detalles", multiline=True, bgcolor="white", color="black")
    
    def archivo_sel(e: ft.FilePickerResultEvent):
        if e.files: input_img.value = e.files[0].path; input_img.update()
    picker = ft.FilePicker(on_result=archivo_sel)
    page.overlay.append(picker)

    vista_form = ft.Container(bgcolor="white", padding=20, border_radius=10, content=ft.Column([
        txt_titulo, input_nombre, input_desc, input_tag,
        ft.Row([input_img, ft.IconButton("photo_library", on_click=lambda _: picker.pick_files())]),
        input_vid, input_cont,
        ft.Row([ft.ElevatedButton("Cancelar", on_click=lambda e: mostrar(estado["seccion"])), ft.ElevatedButton("Guardar", on_click=guardar_item)])
    ], scroll="auto"))

    def abrir_form(item=None):
        estado["edit_id"] = item["id"] if item else None
        txt_titulo.value = "Editar" if item else "Nuevo"
        input_nombre.value = item["titulo"] if item else ""
        input_desc.value = item["desc"] if item else ""
        input_tag.value = item["tag"] if item else ""
        input_img.value = item["imagen"] if item else ""
        input_vid.value = item["video"] if item else ""
        input_cont.value = item["contenido"] if item else ""
        
        if estado["seccion"] == 2:
            input_desc.label = "Lugar"
            input_desc.icon = "map"
        else:
            input_desc.label = "Descripción"
            input_desc.icon = "description"

        fondo_img.visible = False
        contenedor.bgcolor = "#F5F5F5"
        contenedor.alignment = ft.alignment.top_center
        contenedor.content = vista_form
        btn_add.visible = False
        page.update()

    # --- SEGURIDAD ---
    input_pin = ft.TextField(label="PIN", password=True, text_align="center")
    def validar_pin(e, callback):
        if input_pin.value == "1969":
            estado["admin"] = True
            btn_lock.icon = "lock_open"
            btn_lock.icon_color = "yellow"
            page.close(dlg_auth)
            callback()
            page.update()
        else: input_pin.error_text = "Mal"; page.update()

    dlg_auth = ft.AlertDialog(title=ft.Text("Admin"), content=input_pin, actions=[ft.ElevatedButton("Entrar", on_click=None)])
    
    def check_admin(callback):
        if estado["admin"]: callback()
        else:
            input_pin.value = ""
            input_pin.error_text = None
            dlg_auth.actions[0].on_click = lambda e: validar_pin(e, callback)
            page.open(dlg_auth)

    def confirmar_borrado(key, item):
        def si(e): page.close(dlg_del); borrar(key, item["id"])
        dlg_del = ft.AlertDialog(title=ft.Text("¿Borrar?"), actions=[ft.TextButton("No", on_click=lambda e: page.close(dlg_del)), ft.ElevatedButton("Si", on_click=si)])
        page.open(dlg_del)

    def toggle_admin(e):
        if estado["admin"]:
            estado["admin"] = False
            btn_lock.icon = "lock_outline"
            btn_lock.icon_color = "white"
            page.update()
        else: check_admin(lambda: None)
    
    btn_lock = ft.IconButton(icon="lock_outline", icon_color="white", on_click=toggle_admin)
    btn_add = ft.IconButton(icon="add_circle", icon_color="white", icon_size=30, on_click=lambda e: check_admin(lambda: abrir_form(None)), visible=False)

    # --- LISTAS ---
    def get_lista(key, color, icon):
        col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        # Botón para refrescar
        if USAR_NUBE:
            # Recarga simple y segura
            def recargar(e):
                db["recetas"] = cargar_nube("recetas")
                db["restaurantes"] = cargar_nube("restaurantes")
                db["productos"] = cargar_nube("productos")
                mostrar(estado["seccion"])
            col.controls.append(ft.TextButton("Sincronizar", icon="cloud_sync", on_click=recargar))

        for item in db[key]:
            src = item.get("imagen") or IMAGEN_DEFAULT
            tiene_foto = bool(item.get("imagen"))
            
            c_txt = "white" if tiene_foto else "black"
            c_ico = "white" if tiene_foto else "green"
            bg = "#99000000" if tiene_foto else "white"
            
            link = ft.Container()
            if item.get("video"):
                 link = ft.TextButton("Enlace", icon="link", on_click=lambda e, u=item["video"]: page.launch_url(u))
                 link.content.style = ft.ButtonStyle(color=c_txt)

            extras = ft.Container()
            if item.get("contenido"):
                extras = ft.ExpansionTile(title=ft.Text("Ver más", size=12, color="blue"), controls=[ft.Container(padding=10, content=ft.Text(item["contenido"], size=12, color=c_txt))])

            btns = ft.Row([
                link, ft.Container(expand=True),
                ft.IconButton("edit", icon_color="blue", on_click=lambda e, i=item: check_admin(lambda: abrir_form(i))),
                ft.IconButton("delete", icon_color="red", on_click=lambda e, k=key, i=item["id"]: check_admin(lambda: confirmar_borrado(k, i)))
            ], alignment="end")

            info = ft.Column([
                ft.Row([ft.Icon(icon, color="green"), ft.Text(item["titulo"], weight="bold", size=18, color=c_txt, expand=True)]),
                ft.Text(item["desc"], size=12, color=c_txt),
                extras, btns
            ])
            
            stack = []
            if tiene_foto: stack.append(ft.Image(src=src, fit=ft.ImageFit.COVER, opacity=1.0, expand=True))
            stack.append(ft.Container(bgcolor=bg, padding=10, content=info, expand=True))
            
            col.controls.append(ft.Card(elevation=5, content=ft.Container(height=280, content=ft.Stack(controls=stack))))
        return col

    def mostrar(idx):
        estado["seccion"] = idx
        btn_add.visible = (idx != 0)
        fondo_img.visible = (idx == 0)
        contenedor.bgcolor = "#F5F5F5" if idx != 0 else None
        
        if idx == 0:
            contenedor.alignment = ft.alignment.center
            contenedor.content = ft.Container()
            titulo.value = "Vegan Green"
            # Recarga silenciosa al volver al inicio
            if USAR_NUBE:
                 try:
                     db["recetas"] = cargar_datos_nube("recetas")
                     db["restaurantes"] = cargar_datos_nube("restaurantes")
                     db["productos"] = cargar_datos_nube("productos")
                 except: pass
        else:
            contenedor.alignment = ft.alignment.top_center
            key = ["", "recetas", "restaurantes", "productos"][idx]
            contenedor.content = get_lista(key, "green", "star")
        page.update()

    titulo = ft.Text("Vegan Green", color="white", size=20, weight="bold")
    nav = ft.NavigationBar(on_change=lambda e: mostrar(e.control.selected_index), destinations=[
        ft.NavigationBarDestination(icon="home", label="Inicio"),
        ft.NavigationBarDestination(icon="book", label="Recetas"),
        ft.NavigationBarDestination(icon="store", label="Sitios"),
        ft.NavigationBarDestination(icon="shopping_bag", label="Productos")
    ])

    page.add(ft.Column([
        ft.Container(padding=10, bgcolor="green", content=ft.Row([
            ft.Row([ft.Icon("eco", color="white"), titulo]),
            ft.Row([btn_add, btn_lock])
        ], alignment="spaceBetween")),
        ft.Container(content=stack_main, expand=True),
        nav
    ], expand=True))
    mostrar(0)

# Importante: Quitamos assets_dir="assets" temporalmente para que no falle si no está bien subida la carpeta
ft.app(target=main)


