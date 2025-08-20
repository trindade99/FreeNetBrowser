import os
import asyncio
import shutil
import json
import RNS
import RNS.vendor.umsgpack as umsgpack
from FreeNet.IdentityHandler import getIdentity
from FreeNet.DnsHandler import save_known_host, resolve_hostname_to_destination
from FreeNet.Commons import BASE_DIR, APP_NAME, APP_TYPE, DATA_TYPE
from FreeNet.AnnouncerHandler import server

APP_TIMEOUT = 45.0
destination = None

def ensure_server_pages_folder():
    # Use BASE_DIR from Commons instead of app.paths.data
    path = os.path.join(BASE_DIR, "serverPages")
    os.makedirs(path, exist_ok=True)
    return path

def initConfig(self):
    global destination
    server_identity = getIdentity()
    destination = RNS.Destination(
        server_identity,
        RNS.Destination.IN,
        RNS.Destination.SINGLE,
        APP_NAME,
        APP_TYPE,
        DATA_TYPE
    )
    destination.set_proof_strategy(RNS.Destination.PROVE_ALL)

    announce_handler = AnnounceHandler(
            aspect_filter=f"{APP_NAME}.{APP_TYPE}.{DATA_TYPE}"
    )
    # We register the announce handler with Reticulum
    RNS.Transport.register_announce_handler(announce_handler)
    path =  ensure_server_pages_folder()
    server(destination, path)
#     delayed_announceDns("freeNet://CasaDoCaralho.com", "Casinha do Zé")

# def delayed_announceDns(hostname, title, delay=5.0):
#     threading.Timer(delay, announceDns, args=[hostname, title]).start()

class AnnounceHandler:
    def __init__(self, aspect_filter=None):
        self.aspect_filter = aspect_filter

    def received_announce(self, destination_hash, announced_identity, app_data):
        RNS.log(
            "Received an announce from "+
            RNS.prettyhexrep(destination_hash) + " with identity " + str(announced_identity)
        )
        RNS.Identity.save_known_destinations()

        if app_data:
            decoded = json.loads(app_data.decode("utf-8"))
            entry = {
                "destination": destination_hash.hex(),  # Make sure it's hex string
                "hostname": decoded.get("hostname").strip().lower(),
                "page_title" : decoded.get("page_title")
            }
            save_known_host(entry)
            RNS.log(
                "The announce contained the following app data: "+
                str(json.loads(app_data.decode("utf-8")))
            )

def announceDns(hostname, title=""):
    global destination
    if destination is None:
        RNS.log("Error: destination not initialized. Did you call initConfig()?")
        return

    data = {
        "hostname": hostname,
        "page_title": title
    }

    app_data_bytes = json.dumps(data).encode("utf-8")
    destination.announce(app_data=app_data_bytes)

    RNS.log(
        "Sent announce from " +
        RNS.prettyhexrep(destination.hash) +
        " (" + (destination.name or "unnamed") + ")"
    )


def resolve_dns(hostname):
    return resolve_hostname_to_destination(hostname)


