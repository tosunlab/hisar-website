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
| `hisar_website/templates/` | `base.html` layout, one template per page; `partials/` holds the header, footer and shared macros (buttons, code blocks, plan cards, the approval dialog, the legal page layout) |
| `hisar_website/static/` | `css/site.css` (Hisar's colour tokens, light and dark), `js/pricing.js` (the monthly/yearly toggle) and the favicon |

## Settings

| Variable | Default |
|---|---|
| `HISAR_SUPPORT_EMAIL` | `support@tryhisar.com` |
| `HISAR_APP_URL` | `https://api.tryhisar.com` |
| `HISAR_PRO_MONTHLY_PRICE` | `€2.49` |
| `HISAR_PRO_YEARLY_PRICE` | `€19.99` |

## Run the image

```sh
docker build -t hisar-website .
docker run --rm -p 8000:8000 hisar-website
```

The container runs gunicorn on port 8000 as a non-root user.

## Release

1. `git tag -a website-0.1.0 -m "notes" && git push origin website-0.1.0`: the `website-image` job pushes `reg.tryhisar.com/hisar/website:0.1.0` and `:sha-<commit>` (linux/amd64).
2. Press **website-publish** in the tag's pipeline to point `:latest` and `:0.1` at it. A custom build (`website-0.1.0-test`) gets its own image tag and can't be published.
3. On the server: set `HISAR_WEBSITE_VERSION` in `.env` (or keep `latest`), then `docker compose pull website && docker compose up -d website`.

`website-*` tags are protected, because the registry password is a protected group variable.
