# Hisar website

The website at [tryhisar.com](https://tryhisar.com): a Flask app with Jinja templates.

## Develop

```sh
uv sync
uv run flask --app hisar_website:create_app run --debug
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## Layout

| Path | What |
|---|---|
| `hisar_website/__init__.py` | `create_app()`: settings from the environment, security headers |
| `hisar_website/pages.py` | One route per page (`ALL_PAGE`) and `/healthz` |
| `hisar_website/templates/` | `base.html` layout, one template per page, `legal.html` for Terms, Privacy and Refund policy |
| `hisar_website/static/` | `css/site.css` (Hisar's colour tokens, light and dark) and the favicon |

## Settings

| Variable | Default |
|---|---|
| `HISAR_SUPPORT_EMAIL` | `support@tryhisar.com` |
| `HISAR_APP_URL` | `https://api.tryhisar.com` |
| `HISAR_PRO_MONTHLY_PRICE` | `€1.99` |
| `HISAR_PRO_YEARLY_PRICE` | `€19.99` |

## Run the image

```sh
docker build -t hisar-website .
docker run --rm -p 8000:8000 hisar-website
```

The container runs gunicorn on port 8000 as a non-root user.
