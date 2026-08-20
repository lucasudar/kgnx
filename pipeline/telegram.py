"""Post newly auto-published tools to Telegram when secrets are configured.

Required environment variables:
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID

Optional:
    PUBLIC_SITE_URL (defaults to https://kgnx.nx.kg)
"""

from __future__ import annotations

import html
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "data" / "candidates" / "published.json"


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("telegram: not configured; skipping")
        return

    report = json.loads(REPORT.read_text())
    if not report.get("new_tools"):
        print("telegram: no new publication")
        return

    site = os.environ.get("PUBLIC_SITE_URL", "https://kgnx.nx.kg").rstrip("/")
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"

    for tool in report["new_tools"]:
        message = (
            f"<b>{html.escape(tool['name'])}</b>\n"
            f"{html.escape(tool['pitch'])}\n\n"
            f"{html.escape(tool['kind'].title())} · "
            f"{html.escape(' · '.join(tool['platforms']))}\n"
            f"<a href=\"{html.escape(tool['get_url'], quote=True)}\">Project</a> · "
            f"<a href=\"{html.escape(site, quote=True)}\">Known good. Try next.</a>"
        )
        payload = json.dumps(
            {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            }
        ).encode()
        request = urllib.request.Request(
            endpoint, data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
        if not result.get("ok"):
            raise SystemExit(f"telegram rejected publication: {result}")
        print(f"telegram: posted {tool['name']}")


if __name__ == "__main__":
    main()
