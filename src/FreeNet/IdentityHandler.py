import os
import RNS
from RNS.Identity import Identity
import RNS.vendor.umsgpack as umsgpack

def getIdentity() -> RNS.Identity|None:
    from FreeNet.Commons import BASE_DIR
    identity_path = os.path.join(BASE_DIR, "Identity")
    server_identity: RNS.Identity|None = None

    # Check if the identity file exists
    if os.path.exists(identity_path):
        server_identity = RNS.Identity.from_file(identity_path)
    else:
        server_identity = RNS.Identity()
        RNS.Identity.to_file(server_identity, identity_path)

    return server_identity
