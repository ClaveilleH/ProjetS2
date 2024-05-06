import sys, os, signal, socket, select, random, time
"""
Script du jeu coté serveur
https://webusers.i3s.unice.fr/~elozes/enseignement/systeme/
127.0.0.1
python3 chat_killer_server.py 127.0.0.1 25565
"""
HOST = "127.0.0.1" 
MAXBYTES = 4096
BEAT_TIMEOUT = 5
BEAT_CHECK = 5


def console(server):
    line = os.read(0, MAXBYTES).decode()
    if line[0] == '!':
        line = line[1:]
        if line == "quit\n":
            print("Closing all connections and server...")
            for c in server.socketList:
                if c != server.socket and c != 0:
                    c.close()

                    server.nb_clients -= 1
            server.socket.close()

        elif line == "list\n":
            print(server.get_list())
        
    elif line[0] == '@':
        pseudo, command = line.split(1)[0]
        if pseudo in server.dicoPseudo.keys():
            sock = server.dicoPseudo[pseudo]
            if sock in server.socketList:
                pass
            else:
                print(f"Le client {pseudo} n'est pas connecté.")
                return
            
            if command == '!ban':
                sock.send(str("!!BAN\n").encode())
                server.disconnect_client(sock)
            elif command == '!suspend':
                sock.send(str("!!MUTE\n").encode())
            elif command == '!forgive':
                sock.send(str("!!UNMUTE\n").encode())
            else:
                print("Commande invalide")


        else:
            print(f"Le pseudo {pseudo} n'existe pas.")
        
            
    else:
        if line.split()[0] == 'wall':
            msg = str("server: " + line.split(' ', 1)[1]).encode()
            server.mess_all(msg)
        elif line.split()[0] == 'kick':
            pseudo = line.split()[1]
            if pseudo in server.dicoClients.values():
                for c in server.socketList:
                    if c != server.socket and c != 0:
                        if server.dicoClients[c][2] == pseudo:
                            c.close()
                            server.nb_clients -= 1
                            print(f"Kicking {pseudo}...")
            else:
                print(f"Le pseudo {pseudo} n'existe pas.")
        else:
            print(line)


def message_client(sock, server):
    """
    Fonction qui traite les messages des clients
    """
    try:
        message = sock.recv(MAXBYTES)
    except OSError as e:
        print("Erreur: ", e)
        server.disconnect_client(sock)
        return
    if len(message) == 0:
        pass
    else:
        text = message.decode()
        if text[:2] == "!!":
            text = text[2:]
            if text == "BEAT":
                server.dicoClients[sock] = (server.dicoClients[sock][0], server.dicoClients[sock][1], server.dicoClients[sock][2], server.dicoClients[sock][3], time.time())
                sock.send(str("!!BEAT\n").encode())
            elif text == "QUIT\n" or text == "quit\n":
                server.disconnect_client(sock)
                print(f"Client {server.dicoClients[sock][2]} disconnected")
            elif text[:8] == "message ":
                text = text[8:]
                if text == '!list\n':
                    sock.send(server.get_list().encode())

                elif text[0] == '@':
                    if ' ' not in text:
                        print("Erreur: message invalide")
                    pseudo = text.split()[0][1:]
                    _, message = text.split(' ', 1)

                    if pseudo == 'admin':
                        print("Message de " + server.dicoClients[sock][2] + " : " + message)

                    elif pseudo in server.dicoPseudo.keys():
                        server.dicoPseudo[pseudo].send(str(f"(wisper){server.dicoClients[sock][2]}: {message}").encode())

                    else:
                        sock.send(str("Le pseudo n'existe pas\n").encode())
                else:
                    msg = str(f"{server.dicoClients[sock][2]}: {text}").encode()
                    server.mess_all(msg)
            else:   
                print("->>>>" + text)
        elif text[0] == '!':
            text = text[1:]
            if text == "list\n":
                msg = server.get_list() + '\n'
                sock.send(msg.encode())
            else:
                print("-2>>>>" + text)
        else:
            print("---->" + text)

