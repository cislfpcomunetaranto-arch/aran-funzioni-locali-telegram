\
from __future__ import annotations

import logging
import re
from dataclasses import replace
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .models import AranItem

LOGGER = logging.getLogger(__name__)

BASE_URL = "https://www.aranagenzia.it"
LISTING_URL = (
    BASE_URL
    + "/orientamenti-applicativi/"
    + "?orient_check%5B0%5D=COMPARTO+FUNZIONI+LOCALI"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; CISLFP-Taranto-ARAN-Monitor/1.0; "
        "+https://www.aranagenzia.it/)"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.5",
}

ID_RE = re.compile(r"\bId\s*:\s*(\d+)\b", re.IGNORECASE)
PREVIOUS_ID_RE = re.compile(
    r"\bPrecedente\s+ID\s*:\s*([A-Z0-9._/-]+)", re.IGNORECASE
)
DATE_RE = re.compile(
    r"\b(\d{1,2}\s+"
    r"(?:Gennaio|Febbraio|Marzo|Aprile|Maggio|Giugno|Luglio|Agosto|"
    r"Settembre|Ottobre|Novembre|Dicembre)\s+\d{4})\b",
    re.IGNORECASE,
)


class ScraperError(RuntimeError):
    pass


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def _get(session: requests.Session, url: str) -> str:
    try:
        response = session.get(url, timeout=(10, 35))
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScraperError(f"Errore nel recupero di {url}: {exc}") from exc
    return response.text


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _is_orientation_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if parsed.netloc and "aranagenzia.it" not in parsed.netloc:
        return False
    if not path.startswith("/orient-applicativi/"):
        return False
    return path != "/orient-applicativi"


def extract_item_links(html: str, page_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(page_url, anchor["href"]).split("#", 1)[0]
        if _is_orientation_url(absolute) and absolute not in seen:
            seen.add(absolute)
            links.append(absolute)

    return links


def _text_after_label(soup: BeautifulSoup, label: str) -> str:
    label_norm = label.casefold()
    for node in soup.find_all(string=True):
        text = _clean_text(str(node))
        if text.casefold().rstrip(":") != label_norm.rstrip(":"):
            continue

        parent = node.parent
        candidates = []
        if parent:
            candidates.extend(parent.find_next_siblings(limit=3))
            if parent.parent:
                candidates.extend(parent.parent.find_next_siblings(limit=3))

        for candidate in candidates:
            value = _clean_text(candidate.get_text(" ", strip=True))
            if value and value.casefold().rstrip(":") != label_norm.rstrip(":"):
                return value
    return ""


def parse_item(html: str, url: str) -> AranItem:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "form"]):
        tag.decompose()

    page_text = _clean_text(soup.get_text(" ", strip=True))

    id_match = ID_RE.search(page_text)
    if not id_match:
        raise ScraperError(f"ID ARAN non trovato nella pagina: {url}")

    previous_match = PREVIOUS_ID_RE.search(page_text)
    previous_id = previous_match.group(1) if previous_match else ""

    heading = soup.find("h1")
    title = _clean_text(heading.get_text(" ", strip=True)) if heading else ""
    if not title:
        title_tag = soup.find("title")
        title = _clean_text(title_tag.get_text(" ", strip=True)) if title_tag else ""

    area = _text_after_label(soup, "Area/Comparto")
    topic = _text_after_label(soup, "Argomento")
    publication_date = _text_after_label(soup, "Data pubblicazione")

    if not publication_date:
        date_match = DATE_RE.search(page_text)
        publication_date = date_match.group(1) if date_match else ""

    # Il corpo principale viene ricavato in modo conservativo: prima si cercano
    # contenitori tipici di WordPress, poi si ripiega sull'intero <main>.
    body = ""
    selectors = [
        "article .entry-content",
        "article .post-content",
        ".single-orientamento",
        ".orientamento-content",
        "main article",
        "main",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            candidate = _clean_text(node.get_text(" ", strip=True))
            if len(candidate) > len(body):
                body = candidate

    # Rimuove dal testo alcune porzioni di interfaccia ricorrenti.
    for marker in (
        "Condividi",
        "Stampa",
        "Invia",
        "Lascia un feedback",
        "Seguici su:",
    ):
        body = body.split(marker, 1)[0].strip()

    return AranItem(
        item_id=id_match.group(1),
        previous_id=previous_id,
        title=title,
        area=area,
        topic=topic,
        publication_date=publication_date,
        body=body,
        url=url,
    )


def _is_funzioni_locali(item: AranItem) -> bool:
    haystack = f"{item.area} {item.title} {item.body}".casefold()
    return "comparto funzioni locali" in haystack


def fetch_latest_items(max_pages: int = 3) -> list[AranItem]:
    session = _session()
    all_links: list[str] = []
    seen_links: set[str] = set()

    for page_number in range(1, max_pages + 1):
        page_url = LISTING_URL if page_number == 1 else (
            BASE_URL
            + f"/orientamenti-applicativi/page/{page_number}/"
            + "?orient_check%5B0%5D=COMPARTO+FUNZIONI+LOCALI"
        )
        LOGGER.info("Controllo pagina elenco: %s", page_url)
        html = _get(session, page_url)
        links = extract_item_links(html, page_url)

        if not links:
            LOGGER.warning("Nessun collegamento trovato nella pagina %s", page_url)
            continue

        for link in links:
            if link not in seen_links:
                seen_links.add(link)
                all_links.append(link)

    items: list[AranItem] = []
    seen_ids: set[str] = set()

    for link in all_links:
        try:
            item = parse_item(_get(session, link), link)
        except ScraperError as exc:
            LOGGER.warning("%s", exc)
            continue

        if item.item_id in seen_ids:
            continue
        if not _is_funzioni_locali(item):
            LOGGER.info(
                "Escluso ID %s perché non risulta del Comparto Funzioni Locali",
                item.item_id,
            )
            continue

        seen_ids.add(item.item_id)
        items.append(item)

    # Gli ID sono numerici e normalmente crescenti; ordine crescente per
    # pubblicare eventuali novità dalla più vecchia alla più recente.
    items.sort(key=lambda x: int(x.item_id))
    return items
