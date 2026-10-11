import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

import pytest

from hisar_website import create_app
from hisar_website.pages import ALL_PAGE

ALL_PAGE_PATH = [path for path, _ in ALL_PAGE.values()]
ALL_NAV_PATH = ["/features", "/security", "/pricing", "/download"]
ALL_FOOTER_PATH = [
    "/features",
    "/pricing",
    "/download",
    "/status",
    "/security",
    "/privacy",
    "/terms",
    "/refunds",
    "/contact",
]
ALL_LEGAL_PATH = ["/privacy", "/terms", "/refunds"]


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
    for linked_path in ALL_NAV_PATH + ALL_FOOTER_PATH + ["/"]:
        assert linked_path in parser.all_href, f"{path} misses a link to {linked_path}"
    assert "mailto:support@tryhisar.com" in parser.all_href


@pytest.mark.parametrize("path", ALL_PAGE_PATH)
def test_every_page_marks_its_navigation_link_as_current(client, path):
    body = get_body(client, path)
    if path in ALL_NAV_PATH or path in ALL_LEGAL_PATH:
        assert f'href="{path}" aria-current="page"' in body


@pytest.mark.parametrize("path", ALL_PAGE_PATH)
def test_every_page_avoids_banned_wording(client, path):
    text = get_body(client, path).lower()
    for banned_word in ("family", "self-hosted", "smoke test", "lorem"):
        assert banned_word not in text, f"{path} contains {banned_word!r}"


@pytest.mark.parametrize("path", ALL_PAGE_PATH)
def test_every_page_has_no_inline_script_or_style(client, path):
    parser = parse_page(get_body(client, path))
    assert parser.all_inline_script == []
    assert parser.all_style_element == []
    assert parser.all_style_attribute == []
    assert parser.all_event_handler == []


@pytest.mark.parametrize("path", ALL_PAGE_PATH)
def test_every_page_has_no_bracketed_placeholder(client, path):
    text = re.sub(r"<[^>]+>", " ", get_body(client, path))
    assert re.findall(r"\[[A-Z][A-Z ,./]*\]", text) == []


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
    assert len(all_target_by_path) >= len(ALL_PAGE_PATH) + 3


def test_external_links_are_only_known_hosts(client):
    all_allowed_host = {"api.tryhisar.com", "autoriteitpersoonsgegevens.nl"}
    for path in ALL_PAGE_PATH:
        for href in parse_page(get_body(client, path)).all_href:
            link = urlsplit(href)
            if link.scheme in ("http", "https"):
                assert link.netloc in all_allowed_host, href
            elif link.scheme:
                assert link.scheme == "mailto", href


def test_pricing_shows_configured_prices_with_yearly_default(client):
    body = get_body(client, "/pricing")
    assert "€2.49" in body
    assert "€19.99" in body
    assert 'data-billing-period="yearly" aria-pressed="true"' in body
    assert 'data-billing-option="monthly" hidden' in body
    assert "Coming later" in body
    assert "Always free, on every plan" in body
    assert "founding member" in body
    assert "Lemon Squeezy, our reseller and merchant of record" in body
    assert "/static/js/pricing.js" in body


def test_prices_follow_settings():
    app = create_app({"TESTING": True, "PRO_MONTHLY_PRICE": "€9.99", "PRO_YEARLY_PRICE": "€99.99"})
    body = app.test_client().get("/pricing").get_data(as_text=True)
    assert "€9.99" in body
    assert "€99.99" in body


def test_support_email_follows_settings():
    app = create_app({"TESTING": True, "SUPPORT_EMAIL": "help@example.com"})
    body = app.test_client().get("/contact").get_data(as_text=True)
    assert "mailto:help@example.com" in body
    assert "support@tryhisar.com" not in body


def test_contact_offers_access_requests_and_security_reports(client):
    body = get_body(client, "/contact")
    assert 'id="request-access"' in body
    assert "subject=Request%20access" in body
    assert "subject=Security%20report" in body


def test_download_is_for_invited_users(client):
    body = get_body(client, "/download")
    assert "invited users" in body
    assert "TestFlight coming soon" in body
    assert 'href="/contact#request-access"' in body


def test_status_links_to_health_check_and_claims_nothing(client):
    body = get_body(client, "/status")
    assert 'href="https://api.tryhisar.com/healthz"' in body
    assert "operational" not in body.lower()
    assert "all systems" not in body.lower()


@pytest.mark.parametrize("path", ALL_LEGAL_PATH)
def test_legal_pages_name_the_operator_and_date(client, path):
    body = get_body(client, path)
    assert "Effective 11 October 2026" in body
    assert "draft" not in body.lower()
    assert 'aria-label="Legal"' in body


def test_privacy_policy_names_processors_and_rights(client):
    body = get_body(client, "/privacy")
    for expected_text in (
        "Alper Berber",
        "Hetzner Online GmbH",
        "Helsinki, Finland",
        "Google",
        "Data Privacy Framework",
        "Lemon Squeezy, our reseller and merchant of record",
        "Autoriteit Persoonsgegevens",
        "14 days",
        "30 days",
        "portable",
    ):
        assert expected_text in body, expected_text


def test_terms_state_law_notice_and_liability_cap(client):
    body = get_body(client, "/terms")
    for expected_text in ("Alper Berber", "law of the Netherlands", "60 days", "EUR 100", "merchant of record"):
        assert expected_text in body, expected_text


def test_refund_policy_covers_first_payment_only(client):
    body = get_body(client, "/refunds")
    assert "14 days of your first payment" in body
    assert "Renewals" in body
    assert "Lemon Squeezy, our reseller and merchant of record" in body


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
