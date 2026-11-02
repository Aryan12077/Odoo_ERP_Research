import sys
import json
from datetime import datetime
from connector import OdooClient
from extractors.company import extract


class TeeLogger:
    """
    Duplicates stdout so every print() statement outputs to
    both the console and a designated log file.
    """
    def __init__(self, filename="output.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def close(self):
        self.log.close()


# Redirect standard output to both console and output.log
tee = TeeLogger("output.log")
sys.stdout = tee


def pretty(data):
    """Formats dictionaries and lists into readable JSON strings."""
    try:
        return json.dumps(data, indent=2, default=str)
    except Exception:
        return str(data)


try:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Odoo Test Run")
    print("=" * 60)
    print("Authenticating...")
    print("=" * 60)

    client = OdooClient()
    uid = client.authenticate()

    print(f"Authenticated Successfully!")
    print(f"UID : {uid}")

    print()
    print("=" * 60)
    print("Companies (via extractors.company)")
    print("=" * 60)
    companies = extract(client)
    print(pretty(companies))

    print()
    print("=" * 60)
    print("Users (res.users)")
    print("=" * 60)
    users = client.search_read(
        model="res.users",
        fields=["id", "name", "login"]
    )
    print(pretty(users))

    print()
    print("=" * 60)
    print("Partners (res.partner - sample)")
    print("=" * 60)
    partners = client.search_read(
        model="res.partner",
        fields=["id", "name", "email"],
        domain=[],
        # limit is optional if you want to cap it, e.g. kwargs={"limit": 50}
    )
    print(pretty(partners))

    print()
    print("=" * 60)
    print("Partner Count")
    print("=" * 60)
    count = client.search_count(model="res.partner")
    print(f"Total Partners Count: {count}")

    print()
    print("=" * 60)
    print("Partner Read (ID: 1)")
    print("=" * 60)
    partner = client.read(
        model="res.partner",
        ids=[1],
        fields=["id", "name", "email"]
    )
    print(pretty(partner))

    print()
    print("=" * 60)
    print("Partner Search (IDs)")
    print("=" * 60)
    partner_ids = client.search(model="res.partner")
    print(f"Found {len(partner_ids)} Partner IDs:")
    print(partner_ids)

    print()
    print("=" * 60)
    print("[SUCCESS] All test queries completed successfully.")
    print("Full output has been written to: output.log")
    print("=" * 60)

finally:
    # Ensure log file buffer is flushed and closed cleanly
    sys.stdout = tee.terminal
    tee.close()
