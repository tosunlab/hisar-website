import pytest

from hisar_website import create_app
from hisar_website.pages import ALL_PAGE


@pytest.fixture
def client():
    app = create_app({"TESTING": True, "SUPPORT_EMAIL": "support@example.com"})
    return app.test_client()


@pytest.mark.parametrize("path", [path for path, _ in ALL_PAGE.values()])
def test_every_page_renders_with_navigation_and_legal_links(client, path):
    response = client.get(path)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    for legal_path in ("/terms", "/privacy", "/refunds", "/contact"):
        assert f'href="{legal_path}"' in body
    assert "family" not in body.lower()
    assert "self-hosted" not in body.lower()


def test_pricing_shows_configured_prices(client):
    body = client.get("/pricing").get_data(as_text=True)
    assert "€1.99" in body
    assert "€19.99" in body


def test_contact_shows_support_email(client):
    assert "support@example.com" in client.get("/contact").get_data(as_text=True)


def test_security_headers_are_set(client):
    response = client.get("/")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_health_check(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "ok"


def test_unknown_page_is_not_found(client):
    assert client.get("/does-not-exist").status_code == 404
