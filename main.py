import flet as ft
import uuid
import json
import urllib.request
import os
import sys

# --- DETECTOR DE ARCHIVOS CONFLICTIVOS ---
# Esto te avisará si tienes un archivo que está rompiendo la app
if os.path.exists("flet.py"):
    print("\n⚠️ ¡ATENCIÓN! TIENES UN ARCHIVO LLAMADO 'flet.py' ⚠️")
    print("Este archivo confunde a Python. Por favor, cámbiale el nombre o bórralo.")
    print("Luego vuelve a ejecutar este programa.\n")

def main(page: ft.Page):
    # --- CONFIGURACIÓN ---
    page.title = "Vegan Green"
    page.theme_mode = "light"
    page.padding = 0 
    page.bgcolor = "#202020" 
    page.theme = ft.Theme(color_scheme_seed="#388E3C")

    # --- IMÁGENES ---
    FONDO_APP = "/portada.jpg" 
    IMAGEN_DEFAULT = "https://upload.wikimedia.org/wikipedia/commons/1/14/No_Image_Available.jpg"
    
    # --- FIREBASE ---
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
        if USAR_NUBE:
            datos_nube = cargar_datos_nube(key.replace("mis_", ""))
            if datos_nube:
                page.client_storage.set(key, datos_nube)
                return datos_nube
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
    
    estado = {"seccion_actual": 0, "admin": False, "id_editar": None} 

    # --- CAPAS DE FONDO (STACK) ---
    fondo_img = ft.Image(src=FONDO_APP, fit=ft.ImageFit.COVER, opacity=1.0, expand=True, error_content=ft.Container(bgcolor="#388E3C"))
    contenedor_contenido = ft.Container(expand=True, padding=10, alignment=ft.alignment.center)
    stack_principal = ft.Stack(controls=[fondo_img, contenedor_contenido], expand=True)

    def sincronizar_cambios(clave_db):
        page.client_storage.set(f"mis_{clave_db}", db[clave_db])
        if USAR_NUBE: guardar_datos_nube(clave_db, db[clave_db])

    # --- LÓGICA DE BORRADO ---
    def ejecutar_borrado(clave, id_objetivo):
        lista = db[clave]
        nueva_lista = [x for x in lista if x.get("id") != id_objetivo]
        
        if len(nueva_lista) < len(lista):
            db[clave] = nueva_lista
            sincronizar_cambios(clave)
            mostrar_mensaje("¡Eliminado!", "green")
            mostrar_seccion(estado["seccion_actual"])
        else:
            mostrar_mensaje("Error: No encontrado", "red")
        page.update()

    def mostrar_mensaje(texto, color):
        try: page.open(ft.SnackBar(ft.Text(texto), bgcolor=color))
        except: pass

    # --- DIÁLOGOS ---
    def abrir_login_pin(callback_exito):
        campo_pin = ft.TextField(label="Introduce PIN", password=True, text_align="center", autofocus=True)
        def validar(e):
            if campo_pin.value == "1969":
                estado["admin"] = True
                actualizar_candado()
                page.close(dlg)
                callback_exito()
            else:
                campo_pin.error_text = "Incorrecto"
                campo_pin.update()
        dlg = ft.AlertDialog(title=ft.Text("Modo Admin"), content=ft.Column([ft.Text("PIN:"), campo_pin], height=100, tight=True), actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg)), ft.ElevatedButton("ENTRAR", on_click=validar)])
        page.open(dlg)

    def confirmar_borrado(clave, item):
        def si_borrar(e):
            page.close(dlg)
            ejecutar_borrado(clave, item.get("id"))
        dlg = ft.AlertDialog(title=ft.Text("¿Borrar?"), content=ft.Text(f"Eliminar: {item.get('titulo')}"), actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg)), ft.ElevatedButton("BORRAR", on_click=si_borrar, bgcolor="red", color="white")])
        page.open(dlg)

    def click_papelera(clave, item):
        if estado["admin"]: confirmar_borrado(clave, item)
        else: abrir_login_pin(lambda: confirmar_borrado(clave, item))

    def click_editar(item):
        if estado["admin"]: abrir_formulario_edicion(item)
        else: abrir_login_pin(lambda: abrir_formulario_edicion(item))

    # --- FORMULARIO ---
    txt_titulo = ft.Text("Nuevo", size=24, weight="bold", color="#388E3C")
    input_nombre = ft.TextField(label="Nombre", bgcolor="#F5F5F5", color="black")
    input_desc = ft.TextField(label="Descripción", bgcolor="#F5F5F5", color="black")
    input_tag = ft.TextField(label="Etiqueta", bgcolor="#F5F5F5", color="black")
    input_img = ft.TextField(label="URL Imagen", bgcolor="#F5F5F5", color="black", icon="image")
    input_vid = ft.TextField(label="URL Enlace", bgcolor="#F5F5F5", color="black", icon="link")
    input_cont = ft.TextField(label="Detalles", multiline=True, min_lines=5, bgcolor="#F5F5F5", color="black")

    def ajustar_etiquetas():
        # Usamos texto simple ("map", "description") para evitar errores de atributos
        if estado["seccion_actual"] == 2:
            input_desc.label = "Lugar / Dirección"
            input_desc.icon = "map"
        else:
            input_desc.label = "Descripción"
            input_desc.icon = "description"

    def abrir_formulario_edicion(item):
        ajustar_etiquetas()
        txt_titulo.value = "Editar"
        input_nombre.value = item.get("titulo", "")
        input_desc.value = item.get("desc", "")
        input_tag.value = item.get("tag", "")
        input_img.value = item.get("imagen", "")
        input_vid.value = item.get("video", "")
        input_cont.value = item.get("contenido", "")
        estado["id_editar"] = item.get("id")
        ir_formulario()

    def abrir_formulario_nuevo(e):
        ajustar_etiquetas()
        txt_titulo.value = "Nuevo"
        for i in [input_nombre, input_desc, input_tag, input_img, input_vid, input_cont]: i.value = ""
        estado["id_editar"] = None
        ir_formulario()
    
    def archivo_seleccionado(e: ft.FilePickerResultEvent):
        if e.files:
            input_img.value = e.files[0].path
            input_img.update()
            mostrar_mensaje("Imagen cargada", "green")
    picker = ft.FilePicker(on_result=archivo_seleccionado)
    page.overlay.append(picker)

    def guardar(e):
        if not input_nombre.value: return
        datos = {"titulo": input_nombre.value, "desc": input_desc.value, "tag": input_tag.value, "imagen": input_img.value, "video": input_vid.value, "contenido": input_cont.value}
        sec = estado["seccion_actual"]
        target = "recetas" if sec == 1 else "restaurantes" if sec == 2 else "productos" if sec == 3 else None
        
        if target:
            if estado["id_editar"]:
                for i, it in enumerate(db[target]):
                    if it["id"] == estado["id_editar"]:
                        datos["id"] = estado["id_editar"]
                        db[target][i] = datos
                        break
            else:
                datos["id"] = str(uuid.uuid4())
                db[target].append(datos)
            sincronizar_cambios(target)
            mostrar_mensaje("Guardado", "green")
            mostrar_seccion(sec)

    vista_form = ft.Container(bgcolor="white", padding=20, width=340, border_radius=15, alignment=ft.alignment.top_center, content=ft.Column([
        txt_titulo, ft.Divider(), input_nombre, input_desc, input_tag, ft.Divider(),
        ft.Row([input_img, ft.IconButton("photo_library", icon_color="#388E3C", on_click=lambda _: picker.pick_files())]),
        input_vid, input_cont, ft.Container(height=20),
        ft.Row([ft.ElevatedButton("Cancelar", on_click=lambda e: mostrar_seccion(estado["seccion_actual"])), ft.ElevatedButton("GUARDAR", on_click=guardar, bgcolor="#388E3C", color="white")], alignment="center"),
        ft.Container(height=30)
    ], scroll="auto"))

    def ir_formulario():
        fondo_img.visible = False
        contenedor_contenido.bgcolor = "#F5F5F5"
        contenedor_contenido.alignment = ft.alignment.top_center
        contenedor_contenido.content = vista_form
        btn_add.visible = False
        page.update()

    # --- ADMIN Y UI ---
    def toggle_admin(e):
        if estado["admin"]:
            estado["admin"] = False
            actualizar_candado()
            mostrar_mensaje("Sesión cerrada", "orange")
        else:
            abrir_login_pin(lambda: mostrar_mensaje("¡Admin Activo!", "green"))
    
    def actualizar_candado():
        btn_lock.icon = "lock_open" if estado["admin"] else "lock_outline"
        btn_lock.icon_color = "yellow" if estado["admin"] else "white"
        page.update()

    btn_lock = ft.IconButton(icon="lock_outline", icon_color="white", on_click=toggle_admin)
    btn_add = ft.IconButton(icon="add_circle", icon_color="white", icon_size=30, on_click=abrir_formulario_nuevo, visible=False)

    # --- LISTA VISUAL (DISEÑO STACK) ---
    def obtener_lista(clave_db, color_tag, icono):
        col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, horizontal_alignment="center")
        datos = db[clave_db]
        
        if USAR_NUBE:
            col.controls.append(ft.TextButton("Refrescar Nube", icon="cloud_sync", on_click=lambda e: [db.update({k: cargar_datos_nube(k) for k in db}), mostrar_seccion(estado["seccion_actual"])]))

        if not datos:
            col.controls.append(ft.Container(padding=20, content=ft.Column([ft.Icon("info", size=40, color="grey"), ft.Text("Lista vacía", color="grey")], horizontal_alignment="center")))
        else:
            for item in datos:
                src = item.get("imagen") or IMAGEN_DEFAULT
                tiene_imagen = bool(item.get("imagen"))
                
                # Colores adaptables
                color_texto = "white" if tiene_imagen else "black"
                color_icono = "white" if tiene_imagen else "#388E3C"
                color_desc = "#DDDDDD" if tiene_imagen else "#616161"
                bg_overlay = "#99000000" if tiene_imagen else "#FFFFFF"

                # Contenido
                extras = ft.Container()
                if item.get("contenido"):
                    # Usamos tile_padding=0 directamente (evitamos ft.padding.zero si da error)
                    extras = ft.ExpansionTile(title=ft.Text("Ver más", size=12, color="blue"), tile_padding=0, controls=[ft.Container(padding=ft.padding.only(bottom=10), content=ft.Text(item["contenido"], size=12, color=color_texto))])
                
                link_btn = ft.Container()
                if item.get("video"):
                    lbl = item["video"].replace("https://","")[:15]+"..."
                    link_btn = ft.TextButton(lbl, icon="link", icon_color=color_icono, on_click=lambda e, u=item["video"]: page.launch_url(u))
                    link_btn.content.style = ft.ButtonStyle(color=color_texto)
                
                actions = ft.Row([
                    ft.Container(content=ft.Text(item["tag"], size=10, color="white"), bgcolor=color_tag, padding=4, border_radius=4),
                    ft.Container(expand=True), link_btn,
                    ft.IconButton("edit", icon_color=color_icono, icon_size=20, on_click=lambda e, i=item: click_editar(i)),
                    ft.IconButton("delete", icon_color="red", icon_size=20, on_click=lambda e, k=clave_db, i=item: click_papelera(k, i))
                ], spacing=0, alignment="end")

                info = ft.Column([
                    ft.Row([ft.Icon(icono, size=24, color=color_icono), ft.Text(item["titulo"], weight="bold", size=20, font_family="Kanit", color=color_texto, expand=True)], alignment="spaceBetween"),
                    ft.Text(item["desc"], size=13, color=color_desc),
                    ft.Divider(height=10, color="white24" if tiene_imagen else "black12"),
                    extras, actions
                ])

                # --- STACK (Fondo + Contenido) ---
                stack_card = []
                if tiene_imagen:
                    stack_card.append(ft.Image(src=src, fit=ft.ImageFit.COVER, opacity=1.0, expand=True, error_content=ft.Container(bgcolor="#333333")))
                
                stack_card.append(ft.Container(bgcolor=bg_overlay, padding=15, content=info, expand=True))

                tarjeta = ft.Card(elevation=5, color="white", margin=ft.margin.symmetric(horizontal=10), clip_behavior=ft.ClipBehavior.ANTI_ALIAS, content=ft.Container(height=300, content=ft.Stack(controls=stack_card)))
                col.controls.append(tarjeta)
        return col

    def mostrar_seccion(idx):
        estado["seccion_actual"] = idx
        btn_add.visible = (idx != 0)
        fondo_img.visible = (idx == 0)
        contenedor_contenido.bgcolor = "#F5F5F5" if idx != 0 else None
        
        if idx == 0:
            contenedor_contenido.alignment = ft.alignment.center
            contenedor_contenido.content = ft.Container()
            titulo.value = "Vegan Green"
        else:
            contenedor_contenido.alignment = ft.alignment.top_center
            if idx == 1: contenedor_contenido.content = obtener_lista("recetas", "#E65100", "restaurant")
            elif idx == 2: contenedor_contenido.content = obtener_lista("restaurantes", "#1B5E20", "storefront")
            elif idx == 3: contenedor_contenido.content = obtener_lista("productos", "#01579B", "shopping_cart")
        page.update()

    titulo = ft.Text("Vegan Green", color="white", size=20, weight="bold")
    nav = ft.NavigationBar(selected_index=0, on_change=lambda e: mostrar_seccion(e.control.selected_index), destinations=[
        ft.NavigationBarDestination(icon="home", label="Inicio"),
        ft.NavigationBarDestination(icon="menu_book", label="Recetas"),
        ft.NavigationBarDestination(icon="store", label="Sitios"),
        ft.NavigationBarDestination(icon="shopping_bag", label="Productos")
    ])
    
    app_bar = ft.Container(padding=15, bgcolor="#388E3C", content=ft.Row([ft.Row([ft.Icon("eco", color="white"), titulo]), ft.Row([btn_add, btn_lock])], alignment="spaceBetween"))
    
    layout = ft.Column(spacing=0, expand=True, controls=[app_bar, ft.Container(content=stack_principal, expand=True), nav])
    page.add(layout)

ft.app(target=main, assets_dir="assets")
