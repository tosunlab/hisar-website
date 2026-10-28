import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

import pytest

from hisar_website import create_app
from hisar_website.pages import ALL_PAGE

ALL_PAGE_PATH = [path for path, _ in ALL_PAGE.values()]
ALL_NAV_PATH = ["/security", "/download"]
ALL_FOOTER_PATH = ["/security", "/privacy", "/contact"]
REPOSITORY_URL = "https://github.com/tosunlab/hisar"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.all_href: list[str] = []
        self.all_id: set[str] = set()
        self.all_inline_script: list[str] = []
        self.all_style_attribute: list[str] = []
        self.all_style_element: list[str] = []
        self.all_event_handler: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attribute_by_name = dict(attrs)
        if "id" in attribute_by_name:
            self.all_id.add(attribute_by_name["id"] or "")
        if tag == "a" and attribute_by_name.get("href"):
            self.all_href.append(attribute_by_name["href"] or "")
        if tag in ("link", "script") and attribute_by_name.get("src"):
            self.all_href.append(attribute_by_name["src"] or "")
        if tag == "link" and attribute_by_name.get("href"):
            self.all_href.append(attribute_by_name["href"] or "")
        if tag == "script" and not attribute_by_name.get("src"):
            self.all_inline_script.append(tag)
        if tag == "style":
            self.all_style_element.append(tag)
        for name, _ in attrs:
            if name == "style":
                self.all_style_attribute.append(tag)
            if name.startswith("on"):
                self.all_event_handler.append(f"{tag}[{name}]")


def parse_page(body: str) -> PageParser:
    parser = PageParser()
    parser.feed(body)
    return parser


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    return app.test_client()


def get_body(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, path
    return response.get_data(as_text=True)


@pytest.mark.parametrize("path", ALL_PAGE_PATH)
def test_every_page_renders_with_navigation_and_footer(client, path):
    parser = parse_page(get_body(client, path))
    for linked_path in ["/", "/#features", "/#self-host"] + ALL_NAV_PATH + ALL_FOOTER_PATH:
        assert linked_path in parser.all_href, f"{path} misses a link to {linked_path}"
    for repository_link in (REPOSITORY_URL, f"{REPOSITORY_URL}/tree/main/docs", f"{REPOSITORY_URL}/releases"):
        assert repository_link in parser.all_href, f"{path} misses a link to {repository_link}"


@pytest.mark.parametrize("path", ALL_PAGE_PATH)
def test_every_page_marks_its_navigation_link_as_current(client, path):
    body = get_body(client, path)
    if path in ALL_NAV_PATH or path in ALL_FOOTER_PATH:
        assert f'href="{path}" aria-current="page"' in body


@pytest.mark.parametrize("path", ALL_PAGE_PATH)
def test_every_page_has_no_inline_script_or_style(client, path):
    parser = parse_page(get_body(client, path))
    assert parser.all_inline_script == []
    assert parser.all_style_element == []
    assert parser.all_style_attribute == []
    assert parser.all_event_handler == []


@pytest.mark.parametrize("path", ALL_PAGE_PATH)
def test_every_page_has_one_main_heading(client, path):
    body = get_body(client, path)
    assert body.count("<h1") == 1
    assert '<main id="content"' in body
    assert 'href="#content"' in body


def test_no_dead_internal_links(client):
    all_target_by_path: dict[str, PageParser] = {}
    all_pending_path = list(ALL_PAGE_PATH)
    all_checked_link: list[tuple[str, str]] = []
    while all_pending_path:
        path = all_pending_path.pop()
        if path in all_target_by_path:
            continue
        response = client.get(path)
        assert response.status_code == 200, path
        if response.mimetype != "text/html":
            all_target_by_path[path] = PageParser()
            continue
        parser = parse_page(response.get_data(as_text=True))
        all_target_by_path[path] = parser
        for href in parser.all_href:
            link = urlsplit(href)
            if link.scheme or link.netloc:
                continue
            target_path = link.path or path
            all_checked_link.append((target_path, link.fragment))
            all_pending_path.append(target_path)
    for target_path, fragment in all_checked_link:
        if fragment and fragment != "content":
            assert fragment in all_target_by_path[target_path].all_id, f"{target_path}#{fragment}"
    assert len(all_target_by_path) >= len(ALL_PAGE_PATH) + 2


def test_external_links_are_only_known_hosts(client):
    all_allowed_host = {
        "github.com",
        "docs.github.com",
        "eu.tryhisar.com",
        "tosunlab.com",
        "autoriteitpersoonsgegevens.nl",
        "ico.org.uk",
    }
    for path in ALL_PAGE_PATH:
        for href in parse_page(get_body(client, path)).all_href:
            link = urlsplit(href)
            if link.scheme in ("http", "https"):
                assert link.netloc in all_allowed_host, href
            elif link.scheme:
                assert link.scheme == "mailto", href


def test_repository_links_follow_settings():
    app = create_app({"TESTING": True, "REPOSITORY_URL": "https://git.example.com/fork/hisar"})
    for path in ALL_PAGE_PATH:
        body = app.test_client().get(path).get_data(as_text=True)
        assert "https://git.example.com/fork/hisar/releases" in body, path
        assert not re.search(re.escape(REPOSITORY_URL) + r"(?!-website)", body), path


@pytest.mark.parametrize("path", ["/contact", "/privacy", "/security"])
def test_support_email_follows_settings(path):
    app = create_app({"TESTING": True, "SUPPORT_EMAIL": "help@example.com"})
    body = get_body(app.test_client(), path)
    links = parse_page(body).all_href
    assert any(href.startswith("mailto:help@example.com") for href in links)
    assert "support@tryhisar.com" not in body


def test_privacy_sends_hosted_server_users_to_its_own_policy(client):
    body = get_body(client, "/privacy")
    assert 'href="https://eu.tryhisar.com/privacy"' in body


def test_app_store_support_url_is_public_and_has_email_contact(client):
    response = client.get("/contact")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert "Set-Cookie" not in response.headers
    links = parse_page(response.get_data(as_text=True)).all_href
    assert "mailto:support@tryhisar.com" in links
    assert "/privacy" in links


@pytest.mark.parametrize("path", ALL_PAGE_PATH)
def test_every_page_credits_tosunlab(client, path):
    body = get_body(client, path)
    assert 'href="https://tosunlab.com"' in body


def test_security_headers_are_set(client):
    response = client.get("/")
    content_security_policy = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in content_security_policy
    assert "script-src 'self'" in content_security_policy
    assert "style-src 'self'" in content_security_policy
    assert "unsafe-inline" not in content_security_policy
    assert "frame-ancestors 'none'" in content_security_policy
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_health_check(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "ok"


def test_unknown_page_is_not_found(client):
    assert client.get("/does-not-exist").status_code == 404