class Server:
    def __init__(self, serversocket) -> None:
        self.nb_clients = 0
        self.socket = serversocket
        self.socketList = [serversocket, 0] # liste des sockets à surveiller
        self.dicoPseudo = {} # dictionnaire Pseudo -> socket
        self.dicoClients = {} # dictionnaire socket -> (address, socket, pseudo, cookie, last_beat)

    def get_list(self):
        txt = "Liste des clients :"
        for pseudo in self.dicoPseudo.keys():
            txt += '\n' + pseudo + '\t| '
            if pseudo in self.socketList:
                txt += "CONNECTED"
            else:
                txt += "DISCONNECTED"
        return txt

    def mess_all(self, msg):
        """
        Envoi le message msg à tous les clients
        :msg: message à envoyer (bytes)
        :server.socketList: liste des sockets à qui envoyer le message
        :sendersocket: socket qui a envoyé le message
        """
        for c in self.socketList:
            if c != self.socket and c != 0:
                try:
                    c.send(msg)
                except BrokenPipeError:
                    print("Erreur: client introuvable")
                    self.disconnect_client(c)
                except Exception as e:
                    print("Erreur: ", e)
    
    def disconnect_client(self, c):  
        """
        deconnecte un client
        ne supp pas des dico car le client peut se reconnecter
        :c: socket du client à déconnecter
        :server.socketList: liste des sockets à surveiller
        """
        c.close()
        self.socketList.remove(c)
        self.nb_clients -= 1
    
    def new_client(self):
        (clientsocket, address) = self.socket.accept()
        self.socketList.append(clientsocket)
        #! faire un select ppur eviter de bloquer
        txt = clientsocket.recv(MAXBYTES).decode()
        pseudo = None
        if txt[:8] == "!pseudo:":
            pseudo = txt.split()[1]
            if pseudo in self.dicoPseudo.keys():
                clientsocket.send(str("!!wrong_pseudo\n").encode())
                pass
            else:
                self.dicoPseudo[pseudo] = clientsocket
                self.dicoClients[clientsocket] = (address, clientsocket, pseudo, time.time())
                self.nb_clients += 1
                print("New client connected")
                self.mess_all(f"[+]{pseudo}!\n".encode())
        
        if txt[:8] == "!!cookie:":
            cookie = txt.split()[1]
            for key,val in self.dicoClients:
                if cookie == val[3]:
                    self.dicoClients[key] = (address, clientsocket, val[2], cookie[3], time.time())


        cookie = str(random.randint(999999, 9999999)) + '\n'
        ## recuperer le pseudo + gerer si le pseudo existe deja
        pseudo = "client" + str(self.nb_clients)

        self.dicoPseudo[pseudo] = clientsocket
        self.dicoClients[clientsocket] = (address, clientsocket, pseudo, cookie, time.time())
        self.nb_clients += 1
        clientsocket.send(str(f"!!cookie:{cookie}\n").encode())

        self.mess_all(f"[+]{pseudo}!\n".encode())
        print("New client connected")

def main():
    def alrm_handler(sig, frame):
        """
        Verifie si tous les clients ont envoyé un beat
        """
        now = time.time()
        for key in server.socketList:
            if key != server.socket and key != 0:
                if now - server.dicoClients[key][4] > BEAT_TIMEOUT:
                    print("Client {} timeout".format(server.dicoClients[key][2]))
                    server.disconnect_client(key)
        signal.alarm(BEAT_CHECK) # on remet l'alarme

    try:
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4, TCP
        serversocket.bind((HOST, PORT))
        serversocket.listen()
    except OSError as e:
        print("Error: ", e)
        sys.exit(1)
    except Exception as e:
        print("Error: ", e)
        sys.exit(1)
    #! pas sur de ces exceptions
    signal.signal(signal.SIGALRM, alrm_handler)

    server = Server(serversocket)


    first = True
    signal.alarm(BEAT_CHECK) # 5 secondes pour envoyer un beat
    print("Server started")
    while server.nb_clients > 0 or first:
        first = False
        # try:
        # print(server.socketList)
        (activesockets, _, _) = select.select(server.socketList, [], []) 

        # except Exception as e:
        #     print("Erreur: ", e)
        #     sys.exit(1)
        #! gerer les exceptions

        for sock in activesockets:
            if not sock in server.socketList:
                # print("Erreur: socket introuvable")
                continue

            if sock == serversocket:
                server.new_client()
            
            elif sock == 0:
                console(server)

            else:
                message_client(sock, server)
                



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: chat_killer_server.py <port>")
        sys.exit(1)

    PORT = int(sys.argv[1])
    
    
    main()

    sys.exit(0)
