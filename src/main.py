\
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from .aran_scraper import ScraperError, fetch_latest_items
from .storage import load_state, save_state
from .telegram_client import TelegramError, format_message, send_message

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "state.json"

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
LOGGER = logging.getLogger(__name__)


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "sì", "si", "on"}


def main() -> int:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()

    dry_run = env_bool("DRY_RUN", False)
    bootstrap_only = env_bool("BOOTSTRAP_ONLY", True)
    max_pages = int(os.getenv("MAX_LISTING_PAGES", "3"))

    if not dry_run and (not token or not channel_id):
        LOGGER.error(
            "Mancano TELEGRAM_BOT_TOKEN o TELEGRAM_CHANNEL_ID."
        )
        return 2

    state = load_state(STATE_PATH)
    published = set(state["published_ids"])

    try:
        items = fetch_latest_items(max_pages=max_pages)
    except ScraperError as exc:
        LOGGER.error("%s", exc)
        return 3

    if not items:
        LOGGER.error(
            "Nessun orientamento trovato. Il sito ARAN potrebbe aver cambiato "
            "struttura: controllare i log prima di modificare lo stato."
        )
        return 4

    current_ids = {item.item_id for item in items}

    # Prima esecuzione: registra l'esistente, evitando di riversare nel canale
    # centinaia di vecchi orientamenti.
    if not state["initialized"] and bootstrap_only:
        state["initialized"] = True
        state["published_ids"] = sorted(
            current_ids, key=int
        )
        save_state(STATE_PATH, state)
        LOGGER.info(
            "Inizializzazione completata: registrati %d orientamenti già "
            "esistenti. Nessun messaggio pubblicato.",
            len(current_ids),
        )
        return 0

    new_items = [item for item in items if item.item_id not in published]

    if not new_items:
        state["initialized"] = True
        save_state(STATE_PATH, state)
        LOGGER.info("Nessun nuovo orientamento da pubblicare.")
        return 0

    for item in new_items:
        message = format_message(item)
        if dry_run:
            LOGGER.info("DRY RUN — messaggio per ID %s:\n%s", item.item_id, message)
        else:
            try:
                send_message(token, channel_id, message)
            except TelegramError as exc:
                LOGGER.error(
                    "Errore sull'ID %s. Lo stato non sarà aggiornato per "
                    "questo elemento: %s",
                    item.item_id,
                    exc,
                )
                return 5

        published.add(item.item_id)
        state["published_ids"] = sorted(published, key=int)
        state["initialized"] = True
        save_state(STATE_PATH, state)
        LOGGER.info("Gestito orientamento ARAN ID %s", item.item_id)

    return 0


if __name__ == "__main__":
    sys.exit(main())
