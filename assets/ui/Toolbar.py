import flet as ft


class ToolBar:
    def __init__(self) -> None:
        self.toolbar = ft.NavigationBar(
            destinations=[
            ft.NavigationDestination(icon=ft.icons.DOWNLOAD, label="Download"),
            ft.NavigationDestination(icon=ft.icons.BOOK, label="Manga"),
            ft.NavigationDestination(icon=ft.icons.HOME,label="Homepage"),
            ft.NavigationDestination(icon=ft.icons.TV,label="Anime"),
            ft.NavigationDestination(icon=ft.icons.SETTINGS,label="Settings"),
        ],
        indicator_color= '#3B3B3B',
        surface_tint_color='#52535B',
        selected_index=2,
        label_behavior=ft.NavigationBarLabelBehavior.ONLY_SHOW_SELECTED
        )