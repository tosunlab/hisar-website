from flask import Blueprint, render_template

pages = Blueprint("pages", __name__)

ALL_PAGE = {
    "home": ("/", "home.html"),
    "pricing": ("/pricing", "pricing.html"),
    "contact": ("/contact", "contact.html"),
    "terms": ("/terms", "terms.html"),
    "privacy": ("/privacy", "privacy.html"),
    "refunds": ("/refunds", "refunds.html"),
}


def register_page(name: str, path: str, template: str) -> None:
    def render_page() -> str:
        return render_template(template, page=name)

    pages.add_url_rule(path, endpoint=name, view_func=render_page)


for page_name, (page_path, page_template) in ALL_PAGE.items():
    register_page(page_name, page_path, page_template)


@pages.get("/healthz")
def get_health() -> tuple[str, int]:
    return "ok", 200
