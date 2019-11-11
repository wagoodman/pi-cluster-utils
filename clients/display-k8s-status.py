import socket
import fcntl
import struct
import datetime
import queue
import threading
import functools
import time
from xmlrpc.client import ServerProxy

import kubernetes


class Node():
    def __init__(self, event):
        self.event = event

    @property
    @functools.lru_cache()
    def identity(self):
        node = self.event['object']
        return node.status.node_info.machine_id

    @property
    @functools.lru_cache()
    def display_name(self):
        node = self.event['object']
        name = None
        for address in node.status.addresses:
            if address.type == "Hostname":
                name = address.address
                break
            if name == None:
                name = address.address

        if name == None:
            name = self.identity()
            if len(name) > 12:
                name = name[:12]

        return name

    @property
    @functools.lru_cache()
    def status(self):
        node = self.event['object']
        status = []
        for condition in node.status.conditions:
            if condition.type == "Ready":
                if condition.status == 'True':
                    status = ["Ready"] + status
                else:
                    status = ["NotReady"] + status

            elif condition.status == 'True':
                status.append(condition.type)

        return "|".join(status)


class NodeWatcher(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        kubernetes.config.load_kube_config()

        self.api = kubernetes.client.CoreV1Api()
        self.watcher = kubernetes.watch.Watch()
        self.nodes = {}
        self.queue = queue

        self.daemon = True

    def run(self):
        while True:
            try:
                for event in self.watcher.stream(self.api.list_node, pretty=True, _request_timeout=60):
                    node = Node(event)

                    self.nodes[node.identity] = node
                    self.queue.put(node)
                
            except Exception as e:
                print("error: %s" % repr(e))

            # hit timeout or error, retry
            time.sleep(3)

def get_ip_address(ifname='eth0'):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode('utf-8'))
    )[20:24])

def report_status(q):
    last_display = None
    nodes = {} #{id: node}

    with ServerProxy("http://localhost:5000/", allow_none=True) as proxy:

        proxy.register_buffer("status", "lowerleft", 12)

        while True:
            node = q.get()
            nodes[node.display_name] = node

            timestamp = datetime.datetime.now()
            print("%s %s %s %s" % (timestamp, node.identity, node.display_name, node.status))

            num_ready_nodes = len([n for n in nodes.values() if node.status == "Ready"])
            status = "Ready: {}".format(num_ready_nodes)
            ip = get_ip_address()
            display = (ip, status)

            # only update the display if there is a display change
            if last_display != display :
                proxy.update_row("nodes", "0", status)
                proxy.update_row("nodes", "1", ip)

                last_display = display



def report_status_verbose(q):
    last_update = datetime.datetime.now()
    last_status = {}


    with ServerProxy("http://localhost:5000/", allow_none=True) as proxy:

        proxy.register_buffer("nodes", "lowerleft")
        proxy.register_buffer("time", "upperleft")
        proxy.register_buffer("ip", "upperright")

        while True:
            node = q.get()
            timestamp = datetime.datetime.now()

            print("%s %s %s %s" % (timestamp, node.identity, node.display_name, node.status))

            elapsed = timestamp - last_update

            status = "{}: {}".format(node.display_name, node.status)

            # only update the display if there is a display change (or it has been a minute since the last update)
            if last_status.get(node.display_name) != status or elapsed > datetime.timedelta(minutes=1): 
                proxy.update_row("time", "0", timestamp.strftime("%Y-%m-%d %H:%M:%S"))
                proxy.update_row("ip", "0", get_ip_address())
                proxy.update_row("nodes", node.display_name, status)

                last_update = timestamp

            last_status[node.display_name] = status

def main():
    q = queue.Queue()
    watcher = NodeWatcher(q)
    watcher.start()

    while True:
        try:
            report_status(q)
        except Exception as e:
            print("error: %s" % repr(e))
            time.sleep(10)

    print("exiting...")




if __name__ == '__main__':
    main()