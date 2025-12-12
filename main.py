import flet as ft
import uuid
import json
import urllib.request 

def main(page: ft.Page):
    # --- CONFIGURACIÓN BÁSICA ---
    page.title = "Vegan Green"
    page.theme_mode = "light"
    page.padding = 0 
    page.bgcolor = "#202020" 
    page.theme = ft.Theme(color_scheme_seed="#388E3C")

    # --- IMAGEN DE FONDO ---
    FONDO_APP = "/portada.jpg"
    IMAGEN_DEFAULT = "https://upload.wikimedia.org/wikipedia/commons/1/14/No_Image_Available.jpg"

    # --- CONFIGURACIÓN FIREBASE (Si la tienes) ---
    FIREBASE_URL = "" 
    USAR_NUBE = bool(FIREBASE_URL)

    # --- GESTIÓN DE DATOS ---
    def cargar_datos_nube(coleccion):
        if not USAR_NUBE: return []
        try:
            url = f"{FIREBASE_URL}/{coleccion}.json"
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    data = response.read().decode('utf-8')
                    if data != "null":
                        datos = json.loads(data)
                        if isinstance(datos, dict): return list(datos.values())
                        elif isinstance(datos, list): return [x for x in datos if x is not None]
            return []
        except: return []

    def guardar_datos_nube(coleccion, datos_lista):
        if not USAR_NUBE: return
        try:
            url = f"{FIREBASE_URL}/{coleccion}.json"
            json_data = json.dumps(datos_lista).encode('utf-8')
            req = urllib.request.Request(url, data=json_data, method='PUT')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req) as response: pass
        except: pass

    def cargar_y_sanear(key):
        # 1. Nube
        if USAR_NUBE:
            datos_nube = cargar_datos_nube(key.replace("mis_", ""))
            if datos_nube:
                page.client_storage.set(key, datos_nube)
                return datos_nube
        # 2. Local
        try:
            datos = page.client_storage.get(key)
            if datos is None: return []
            lista_saneada = []
            cambios = False
            for item in datos:
                if not isinstance(item, dict): continue
                if "id" not in item:
                    item["id"] = str(uuid.uuid4())
                    cambios = True
                lista_saneada.append(item)
            if cambios: page.client_storage.set(key, lista_saneada)
            return lista_saneada
        except: return []

    db = {
        "recetas": cargar_y_sanear("mis_recetas"),
        "restaurantes": cargar_y_sanear("mis_restaurantes"),
        "productos": cargar_y_sanear("mis_productos")
    }
    
    # ESTADO GLOBAL
    # Guardamos aquí temporalmente lo que queremos borrar para que el diálogo lo sepa
    estado = {"seccion_actual": 0, "admin": False, "borrar_clave": None, "borrar_id": None} 

    # --- CAPAS DE FONDO ---
    imagen_fondo = ft.Image(src=FONDO_APP, fit=ft.ImageFit.COVER, opacity=1.0, expand=True, error_content=ft.Container(bgcolor="#388E3C"))
    contenedor_contenido = ft.Container(expand=True, padding=10, alignment=ft.alignment.center)
    stack_principal = ft.Stack(controls=[imagen_fondo, contenedor_contenido], expand=True)

    def sincronizar_cambios(clave_db):
        page.client_storage.set(f"mis_{clave_db}", db[clave_db])
        if USAR_NUBE: guardar_datos_nube(clave_db, db[clave_db])

    # --- LÓGICA DE BORRADO ---
    def ejecutar_borrado_final():
        clave = estado["borrar_clave"]
        id_obj = estado["borrar_id"]
        
        if not clave or not id_obj: return

        lista_memoria = db[clave]
        lista_nueva = [x for x in lista_memoria if x.get("id") != id_obj]
        
        if len(lista_nueva) < len(lista_memoria):
            db[clave] = lista_nueva
            sincronizar_cambios(clave)
            page.open(ft.SnackBar(ft.Text("¡Eliminado correctamente!"), bgcolor="green"))
        else:
            # Si falla por ID, intentamos recargar y forzar
            page.open(ft.SnackBar(ft.Text("Error al borrar. Intenta refrescar."), bgcolor="red"))
        
        mostrar_seccion(estado["seccion_actual"])
        page.update()

    # --- DIÁLOGO DE BORRADO UNIFICADO ---
    # Un solo cuadro de diálogo que se adapta si eres admin o no
    
    campo_pin_borrar = ft.TextField(label="PIN (1969)", password=True, text_align="center")
    
    def confirmar_borrado_click(e):
        # 1. Comprobar PIN si no es admin
        if not estado["admin"]:
            if campo_pin_borrar.value == "1969":
                estado["admin"] = True # Hacemos admin temporalmente
                actualizar_candado()
            else:
                campo_pin_borrar.error_text = "PIN Incorrecto"
                campo_pin_borrar.update()
                return # No borramos si el PIN está mal
        
        # 2. Si llegamos aquí, es que podemos borrar
        page.close(dlg_borrar)
        ejecutar_borrado_final()

    dlg_borrar = ft.AlertDialog(
        title=ft.Text("Eliminar Elemento"),
        content=ft.Column([
            ft.Text("¿Estás seguro de que quieres borrar esto?"),
            ft.Divider(),
            # El campo PIN solo se ve si NO eres admin
            campo_pin_borrar
        ], height=150, tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_borrar)),
            ft.ElevatedButton("BORRAR AHORA", on_click=confirmar_borrado_click, bgcolor="red", color="white")
        ]
    )

    def abrir_menu_borrar(clave, item):
        # Guardamos la intención de borrar en el estado global
        estado["borrar_clave"] = clave
        estado["borrar_id"] = item.get("id")
        
        # Preparamos el diálogo
        campo_pin_borrar.value = ""
        campo_pin_borrar.error_text = None
        # Si ya es admin, ocultamos el campo PIN para que sea más rápido
        campo_pin_borrar.visible = not estado["admin"]
        
        page.open(dlg_borrar)

    # --- OTROS DIÁLOGOS (Login Admin Global) ---
    campo_pin_global = ft.TextField(label="PIN", password=True, text_align="center")
    def login_admin_global(e):
        if campo_pin_global.value == "1969":
            estado["admin"] = True
            actualizar_candado()
            page.close(dlg_admin)
            page.open(ft.SnackBar(ft.Text("Modo Admin Activado"), bgcolor="green"))
        else:
            campo_pin_global.error_text = "Mal"
            campo_pin_global.update()

    dlg_admin = ft.AlertDialog(
        title=ft.Text("Acceso Admin"),
        content=campo_pin_global,
        actions=[ft.ElevatedButton("Entrar", on_click=login_admin_global)]
    )

    def toggle_admin(e):
        if estado["admin"]:
            estado["admin"] = False
            actualizar_candado()
            page.open(ft.SnackBar(ft.Text("Sesión cerrada"), bgcolor="orange"))
        else:
            page.open(dlg_admin)

    def actualizar_candado():
        btn_lock.icon = "lock_open" if estado["admin"] else "lock_outline"
        btn_lock.icon_color = "yellow" if estado["admin"] else "white"
        page.update()

    btn_lock = ft.IconButton(icon="lock_outline", icon_color="white", on_click=toggle_admin)

    # --- FORMULARIO Y EDICIÓN ---
    # (Misma lógica de antes)
    txt_titulo_form = ft.Text("Nuevo", size=24, weight="bold", color="#388E3C")
    txt_nombre = ft.TextField(label="Nombre", bgcolor="#F5F5F5", color="black")
    txt_desc = ft.TextField(label="Descripción", bgcolor="#F5F5F5", color="black")
    txt_tag = ft.TextField(label="Etiqueta", bgcolor="#F5F5F5", color="black")
    txt_img = ft.TextField(label="URL Imagen", bgcolor="#F5F5F5", color="black", icon="image")
    txt_vid = ft.TextField(label="URL Enlace", bgcolor="#F5F5F5", color="black", icon="link")
    txt_cont = ft.TextField(label="Detalles", multiline=True, min_lines=5, bgcolor="#F5F5F5", color="black")

    def abrir_formulario(item=None):
        # Si item existe, es editar. Si no, es nuevo.
        es_editar = item is not None
        txt_titulo_form.value = "Editar" if es_editar else "Nuevo"
        
        txt_nombre.value = item["titulo"] if es_editar else ""
        txt_desc.value = item["desc"] if es_editar else ""
        txt_tag.value = item["tag"] if es_editar else ""
        txt_img.value = item["imagen"] if es_editar else ""
        txt_vid.value = item["video"] if es_editar else ""
        txt_cont.value = item["contenido"] if es_editar else ""
        
        estado["id_editar"] = item["id"] if es_editar else None
        
        imagen_fondo.visible = False
        contenedor_contenido.bgcolor = "#F5F5F5"
        contenedor_contenido.alignment = ft.alignment.top_center
        contenedor_contenido.content = vista_formulario
        btn_add_top.visible = False
        page.update()

    def click_editar(item):
        # Solo permite editar si eres admin o conoces el PIN
        if estado["admin"]:
            abrir_formulario(item)
        else:
            # Reutilizamos el dialogo de borrar para pedir PIN, un truco rápido
            # Pero mejor abrir el login global primero
            page.open(ft.SnackBar(ft.Text("Pulsa el candado arriba para identificarte primero."), bgcolor="blue"))

    def guardar(e):
        if not txt_nombre.value: return
        datos = {"titulo": txt_nombre.value, "desc": txt_desc.value, "tag": txt_tag.value, "imagen": txt_img.value, "video": txt_vid.value, "contenido": txt_cont.value}
        sec = estado["seccion_actual"]
        target_db = "recetas" if sec == 1 else "restaurantes" if sec == 2 else "productos" if sec == 3 else None
        
        if target_db:
            if estado["id_editar"]:
                # Editar
                for i, it in enumerate(db[target_db]):
                    if it["id"] == estado["id_editar"]:
                        datos["id"] = estado["id_editar"]
                        db[target_db][i] = datos
                        break
            else:
                # Nuevo
                datos["id"] = str(uuid.uuid4())
                db[target_db].append(datos)
            
            sincronizar_cambios(target_db)
            page.open(ft.SnackBar(ft.Text("Guardado"), bgcolor="green"))
            mostrar_seccion(sec)

    def cancelar(e): mostrar_seccion(estado["seccion_actual"])
    def archivo_seleccionado(e: ft.FilePickerResultEvent):
        if e.files:
            txt_img.value = e.files[0].path
            txt_img.update()
            page.open(ft.SnackBar(ft.Text("Imagen OK"), bgcolor="green"))

    picker = ft.FilePicker(on_result=archivo_seleccionado)
    page.overlay.append(picker)

    vista_formulario = ft.Container(
        bgcolor="white", padding=20, width=340, border_radius=15, alignment=ft.alignment.top_center, 
        content=ft.Column([
            txt_titulo_form, ft.Divider(), txt_nombre, txt_desc, txt_tag, ft.Divider(),
            ft.Row([txt_img, ft.IconButton("photo_library", icon_color="#388E3C", on_click=lambda _: picker.pick_files())]),
            txt_vid, txt_cont, ft.Container(height=20),
            ft.Row([ft.ElevatedButton("Cancelar", on_click=cancelar), ft.ElevatedButton("GUARDAR", on_click=guardar, bgcolor="#388E3C", color="white")], alignment="center"),
            ft.Container(height=30)
        ], scroll="auto")
    )
    
    btn_add_top = ft.IconButton(icon="add_circle", icon_color="white", icon_size=30, on_click=lambda e: abrir_formulario(None), visible=False)

    # --- LISTA VISUAL ---
    def obtener_lista_visual(clave_db, color_tag, icono_defecto):
        columna = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        datos = db[clave_db]
        
        # Botón Refrescar Nube
        if USAR_NUBE:
            columna.controls.append(ft.TextButton("Sincronizar Nube", icon="cloud_sync", on_click=lambda e: [db.update({k: cargar_datos_nube(k) for k in db}), mostrar_seccion(estado["seccion_actual"])]))

        if not datos:
            columna.controls.append(ft.Container(alignment=ft.alignment.center, padding=20, content=ft.Container(padding=30, width=320, bgcolor="#99FFFFFF", border_radius=15, content=ft.Column([ft.Icon("info", size=40, color="grey"), ft.Text("Lista vacía", color="grey")], horizontal_alignment="center"))))
        else:
            for item in datos:
                # Componentes tarjeta
                src_img = item.get("imagen") or IMAGEN_DEFAULT
                img = ft.Container(width=110, height=110, border_radius=ft.border_radius.only(top_left=10, bottom_left=10), bgcolor="#EEE", content=ft.Image(src=src_img, fit=ft.ImageFit.COVER, error_content=ft.Icon(icono_defecto)))
                
                extras = ft.Container()
                if item.get("contenido"):
                    extras = ft.ExpansionTile(title=ft.Text("Ver más", size=12, color="blue"), tile_padding=0, controls=[ft.Container(padding=ft.padding.only(bottom=10), content=ft.Text(item["contenido"], size=12, color="black"))])
                
                link = ft.Container()
                if item.get("video"):
                    lbl = item["video"].replace("https://","")[:15]+"..."
                    link = ft.TextButton(lbl, icon="link", on_click=lambda e, u=item["video"]: page.launch_url(u))

                # Botón borrar llama al menú unificado
                btn_del = ft.IconButton(icon="delete", icon_color="red", on_click=lambda e, k=clave_db, i=item: abrir_menu_borrar(k, i))
                btn_edit = ft.IconButton(icon="edit", icon_color="blue", on_click=lambda e, i=item: click_editar(i))

                info = ft.Container(expand=True, padding=10, content=ft.Column([
                    ft.Text(item["titulo"], weight="bold", size=16),
                    ft.Text(item["desc"], size=12, color="grey"),
                    extras,
                    ft.Row([ft.Container(content=ft.Text(item["tag"], size=10, color="white"), bgcolor=color_tag, padding=4, border_radius=4), ft.Container(expand=True), link, btn_edit, btn_del], spacing=0, alignment="end")
                ], spacing=2))
                
                columna.controls.append(ft.Card(elevation=3, color="white", margin=ft.margin.symmetric(horizontal=10), content=ft.Container(content=ft.Row([img, info], spacing=0, vertical_alignment="start"))))
        return columna

    def mostrar_seccion(indice):
        estado["seccion_actual"] = indice
        btn_add_top.visible = (indice != 0)
        imagen_fondo.visible = (indice == 0)
        contenedor_contenido.bgcolor = "#F5F5F5" if indice != 0 else None
        
        if indice == 0:
            contenedor_contenido.alignment = ft.alignment.center
            contenedor_contenido.content = ft.Container() 
            titulo.value = "Vegan Green"
        else:
            contenedor_contenido.alignment = ft.alignment.top_center
            if indice == 1: contenedor_contenido.content = obtener_lista_visual("recetas", "#E65100", "restaurant")
            elif indice == 2: contenedor_contenido.content = obtener_lista_visual("restaurantes", "#1B5E20", "storefront")
            elif indice == 3: contenedor_contenido.content = obtener_lista_visual("productos", "#01579B", "shopping_cart")
        page.update()

    def cambiar_tab(e): mostrar_seccion(e.control.selected_index)

    nav = ft.NavigationBar(selected_index=0, on_change=cambiar_tab, destinations=[ft.NavigationBarDestination(icon="home", label="Inicio"), ft.NavigationBarDestination(icon="menu_book", label="Recetas"), ft.NavigationBarDestination(icon="store", label="Sitios"), ft.NavigationBarDestination(icon="shopping_bag", label="Productos")])
    titulo = ft.Text("Vegan Green", color="white", size=20, weight="bold")
    app_bar = ft.Container(padding=15, bgcolor="#388E3C", content=ft.Row([ft.Row([ft.Icon("eco", color="white"), titulo]), ft.Row([btn_add_top, btn_lock])], alignment="spaceBetween"))
    layout_principal = ft.Column(spacing=0, expand=True, controls=[app_bar, ft.Container(content=stack_principal, expand=True), nav])
    page.add(layout_principal)

ft.app(target=main, assets_dir="assets")
