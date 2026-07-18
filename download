\
from __future__ import annotations

import html
import logging
from dataclasses import dataclass

import requests

from .models import AranItem

LOGGER = logging.getLogger(__name__)
TELEGRAM_LIMIT = 4096


class TelegramError(RuntimeError):
    pass


def _excerpt(item: AranItem, max_length: int = 1250) -> str:
    text = item.body

    # Evita di ripetere tutta la testata se il parser ha incluso anche il titolo.
    if item.title and text.startswith(item.title):
        text = text[len(item.title):].strip(" :-")

    if len(text) <= max_length:
        return text

    shortened = text[: max_length - 1].rsplit(" ", 1)[0]
    return shortened + "…"


def format_message(item: AranItem) -> str:
    lines = [
        "<b>NUOVO ORIENTAMENTO APPLICATIVO ARAN</b>",
        "",
        f"<b>{html.escape(item.title)}</b>",
        "",
        f"<b>ID:</b> {html.escape(item.item_id)}",
    ]

    if item.previous_id:
        lines.append(
            f"<b>Precedente ID:</b> {html.escape(item.previous_id)}"
        )
    if item.topic:
        lines.append(f"<b>Argomento:</b> {html.escape(item.topic)}")
    if item.publication_date:
        lines.append(
            f"<b>Data di pubblicazione:</b> "
            f"{html.escape(item.publication_date)}"
        )

    excerpt = _excerpt(item)
    if excerpt:
        lines.extend(["", html.escape(excerpt)])

    lines.extend([
        "",
        f'<a href="{html.escape(item.url, quote=True)}">'
        "Consulta la fonte ufficiale ARAN</a>",
        "",
        "<i>Canale informativo non ufficiale, a cura della "
        "CISL FP Comune di Taranto.</i>",
    ])

    message = "\n".join(lines)
    if len(message) > TELEGRAM_LIMIT:
        # Margine prudenziale in caso di caratteri HTML convertiti.
        message = message[: TELEGRAM_LIMIT - 20].rsplit(" ", 1)[0] + "…"
    return message


def send_message(
    token: str,
    channel_id: str,
    message: str,
    disable_notification: bool = False,
) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
        "disable_notification": disable_notification,
    }

    try:
        response = requests.post(url, json=payload, timeout=(10, 30))
        response.raise_for_status()
        body = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise TelegramError(f"Invio Telegram non riuscito: {exc}") from exc

    if not body.get("ok"):
        raise TelegramError(f"Telegram ha rifiutato il messaggio: {body}")
