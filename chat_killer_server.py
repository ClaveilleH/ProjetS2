import sys, os, signal, socket, select, random, time
"""
Script du jeu coté serveur
https://webusers.i3s.unice.fr/~elozes/enseignement/systeme/
127.0.0.1
python3 chat_killer_server.py 25565
"""
HOST = "127.0.0.1" 
MAXBYTES = 4096
BEAT_TIMEOUT = 5
BEAT_CHECK = 3
BEAT_CPT = 0

def console(server):
	try:
		line = os.read(0, MAXBYTES).decode()
	except OSError as e:
		print("Erreur: ", e)
		return
	if line[0] == '!':
		line = line[1:]
		if line == "quit\n":
			print("Closing all connections and server...")
			for c in server.socketList:
				if c != server.socket and c != 0:
					c.close()

					server.nb_clients -= 1
			server.socket.close()


			try:
				os.remove("/tmp/chat_killer_server{}".format(PORT))
			except:
				print("Erreur: impossible de supprimer le fichier de sauvegarde")
			
			sys.exit(0)


		elif line == "list\n":
			print(server.get_list())
		
	elif line[0] == '@':
		line = line[1:]
		if not ' ' in line:
			print("Erreur: commande invalide")
			return
		pseudo, command = line.split()
		if pseudo in server.dicoPseudo.keys():
			client = server.dicoPseudo[pseudo]
			if client.socket in server.socketList:
				pass
			else:
				print(f"Le client {pseudo} n'est pas connecté.")
				return
			
			if command == '!ban' or command == 'ban':
				client.send(str("!!BAN\n").encode())
				server.disconnect_client(client.socket)
			elif command == '!suspend' or command == 'suspend':
				client.send(str("!!MUTE\n").encode())
			elif command == '!forgive' or command == 'forgive':
				client.send(str("!!UNMUTE\n").encode())
			else:
				print("Commande invalide")


		else:
			print(f"Le pseudo {pseudo} n'existe pas.")
		
			
	else:
		if line.split()[0] == 'wall':
			msg = str("server: " + line.split(' ', 1)[1]).encode()
			server.mess_all(msg)
		else:
			print(line)


def message_client(sock, server):
	"""
	Fonction qui traite les messages des clients
	"""
	try:
		message = sock.recv(MAXBYTES)
	except OSError as e:
		# print("Erreur: ", e)
		server.disconnect_client(sock)
		return
	
	if not sock in server.dicoClients.keys():
		print("Erreur: client introuvable")
		return
	
	client = server.dicoClients[sock]

	if len(message) == 0:
		pass
	else:
		text = message.decode()
		if text[:2] == "!!":
			text = text[2:]
			if text == "BEAT":
				client.last_beat = time.time()
				client.send(str("!!BEAT\n").encode())

			elif text == "quit":
				server.disconnect_client(sock)
				print(f"Client {client.pseudo} disconnected")
				server.mess_all(f"[-]{client.pseudo}!\n".encode())

			elif text[:8] == "message ":
				text = text[8:]

				if text[0] == '@': # whisper
					if not ' ' in text:
						print("Erreur: message invalide")
						return
					
					pseudo, message = text.split(' ', 1)
					pseudo = pseudo[1:]

					if pseudo == 'admin':
						print("Message de " + client.pseudo + " : " + message)

					elif pseudo in server.dicoPseudo.keys():
						server.dicoPseudo[pseudo].send(str(f"(wisper){server.dicoClients[sock].pseudo}: {message}").encode())

					else:
						client.send(str("Le pseudo n'existe pas\n").encode())
				else:
					msg = str(f"{client.pseudo}: {text}").encode()
					server.mess_all(msg)
			# else:   
				# print("->>>>" + text)
		elif text[0] == '!':
			text = text[1:]
			if text == "list\n":
				msg = server.get_list() + '\n'
				client.send(msg.encode())
			# else:
				# print("-2>>>>" + text)
		# else:
			# print("---->" + text)

class Client:
	def __init__(self, address, socket, pseudo, cookie, last_beat) -> None:
		self.address = address
		self.socket = socket
		self.pseudo = pseudo
		self.cookie = cookie
		self.last_beat = last_beat
	
	def send(self, msg):
		self.socket.send(msg)


