import datetime
from xmlrpc.client import ServerProxy

SERVER = "http://localhost:5000/"

with ServerProxy(SERVER, allow_none=True) as proxy:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    proxy.register_buffer("nodes", "lowerleft")
    proxy.update_row("nodes", "pi-1", "pi1: Ready")
    proxy.update_row("nodes", "pi-4", "pi2: Offline")
    proxy.update_row("nodes", "pi-3", "pi3: DiskPressure")
    proxy.update_row("nodes", "pi-2", "pi4: MemPressure") 

    proxy.register_buffer("time", "upperleft")
    proxy.update_row("time", "0", timestamp)


    proxy.register_buffer("ip", "upperright")
    proxy.update_row("ip", "0", "192.168.234.32")

# todo: daemonset client to update to swag-pi-1:port


# # On Shutdown / Offline
# 8 bit dino

# # When Online
# <Master IP>                                           <Date/Timestamp>

# pi<num> - <k8s node status> - <num> pods
