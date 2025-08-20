import os
import json
from FreeNet.Commons import BASE_DIR
KNOWN_HOSTS_DB = os.path.join(BASE_DIR, "known_hosts.json.enc")
from FreeNet.IdentityHandler import getIdentity

def save_known_host(entry: dict):

    identity = getIdentity()
    if not identity:
        print("❌ Error: Could not retrieve identity. Aborting save.")
        return

    destination = entry.get("destination", "").strip().lower()
    hostname = entry.get("hostname", "").strip().lower()
    page_title = entry.get("page_title", "")

    if not destination or not hostname:
        # print("❌ Invalid entry: 'destination' and 'hostname' are required")
        return

    db = {}
    if os.path.exists(KNOWN_HOSTS_DB):
        try:
            with open(KNOWN_HOSTS_DB, "rb") as f:
                encrypted_data = f.read()
                decrypted = identity.decrypt(encrypted_data)
                db = json.loads(decrypted.decode("utf-8"))
        except Exception as e:
            # print(f"⚠️ Failed to load existing DB, starting fresh: {e}")
            db = {}

    # ✅ Prevent hostname stealing — check normalized
    for existing_dest, info in db.items():
        existing_hostname = info.get("hostname", "").strip().lower()
        if existing_hostname == hostname and existing_dest != destination:
            # print(f"⚠️ Hostname '{hostname}' is already registered to another destination. Skipping.")
            return

    # ✅ Save or update (allowed if same destination)
    db[destination] = {"hostname": hostname, "page_title": page_title}

    try:
        plaintext = json.dumps(db, indent=2).encode("utf-8")
        encrypted = identity.encrypt(plaintext)

        with open(KNOWN_HOSTS_DB, "wb") as f:
            f.write(encrypted)

        # print(f"✅ Saved known host: {hostname} → {destination}")
        print(f"📘 Current DB: {json.dumps(db, indent=2)}")
    except Exception as e:
        print(f"❌ Error saving host DB: {e}")

def load_known_hosts() -> dict:

    identity = getIdentity()
    if not identity:
        # print("❌ Error: Could not retrieve identity. Cannot load known hosts.")
        return {}

    if not os.path.exists(KNOWN_HOSTS_DB):
        return {}

    try:
        with open(KNOWN_HOSTS_DB, "rb") as f:
            encrypted = f.read()
            decrypted = identity.decrypt(encrypted)
            return json.loads(decrypted.decode("utf-8"))
    except Exception as e:
        # print(f"❌ Failed to load known hosts: {e}")
        return {}

def resolve_hostname_to_destination(hostname: str) -> str | None:
    hosts = load_known_hosts()
    hostname = hostname.strip().lower()

    # 1. Check if the input is already a known destination hash
    if hostname in hosts:
        return hostname

    # 2. Otherwise, search by hostname
    for dest_hash, entry in hosts.items():
        if entry.get("hostname") == hostname:
            return dest_hash

    return None

def get_known_hosts_list(search: str | None = None) -> list[dict]:
    hosts = load_known_hosts()

    results = []

    # Normalize search input
    search = search.strip().lower() if search else None

    for destination, info in hosts.items():
        hostname = info.get("hostname", "Unknown Host").strip()
        page_title = info.get("page_title", "Unknown Page Title").strip()

        # If a search term is provided, skip entries that don't match
        if search and search not in hostname.lower() and search not in destination.lower():
            continue

        results.append({
            "icon": None,
            "title": page_title,
            "subtitle": hostname
        })

    return results

def delete_known_host_by_hostname(hostname: str) -> bool:
    identity = getIdentity()
    if not identity:
        # print("❌ Could not retrieve identity. Aborting delete.")
        return False

    if not os.path.exists(KNOWN_HOSTS_DB):
        return False

    hostname = hostname.strip().lower()

    try:
        with open(KNOWN_HOSTS_DB, "rb") as f:
            encrypted = f.read()
            decrypted = identity.decrypt(encrypted)
            db = json.loads(decrypted.decode("utf-8"))

        # Find the destination hash for the given hostname
        destination_to_delete = None
        for dest, info in db.items():
            if info.get("hostname", "").strip().lower() == hostname:
                destination_to_delete = dest
                break

        if destination_to_delete:
            del db[destination_to_delete]

            plaintext = json.dumps(db, indent=2).encode("utf-8")
            encrypted = identity.encrypt(plaintext)
            with open(KNOWN_HOSTS_DB, "wb") as f:
                f.write(encrypted)

            return True
        else:
            return False
    except Exception as e:
        return False
