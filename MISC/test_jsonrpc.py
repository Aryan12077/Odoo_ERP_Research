import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

url = os.getenv("ODOO_URL")
db = os.getenv("ODOO_DB")
username = os.getenv("ODOO_USERNAME")
secret = os.getenv("ODOO_SECRET")

jsonrpc_url = f"{url}/jsonrpc"

# -----------------------------
# Authenticate
# -----------------------------
payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "common",
        "method": "authenticate",
        "args": [
            db,
            username,
            secret,
            {}
        ]
    },
    "id": 1
}

response = requests.post(jsonrpc_url, json=payload)
response.raise_for_status()

result = response.json()

print("Authentication Response:")
print(result)

uid = result.get("result")

print(f"\nUID: {uid} ({type(uid)})")

if uid:

    # -----------------------------
    # Fetch Users
    # -----------------------------
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "object",
            "method": "execute_kw",
            "args": [
                db,
                uid,
                secret,
                "res.users",
                "search_read",
                [[]],
                {
                    "fields": [
                        "id",
                        "name",
                        "login"
                    ]
                }
            ]
        },
        "id": 2
    }

    users = requests.post(jsonrpc_url, json=payload).json()["result"]
    print("\nUsers:")
    print(users)

    # -----------------------------
    # Fetch Partners
    # -----------------------------
    payload["params"]["args"][3] = "res.partner"
    payload["params"]["args"][5] = [[]]
    payload["params"]["args"][6] = {
        "fields": [
            "id",
            "name",
            "email"
        ]
    }

    partners = requests.post(jsonrpc_url, json=payload).json()["result"]
    print("\nPartners:")
    print(partners)

    # -----------------------------
    # Partner Count
    # -----------------------------
    payload["params"]["args"] = [
        db,
        uid,
        secret,
        "res.partner",
        "search_count",
        [[]]
    ]

    count = requests.post(jsonrpc_url, json=payload).json()["result"]

    print("\nPartner Count:")
    print(count)

    # -----------------------------
    # Read Partner ID = 1
    # -----------------------------
    payload["params"]["args"] = [
        db,
        uid,
        secret,
        "res.partner",
        "read",
        [[1]],
        {
            "fields": [
                "id",
                "name",
                "email"
            ]
        }
    ]

    partner = requests.post(jsonrpc_url, json=payload).json()["result"]

    print("\nPartner Read:")
    print(partner)

else:
    print("\nAuthentication Failed!")