class Server:
	def __init__(self, serversocket) -> None:
		self.nb_clients = 0
		self.socket = serversocket
		self.socketList = [serversocket, 0] # liste des sockets à surveiller
		self.dicoPseudo = {} # dictionnaire Pseudo -> socket
		self.dicoClients = {} # dictionnaire socket -> Client
		self.fileName = "/tmp/chat_killer_server{}".format(PORT)

		if os.path.exists(self.fileName):
			print("Fichier de sauvegarde trouvé")

			file = os.open(self.fileName, os.O_RDONLY)
			data = ""
			buf = os.read(file, MAXBYTES)

			while buf != b"":
				data += buf.decode()
				buf = os.read(file, MAXBYTES)

			os.close(file)

			for line in data.split('\n'):
				if line == "":
					continue
				if line[0] == '#':
					continue
				if line[0] == 'C': # on a un client
					#C:adresse:pseudo:cookie
					_, address, pseudo, cookie = line.split(':')
					client = Client(address, None, pseudo, cookie, time.time())
					self.dicoPseudo[pseudo] = client
					self.dicoClients[address] = client
					# self.socketList.append(client.socket) # on ne peut pas ajouter le socket car il n'est pas encore reconnecté
					self.nb_clients += 1

			print("Chargement terminé")
				
	def backup(self):
		"""
		Sauvegarde les clients dans un fichier
		"""
		try:
			file = os.open(self.fileName, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
			data = ""
			for client in self.dicoClients.values():
				data += f"C:{client.address}:{client.pseudo}:{client.cookie}\n"
			os.write(file, data.encode())
			os.close(file)
		except:
			print("Erreur: impossible de sauvegarder les clients")
			return

		liste = self.socketList.copy()

		try: # netoyage de la liste, pas l'ideal mais pas le temps de faire mieux
			self.socketList = list(set(self.socketList))
		except:
			self.socketList = liste




	def get_client(self, id):
		"""
		Retourne le client associé au pseudo
		"""
		if isinstance(id, socket.socket):
			return self.dicoClients[id]
		elif isinstance(id, str):
			return self.dicoPseudo[id]
		


	def get_list(self):
		txt = "Liste des clients :"
		for pseudo in self.dicoPseudo.keys():
			txt += '\n' + pseudo + '\t| '
			if self.dicoPseudo[pseudo].socket in self.socketList:
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
		for sock in self.socketList:
			if sock != self.socket and sock != 0:
				try:
					sock.send(msg)
				except BrokenPipeError:
					print("Erreur: client introuvable")
					self.disconnect_client(sock)
				except Exception as e:
					# print("Erreur: ", e)
					pass
	
	def disconnect_client(self, sock):  
		"""
		deconnecte un client
		ne supp pas des dico car le client peut se reconnecter
		:c: socket du client à déconnecter
		:server.socketList: liste des sockets à surveiller
		"""
		sock.close()
		self.socketList.remove(sock)
		self.nb_clients -= 1
	
	def new_client(self):
		(clientsocket, address) = self.socket.accept()
		
		self.socketList.append(clientsocket)
		#! faire un select ppur eviter de bloquer
		txt = clientsocket.recv(MAXBYTES).decode()
		# print(txt)
		
		if txt[:8] == "!!cookie":
			if not ' ' in txt:
				print("Erreur: cookie invalide")
				self.socketList.remove(clientsocket)
				return
			cookie = txt.split()[1]
			
			cookie = cookie # on enleve le \n
			# print("cookie: ", cookie)
			# print(self.dicoClients)

			for client in self.dicoClients.values():
				# print(client.cookie, cookie)
				if client.cookie == cookie: # on retrouve le client
					
					if client.socket in self.socketList: # si le serveur a crashé, le client a été déconnecté
						self.socketList.remove(client.socket)
					
					self.socketList.append(clientsocket)
					client.last_beat = time.time()
					client.socket = clientsocket # on met à jour le socket
					self.dicoClients[clientsocket] = client
					
					return
			print("Erreur: cookie invalide")
				

		elif txt[:8] == "!!pseudo":
			pseudo = txt.split()[1]
			if pseudo in self.dicoPseudo.keys():
				clientsocket.send(str("!!wrong_pseudo\n").encode())
				clientsocket.close()
				self.socketList.remove(clientsocket)
				return

			cookie = str(random.randint(1000000, 9999999))
			
			client = Client(address, clientsocket, pseudo, cookie, time.time())

			self.dicoPseudo[pseudo] = client
			self.dicoClients[clientsocket] = client

			self.nb_clients += 1

			clientsocket.send(str(f"!!cookie {cookie}\n").encode())
			print("New client connected")
			self.mess_all(f"[+]{pseudo}\n".encode())
		
		else:
			self.disconnect_client(clientsocket)
			print("Erreur: message invalide")
			return

def main():
	def alrm_handler(sig, frame):
		"""
		Verifie si tous les clients ont envoyé un beat
		"""
		global BEAT_CPT
		BEAT_CPT += 1
		now = time.time()
		for sock in server.socketList:
			if sock != server.socket and sock != 0:
				if sock in server.dicoClients.keys() and now - server.dicoClients[sock].last_beat > BEAT_TIMEOUT:
					print("Client {} timeout".format(server.dicoClients[sock].pseudo))
					server.disconnect_client(sock)
		signal.alarm(BEAT_CHECK) # on remet l'alarme
		if BEAT_CPT % 20 == 0: # on sauvegarde tous les 20 beats (1 minute)
			server.backup()

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
		try:
			(activesockets, _, _) = select.select(server.socketList, [], []) 

		except Exception as e: # un client a été déconnecté
			# print("Erreur: ", e)
			continue
		#! gerer les exceptions

		for sock in activesockets:
			if not sock in server.socketList:
				# le socket a été enlevé entre temps
				continue

			if sock == serversocket:
				server.new_client()
			
			elif sock == 0:
				console(server)

			else:
				message_client(sock, server)
	
	# il n'y a plus de clients
				



if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Usage: chat_killer_server.py <port>")
		sys.exit(1)

	PORT = int(sys.argv[1])
	
	
	main()


	print("Plus de clients, fermeture du serveur...")
	try:
		os.remove("/tmp/chat_killer_server{}".format(PORT))
	except:
		print("Erreur: impossible de supprimer le fichier de sauvegarde")

	sys.exit(0)
