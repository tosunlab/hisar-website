import os

from flask import Flask

from hisar_website.pages import pages


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SUPPORT_EMAIL=os.environ.get("HISAR_SUPPORT_EMAIL", "support@tryhisar.com"),
        REPOSITORY_URL=os.environ.get("HISAR_REPOSITORY_URL", "https://github.com/tosunlab/hisar").rstrip("/"),
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
