import socket
import pickle
import errno
import urllib.request
import miniupnpc
import subprocess
import ctypes


class NetworkManager:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = 5555
        self.connected = False

        # recup ip locale direct (rapide)
        self.local_ip = self._get_local_ip()
        self.public_ip = "recherche..."  # sera set dans host_game

    def _get_local_ip(self):
        # recup l'ip du lan
        try:
            # ping un dns public (google) juste pr choper l'interface reseau active
            # envoie rien en vrai
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def _is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def _open_firewall(self):
        # open port 5555 ds le firewall windows
        if not self._is_admin(): return

        # cmd netsh pr add rule tcp in
        cmd = f'netsh advfirewall firewall add rule name="RiftFighters" dir=in action=allow protocol=TCP localport={self.port}'
        try:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

    def host_game(self):
        # 1. config firewall
        self._open_firewall()

        # 2. ip publique (upnp ou web)
        print("config du reseau...")
        try:
            # try upnp
            upnp = miniupnpc.UPnP()
            upnp.discoverdelay = 200
            upnp.discover()
            upnp.selectigd()
            # map external -> internal
            upnp.addportmapping(self.port, 'TCP', upnp.lanaddr, self.port, 'RiftFighters', '')
            self.public_ip = upnp.externalipaddress()
        except:
            # fallback api web si upnp fail
            try:
                self.public_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
            except:
                self.public_ip = "inconnue"

        # 3. bind socket
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(("0.0.0.0", self.port))
            server.listen(1)
            server.setblocking(False)  # non-blocking pr pas freeze le thread
            print(f"server ready sur {self.local_ip} (lan) / {self.public_ip} (wan)")
            return server
        except Exception as e:
            print(f"err host : {e}")
            return None

    def accept_client(self, server_socket):
        try:
            conn, addr = server_socket.accept()
            conn.setblocking(False)
            self.client = conn
            self.connected = True
            return "HOST"
        except BlockingIOError:
            return None

    def join_game(self, ip):
        try:
            self.client.connect((ip, self.port))
            self.client.setblocking(False)
            self.connected = True
            return "CLIENT"
        except Exception as e:
            print(f"err join : {e}")
            return None

    def send(self, data):
        if self.connected:
            try:
                self.client.send(pickle.dumps(data))
            except:
                pass

    def receive(self):
        if self.connected:
            try:
                data = self.client.recv(4096)
                if not data: return None
                return pickle.loads(data)
            except socket.error as e:
                # ignore eagain/ewouldblock (normal en non-blocking)
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK: pass
                return None
        return None