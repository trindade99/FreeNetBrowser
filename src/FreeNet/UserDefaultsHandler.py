import os
import json
from FreeNet.Commons import BASE_DIR
FAVOURITES_DB = os.path.join(BASE_DIR, "favourites.json.enc")
from FreeNet.IdentityHandler import getIdentity

def save_favorite(url: str, title: str):
    identity = getIdentity()
    if not identity:
        # print("❌ Could not retrieve identity. Aborting save.")
        return

    db = {}
    if os.path.exists(FAVOURITES_DB):
        try:
            with open(FAVOURITES_DB, "rb") as f:
                decrypted = identity.decrypt(f.read())
                db = json.loads(decrypted.decode("utf-8"))
        except Exception as e:
            print(f"⚠️ Failed to load favorites DB: {e}")

    db[url] = {
        "title": title,
        "url": url
    }

    try:
        encrypted = identity.encrypt(json.dumps(db, indent=2).encode("utf-8"))
        with open(FAVOURITES_DB, "wb") as f:
            f.write(encrypted)
        # print(f"✅ Saved favorite: {title}")
    except Exception as e:
        print(f"❌ Error saving favorite: {e}")

def get_favorites_list(search: str = "") -> list:
    identity = getIdentity()
    if not identity or not os.path.exists(FAVOURITES_DB):
        return []

    try:
        with open(FAVOURITES_DB, "rb") as f:
            decrypted = identity.decrypt(f.read())
            db = json.loads(decrypted.decode("utf-8"))
            result = []
            for url, entry in db.items():
                title = entry.get("title", "Untitled")
                if search.lower() in title.lower() or search.lower() in url.lower():
                    result.append({
                        "icon": None,
                        "title": title,
                        "subtitle": url
                    })
            return result
    except Exception as e:
        # print(f"❌ Error loading favorites: {e}")
        return []

def delete_favorite(url: str) -> bool:
    identity = getIdentity()
    if not identity or not os.path.exists(FAVOURITES_DB):
        return False

    try:
        with open(FAVOURITES_DB, "rb") as f:
            decrypted = identity.decrypt(f.read())
            db = json.loads(decrypted.decode("utf-8"))

        if url in db:
            del db[url]
            encrypted = identity.encrypt(json.dumps(db, indent=2).encode("utf-8"))
            with open(FAVOURITES_DB, "wb") as f:
                f.write(encrypted)
            # print(f"✅ Deleted favorite: {url}")
            return True
        else:
            # print(f"⚠️ Favorite not found: {url}")
            return False
    except Exception as e:
        # print(f"❌ Error deleting favorite: {e}")
        return False


def is_favorite(url: str) -> bool:
    identity = getIdentity()
    if not identity:
        # print("❌ Could not retrieve identity.")
        return False

    if not os.path.exists(FAVOURITES_DB):
        return False

    try:
        with open(FAVOURITES_DB, "rb") as f:
            encrypted = f.read()
            decrypted = identity.decrypt(encrypted)
            db = json.loads(decrypted.decode("utf-8"))

        return url in db
    except Exception as e:
        # print(f"❌ Error checking favorites: {e}")
        return False
