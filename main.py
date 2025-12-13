                 ft.Container(
                        bgcolor=bg_overlay,
                        padding=15,
                        content=info_column,
                        expand=True
                    )
                )

                tarjeta = ft.Card(
                    elevation=5, 
                    color="white", 
                    margin=ft.margin.symmetric(horizontal=10), 
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS, 
                    content=ft.Container(
                        height=300, # Altura fija para que se vea bien la foto
                        content=ft.Stack(controls=stack_card)
                    )
                )
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
   
   
