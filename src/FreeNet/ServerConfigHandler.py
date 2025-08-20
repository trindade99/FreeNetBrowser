import os
import json
from FreeNet.Commons import BASE_DIR
from FreeNet.IdentityHandler import getIdentity

USER_CONFIG_FILE = os.path.join(BASE_DIR, "user_config.json.enc")

def sanitize_hostname(hostname: str) -> str:
    # Remove leading/trailing spaces
    hostname = hostname.strip()

    # Remove any protocol-like prefix (everything before and including "://")
    if "://" in hostname:
        hostname = hostname.split("://", 1)[1]

    # Ensure there's a "." (domain suffix), otherwise append ".com"
    if "." not in hostname:
        hostname += ".com"

    # Add the correct prefix
    return f"freenet://{hostname}"

def save_user_config(title: str, hostname: str):

    identity = getIdentity()
    if not identity:
        return

    config = {
        "title": title,
        "hostname": sanitize_hostname(hostname)
    }

    try:
        plaintext = json.dumps(config, indent=2).encode("utf-8")
        encrypted = identity.encrypt(plaintext)

        with open(USER_CONFIG_FILE, "wb") as f:
            f.write(encrypted)

        # print(f"✅ User config saved")
    except Exception as e:
        print(f"❌ Error saving user config: {e}")


def load_user_config() -> dict:
    identity = getIdentity()
    if not identity or not os.path.exists(USER_CONFIG_FILE):
        return {}

    try:
        with open(USER_CONFIG_FILE, "rb") as f:
            encrypted = f.read()
            decrypted = identity.decrypt(encrypted)
            return json.loads(decrypted.decode("utf-8"))
    except Exception as e:
        print(f"❌ Error loading user config: {e}")
        return {}
