import socket
import pickle #data serialization
import errno
import urllib.request
import miniupnpc
import subprocess #executer commande
import ctypes #savoir si t'es admin


class NetworkManager:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = 5555
        self.connected = False

        # recup ip locale direct (rapide)
        self.local_ip = self._get_local_ip()
        self.public_ip = "recherche..."

    def _get_local_ip(self):
        try:
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

    def check_firewall_rule(self):
        # check si la regle existe deja via netsh
        # return true si la regle est trouvee
        cmd = 'netsh advfirewall firewall show rule name="RiftFighters"'
        try:
            # check=True va raise une erreur si la commande fail (donc si regle pas trouvee)
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            return False

    def open_firewall(self):
        # lance la demande d'ouverture (uac si besoin)
        rule_name = "RiftFighters"
        params = f'advfirewall firewall add rule name="{rule_name}" dir=in action=allow protocol=TCP localport={self.port}'

        if self._is_admin():
            try:
                subprocess.run(f'netsh {params}', shell=True, check=True, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                print("firewall config ok (admin mode)")
            except:
                pass
        else:
            print("demande elevation uac pr firewall...")
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", "netsh", params, None, 0)
            except Exception as e:
                print(f"err uac : {e}")

    def host_game(self):
        # note: on ne force plus le firewall ici !

        # 1. ip publique (upnp ou web)
        print("config du reseau...")
        try:
            upnp = miniupnpc.UPnP()
            upnp.discoverdelay = 200
            upnp.discover()
            upnp.selectigd()
            upnp.addportmapping(self.port, 'TCP', upnp.lanaddr, self.port, 'RiftFighters', '')
            self.public_ip = upnp.externalipaddress()
            print("config du réseau réussie !")
        except:
            print("config du réseau échouée (UPnP)")
            self.public_ip = "ouvrez le port 5555 de votre box vers ce pc"
            #try:
            #    self.public_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
            #except:
            #    self.public_ip = "inconnue"

        # 2. bind socket
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(("0.0.0.0", self.port))
            server.listen(1)
            server.setblocking(False)
            print(f"server ready sur {self.local_ip}:{self.port}")
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
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK: pass
                return None
        return None