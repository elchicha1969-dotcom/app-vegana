import flet as ft
import uuid
import json
import urllib.request 

def main(page: ft.Page):
    # --- CONFIGURACIÓN ---
    page.title = "Vegan Green"
    page.theme_mode = "light"
    page.padding = 0 
    page.bgcolor = "#202020" 
    page.theme = ft.Theme(color_scheme_seed="#388E3C")

    # --- IMAGEN ---
    # Usamos URL de internet para evitar problemas si falta la carpeta assets
    FONDO_APP = "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?auto=format&fit=crop&w=640&q=80"
    IMAGEN_DEFAULT = "https://upload.wikimedia.org/wikipedia/commons/1/14/No_Image_Available.jpg"
    
    # --- FIREBASE (Pega tu URL si la tienes, si no, déjalo vacío) ---
    FIREBASE_URL = "" 
    USAR_NUBE = bool(FIREBASE_URL)

    # --- DATOS DE EJEMPLO (Se verán al instalar) ---
    DATOS_INICIO = {
        "recetas": [{"id": "1", "titulo": "Tarta de Higos", "desc": "Postre natural", "tag": "Dulce", "imagen": "https://images.unsplash.com/photo-1602351447937-745cb720612f?auto=format&fit=crop&w=500&q=60", "video": "", "contenido": "Ingredientes: Higos..."}],
        "restaurantes": [],
        "productos": []
    }

    # --- GESTIÓN DE DATOS ---
    def cargar_datos_nube(coleccion):
        if not USAR_NUBE: return []
        try:
            with urllib.request.urlopen(f"{FIREBASE_URL}/{coleccion}.json") as r:
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
            with urllib.request.urlopen(req): pass
        except: pass

    def cargar(key, default):
        # 1. Nube
        if USAR_NUBE:
            nube = cargar_datos_nube(key.replace("mis_", ""))
            if nube: 
                page.client_storage.set(key, nube)
                return nube
        # 2. Local
        try:
            local = page.client_storage.get(key)
            if not local:
                page.client_storage.set(key, default)
                return default
            # Sanear IDs
            for i in local:
                if "id" not in i: i["id"] = str(uuid.uuid4())
            return local
        except: return default

    db = {
        "recetas": cargar("mis_recetas", DATOS_INICIO["recetas"]),
        "restaurantes": cargar("mis_restaurantes", DATOS_INICIO["restaurantes"]),
        "productos": cargar("mis_productos", DATOS_INICIO["productos"])
    }
    
    estado = {"seccion": 0, "admin": False, "edit_id": None} 

    # --- FONDO (STACK) ---
    fondo = ft.Image(src=FONDO_APP, fit=ft.ImageFit.COVER, opacity=1.0, expand=True)
    contenido = ft.Container(expand=True, padding=10, alignment=ft.alignment.center)
    stack_main = ft.Stack(controls=[fondo, contenido], expand=True)

    def sync(key):
        page.client_storage.set(f"mis_{key}", db[key])
        if USAR_NUBE: guardar_datos_nube(key, db[key])

    # --- LÓGICA ---
    def borrar(key, id_obj):
        db[key] = [x for x in db[key] if x.get("id") != id_obj]
        sync(key)
        page.open(ft.SnackBar(ft.Text("Borrado"), bgcolor="green"))
        mostrar(estado["seccion"])

    def guardar_item(e):
        if not input_nombre.value: return
        data = {"titulo": input_nombre.value, "desc": input_desc.value, "tag": input_tag.value, "imagen": input_img.value, "video": input_vid.value, "contenido": input_cont.value}
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
        page.open(ft.SnackBar(ft.Text("Guardado"), bgcolor="green"))
        mostrar(estado["seccion"])

    # --- UI ---
    input_nombre = ft.TextField(label="Nombre", bgcolor="white", color="black")
    input_desc = ft.TextField(label="Descripción", bgcolor="white", color="black")
    input_tag = ft.TextField(label="Etiqueta", bgcolor="white", color="black")
    input_img = ft.TextField(label="URL Imagen", bgcolor="white", color="black")
    input_vid = ft.TextField(label="URL Enlace", bgcolor="white", color="black")
    input_cont = ft.TextField(label="Detalles", multiline=True, bgcolor="white", color="black")
    
    form = ft.Container(bgcolor="white", padding=20, border_radius=10, content=ft.Column([
        ft.Text("Editar/Nuevo", color="green", size=20),
        input_nombre, input_desc, input_tag, input_img, input_vid, input_cont,
        ft.Row([ft.ElevatedButton("Cancelar", on_click=lambda e: mostrar(estado["seccion"])), ft.ElevatedButton("Guardar", on_click=guardar)])
    ]))

    def abrir_form(item=None):
        estado["edit_id"] = item["id"] if item else None
        input_nombre.value = item["titulo"] if item else ""
        input_desc.value = item["desc"] if item else ""
        input_tag.value = item["tag"] if item else ""
        input_img.value = item["imagen"] if item else ""
        input_vid.value = item["video"] if item else ""
        input_cont.value = item["contenido"] if item else ""
        
        fondo.visible = False
        contenido.bgcolor = "#F5F5F5"
        contenido.alignment = ft.alignment.top_center
        contenido.content = form
        btn_add.visible = False
        page.update()

    def get_list(key, tag_color, icon):
        col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        for item in db[key]:
            img = ft.Container(width=100, height=100, content=ft.Image(src=item["imagen"] or IMAGEN_DEFAULT, fit=ft.ImageFit.COVER))
            
            info = ft.Column([
                ft.Text(item["titulo"], weight="bold", size=16),
                ft.Text(item["desc"], size=12, color="grey"),
                ft.Row([
                    ft.IconButton("edit", on_click=lambda e, i=item: abrir_form(i)),
                    ft.IconButton("delete", on_click=lambda e, k=key, i=item["id"]: borrar(k, i))
                ])
            ])
            col.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Row([img, ft.Container(content=info, expand=True)]))))
        return col

    def mostrar(idx):
        estado["seccion"] = idx
        btn_add.visible = (idx != 0)
        fondo.visible = (idx == 0)
        contenido.bgcolor = "#F5F5F5" if idx != 0 else None
        
        if idx == 0:
            contenido.alignment = ft.alignment.center
            contenido.content = ft.Container()
        else:
            contenido.alignment = ft.alignment.top_center
            key = ["", "recetas", "restaurantes", "productos"][idx]
            contenido.content = get_list(key, "green", "star")
        page.update()

    btn_add = ft.FloatingActionButton(icon="add", on_click=lambda e: abrir_form(None))
    nav = ft.NavigationBar(on_change=lambda e: mostrar(e.control.selected_index), destinations=[
        ft.NavigationDestination(icon="home", label="Inicio"),
        ft.NavigationDestination(icon="book", label="Recetas"),
        ft.NavigationDestination(icon="store", label="Sitios"),
        ft.NavigationDestination(icon="shopping_bag", label="Productos")
    ])

    page.add(ft.Column([
        ft.Container(padding=10, bgcolor="green", content=ft.Text("Vegan Green", color="white", size=20)),
        ft.Container(content=stack_main, expand=True),
        nav
    ], expand=True))
    page.floating_action_button = btn_add
    mostrar(0)

ft.app(target=main)
