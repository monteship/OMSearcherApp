import flet as ft
from flet import RouteChangeEvent, MainAxisAlignment, CrossAxisAlignment, ViewPopEvent
from flet import View, AppBar, Text, ElevatedButton, Dropdown

# from flet.auth import
from database import DomainItem, PostgresqlDatabase

TEST_DOMAINS = [
    DomainItem(
        domain="google.com",
        link="https://www.google.com",
        title="Google",
        snippet="Google's search engine",
        searcher="Hanna Y",
    ),
    DomainItem(
        domain="stackoverflow.com",
        link="https://www.stackoverflow.com",
        title="Stack Overflow",
        snippet="Stack Overflow is a question and answer site for programmers",
        searcher="Hanna Y",
    ),
    DomainItem(
        domain="github.com",
        link="https://www.github.com",
        title="GitHub",
        snippet="GitHub is a code hosting platform for version control",
        searcher="Hanna Y",
    ),
]


def main(page: ft.Page):
    page.title = "OMSearchers Login"
    logged_as: str | None = None

    def route_change(e: RouteChangeEvent) -> None:
        page.views.clear()

        def login_as(e) -> None:
            logged_as = e.value
            print(f"Logged as {logged_as}")
            page.update()

        # Home view
        page.views.append(
            View(
                route="/",
                controls=[
                    AppBar(title=Text("OMSearchers Home"), bgcolor="blue"),
                    Dropdown(
                        width=500,
                        options=[
                            ft.dropdown.Option("Hanna Y"),
                            ft.dropdown.Option("Yulia H"),
                            ft.dropdown.Option("Christian B"),
                        ],
                        on_change=lambda _: login_as,
                    ),
                    ElevatedButton(
                        text=f"Logged as {logged_as}"
                        if logged_as is not None
                        else "Login",
                        width=250,
                        disabled=logged_as is not None,
                        on_click=lambda _: page.go("/work"),
                    ),
                ],
                vertical_alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=26,
            )
        )

        # Domain processing view

        if page.route == "/work":
            database = PostgresqlDatabase()
            cities = database.read()
            page.views.append(
                View(
                    route="/work",
                    controls=[
                        AppBar(title=Text("OMSearchers Searching"), bgcolor="blue"),
                        ElevatedButton(
                            text=f"Logged as {logged_as}",
                            width=250,
                            disabled=True,
                        ),
                        Dropdown(
                            width=500,
                            options=[
                                ft.dropdown.Option("Hanna Y"),
                                ft.dropdown.Option("Yulia H"),
                                ft.dropdown.Option("Christian B"),
                            ],
                            # on_change=lambda _: load_domains,
                        ),
                    ],
                    vertical_alignment=MainAxisAlignment.CENTER,
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                    spacing=26,
                )
            )
        page.update()

    def view_pop(e: ViewPopEvent) -> None:
        page.views.pop()
        top_view: View = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


if __name__ == "__main__":
    ft.app(target=main)
