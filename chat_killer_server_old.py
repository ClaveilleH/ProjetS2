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



def disconnect_client(c, socketList):  
    """
    deconnecte un client
    ne supp pas des dico car le client peut se reconnecter
    :c: socket du client à déconnecter
    :socketList: liste des sockets à surveiller
    """
    global nb_clients
    c.close()
    socketList.remove(c)
    nb_clients -= 1

def mess_all(socketList, sendersocket, msg):
    """
    Envoi le message msg à tous les clients
    :msg: message à envoyer (bytes)
    :socketList: liste des sockets à qui envoyer le message
    :sendersocket: socket qui a envoyé le message
    """
    for c in socketList:
        if c != serversocket and c != 0 and c != sendersocket:
                            # s.send(msg)
            try:
                c.send(msg)
            except BrokenPipeError:
                print("Erreur: client introuvable")
                disconnect_client(c, socketList)
            except Exception as e:
                print("Erreur: ", e)


def new_client(serversocket, socketList, dicoClients, dicoPseudo):
    global nb_clients
    (clientsocket, address) = serversocket.accept()
    socketList.append(clientsocket)
    
    txt = clientsocket.recv(MAXBYTES).decode()
    if txt[:8] == "!pseudo:":
        pseudo = txt.split()[1]
        if pseudo in dicoPseudo.keys():
            # le pseudo existe deja donc 
            pass
    
    if txt[:8] == "!cookie:":
        cookie = txt.split()[1]
        for key,val in dicoClients:
            if cookie == val[3]:
                dicoClients[key] = (address, clientsocket, val[2], cookie[3], time.time())


    cookie = str(random.randint(999999, 9999999))
    ## recuperer le pseudo gerer si le pseudo existe deja
    pseudo = "client" + str(nb_clients)

    dicoPseudo[pseudo] = clientsocket
    dicoClients[clientsocket] = (address, clientsocket, pseudo, cookie)
    nb_clients += 1

    mess_all(socketList, clientsocket, f"[+]{pseudo}!\n".encode())
    print("New client connected")


def console(serversocket, socketlist, dicoClients):
    global nb_clients
    line = os.read(0, MAXBYTES).decode()
    if line[0] == '!':
        if line == "!quit\n":
            print("Closing all connections and server...")
            for c in socketlist:
                if c != serversocket and c != 0:
                    c.close()

                    nb_clients -= 1
            serversocket.close()
            
    else:
        if line.split()[0] == 'wall':
            msg = str("server: " + line.split(' ', 1)[1]).encode()
            # mess_all(socketlist, 0, msg)
        elif line.split()[0] == 'kick':
            pseudo = line.split()[1]
            if pseudo in dicoClients.values():
                for c in socketlist:
                    if c != serversocket and c != 0:
                        if dicoClients[c][2] == pseudo:
                            c.close()
                            nb_clients -= 1
                            print(f"Kicking {pseudo}...")
            else:
                print(f"Le pseudo {pseudo} n'existe pas.")
        else:
            print(line)


def message_client(sock, dicoclients):
    """
    Fonction qui traite les messages des clients
    """
    message = sock.recv(MAXBYTES)
    if len(message) == 0:
        # run = False
        pass
    else:
        text = message.decode()
        if text[0] == '!': #commandes
            if text[1] == '!': #commandes serveur
                text = text[2:]
                if text == "quit\n":
                    pass
                elif text == "beat\n":
                    dicoclients[sock] = (dicoclients[sock][0], dicoclients[sock][1], dicoclients[sock][2], dicoclients[sock][3], time.time())
            
            # if text == "!list\n":
            #     sock.send(str("Liste des clients connectés:\n").encode())
            #     for c in socketlist:
            #         if c != serversocket and c != 0:
            #             sock.send(str('-' + dicoClients[c][2] + "\n").encode())

            # elif text.split()[0] == "!pseudo":
            #     if dicoPseudo[s] == "anonymous":
            #         msg = str(f"[+]{text.split()[1]}\n").encode()
            #         mess_all(socketlist, 0, msg)

            #     dicoPseudo[s] = text.split()[1]
            #     print(f"Connection from {dicoClients[s][2]} has changed pseudo to {dicoPseudo[s]}")
            #     dicoClients[s] = (dicoClients[s][0], dicoClients[s][1], text.split()[1])


def main():
    global serversocket, nb_clients

    def alrm_handler(sig, frame):
        """
        Verifie si tous les clients ont envoyé un beat
        """
        now = time.time()
        for key in socketList:
            if key != serversocket and key != 0:
                if now - dicoClients[key][4] > BEAT_TIMEOUT:
                    print("Client {} timeout".format(dicoClients[key][2]))
                    disconnect_client(key, socketList)
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

    print("Server started")

    nb_clients = 0
    socketList = [serversocket, 0] # liste des sockets à surveiller
    dicoPseudo = {} # dictionnaire Pseudo -> socket
    dicoClients = {} # dictionnaire socket -> (address, socket, pseudo, cookie, last_beat)

    first = True
    signal.alarm(BEAT_CHECK) # 5 secondes pour envoyer un beat
    while nb_clients > 0 or first:
        first = False
        (activesockets, _, _) = select.select(socketList, [], []) 
        #! gerer les exceptions

        for sock in activesockets:
            if sock == serversocket:
                new_client(serversocket, socketList, dicoClients, dicoPseudo)
            
            elif sock == 0:
                console(serversocket, socketList, dicoClients)

            else:
                message_client(sock, dicoClients)
                # message_client(sock, socketList, dicoClients, dicoPseudo)
                



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: chat_killer_server.py <port>")
        sys.exit(1)

    PORT = int(sys.argv[1])
    nb_clients = 0
    
    main()

    sys.exit(0)