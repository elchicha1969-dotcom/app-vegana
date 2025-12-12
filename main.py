import flet as ft
import uuid 

def main(page: ft.Page):
    # --- CONFIGURACIÓN BÁSICA ---
    page.title = "Vida Vegana"
    page.theme_mode = "light"
    page.padding = 0 
    page.bgcolor = "#202020" 
    page.theme = ft.Theme(color_scheme_seed="#388E3C")

    # --- FUENTES ---
    page.fonts = {
        "Kanit": "https://raw.githubusercontent.com/google/fonts/master/ofl/kanit/Kanit-Bold.ttf"
    }

    # --- IMAGEN DE FONDO (PORTADA) ---
    # Opción 1: Internet (Garantiza que se vea algo)
    FONDO_APP = "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?auto=format&fit=crop&w=640&q=80"
    
    # Opción 2: Local (Descomenta la línea de abajo si usas la carpeta assets)
    # FONDO_APP = "/portada.jpg" 

    # --- GESTIÓN DE DATOS ---
    def cargar_y_sanear(key):
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
    estado = {"seccion_actual": 0, "admin": False, "id_editar": None} 

    # --- CAPAS DE FONDO ---
    imagen_fondo = ft.Image(
        src=FONDO_APP, 
        fit=ft.ImageFit.COVER, 
        opacity=1.0, 
        expand=True,
        error_content=ft.Container(bgcolor="#2E7D32") 
    )
    
    contenedor_contenido = ft.Container(expand=True, padding=10, alignment=ft.alignment.center)
    stack_principal = ft.Stack(controls=[imagen_fondo, contenedor_contenido], expand=True)

    # --- LÓGICA DE ACTUALIZACIÓN (EDITAR) ---
    def ejecutar_edicion(clave_db, id_item, nuevos_datos):
        lista = db[clave_db]
        encontrado = False
        for i, item in enumerate(lista):
            if item.get("id") == id_item:
                nuevos_datos["id"] = id_item
                lista[i] = nuevos_datos
                encontrado = True
                break
        
        if encontrado:
            page.client_storage.set(f"mis_{clave_db}", lista)
            page.open(ft.SnackBar(ft.Text("¡Artículo actualizado!"), bgcolor="blue"))
            cancelar_formulario(None) 
        else:
            page.open(ft.SnackBar(ft.Text("Error al editar."), bgcolor="red"))
        page.update()

    # --- LÓGICA DE BORRADO ---
    def ejecutar_borrado(clave, id_objetivo):
        lista_memoria = db[clave]
        lista_nueva = [x for x in lista_memoria if x.get("id") != id_objetivo]
        
        if len(lista_nueva) < len(lista_memoria):
            db[clave] = lista_nueva
            page.client_storage.set(f"mis_{clave}", lista_nueva)
            page.open(ft.SnackBar(ft.Text("¡Eliminado!"), bgcolor="green"))
            mostrar_seccion(estado["seccion_actual"])
        else:
            page.open(ft.SnackBar(ft.Text("Error al borrar."), bgcolor="red"))
        page.update()

    # --- DIÁLOGOS DE SEGURIDAD ---
    def solicitar_accion_protegida(accion_callback):
        if estado["admin"]:
            accion_callback()
        else:
            abrir_login_pin(accion_callback)

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
            title=ft.Text("Modo Admin"),
            content=ft.Column([ft.Text("PIN de administrador:"), campo_pin], height=100, tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg)),
                ft.ElevatedButton("ENTRAR", on_click=validar)
            ]
        )
        page.open(dlg)

    def abrir_dialogo_borrar_final(clave, item):
        def confirmar(e):
            page.close(dlg)
            ejecutar_borrado(clave, item.get("id"))

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Borrar?"),
            content=ft.Text(f"Eliminar: {item.get('titulo')}"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg)),
                ft.ElevatedButton("BORRAR", on_click=confirmar, bgcolor="red", color="white")
            ]
        )
        page.open(dlg)

    # --- ROUTERS ---
    def click_papelera(clave, item):
        solicitar_accion_protegida(lambda: abrir_dialogo_borrar_final(clave, item))

    def click_editar(item):
        solicitar_accion_protegida(lambda: abrir_formulario_edicion(item))

    # --- FORMULARIO ---
    txt_titulo_form = ft.Text("Nuevo", size=24, weight="bold", color="#388E3C")
    txt_nombre = ft.TextField(label="Nombre", bgcolor="#F5F5F5", color="black")
    
    # Campo dinámico
    txt_desc = ft.TextField(label="Descripción", bgcolor="#F5F5F5", color="black")
    
    txt_tag = ft.TextField(label="Etiqueta", bgcolor="#F5F5F5", color="black")
    txt_img = ft.TextField(label="URL Imagen", bgcolor="#F5F5F5", color="black", icon="image")
    txt_vid = ft.TextField(label="URL Enlace", bgcolor="#F5F5F5", color="black", icon="link")
    txt_cont = ft.TextField(label="Detalles", multiline=True, min_lines=5, bgcolor="#F5F5F5", color="black")

    def ajustar_etiquetas():
        # AQUÍ ESTABA EL ERROR: Usamos strings "map" y "description"
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
        for c in [txt_nombre, txt_desc, txt_tag, txt_img, txt_vid, txt_cont]: c.value = ""
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
        if not txt_nombre.value:
            txt_nombre.error_text = "!"
            page.update()
            return
        
        datos = {
            "titulo": txt_nombre.value, "desc": txt_desc.value, "tag": txt_tag.value,
            "imagen": txt_img.value, "video": txt_vid.value, "contenido": txt_cont.value
        }
        
        sec = estado["seccion_actual"]
        target_db = None
        if sec == 1: target_db = "recetas"
        elif sec == 2: target_db = "restaurantes"
        elif sec == 3: target_db = "productos"
        
        if target_db:
            if estado["id_editar"]:
                ejecutar_edicion(target_db, estado["id_editar"], datos)
            else:
                datos["id"] = str(uuid.uuid4())
                db[target_db].append(datos)
                page.client_storage.set(f"mis_{target_db}", db[target_db])
                page.open(ft.SnackBar(ft.Text("Guardado"), bgcolor="green"))
                cancelar_formulario(None)

    def cancelar_formulario(e):
        mostrar_seccion(estado["seccion_actual"])

    vista_formulario = ft.Container(
        bgcolor="white", padding=20, width=340, border_radius=15, alignment=ft.alignment.top_center, 
        content=ft.Column([
            txt_titulo_form, ft.Divider(), txt_nombre, txt_desc, txt_tag, ft.Divider(),
            ft.Row([txt_img, ft.IconButton("photo_library", icon_color="#388E3C", on_click=lambda _: picker.pick_files())]),
            txt_vid, txt_cont, ft.Container(height=20),
            ft.Row([
                ft.ElevatedButton("Cancelar", on_click=cancelar_formulario, bgcolor="grey", color="white"),
                ft.ElevatedButton("GUARDAR", on_click=guardar, bgcolor="#388E3C", color="white")
            ], alignment="center"),
            ft.Container(height=30)
        ], scroll="auto")
    )

    # --- NAVEGACIÓN ---
    def ir_formulario():
        imagen_fondo.visible = False 
        contenedor_contenido.bgcolor = "#F5F5F5"
        contenedor_contenido.alignment = ft.alignment.top_center 
        contenedor_contenido.content = vista_formulario
        btn_add_top.visible = False 
        page.update()

    # SISTEMA ADMIN
    def toggle_admin(e):
        if estado["admin"]:
            estado["admin"] = False
            actualizar_candado()
            page.open(ft.SnackBar(ft.Text("Sesión cerrada."), bgcolor="orange"))
        else:
            abrir_login_pin(lambda: page.open(ft.SnackBar(ft.Text("¡Admin Activo!"), bgcolor="green")))
        page.update()

    def actualizar_candado():
        if estado["admin"]:
            btn_lock.icon = "lock_open"
            btn_lock.icon_color = "yellow"
        else:
            btn_lock.icon = "lock_outline"
            btn_lock.icon_color = "white"
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
                # Contenedor de imagen cuadrado
                imagen_componente = ft.Container(
                    width=110, 
                    height=110,
                    border_radius=ft.border_radius.only(top_left=10, bottom_left=10),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    bgcolor="#EEEEEE", 
                    content=ft.Image(
                        src=item["imagen"] if item.get("imagen") else "",
                        fit=ft.ImageFit.COVER, 
                        error_content=ft.Icon(icono_defecto, size=40, color="grey")
                    ),
                    alignment=ft.alignment.top_left 
                )

                # Recuperar contenido
                contenido_extra = ft.Container()
                if item.get("contenido"):
                    contenido_extra = ft.ExpansionTile(
                        title=ft.Text("Ver más", size=12, color="blue"),
                        # Eliminamos 'tile_padding' para compatibilidad total
                        controls=[
                            ft.Container(
                                padding=ft.padding.only(bottom=10),
                                content=ft.Text(item["contenido"], size=12, color="black")
                            )
                        ]
                    )

                link_componente = ft.Container()
                if item.get("video"):
                    url_completa = item["video"]
                    texto_boton = url_completa.replace("https://", "").replace("http://", "")
                    if len(texto_boton) > 15:
                        texto_boton = texto_boton[:12] + "..."
                        
                    link_componente = ft.TextButton(
                        text=texto_boton,
                        icon="link",
                        icon_color="blue",
                        tooltip=url_completa,
                        on_click=lambda e, url=url_completa: page.launch_url(url)
                    )

                info_componente = ft.Container(
                    expand=True,
                    padding=10,
                    content=ft.Column([
                        ft.Text(item["titulo"], weight="bold", size=16, font_family="Kanit", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(item["desc"], size=12, color="grey", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        contenido_extra,
                        ft.Row([
                            ft.Container(content=ft.Text(item["tag"], size=10, color="white"), bgcolor=color_tag, padding=4, border_radius=4),
                            ft.Container(expand=True),
                            link_componente,
                            ft.IconButton(icon="edit", icon_size=18, icon_color="blue", on_click=lambda e, it=item: click_editar(it)),
                            ft.IconButton(icon="delete", icon_size=18, icon_color="red", on_click=lambda e, it=item: click_papelera(clave_db, it))
                        ], spacing=0, alignment=ft.MainAxisAlignment.END)
                    ], spacing=2)
                )

                tarjeta = ft.Card(
                    elevation=3,
                    color="white",
                    margin=ft.margin.symmetric(horizontal=10),
                    content=ft.Container(
                        content=ft.Row([
                            imagen_componente,
                            info_componente
                        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)
                    )
                )
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
            titulo.value = "Inicio"
        else:
            contenedor_contenido.alignment = ft.alignment.top_center
            if indice == 1: contenedor_contenido.content = obtener_lista_visual("recetas", "#E65100", "restaurant")
            elif indice == 2: contenedor_contenido.content = obtener_lista_visual("restaurantes", "#1B5E20", "storefront")
            elif indice == 3: contenedor_contenido.content = obtener_lista_visual("productos", "#01579B", "shopping_cart")
        page.update()

    def cambiar_tab(e):
        mostrar_seccion(e.control.selected_index)

    # --- MONTAJE ---
    nav = ft.NavigationBar(
        selected_index=0, on_change=cambiar_tab,
        destinations=[
            ft.NavigationBarDestination(icon="home", label="Inicio"),
            ft.NavigationBarDestination(icon="menu_book", label="Recetas"),
            ft.NavigationBarDestination(icon="store", label="Sitios"),
            ft.NavigationBarDestination(icon="shopping_bag", label="Productos"),
        ]
    )
    titulo = ft.Text("Inicio", color="white", size=20, weight="bold")
    app_bar = ft.Container(padding=15, bgcolor="#388E3C", content=ft.Row([ft.Row([ft.Icon("eco", color="white"), titulo]), ft.Row([btn_add_top, btn_lock])], alignment="spaceBetween"))
    layout_principal = ft.Column(spacing=0, expand=True, controls=[app_bar, ft.Container(content=stack_principal, expand=True), nav])
    page.add(layout_principal)

# IMPORTANTE: assets_dir permite cargar la imagen local 'portada.jpg'
ft.app(target=main, assets_dir="assets")
