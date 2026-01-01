import socket
import pickle
import errno


class NetworkManager:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = 5555
        self.connected = False

    def host_game(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(("0.0.0.0", self.port))
            server.listen(1)
            server.setblocking(False)  # Important : ne pas bloquer le main thread
            print("En attente (Host)...")
            return server
        except Exception as e:
            print(f"Erreur Host : {e}")
            return None

    def accept_client(self, server_socket):
        """fonction a appeler dans la boucle tant que pas connecté"""
        try:
            conn, addr = server_socket.accept()
            conn.setblocking(False)  # Le client aussi est non-bloquant
            self.client = conn
            self.connected = True
            print(f"Connecté à {addr}")
            return "HOST"
        except BlockingIOError:
            return None  # Personne n'est encore là

    def join_game(self, ip):
        try:
            self.client.connect((ip, self.port))
            self.client.setblocking(False)
            self.connected = True
            return "CLIENT"
        except Exception as e:
            print(f"Erreur Join : {e}")
            return None

    def send(self, data):
        if self.connected:
            try:
                self.client.send(pickle.dumps(data))
            except socket.error as e:
                print(e)

    def receive(self):
        """tente de lire des données sans bloquer le jeu ( c important de pas bloquer le jeu aka freeze)"""
        if self.connected:
            try:
                data = self.client.recv(4096)
                if not data: return None
                return pickle.loads(data)
            except socket.error as e:
                # éafaéz"f
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print(f"Erreur Socket: {e}")
                return None
        return None