async def download_all_from_server(destination_hexhash, configpath, save_dir):

    loop = asyncio.get_running_loop()

    filelist_fut = loop.create_future()

    # sanity check
    dest_len = (RNS.Reticulum.TRUNCATED_HASHLENGTH // 8) * 2
    if len(destination_hexhash) != dest_len:
        raise ValueError(f"Destination length must be {dest_len} hexadecimal characters")

    destination_hash = bytes.fromhex(destination_hexhash)

    # clean save dir
    if os.path.exists(save_dir):
        for filename in os.listdir(save_dir):
            p = os.path.join(save_dir, filename)
            try:
                if os.path.isfile(p) or os.path.islink(p):
                    os.unlink(p)
                elif os.path.isdir(p):
                    shutil.rmtree(p)
            except Exception as e:
                RNS.log(f"⚠️ Failed to delete {p}: {e}")
    else:
        os.makedirs(save_dir, exist_ok=True)

    # ensure path known
    if not RNS.Transport.has_path(destination_hash):
        RNS.Transport.request_path(destination_hash)
        while not RNS.Transport.has_path(destination_hash):
            await asyncio.sleep(0.05)

    # build OUT destination & link
    server_identity = RNS.Identity.recall(destination_hash)
    server_destination = RNS.Destination(
        server_identity,
        RNS.Destination.OUT,
        RNS.Destination.SINGLE,
        APP_NAME,
        APP_TYPE,
        DATA_TYPE
    )

    link = RNS.Link(server_destination)

    # ---- link lifecycle sync ----
    link_up = loop.create_future()
    link_down = loop.create_future()

    def _on_established(l):
        RNS.log("🟢 Link established")
        if not link_up.done():
            loop.call_soon_threadsafe(link_up.set_result, True)

    def _on_closed(l):
        RNS.log("🔴 Link closed")
        if not link_down.done():
            loop.call_soon_threadsafe(link_down.set_result, True)

    link.set_link_established_callback(_on_established)
    link.set_link_closed_callback(_on_closed)

    # accept resources BEFORE anything else (avoid races)
    link.set_resource_strategy(RNS.Link.ACCEPT_ALL)

    # packets: file list
    def filelist_received(data, packet):
        try:
            fl = umsgpack.unpackb(data)
            RNS.log(f"📜 Received file list: {fl}")
            if not filelist_fut.done():
                loop.call_soon_threadsafe(filelist_fut.set_result, fl)
        except Exception as e:
            if not filelist_fut.done():
                loop.call_soon_threadsafe(filelist_fut.set_exception, e)

    link.set_packet_callback(filelist_received)

    # wait link
    await asyncio.wait_for(link_up, timeout=APP_TIMEOUT)

    # wait file list
    filelist = await asyncio.wait_for(filelist_fut, timeout=APP_TIMEOUT)
    if not isinstance(filelist, (list, tuple)):
        raise RuntimeError(f"Unexpected file list type: {type(filelist)}")

    downloaded_files = []

    async def download_file(filename: str):
        RNS.log(f"⬇️  Requesting {filename!r} ...")
        download_fut = loop.create_future()

        def _res_started(res):
            RNS.log(f"📦 Resource started for {filename}, size={res.size if hasattr(res,'size') else 'unknown'}")

        def _res_concluded(res):
            try:
                if res.status == RNS.Resource.COMPLETE:
                    # read while still open
                    data = res.data.read() if res.data else b""
                    RNS.log(f"✅ Resource complete for {filename}, bytes={len(data)}")
                    loop.call_soon_threadsafe(download_fut.set_result, data)
                else:
                    msg = f"Resource failed for {filename}, status={res.status}"
                    RNS.log(f"❌ {msg}")
                    loop.call_soon_threadsafe(download_fut.set_exception, RuntimeError(msg))
            except Exception as e:
                loop.call_soon_threadsafe(download_fut.set_exception, e)

        # install callbacks BEFORE sending request
        link.set_resource_started_callback(_res_started)
        link.set_resource_concluded_callback(_res_concluded)

        # send filename request packet
        pkt = RNS.Packet(link, filename.encode("utf-8"), create_receipt=False)
        sent = pkt.send()
        RNS.log(f"➡️  Filename packet sent={sent}")

        # wait for resource
        file_bytes = await asyncio.wait_for(download_fut, timeout=APP_TIMEOUT)

        # save
        save_path = os.path.join(save_dir, filename)
        base, ext = os.path.splitext(save_path)
        idx = 0
        while os.path.exists(save_path):
            idx += 1
            save_path = f"{base}_{idx}{ext}"

        with open(save_path, "wb") as f:
            f.write(file_bytes)
        downloaded_files.append(save_path)
        RNS.log(f"💾 Saved {filename} to {save_path}")

    # sequential for clarity
    for name in filelist:
        await download_file(name)

    # wrap up
    try:
        link.teardown()
    except Exception:
        pass

    return downloaded_files
