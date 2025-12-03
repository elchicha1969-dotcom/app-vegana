import flet as ft
import uuid 

def main(page: ft.Page):
    # --- CONFIGURACIÓN BÁSICA ---
    page.title = "Vida Vegana"
    page.theme_mode = "light"
    page.padding = 20 
    page.bgcolor = "#202020" 
    page.window_width = 1000 
    page.window_height = 900
    page.theme = ft.Theme(color_scheme_seed="#388E3C")

    # --- IMAGEN DE FONDO ---
    FONDO_APP = "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?auto=format&fit=crop&w=640&q=80"

    # --- GESTIÓN DE DATOS ---
    def cargar_y_sanear(key):
        """Carga datos asegurando que todos tengan ID"""
        try:
            datos = page.client_storage.get(key)
            if datos is None: return []
            
            lista_saneada = []
            cambios = False
            for item in datos:
                if not isinstance(item, dict): continue
                # Generar ID si no existe
                if "id" not in item:
                    item["id"] = str(uuid.uuid4())
                    cambios = True
                lista_saneada.append(item)
            
            if cambios: 
                page.client_storage.set(key, lista_saneada)
            return lista_saneada
        except: 
            return []

    # Cargamos inicial
    db = {
        "recetas": cargar_y_sanear("mis_recetas"),
        "restaurantes": cargar_y_sanear("mis_restaurantes"),
        "productos": cargar_y_sanear("mis_productos")
    }
    
    # ESTADO GLOBAL
    # guardamos solo el ID para borrar, es más seguro
    estado = {"seccion_actual": 0, "admin": False, "id_pendiente": None, "db_pendiente": None} 

    # --- CAPAS DE FONDO ---
    imagen_fondo = ft.Image(src=FONDO_APP, fit=ft.ImageFit.COVER, opacity=1.0, expand=True)
    contenedor_contenido = ft.Container(expand=True, padding=10, alignment=ft.alignment.center)
    stack_principal = ft.Stack(controls=[imagen_fondo, contenedor_contenido], expand=True)

    # --- LÓGICA DE BORRADO BLINDADA ---
    def ejecutar_borrado_final(clave_db, id_a_borrar):
        # 1. Recargar datos frescos del almacenamiento para evitar desincronización
        lista_actual = page.client_storage.get(f"mis_{clave_db}")
        if lista_actual is None: lista_actual = []

        # 2. Filtrar: Crear nueva lista CON TODO MENOS el ID objetivo
        # Esto es más seguro que .remove()
        lista_nueva = [item for item in lista_actual if item.get("id") != id_a_borrar]
        
        # 3. Verificar si hubo cambios
        if len(lista_nueva) < len(lista_actual):
            # Guardamos la nueva lista limpia
            page.client_storage.set(f"mis_{clave_db}", lista_nueva)
            # Actualizamos la variable global también
            db[clave_db] = lista_nueva
            
            page.show_snack_bar(ft.SnackBar(ft.Text("¡Eliminado correctamente!"), bgcolor="green"))
        else:
            page.show_snack_bar(ft.SnackBar(ft.Text("No se encontró el item (¿ya estaba borrado?)"), bgcolor="orange"))
        
        # 4. Refrescar interfaz
        mostrar_seccion(estado["seccion_actual"])
        page.update()

    def solicitar_borrado(clave_db, id_item):
        if estado["admin"]:
            ejecutar_borrado_final(clave_db, id_item)
        else:
            # Guardamos la intención (Base de datos y ID)
            estado["db_pendiente"] = clave_db
            estado["id_pendiente"] = id_item
            page.dialog = dialogo_login
            dialogo_login.open = True
            page.update()

    # --- SISTEMA DE ADMIN ---
    def intentar_login(e):
        if campo_pin.value == "1234":
            estado["admin"] = True
            campo_pin.value = ""
            dialogo_login.open = False
            actualizar_candado()
            
            # Ejecutar borrado pendiente si existe
            if estado["id_pendiente"] and estado["db_pendiente"]:
                ejecutar_borrado_final(estado["db_pendiente"], estado["id_pendiente"])
                # Limpiar pendientes
                estado["id_pendiente"] = None
                estado["db_pendiente"] = None
            else:
                page.show_snack_bar(ft.SnackBar(ft.Text("MODO ADMIN ACTIVADO"), bgcolor="green"))
            
            page.update()
        else:
            campo_pin.error_text = "PIN Incorrecto"
            campo_pin.update()

    def actualizar_candado():
        if estado["admin"]:
            btn_lock.icon = "lock_open"
            btn_lock.icon_color = "yellow"
        else:
            btn_lock.icon = "lock_outline"
            btn_lock.icon_color = "white"
        page.update()

    def toggle_admin(e):
        if estado["admin"]:
            estado["admin"] = False
            actualizar_candado()
            page.show_snack_bar(ft.SnackBar(ft.Text("Modo Admin Cerrado."), bgcolor="orange"))
        else:
            # Limpiamos pendientes al abrir manual
            estado["id_pendiente"] = None
            page.dialog = dialogo_login
            dialogo_login.open = True
            page.update()

    campo_pin = ft.TextField(label="PIN (1234)", password=True, text_align="center", autofocus=True)
    
    dialogo_login = ft.AlertDialog(
        title=ft.Text("Seguridad"),
        content=ft.Column([ft.Text("Introduce PIN para autorizar:", size=14), campo_pin], height=100),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialogo_login, 'open', False) or page.update()),
            ft.ElevatedButton("CONFIRMAR", on_click=intentar_login)
        ]
    )

    btn_lock = ft.IconButton(icon="lock_outline", icon_color="white", on_click=toggle_admin)

    # --- LISTAS VISUALES ---
    def obtener_lista_visual(clave_db, color_tag, icono_defecto):
        columna = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Leemos siempre de la variable global actualizada
        datos = db[clave_db]
        
        if not datos:
            columna.controls.append(
                ft.Container(
                    alignment=ft.alignment.center, padding=20,
                    content=ft.Container(
                        padding=30, width=320, bgcolor="#99FFFFFF", border_radius=15,
                        content=ft.Column([
                            ft.Icon("info", size=40, color="grey"),
                            ft.Text("Lista vacía", color="grey", weight="bold"),
                            ft.Text("Usa (+) para añadir.", color="grey", size=12)
                        ], horizontal_alignment="center")
                    )
                )
            )
        else:
            for item in datos:
                # Capturamos el ID en una variable local
                this_id = item.get("id")

                imagen_item = ft.Container()
                if item.get("imagen"):
                    imagen_item = ft.Image(
                        src=item["imagen"], width=400, height=150, fit=ft.ImageFit.COVER,
                        border_radius=ft.border_radius.vertical(top=10),
                        error_content=ft.Icon("broken_image", color="grey")
                    )

                detalles = ft.Container()
                if item.get("contenido"):
                    detalles = ft.ExpansionTile(
                        title=ft.Text("Ver Detalles", color="#388E3C", size=14),
                        controls=[ft.Container(padding=10, content=ft.Text(item["contenido"], size=13, color="#424242"))]
                    )

                link_btn = ft.Container()
                if item.get("video"): 
                    link_btn = ft.TextButton("Abrir Enlace", icon="public", icon_color="blue", on_click=lambda e: page.launch_url(item["video"]))

                # BOTÓN BORRAR
                # Pasamos el ID explícito (this_id) a la función lambda
                delete_btn = ft.IconButton(
                    icon="delete_forever",
                    icon_color="red",
                    icon_size=30,
                    tooltip="Borrar item",
                    on_click=lambda e, id_ref=this_id: solicitar_borrado(clave_db, id_ref)
                )

                acciones_row = ft.Row([link_btn, ft.Container(expand=True), delete_btn], alignment="spaceBetween")

                tarjeta = ft.Card(
                    width=320, elevation=5, color="#F2FFFFFF", clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    content=ft.Container(
                        content=ft.Column([
                            imagen_item,
                            ft.Container(
                                padding=15,
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(icono_defecto, size=24, color="#388E3C"),
                                        ft.Text(item["titulo"], weight="bold", size=18, color="black", expand=True),
                                        ft.Container(content=ft.Text(item["tag"], size=10, color="white", weight="bold"), bgcolor=color_tag, padding=5, border_radius=5)
                                    ], alignment="spaceBetween"),
                                    ft.Text(item["desc"], size=13, color="#616161"),
                                    ft.Divider(height=10, color="transparent"),
                                    detalles,
                                    acciones_row 
                                ])
                            )
                        ], spacing=0)
                    )
                )
                columna.controls.append(tarjeta)
        return columna

    # --- FORMULARIO ---
    txt_nombre = ft.TextField(label="Nombre", bgcolor="#F5F5F5", color="black", border_color="#388E3C")
    txt_desc = ft.TextField(label="Descripción", bgcolor="#F5F5F5", color="black", border_color="#388E3C")
    txt_tag = ft.TextField(label="Etiqueta", bgcolor="#F5F5F5", color="black", border_color="#388E3C")
    txt_img = ft.TextField(label="URL Imagen", bgcolor="#F5F5F5", color="black", icon="image", expand=True)
    txt_vid = ft.TextField(label="URL Enlace", bgcolor="#F5F5F5", color="black", icon="link")
    txt_cont = ft.TextField(label="Detalles", multiline=True, min_lines=5, bgcolor="#F5F5F5", color="black")

    def archivo_seleccionado(e: ft.FilePickerResultEvent):
        if e.files:
            txt_img.value = e.files[0].path
            txt_img.update()
            page.show_snack_bar(ft.SnackBar(ft.Text("Imagen cargada"), bgcolor="green"))

    picker = ft.FilePicker(on_result=archivo_seleccionado)
    page.overlay.append(picker)

    def guardar(e):
        if not txt_nombre.value:
            txt_nombre.error_text = "!"
            page.update()
            return
        
        # ID ÚNICO GENERADO AQUÍ
        nuevo = {
            "id": str(uuid.uuid4()),
            "titulo": txt_nombre.value, "desc": txt_desc.value, "tag": txt_tag.value,
            "imagen": txt_img.value, "video": txt_vid.value, "contenido": txt_cont.value
        }
        
        sec = estado["seccion_actual"]
        target_db = None
        if sec == 1: target_db = "recetas"
        elif sec == 2: target_db = "restaurantes"
        elif sec == 3: target_db = "productos"
        
        if target_db:
            # Añadir a memoria y a disco
            db[target_db].append(nuevo)
            page.client_storage.set(f"mis_{target_db}", db[target_db])
            
            # Limpiar
            for t in [txt_nombre, txt_desc, txt_tag, txt_img, txt_vid, txt_cont]: t.value = ""
            txt_nombre.error_text = None
            mostrar_seccion(sec)
            page.show_snack_bar(ft.SnackBar(ft.Text("Guardado"), bgcolor="green"))

    def cancelar(e):
        mostrar_seccion(estado["seccion_actual"])

    vista_formulario = ft.Container(
        bgcolor="white", padding=20, width=320, border_radius=15, alignment=ft.alignment.top_center, 
        content=ft.Column([
            ft.Text("Añadir Nuevo", size=24, weight="bold", color="#388E3C"),
            ft.Divider(),
            txt_nombre, txt_desc, txt_tag,
            ft.Divider(),
            ft.Row([txt_img, ft.IconButton("photo_library", icon_color="#388E3C", on_click=lambda _: picker.pick_files())]),
            txt_vid, txt_cont,
            ft.Container(height=20),
            ft.Row([
                ft.ElevatedButton("Cancelar", on_click=cancelar, bgcolor="grey", color="white"),
                ft.ElevatedButton("GUARDAR", on_click=guardar, bgcolor="#388E3C", color="white")
            ], alignment="center"),
            ft.Container(height=30)
        ], scroll="auto")
    )

    # --- NAVEGACIÓN ---
    def ir_formulario(e):
        imagen_fondo.visible = False 
        contenedor_contenido.bgcolor = "#F5F5F5"
        contenedor_contenido.alignment = ft.alignment.top_center 
        contenedor_contenido.content = vista_formulario
        btn_add.visible = False
        page.update()

    btn_add = ft.FloatingActionButton(icon="add", bgcolor="#388E3C", on_click=ir_formulario)

    def mostrar_seccion(indice):
        estado["seccion_actual"] = indice
        btn_add.visible = (indice != 0)
        imagen_fondo.visible = True
        contenedor_contenido.bgcolor = None
        
        if indice == 0:
            contenedor_contenido.alignment = ft.alignment.center
            contenido_inicio = ft.Container(
                bgcolor="#99FFFFFF", padding=30, width=300, border_radius=20,
                content=ft.Column([
                    ft.Icon("eco", size=80, color="#388E3C"),
                    ft.Text("Bienvenido", size=30, weight="bold", color="#388E3C"),
                    ft.Text("Tu espacio vegano.", size=16, color="#111111", text_align="center"),
                    ft.Container(height=20),
                    ft.Text("👇 Elige una opción abajo", size=14, weight="bold", color="#388E3C"),
                    ft.Container(height=10),
                    ft.Text("Pulsa la papelera roja para borrar.", size=10, color="grey")
                ], horizontal_alignment="center", spacing=5)
            )
            contenedor_contenido.content = contenido_inicio
            titulo.value = "Inicio"
        else:
            contenedor_contenido.alignment = ft.alignment.top_center
            if indice == 1: contenedor_contenido.content = obtener_lista_visual("recetas", "#E65100", "restaurant")
            elif indice == 2: contenedor_contenido.content = obtener_lista_visual("restaurantes", "#1B5E20", "storefront")
            elif indice == 3: contenedor_contenido.content = obtener_lista_visual("productos", "#01579B", "shopping_cart")
        page.update()

    def cambiar_tab(e):
        mostrar_seccion(e.control.selected_index)

    # --- MONTAJE FINAL ---
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
    
    app_bar_movil = ft.Container(
        padding=15, bgcolor="#388E3C", 
        content=ft.Row([
            ft.Row([ft.Icon("eco", color="white"), titulo]),
            btn_lock
        ], alignment="spaceBetween")
    )

    celular_simulado = ft.Container(
        width=390, height=844, bgcolor="white", border_radius=30, border=ft.border.all(8, "black"),
        clip_behavior=ft.ClipBehavior.HARD_EDGE, shadow=ft.BoxShadow(blur_radius=20, color="black", offset=ft.Offset(0,10)),
        content=ft.Column(spacing=0, controls=[app_bar_movil, ft.Container(content=stack_principal, expand=True), nav])
    )

    page.add(ft.Container(content=celular_simulado, alignment=ft.alignment.center, expand=True))
    stack_principal.controls.append(ft.Container(content=btn_add, right=20, bottom=20))
    btn_add.visible = False

ft.app(target=main)
