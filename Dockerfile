FROM python:3.14-slim AS build
RUN pip install --no-cache-dir uv==0.11.31
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY hisar_website ./hisar_website

FROM python:3.14-slim
RUN useradd --system --uid 10001 hisar
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/hisar_website /app/hisar_website
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER hisar
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "hisar_website:create_app()"]
