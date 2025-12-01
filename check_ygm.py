import os
import sys
import requests

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def main() -> None:
    if not WEBHOOK_URL:
        print("ERROR: DISCORD_WEBHOOK_URL environment variable is not set.")
        sys.exit(1)

    message = "👻 Test alert from GitHub Actions – if you see this, Discord wiring works."

    try:
        resp = requests.post(
            WEBHOOK_URL,
            json={"content": message},
            timeout=10,
        )
        print(f"Discord response status: {resp.status_code}")
        # Print a small slice of body for debugging, if any
        print(f"Discord response body (first 200 chars): {resp.text[:200]!r}")

        resp.raise_for_status()
        print("SUCCESS: Discord notification sent.")
    except Exception as e:
        print(f"ERROR sending Discord notification: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
