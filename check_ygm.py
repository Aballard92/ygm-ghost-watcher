import os
import sys
import requests
from typing import Dict, Tuple, List

# Pages to watch
PAGES: Dict[str, str] = {
    "Shop": "https://www.yorkghostmerchants.com/shop",
    # Bowler Hat entry page – shows "entry period has now ended" when closed
    "Bowler Hat": "https://yorkghostmerchants.co.uk/apply/null",
}

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def send_discord_message(message: str) -> None:
    """Send a message to Discord via webhook."""
    if not WEBHOOK_URL:
        print("No DISCORD_WEBHOOK_URL configured", file=sys.stderr)
        return

    try:
        resp = requests.post(
            WEBHOOK_URL,
            json={"content": message},
            timeout=10,
        )
        resp.raise_for_status()
        print("Discord notification sent.")
    except Exception as e:
        print(f"Error sending Discord notification: {e}", file=sys.stderr)


def check_shop_page(name: str, url: str) -> Tuple[bool, str]:
    """
    Logic for the main shop page.

    Returns (has_stock, info_message).
    has_stock = True if 'No results found' is NOT present.
    """
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (YGM watcher)"},
            timeout=20,
        )
        resp.raise_for_status()
    except Exception as e:
        return False, f"{name}: error fetching page: {e}"

    html = resp.text

    if "No results found" in html:
        return False, f"{name}: no results found."
    else:
        return True, f"{name}: POSSIBLE STOCK DETECTED (no 'No results found')."


def check_bowler_hat_page(name: str, url: str) -> Tuple[bool, str]:
    """
    Logic for the Bowler Hat entry page.

    When closed it says:
    'The Bowler Hat entry period has now ended...'

    We treat that message as 'closed'. If that message disappears / changes,
    we assume the entry period may be open.
    """
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (YGM watcher)"},
            timeout=20,
        )
        resp.raise_for_status()
    except Exception as e:
        return False, f"{name}: error fetching page: {e}"

    html = resp.text
    closed_phrase = "entry period has now ended"

    if closed_phrase.lower() in html.lower():
        return False, f"{name}: entry period closed."
    else:
        return True, f"{name}: POSSIBLE ENTRY WINDOW OPEN (closed message missing)."


def check_page(name: str, url: str) -> Tuple[bool, str]:
    """Dispatch to the right checker based on page name."""
    if name == "Shop":
        return check_shop_page(name, url)
    elif name == "Bowler Hat":
        return check_bowler_hat_page(name, url)
    else:
        # Fallback: treat like shop
        return check_shop_page(name, url)


def main() -> None:
    pages_with_activity: List[Tuple[str, str]] = []
    debug_lines: List[str] = []

    for name, url in PAGES.items():
        has_activity, info = check_page(name, url)
        debug_lines.append(info)
        if has_activity:
            pages_with_activity.append((name, url))

    # Log what happened to GitHub Actions logs
    print("\n".join(debug_lines))

    # ONLY notify if at least one page looks live
    if not pages_with_activity:
        print("No activity detected on any monitored page this run.")
        return

    # Build a single alert summarising all 'hot' pages
    lines = [
        "👻 **York Ghost Merchants Alert**",
        "",
        "Possible drop / entry detected on:",
    ]
    for name, url in pages_with_activity:
        lines.append(f"- **{name}** → {url}")

    lines.append("")
    lines.append("Check quickly (could be a clandestine drop or Bowler Hat window).")

    send_discord_message("\n".join(lines))


if __name__ == "__main__":
    main()
