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



def disconnect_client(c, server):  
    """
    deconnecte un client
    ne supp pas des dico car le client peut se reconnecter
    :c: socket du client à déconnecter
    :server.socketList: liste des sockets à surveiller
    """
    c.close()
    server.socketList.remove(c)
    server.nb_clients -= 1

def mess_all(server, msg):
    """
    Envoi le message msg à tous les clients
    :msg: message à envoyer (bytes)
    :server.socketList: liste des sockets à qui envoyer le message
    :sendersocket: socket qui a envoyé le message
    """
    for c in server.socketList:
        if c != server.socket and c != 0:
                            # s.send(msg)
            try:
                c.send(msg)
            except BrokenPipeError:
                print("Erreur: client introuvable")
                disconnect_client(c, server)
            except Exception as e:
                print("Erreur: ", e)


def new_client(server):
    (clientsocket, address) = server.socket.accept()
    server.socketList.append(clientsocket)
    #! faire un select ppur eviter de bloquer
    txt = clientsocket.recv(MAXBYTES).decode()
    pseudo = None
    if txt[:8] == "!pseudo:":
        pseudo = txt.split()[1]
        if pseudo in server.dicoPseudo.keys():
            clientsocket.send(str("!!wrong_pseudo\n").encode())
            pass
        else:
            server.dicoPseudo[pseudo] = clientsocket
            server.dicoClients[clientsocket] = (address, clientsocket, pseudo, time.time())
            server.nb_clients += 1
            print("New client connected")
            mess_all(server, f"[+]{pseudo}!\n".encode())
    
    if txt[:8] == "!!cookie:":
        cookie = txt.split()[1]
        for key,val in server.dicoClients:
            if cookie == val[3]:
                server.dicoClients[key] = (address, clientsocket, val[2], cookie[3], time.time())


    cookie = str(random.randint(999999, 9999999)) + '\n'
    ## recuperer le pseudo gerer si le pseudo existe deja
    pseudo = "client" + str(server.nb_clients)

    server.dicoPseudo[pseudo] = clientsocket
    server.dicoClients[clientsocket] = (address, clientsocket, pseudo, cookie, time.time())
    server.nb_clients += 1
    clientsocket.send(str(f"!!cookie:{cookie}\n").encode())

    mess_all(server, f"[+]{pseudo}!\n".encode())
    print("New client connected")


def console(server):
    line = os.read(0, MAXBYTES).decode()
    if line[0] == '!':
        if line == "!quit\n":
            print("Closing all connections and server...")
            for c in server.socketList:
                if c != server.socket and c != 0:
                    c.close()

                    server.nb_clients -= 1
            server.socket.close()
            
    else:
        if line.split()[0] == 'wall':
            msg = str("server: " + line.split(' ', 1)[1]).encode()
            # mess_all(server.socketList, 0, msg)
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
        disconnect_client(sock, server)
        return
    if len(message) == 0:
        # run = False
        pass
    else:
        text = message.decode()
        if text[:2] == "!!":
            text = text[2:]
            if text == "BEAT":
                # print(f"Client {server.dicoClients[sock][2]} sent a beat")
                server.dicoClients[sock] = (server.dicoClients[sock][0], server.dicoClients[sock][1], server.dicoClients[sock][2], server.dicoClients[sock][3], time.time())
                sock.send(str("!!BEAT\n").encode())
            elif text == "QUIT\n" or text == "quit\n":
                disconnect_client(sock, server)
                print(f"Client {server.dicoClients[sock][2]} disconnected")
            elif text[:8] == "message ":
                text = text[8:]
                if text[0] == '@':
                    if ' ' not in text:
                        print("Erreur: message invalide")
                    pseudo = text.split()[0][1:]
                    print(pseudo)
                    _, message = text.split(' ', 1)
                    if pseudo in server.dicoPseudo.keys():
                        server.dicoPseudo[pseudo].send(str(f"(wisper){server.dicoClients[sock][2]}: {message}").encode())
                    else:
                        print(f"Le pseudo {pseudo} n'existe pas.")
                else:
                    msg = str(f"{server.dicoClients[sock][2]}: {text}").encode()
                    mess_all(server, msg)
            else:   
                print("->>>>" + text)
        else:
            print("---->" + text)

            # if text.split()[0] == "!!cookie:":
            #     cookie = text.split()[1]
            #     for key,val in server.dicoClients:
            #         if cookie == val[3]:
            #             server.dicoClients[key] = (server.dicoClients[key][0], server.dicoClients[key][1], server.dicoClients[key][2], cookie[3], time.time())

        if text[0] == '!': #commandes
            if text[1] == '!': #commandes serveur
                text = text[2:]
                if text == "quit\n":
                    pass
                elif text == "BEAT\n":
                    server.dicoClients[sock] = (server.dicoClients[sock][0], server.dicoClients[sock][1], server.dicoClients[sock][2], server.dicoClients[sock][3], time.time())
            
            # if text == "!list\n":
            #     sock.send(str("Liste des clients connectés:\n").encode())
            #     for c in server.socketList:
            #         if c != serversocket and c != 0:
            #             sock.send(str('-' + server.dicoClients[c][2] + "\n").encode())

            # elif text.split()[0] == "!pseudo":
            #     if server.dicoPseudo[s] == "anonymous":
            #         msg = str(f"[+]{text.split()[1]}\n").encode()
            #         mess_all(server.socketList, 0, msg)

            #     server.dicoPseudo[s] = text.split()[1]
            #     print(f"Connection from {server.dicoClients[s][2]} has changed pseudo to {server.dicoPseudo[s]}")
            #     server.dicoClients[s] = (server.dicoClients[s][0], server.dicoClients[s][1], text.split()[1])
    
class Server:
    def __init__(self, serversocket) -> None:
        self.nb_clients = 0
        self.socket = serversocket
        self.socketList = [serversocket, 0] # liste des sockets à surveiller
        self.dicoPseudo = {} # dictionnaire Pseudo -> socket
        self.dicoClients = {} # dictionnaire socket -> (address, socket, pseudo, cookie, last_beat)



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
                    disconnect_client(key, server)
        print("Timeout")
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
                new_client(server)
            
            elif sock == 0:
                console(server)

            else:
                message_client(sock, server)
                # message_client(sock, server.socketList, server.dicoClients, server.dicoPseudo)
                



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: chat_killer_server.py <port>")
        sys.exit(1)

    PORT = int(sys.argv[1])
    
    
    main()

    sys.exit(0)