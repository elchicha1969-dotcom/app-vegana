import flet as ft
import uuid 

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
    
    # --- FIREBASE ---
    FIREBASE_URL = "" 
    USAR_NUBE = bool(FIREBASE_URL)

    # --- GESTIÓN DE DATOS ---
    def cargar_datos_nube(coleccion):
        # (Código de nube omitido por brevedad, usa lógica local si está vacío)
        return []

    def guardar_datos_nube(coleccion, datos_lista):
        pass

    def cargar_y_sanear(key):
        # 1. Cargar datos
        try:
            datos = page.client_storage.get(key)
            if datos is None: return []
        except: return []

        lista_saneada = []
        cambios = False
        
        # 2. Sanear (Asegurar que todos tengan ID)
        for item in datos:
            if not isinstance(item, dict): continue
            
            # Si no tiene ID, le ponemos uno
            if "id" not in item:
                item["id"] = str(uuid.uuid4())
                cambios = True
                
            lista_saneada.append(item)
        
        # 3. Guardar correcciones
        if cambios: 
            page.client_storage.set(key, lista_saneada)
            
        return lista_saneada

    # Cargamos datos al inicio
    db = {
        "recetas": cargar_y_sanear("mis_recetas"),
        "restaurantes": cargar_y_sanear("mis_restaurantes"),
        "productos": cargar_y_sanear("mis_productos")
    }
    
    estado = {"seccion_actual": 0, "admin": False, "id_editar": None} 

    # --- CAPAS DE FONDO ---
    imagen_fondo = ft.Image(src=FONDO_APP, fit=ft.ImageFit.COVER, opacity=1.0, expand=True, error_content=ft.Container(bgcolor="#388E3C"))
    contenedor_contenido = ft.Container(expand=True, padding=10, alignment=ft.alignment.center)
    stack_principal = ft.Stack(controls=[imagen_fondo, contenedor_contenido], expand=True)

    def sincronizar_cambios(clave_db):
        page.client_storage.set(f"mis_{clave_db}", db[clave_db])

    # --- LÓGICA DE BORRADO (INFALIBLE) ---
    def ejecutar_borrado(clave_db, id_objetivo):
        # 1. Obtenemos la lista actual
        lista_actual = db[clave_db]
        
        # 2. FILTRO: Nos quedamos con todo lo que NO sea ese ID
        # Esta es la forma más segura de borrar
        lista_nueva = [x for x in lista_actual if x.get("id") != id_objetivo]
        
        # 3. Comprobamos si borró algo
        if len(lista_nueva) < len(lista_actual):
            db[clave_db] = lista_nueva # Actualizamos memoria
            sincronizar_cambios(clave_db) # Guardamos en disco
            page.open(ft.SnackBar(ft.Text("¡Eliminado correctamente!"), bgcolor="green"))
        else:
            page.open(ft.SnackBar(ft.Text("Error: No se encontró el ID."), bgcolor="red"))
        
        # 4. Refrescar visualmente
        mostrar_seccion(estado["seccion_actual"])
        page.update()

    # --- DIÁLOGOS Y SEGURIDAD ---
    
    def solicitar_borrado(clave_db, id_item):
        if estado["admin"]:
            # Si es admin, confirmación directa
            abrir_dialogo_confirmar(clave_db, id_item)
        else:
            # Si no, pedir PIN
            abrir_login_pin(lambda: abrir_dialogo_confirmar(clave_db, id_item))

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

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Seguridad"),
            content=ft.Column([ft.Text("Introduce PIN de administrador:"), campo_pin], height=100, tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg)),
                ft.ElevatedButton("ENTRAR", on_click=validar)
            ]
        )
        page.open(dlg)

    def abrir_dialogo_confirmar(clave_db, id_item):
        def confirmar(e):
            page.close(dlg_conf)
            ejecutar_borrado(clave_db, id_item)

        dlg_conf = ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Borrar definitivamente?"),
            content=ft.Text("Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_conf)),
                ft.ElevatedButton("SÍ, BORRAR", on_click=confirmar, bgcolor="red", color="white")
            ]
        )
        page.open(dlg_conf)

    # --- ROUTERS ---
    def click_papelera(clave, item):
        # Pasamos el ID, no el objeto entero
        solicitar_borrado(clave, item.get("id"))

    def click_editar(item):
        if estado["admin"]: abrir_formulario_edicion(item)
        else: abrir_login_pin(lambda: abrir_formulario_edicion(item))

    # --- FORMULARIO ---
    txt_titulo_form = ft.Text("Nuevo", size=24, weight="bold", color="#388E3C")
    txt_nombre = ft.TextField(label="Nombre", bgcolor="#F5F5F5", color="black")
    txt_desc = ft.TextField(label="Descripción", bgcolor="#F5F5F5", color="black")
    txt_tag = ft.TextField(label="Etiqueta", bgcolor="#F5F5F5", color="black")
    txt_img = ft.TextField(label="URL Imagen", bgcolor="#F5F5F5", color="black", icon="image")
    txt_vid = ft.TextField(label="URL Enlace", bgcolor="#F5F5F5", color="black", icon="link")
    txt_cont = ft.TextField(label="Detalles", multiline=True, min_lines=5, bgcolor="#F5F5F5", color="black")

    def ajustar_etiquetas():
        if estado["seccion_actual"] == 2:
            txt_desc.label = "Lugar / Dirección"
            txt_desc.icon = "map" 
        else:
            txt_desc.label = "Descripción"
            txt_desc.icon = "description"

    def abrir_formulario_edicion(item):
        ajustar_etiquetas()
        txt_titulo_form.value = "Editar"
        txt_nombre.value = item.get("titulo", "")
        txt_desc.value = item.get("desc", "")
        txt_tag.value = item.get("tag", "")
        txt_img.value = item.get("imagen", "")
        txt_vid.value = item.get("video", "")
        txt_cont.value = item.get("contenido", "")
        estado["id_editar"] = item.get("id")
        ir_formulario()

    def abrir_formulario_nuevo(e):
        ajustar_etiquetas()
        txt_titulo_form.value = "Nuevo"
        for i in [txt_nombre, txt_desc, txt_tag, txt_img, txt_vid, txt_cont]: i.value = ""
        estado["id_editar"] = None
        ir_formulario()
    
    def archivo_seleccionado(e: ft.FilePickerResultEvent):
        if e.files:
            txt_img.value = e.files[0].path
            txt_img.update()
            page.open(ft.SnackBar(ft.Text("Imagen OK"), bgcolor="green"))
    picker = ft.FilePicker(on_result=archivo_seleccionado)
    page.overlay.append(picker)

    def guardar(e):
        if not txt_nombre.value: return
        datos = {"titulo": txt_nombre.value, "desc": txt_desc.value, "tag": txt_tag.value, "imagen": txt_img.value, "video": txt_vid.value, "contenido": txt_cont.value}
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
            page.open(ft.SnackBar(ft.Text("Guardado"), bgcolor="green"))
            mostrar_seccion(sec)

    vista_form = ft.Container(bgcolor="white", padding=20, width=340, border_radius=15, alignment=ft.alignment.top_center, content=ft.Column([
        txt_titulo_form, ft.Divider(), txt_nombre, txt_desc, txt_tag, ft.Divider(),
        ft.Row([txt_img, ft.IconButton("photo_library", icon_color="#388E3C", on_click=lambda _: picker.pick_files())]),
        txt_vid, txt_cont, ft.Container(height=20),
        ft.Row([ft.ElevatedButton("Cancelar", on_click=lambda e: mostrar_seccion(estado["seccion_actual"])), ft.ElevatedButton("GUARDAR", on_click=guardar, bgcolor="#388E3C", color="white")], alignment="center"),
        ft.Container(height=30)
    ], scroll="auto"))

    def ir_formulario():
        imagen_fondo.visible = False 
        contenedor_contenido.bgcolor = "#F5F5F5"
        contenedor_contenido.alignment = ft.alignment.top_center 
        contenedor_contenido.content = vista_form
        btn_add_top.visible = False 
        page.update()

    # --- ADMIN Y UI ---
    def toggle_admin(e):
        if estado["admin"]:
            estado["admin"] = False
            actualizar_candado()
            page.open(ft.SnackBar(ft.Text("Sesión cerrada."), bgcolor="orange"))
        else:
            abrir_login_pin(lambda: page.open(ft.SnackBar(ft.Text("¡Admin Activo!"), bgcolor="green")))
    
    def actualizar_candado():
        btn_lock.icon = "lock_open" if estado["admin"] else "lock_outline"
        btn_lock.icon_color = "yellow" if estado["admin"] else "white"
        page.update()

    btn_lock = ft.IconButton(icon="lock_outline", icon_color="white", on_click=toggle_admin)
    btn_add_top = ft.IconButton(icon="add_circle", icon_color="white", icon_size=30, on_click=abrir_formulario_nuevo, visible=False)

    # --- LISTA VISUAL ---
    def obtener_lista_visual(clave_db, color_tag, icono_defecto):
        columna = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        datos = db[clave_db]
        
        if not datos:
            columna.controls.append(ft.Container(alignment=ft.alignment.center, padding=20, content=ft.Container(padding=30, width=320, bgcolor="#99FFFFFF", border_radius=15, content=ft.Column([ft.Icon("info", size=40, color="grey"), ft.Text("Lista vacía", color="grey"), ft.Text("Usa (+) arriba.", size=12)], horizontal_alignment="center"))))
        else:
            for item in datos:
                src = item.get("imagen") or IMAGEN_DEFAULT
                tiene_imagen = bool(item.get("imagen"))
                
                # Stack de la tarjeta para fondo de imagen
                stack_card = []
                
                # Info a mostrar
                color_texto = "white" if tiene_imagen else "black"
                color_icono = "white" if tiene_imagen else "#388E3C"
                bg_overlay = "#99000000" if tiene_imagen else "#FFFFFF"

                extras = ft.Container()
                if item.get("contenido"):
                    extras = ft.ExpansionTile(title=ft.Text("Ver más", size=12, color="blue"), tile_padding=0, controls=[ft.Container(padding=ft.padding.only(bottom=10), content=ft.Text(item["contenido"], size=12, color=color_texto))])
                
                link_btn = ft.Container()
                if item.get("video"):
                    lbl = item["video"].replace("https://","")[:15]+"..."
                    link_btn = ft.TextButton(lbl, icon="link", icon_color="blue", on_click=lambda e, u=item["video"]: page.launch_url(u))
                    link_btn.content.style = ft.ButtonStyle(color=color_texto)

                # Pasamos el item completo a las funciones de click
                info_col = ft.Column([
                    ft.Row([ft.Icon(icono_defecto, size=24, color=color_icono), ft.Text(item["titulo"], weight="bold", size=20, font_family="Kanit", color=color_texto, expand=True)], alignment="spaceBetween"),
                    ft.Text(item["desc"], size=13, color=color_texto),
                    ft.Divider(height=10, color="white24" if tiene_imagen else "black12"),
                    extras,
                    ft.Row([
                        ft.Container(content=ft.Text(item["tag"], size=10, color="white"), bgcolor=color_tag, padding=4, border_radius=4),
                        ft.Container(expand=True), link_btn,
                        ft.IconButton("edit", icon_color=color_icono, icon_size=20, on_click=lambda e, i=item: click_editar(i)),
                        ft.IconButton("delete", icon_color="red", icon_size=20, on_click=lambda e, k=clave_db, i=item: click_papelera(k, i))
                    ], spacing=0, alignment="end")
                ])
                
                if tiene_imagen:
                    stack_card.append(ft.Image(src=src, fit=ft.ImageFit.COVER, opacity=1.0, expand=True, error_content=ft.Container(bgcolor="#333333")))
                
                stack_card.append(ft.Container(bgcolor=bg_overlay, padding=15, content=info_col, expand=True))

                tarjeta = ft.Card(elevation=5, color="white", margin=ft.margin.symmetric(horizontal=10), clip_behavior=ft.ClipBehavior.ANTI_ALIAS, content=ft.Container(height=300, content=ft.Stack(controls=stack_card)))
                columna.controls.append(tarjeta)
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
