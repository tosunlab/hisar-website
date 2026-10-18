# Hisar website

The website at [tryhisar.com](https://tryhisar.com) for the open-source, self-hosted Hisar: a Flask app with Jinja templates. Pages: home, download, security model and privacy.

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
| `hisar_website/templates/` | `base.html` layout, one template per page; `partials/` holds the header, footer and shared macros (icons, buttons, code blocks, the approval dialog) |
| `hisar_website/static/` | `css/site.css` (Hisar's colour tokens, light and dark), `fonts/` (IBM Plex Sans and Mono, latin subset, SIL Open Font License in `OFL.txt`) and the favicon |

## Settings

| Variable | Default |
|---|---|
| `HISAR_SUPPORT_EMAIL` | `support@tryhisar.com` |
| `HISAR_REPOSITORY_URL` | `https://github.com/tosunlab/hisar`: the source, docs, releases and issues links |

## Run the image

```sh
docker build -t hisar-website .
docker run --rm -p 8000:8000 hisar-website
```

The container runs gunicorn on port 8000 as a non-root user.

## Release

GitHub Actions (`.github/workflows/`): `ci.yml` runs ruff and pytest on every pull request and builds the image without pushing; `release.yml` and `publish.yml` push to the private GitHub Container Registry package `ghcr.io/tosunlab/hisar-website`.

1. `git tag -a website-0.1.0 -m "notes" && git push origin website-0.1.0`: the "Release website image" workflow pushes `ghcr.io/tosunlab/hisar-website:0.1.0` and `:sha-<commit>` (linux/amd64).
2. Run the Publish workflow with the tag (`gh workflow run publish.yml -f tag=website-0.1.0`) to point `:latest` and `:0.1` at it. A custom build (`website-0.1.0-test`) gets its own image tag and can't be published.
3. On the server: `docker login ghcr.io -u <GitHub user>` with a token that has `read:packages`, set `HISAR_WEBSITE_VERSION` in `.env` (or keep `latest`), then `docker compose pull website && docker compose up -d website`.

Anyone who can push a `website-*` tag or run a workflow can release, so protect `website-*` tags with a repository ruleset.
