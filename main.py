import flet as ft
import uuid
import json
import urllib.request 

def main(page: ft.Page):
    # --- 1. CONFIGURACIÓN INICIAL ---
    page.title = "Vegan Green"
    page.theme_mode = "light"
    page.padding = 0 
    page.bgcolor = "#202020" 
    page.theme = ft.Theme(color_scheme_seed="#388E3C")

    # --- 2. CONFIGURACIÓN DE IMÁGENES Y NUBE ---
    FONDO_APP = "/portada.jpg" 
    IMAGEN_DEFAULT = "https://upload.wikimedia.org/wikipedia/commons/1/14/No_Image_Available.jpg"
    
    FIREBASE_URL = "" # Pega tu URL aquí entre las comillas
    USAR_NUBE = bool(FIREBASE_URL)

    # --- 3. FUNCIONES DE BASE DE DATOS (Compatibles Android) ---
    def cargar_nube(coleccion):
        if not USAR_NUBE: return []
        try:
            url = f"{FIREBASE_URL}/{coleccion}.json"
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    data = response.read().decode('utf-8')
                    if data != "null":
                        datos = json.loads(data)
                        if isinstance(datos, dict): return list(datos.values())
                        elif isinstance(datos, list): return [x for x in datos if x]
            return []
        except: return []

    def guardar_nube(coleccion, datos):
        if not USAR_NUBE: return
        try:
            url = f"{FIREBASE_URL}/{coleccion}.json"
            req = urllib.request.Request(url, data=json.dumps(datos).encode(), method='PUT')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req): pass
        except: pass

    # --- 4. GESTIÓN DE DATOS LOCALES Y SANEAMIENTO ---
    def cargar_datos(key):
        # Prioridad Nube
        if USAR_NUBE:
            nube = cargar_nube(key.replace("mis_", ""))
            if nube:
                page.client_storage.set(key, nube)
                return nube
        
        # Fallback Local
        try:
            local = page.client_storage.get(key)
            if not local: return []
            
            # Saneamiento: Poner ID si falta
            arreglado = False
            for item in local:
                if "id" not in item:
                    item["id"] = str(uuid.uuid4())
                    arreglado = True
            
            if arreglado: page.client_storage.set(key, local)
            return local
        except: return []

    db = {
        "recetas": cargar_datos("mis_recetas"),
        "restaurantes": cargar_datos("mis_restaurantes"),
        "productos": cargar_datos("mis_productos")
    }
    
    estado = {"seccion": 0, "admin": False, "edit_id": None} 

    # --- 5. INTERFAZ PRINCIPAL (FONDO + CONTENIDO) ---
    # Usamos Stack para el fondo de la app (compatible con todo)
    fondo_img = ft.Image(src=FONDO_APP, fit=ft.ImageFit.COVER, opacity=1.0, expand=True, error_content=ft.Container(bgcolor="#388E3C"))
    contenedor_contenido = ft.Container(expand=True, padding=10, alignment=ft.alignment.center)
    stack_principal = ft.Stack(controls=[fondo_img, contenedor_contenido], expand=True)

    # --- 6. FUNCIONES DE GUARDADO Y BORRADO ---
    def sync_db(key):
        page.client_storage.set(f"mis_{key}", db[key])
        if USAR_NUBE: guardar_nube(key, db[key])

    def borrar(key, id_obj):
        # Borrado por filtro de ID (Infalible)
        db[key] = [x for x in db[key] if x.get("id") != id_obj]
        sync_db(key)
        
        # Feedback visual
        try: page.open(ft.SnackBar(ft.Text("¡Eliminado!"), bgcolor="green"))
        except: pass # Si falla el snackbar en versiones viejas, no rompe la app
        
        mostrar(estado["seccion"]) # Refrescar pantalla
        page.update()

    def guardar(e):
        if not input_nombre.value: return
        
        # Recoger datos del formulario
        item_data = {
            "titulo": input_nombre.value,
            "desc": input_desc.value,
            "tag": input_tag.value,
            "imagen": input_img.value,
            "video": input_vid.value,
            "contenido": input_cont.value
        }
        
        sec_idx = estado["seccion"]
        key = "recetas" if sec_idx == 1 else "restaurantes" if sec_idx == 2 else "productos" if sec_idx == 3 else None
        
        if key:
            if estado["edit_id"]: # EDITAR
                for i, x in enumerate(db[key]):
                    if x["id"] == estado["edit_id"]:
                        item_data["id"] = estado["edit_id"]
                        db[key][i] = item_data
                        break
            else: # NUEVO
                item_data["id"] = str(uuid.uuid4())
                db[key].append(item_data)
            
            sync_db(key)
            try: page.open(ft.SnackBar(ft.Text("Guardado"), bgcolor="green"))
            except: pass
            
            mostrar(sec_idx)

    # --- 7. SISTEMA DE SEGURIDAD (PIN) ---
    input_pin = ft.TextField(label="PIN", password=True, text_align="center", autofocus=True)
    
    def validar_pin(e, callback):
        if input_pin.value == "1969":
            estado["admin"] = True
            btn_lock.icon = "lock_open"
            btn_lock.icon_color = "yellow"
            page.close(dlg_auth)
            callback()
        else:
            input_pin.error_text = "Mal"
        page.update()

    # Variable para guardar qué acción quería hacer el usuario
    accion_pendiente = None 
    
    def ejecutar_accion_segura(accion):
        nonlocal accion_pendiente
        if estado["admin"]:
            accion()
        else:
            accion_pendiente = accion
            input_pin.value = ""
            input_pin.error_text = None
            # Configuramos el botón del diálogo para ejecutar la acción pendiente
            dlg_auth.actions[1].on_click = lambda e: validar_pin(e, accion_pendiente)
            page.open(dlg_auth)

    dlg_auth = ft.AlertDialog(
        title=ft.Text("Admin"),
        content=input_pin,
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_auth)),
            ft.ElevatedButton("Entrar", on_click=None) # Se asigna dinámicamente
        ]
    )

    def confirmar_borrado(key, item):
        def si(e):
            page.close(dlg_del)
            borrar(key, item["id"])
        
        dlg_del = ft.AlertDialog(
            title=ft.Text("¿Borrar?"),
            content=ft.Text(f"Eliminar: {item['titulo']}"),
            actions=[
                ft.TextButton("No", on_click=lambda e: page.close(dlg_del)),
                ft.ElevatedButton("Si", on_click=si, bgcolor="red", color="white")
            ]
        )
        page.open(dlg_del)

    # --- 8. FORMULARIO ---
    txt_form_titulo = ft.Text("Nuevo", size=20, weight="bold", color="green")
    input_nombre = ft.TextField(label="Nombre")
    input_desc = ft.TextField(label="Descripción")
    input_tag = ft.TextField(label="Etiqueta")
    input_img = ft.TextField(label="URL Imagen", icon="image")
    input_vid = ft.TextField(label="URL Enlace", icon="link")
    input_cont = ft.TextField(label="Detalles", multiline=True)

    def archivo_sel(e: ft.FilePickerResultEvent):
        if e.files: input_img.value = e.files[0].path; input_img.update()
    picker = ft.FilePicker(on_result=archivo_sel)
    page.overlay.append(picker)

    vista_form = ft.Container(
        bgcolor="white", padding=20, border_radius=10,
        content=ft.Column([
            txt_form_titulo,
            input_nombre, input_desc, input_tag,
            ft.Row([input_img, ft.IconButton("photo_library", on_click=lambda _: picker.pick_files())]),
            input_vid, input_cont,
            ft.Row([
                ft.ElevatedButton("Cancelar", on_click=lambda e: mostrar(estado["seccion"])),
                ft.ElevatedButton("Guardar", on_click=guardar, bgcolor="green", color="white")
            ], alignment="center"),
            ft.Container(height=50) # Espacio final para scroll
        ], scroll="auto")
    )

    def abrir_form(item=None):
        es_editar = item is not None
        txt_form_titulo.value = "Editar" if es_editar else "Nuevo"
        
        # Rellenar campos
        input_nombre.value = item["titulo"] if es_editar else ""
        input_desc.value = item["desc"] if es_editar else ""
        input_tag.value = item["tag"] if es_editar else ""
        input_img.value = item["imagen"] if es_editar else ""
        input_vid.value = item["video"] if es_editar else ""
        input_cont.value = item["contenido"] if es_editar else ""
        
        estado["id_editar"] = item["id"] if es_editar else None
        
        # Cambiar vista
        fondo_img.visible = False
        contenedor_contenido.bgcolor = "#F5F5F5"
        contenedor_contenido.alignment = ft.alignment.top_center
        contenedor_contenido.content = vista_form
        btn_add.visible = False
        page.update()

    # --- 9. LISTAS VISUALES ---
    def get_lista(key, color, icono):
        col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        # Botón refrescar si hay nube
        if USAR_NUBE:
            col.controls.append(ft.TextButton("Sincronizar Nube", icon="cloud_sync", on_click=lambda e: [db.update({k: cargar_nube(k) for k in db}), mostrar(estado["seccion"])]))

        for item in db[key]:
            tiene_foto = bool(item.get("imagen"))
            src = item.get("imagen") or IMAGEN_DEFAULT
            
            # Colores dinámicos
            c_txt = "white" if tiene_foto else "black"
            c_ico = "white" if tiene_foto else "green"
            bg = "#99000000" if tiene_foto else "white"

            # Partes de la tarjeta
            extras = ft.Container()
            if item.get("contenido"):
                extras = ft.ExpansionTile(
                    title=ft.Text("Ver más", size=12, color="blue"), 
                    tile_padding=0,
                    controls=[ft.Container(padding=10, content=ft.Text(item["contenido"], size=12, color=c_txt))]
                )
            
            link = ft.Container()
            if item.get("video"):
                 link = ft.TextButton("Enlace", icon="link", icon_color="blue", on_click=lambda e, u=item["video"]: page.launch_url(u))

            # Botones acción (protegidos)
            btns = ft.Row([
                link, ft.Container(expand=True),
                ft.IconButton("edit", icon_color="blue", on_click=lambda e, i=item: ejecutar_accion_segura(lambda: abrir_form(i))),
                ft.IconButton("delete", icon_color="red", on_click=lambda e, k=key, i=item: ejecutar_accion_segura(lambda: confirmar_borrado(k, i)))
            ], alignment="end")

            info = ft.Column([
                ft.Row([
                    ft.Icon(icono, color=c_ico), 
                    ft.Text(item["titulo"], weight="bold", size=18, color=c_txt, expand=True),
                    ft.Container(content=ft.Text(item["tag"], size=10, color="white"), bgcolor=color, padding=4, border_radius=4)
                ]),
                ft.Text(item["desc"], size=12, color=c_txt),
                ft.Divider(height=5, color="white24" if tiene_foto else "black12"),
                extras, btns
            ])

            # Montaje Stack
            stack_card = []
            if tiene_foto:
                stack_card.append(ft.Image(src=src, fit=ft.ImageFit.COVER, opacity=1.0, expand=True))
            
            stack_card.append(ft.Container(bgcolor=bg, padding=10, content=info, expand=True))

            card = ft.Card(
                elevation=5, 
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Container(
                    height=280, # Altura fija para ver bien la foto
                    content=ft.Stack(controls=stack_card)
                )
            )
            col.controls.append(card)
        return col

    # --- 10. NAVEGACIÓN ---
    def mostrar(idx):
        estado["seccion"] = idx
        btn_add.visible = (idx != 0)
        fondo_img.visible = (idx == 0)
        contenedor_contenido.bgcolor = "#F5F5F5" if idx != 0 else None

        if idx == 0:
            contenedor_contenido.alignment = ft.alignment.center
            contenedor_contenido.content = ft.Container()
            titulo.value = "Vegan Green"
        else:
            contenedor_contenido.alignment = ft.alignment.top_center
            if idx == 1: contenedor_contenido.content = get_lista("recetas", "green", "book")
            elif idx == 2: contenedor_contenido.content = get_lista("restaurantes", "orange", "store")
            elif idx == 3: contenedor_contenido.content = get_lista("productos", "blue", "shopping_bag")
        page.update()

    # --- UI GLOBAL ---
    titulo = ft.Text("Vegan Green", color="white", size=20, weight="bold")
    btn_lock = ft.IconButton(icon="lock_outline", icon_color="white", on_click=lambda e: ejecutar_accion_segura(lambda: page.open(ft.SnackBar(ft.Text("Admin OK"), bgcolor="green"))))
    btn_add = ft.IconButton(icon="add_circle", icon_color="white", icon_size=30, visible=False, on_click=lambda e: ejecutar_accion_segura(lambda: abrir_form(None)))
    
    app_bar = ft.Container(padding=10, bgcolor="green", content=ft.Row([ft.Row([ft.Icon("eco", color="white"), titulo]), ft.Row([btn_add, btn_lock])], alignment="spaceBetween"))
    
    nav = ft.NavigationBar(on_change=lambda e: mostrar(e.control.selected_index), destinations=[
        ft.NavigationDestination(icon="home", label="Inicio"),
        ft.NavigationDestination(icon="book", label="Recetas"),
        ft.NavigationDestination(icon="store", label="Sitios"),
        ft.NavigationDestination(icon="shopping_bag", label="Productos")
    ])

    layout = ft.Column(spacing=0, expand=True, controls=[app_bar, ft.Container(content=stack_principal, expand=True), nav])
    page.add(layout)

# IMPORTANTE: assets_dir="assets" debe estar aquí para que coja la foto
ft.app(target=main, assets_dir="assets")
