import os
import threading
import json
import RNS
import RNS.vendor.umsgpack as umsgpack
from RNS.Identity import Identity
from RNS.vendor.configobj import UnknownType
import RNS.vendor.umsgpack as umsgpack
from FreeNet.IdentityHandler import getIdentity
from FreeNet.DnsHandler import save_known_host, load_known_hosts, resolve_hostname_to_destination
import threading
from FreeNet.Commons import BASE_DIR, APP_NAME, APP_TYPE, DATA_TYPE
from FreeNet.ServerConfigHandler import load_user_config

ANNOUNCE_INTERVAL = 60  # 10 minutes

import os
import threading
import RNS
import RNS.vendor.umsgpack as umsgpack
import json

APP_TIMEOUT = 30.0

##########################################################
#### Server Part #########################################
##########################################################

serve_path = None

# This initialisation is executed when the users chooses
# to run as a server
def server(destination: RNS.Destination, path):
    global serve_path
    serve_path = path

    destination.set_link_established_callback(client_connected)
    destination.set_proof_strategy(RNS.Destination.PROVE_ALL)

    threading.Timer(60.0, announceLoop, args=[destination]).start()

def announceLoop(destination):
    RNS.log("File server "+RNS.prettyhexrep(destination.hash)+" running")
    RNS.log("Hit enter to manually send an announce (Ctrl-C to quit)")

    config = load_user_config()
    if config:
        data = {
            "hostname": config.get("hostname"),
            "page_title": config.get("title")
        }

        # Convert dict to JSON string, then to bytes
        app_data_bytes = json.dumps(data).encode("utf-8")

        destination.set_proof_strategy(RNS.Destination.PROVE_ALL)
        # Send the announce including the app data
        destination.announce(app_data=app_data_bytes)
        RNS.log(
            "Sent announce from "+
            RNS.prettyhexrep(destination.hash)+
            " ("+destination.name+")"
        )

    threading.Timer(45.0, announceLoop, args=[destination]).start()

def list_files():
    # We add all entries from the directory that are
    # actual files, and does not start with "."
    global serve_path
    files = [file for file in os.listdir(serve_path) if os.path.isfile(os.path.join(serve_path, file)) and file[:1] != "."]
    RNS.log("Listing files in directory: "+str(files)+" directory: "+serve_path)
    return files

def client_connected(link):
    # Check if the served directory still exists
    if os.path.isdir(serve_path):
        RNS.log("Client connected, sending file list...")

        link.set_link_closed_callback(client_disconnected)

        # We pack a list of files for sending in a packet
        data = umsgpack.packb(list_files())

        # Check the size of the packed data
        if len(data) <= RNS.Link.MDU:
            list_packet = RNS.Packet(link, data)
            list_receipt = list_packet.send()
            list_receipt.set_timeout(APP_TIMEOUT)
            list_receipt.set_delivery_callback(list_delivered)
            list_receipt.set_timeout_callback(list_timeout)
        else:
            RNS.log("Too many files in served directory!", RNS.LOG_ERROR)
            RNS.log("You should implement a function to split the filelist over multiple packets.", RNS.LOG_ERROR)
            RNS.log("Hint: The client already supports it :)", RNS.LOG_ERROR)

        link.set_packet_callback(client_request)
    else:
        RNS.log("Client connected, but served path no longer exists!", RNS.LOG_ERROR)
        link.teardown()

def client_disconnected(link):
    RNS.log("Client disconnected")

def client_request(message, packet):
    global serve_path

    try:
        filename = message.decode("utf-8")
    except Exception as e:
        filename = None

    if filename in list_files():
        try:
            # If we have the requested file, we'll
            # read it and pack it as a resource
            RNS.log("Client requested \""+filename+"\"")
            file = open(os.path.join(serve_path, filename), "rb")

            file_resource = RNS.Resource(
                file,
                packet.link,
                callback=resource_sending_concluded
            )

            file_resource.filename = filename
        except Exception as e:
            # If somethign went wrong, we close
            # the link
            RNS.log("Error while reading file \""+filename+"\"", RNS.LOG_ERROR)
            packet.link.teardown()
            raise e
    else:
        # If we don't have it, we close the link
        RNS.log("Client requested an unknown file")
        packet.link.teardown()

def resource_sending_concluded(resource):
    if hasattr(resource, "filename"):
        name = resource.filename
    else:
        name = "resource"

    if resource.status == RNS.Resource.COMPLETE:
        RNS.log("Done sending \""+name+"\" to client")
    elif resource.status == RNS.Resource.FAILED:
        RNS.log("Sending \""+name+"\" to client failed")

def list_delivered(receipt):
    RNS.log("The file list was received by the client")

def list_timeout(receipt):
    RNS.log("Sending list to client timed out, closing this link")
    link = receipt.destination
    link.teardown()
