import socket
import json
import miniupnpc
import time
import subprocess
import ctypes


class NetworkManager:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.port = 6767
        self.connected = False
        self.peer_addr = None  #(IP, Port) de ladversaire

        self.local_seq = 0
        self.highest_remote_seq = 0

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
        # Vérifie spécifiquement si la règle UDP existe pour RiftFighters
        cmd = 'netsh advfirewall firewall show rule name="RiftFighters_UDP"'
        try:
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            return False

    def open_firewall(self):
        # Lance la demande d'ouverture UAC pour le protocole UDP
        rule_name = "RiftFighters_UDP"
        params = f'advfirewall firewall add rule name="{rule_name}" dir=in action=allow protocol=UDP localport={self.port}'

        if self._is_admin():
            try:
                subprocess.run(f'netsh {params}', shell=True, check=True, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                print("Pare-feu Windows configuré avec succès pour l'UDP.")
            except Exception as e:
                print(f"Erreur pare-feu (admin) : {e}")
        else:
            print("Demande d'élévation administrateur pour le pare-feu...")
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", "netsh", params, None, 0)
            except Exception as e:
                print(f"Erreur UAC : {e}")

    def host_game(self):
        print("Configuration de la box Internet (UPnP)...")
        try:
            upnp = miniupnpc.UPnP()
            upnp.discoverdelay = 200
            upnp.discover()
            upnp.selectigd()
            # Demande à la box de rediriger le port UDP 6767 vers ce PC
            upnp.addportmapping(self.port, 'UDP', upnp.lanaddr, self.port, 'RiftFighters_UDP', '')
            self.public_ip = upnp.externalipaddress()
            print(f"UPnP réussi ! IP Publique : {self.public_ip}")
        except Exception as e:
            print(f"UPnP échoué: {e}")
            self.public_ip = f"Échec UPnP (Ouvrez UDP {self.port} manuellement)"

        try:
            self.sock.bind(("0.0.0.0", self.port))
            self.sock.setblocking(False)
            print(f"Serveur UDP prêt sur le port {self.port}")
            return self.sock
        except Exception as e:
            print(f"Erreur lors de l'ouverture du serveur : {e}")
            return None

    def accept_client(self, server_socket, host_character="Cromagnon"):
        """Attente asynchrone d'un message JOIN du client, avec échange des persos"""
        try:
            data, addr = self.sock.recvfrom(1024)
            msg = json.loads(data.decode('utf-8'))

            if msg.get("type") == "JOIN":
                self.peer_addr = addr
                self.connected = True
                client_character = msg.get("character", "Cromagnon")

                # Répond pour confirmer la connexion en envoyant le perso de l'Hôte
                self.sock.sendto(json.dumps({
                    "type": "ACCEPT",
                    "character": host_character
                }).encode('utf-8'), self.peer_addr)

                print(f"Adversaire connecté depuis {addr} avec le perso {client_character} !")
                return client_character
        except BlockingIOError:
            pass  # On attend
        except Exception as e:
            print(f"Erreur accept_client : {e}")

        return None

    def join_game(self, ip, client_character="Cromagnon"):
        """Tentative de connexion vers l'Hôte en envoyant son perso"""
        self.peer_addr = (ip, self.port)
        self.sock.settimeout(2.0)

        try:
            print(f"Tentative de connexion à {self.peer_addr}...")
            join_msg = json.dumps({
                "type": "JOIN",
                "character": client_character
            }).encode('utf-8')

            # Envoi redondant en UDP pour être sûr que ça passe
            for _ in range(3):
                self.sock.sendto(join_msg, self.peer_addr)
                time.sleep(0.1)

            data, addr = self.sock.recvfrom(1024)
            msg = json.loads(data.decode('utf-8'))
            if msg.get("type") == "ACCEPT" and addr == self.peer_addr:
                self.connected = True
                self.sock.setblocking(False)
                host_character = msg.get("character", "Cromagnon")
                print(f"Connecté au Host ! Il joue {host_character}")
                return host_character
        except socket.timeout:
            print("Délai d'attente dépassé. L'Hôte est injoignable.")
        except Exception as e:
            print(f"Erreur join_game : {e}")

        self.sock.setblocking(False)
        return None

    def send(self, data, ack_seq=0):
        if self.connected and self.peer_addr:
            self.local_seq += 1
            payload = {"seq": self.local_seq, "ack_seq": ack_seq, "data": data}
            try:
                msg = json.dumps(payload).encode('utf-8')
                self.sock.sendto(msg, self.peer_addr)
            except BlockingIOError:
                pass

    def receive(self):
        if not self.connected:
            return None

        latest_data = None
        latest_ack = 0
        try:
            # On vide le buffer réseau et on ne garde que le message le plus récent
            while True:
                data, addr = self.sock.recvfrom(4096)
                if addr == self.peer_addr:
                    msg = json.loads(data.decode('utf-8'))

                    if msg.get("type") in ["JOIN", "ACCEPT"]:
                        continue

                    seq = msg.get("seq", 0)
                    if seq > self.highest_remote_seq:
                        self.highest_remote_seq = seq
                        latest_data = msg.get("data")
                        latest_ack = msg.get("ack_seq", 0)
        except BlockingIOError:
            pass
        except Exception as e:
            pass

        if latest_data is not None:
            return {"data": latest_data, "seq": self.highest_remote_seq, "ack_seq": latest_ack}
        return None