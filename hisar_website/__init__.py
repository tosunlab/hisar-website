import os

from flask import Flask

from hisar_website.pages import pages


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SUPPORT_EMAIL=os.environ.get("HISAR_SUPPORT_EMAIL", "support@tryhisar.com"),
        APP_URL=os.environ.get("HISAR_APP_URL", "https://api.tryhisar.com"),
        PRO_MONTHLY_PRICE=os.environ.get("HISAR_PRO_MONTHLY_PRICE", "€1.99"),
        PRO_YEARLY_PRICE=os.environ.get("HISAR_PRO_YEARLY_PRICE", "€19.99"),
    )
    if config:
        app.config.update(config)
    app.register_blueprint(pages)

    @app.context_processor
    def add_site_settings() -> dict:
        return {"site": app.config}

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'",
        )
        return response

    return app
