import os, socket, sys, select,signal,time


def alarm_hdler(sig_num,frame): #Handler qui gère le heartbeat. Il envoie un "!!BEAT" au server toutes les secondes
	global server
	global server_statut
	msg="!!BEAT"
	try :
		server.send(msg.encode('utf-8')) #detection d'erreur
		server_statut= True
		signal.alarm(1)
	except :
		erreur_rep_server()
	
def erreur_rep_server():
	global server_statut
	server_statut = False

	
def server_connection(): #Protocole de gestion des connexions client-server
	HOST = "127.0.0.1"
	if len(sys.argv)>1:
		PORT = int(sys.argv[1])
	else :
		PORT = 25565
	sockaddr = (HOST, PORT)
	global server
	global server_statut
	global COOKIE
	global run
	global quit
	if (os.path.exists(pathcookie)):
		COOKIE = True
	try:
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPv4, TCP
		server.connect(sockaddr)
		if COOKIE :							#Protocole de reconnection si présence de cookie
			fd = os.open(pathcookie, os.O_RDONLY)
			fdr=os.read(fd,MAXBYTES).decode()
			print("Envoie du cookie au server... ")
			try :
				server.send(str('!!cookie '+fdr).encode())
			except :
				if run:
					erreur_rep_server()
				else :
					print("Erreur: envoie au server")
					sys.exit(1)
			os.close(fd)
		else :								#Protocole de premiere connection
			try :
				server.send(str('!!pseudo ' + pseudo).encode())
				fd=os.open("/tmp/"+pseudo+".cookie", os.O_WRONLY|os.O_CREAT)
				print("En attente de reception de cookie... ")
				cookie=server.recv(2048).decode('utf-8')
				cookie = cookie.split()[1]
				os.write(fd,cookie.encode())
				os.close(fd)
			except:
				if run:
					erreur_rep_server()
				else :
					print("Erreur: envoie au server")
					sys.exit(1)
		signal.signal(signal.SIGALRM, alarm_hdler) #Setup le HEARTBEAT
		signal.alarm(1)
		print('connected to:', sockaddr)
		socketlist = [server]
		server_statut = True
		run = True
		return socketlist,server
	except socket.error as e:
		print('erreur connexion:', e)
		sys.exit(1)
	except OSError as e :
		print('Erreur :',e)
		quit = True



def help(fd): #Affichage des commandes en ligne
    os.write(fd,"liste des commandes: \n".encode('utf-8'))
    os.write(fd,"	!quit pour quitter \n".encode('utf-8'))
    os.write(fd,"	!list pour lister les utilisateurs \n".encode('utf-8'))
    os.write(fd,"	!help pour afficher la liste des commandes \n".encode('utf-8'))
    os.write(fd,"	@pseudo message pour envoyer un message privé à :pseudo: \n".encode('utf-8'))
    os.write(fd,"	message pour envoyer un message public \n".encode('utf-8'))
    
def help_offline(fd):#Affichage des commandes hors ligne
	os.write(fd,"Vous n'êtes plus connecté au server \n\n".encode('utf-8'))
	os.write(fd,"Voici la liste des commandes hors ligne: \n".encode('utf-8'))
	os.write(fd,"	!quit pour fermer le client \n".encode('utf-8'))
	os.write(fd,"	!help pour afficher la liste des commandes \n".encode('utf-8'))
	os.write(fd,"	!reconnect pour essayer de vous reconnecter au server\n".encode('utf-8'))

def term_saisie():    #tant que run == True, fermer un term le relance tout de suite
	global pathfifo
	global quit
	try :
		while True :
			pid = os.fork()
			if pid == 0:
				argv=["xterm","-e","cat > "+pathfifo]
				os.execvp("xterm",argv) #lance le terminal ou entree standard > fifo
			else :
				os.wait()
	except OSError as e: 
		print("Erreur :",e)
		quit = True
	except :
		quit = True
			

def term_affichage():	#tant que run == True, fermer un term le relance tout de suite
	global pathlog
	global quit
	try:
		while True :
			pid = os.fork()
			if pid == 0:
				argv1 =["xterm","-e","tail -f "+pathlog]
				os.execvp("xterm",argv1)
			else :
				os.wait()
	except OSError as e: 
		print("Erreur :",e)
		quit = True
	except :
		quit = True

def quitter(p1,p2):
	os.kill(p1,signal.SIGQUIT)
	os.kill(p2,signal.SIGQUIT)


def lancement_client(socketlist,server): #Protocol de communication client-server
	if not (os.path.exists(pathfifo)):
		os.mkfifo(pathfifo) #tube nommé pour communication entre terminal de saisie et superviseur
	try :
		pid = os.fork()
		if pid == 0:
			term_saisie()
		else :
			fifo=os.open(pathfifo,os.O_RDONLY) #descripteur de fichier fifo readonly
			socketlist.append(fifo)
			log=os.open(pathlog, os.O_APPEND|os.O_TRUNC|os.O_CREAT|os.O_WRONLY) #descripteur de fichier log append, create if not exist, supprime le contenu à l'ouverture
			pid2= os.fork()
			if pid2== 0:
				term_affichage()
			else:
				global server_statut
				global run
				global quit
				cleanquit = False
				quit = False
				mute = False
				help(log)
				while run and not(quit): #Boucle du client
					while server_statut : #Boucle client en ligne
						(activesockets, _, _) = select.select(socketlist, [], [])
						for s in activesockets:
							if s == fifo:
								line = os.read(fifo, MAXBYTES)
								lineD = line.decode()
								if len(line)==0:
									continue
								elif lineD[0] == '!':
									if lineD == "!quit\n":
										try:
											server.send("!!quit".encode())
										except:
											pass
										server.close()
										run = False
										server_statut = False
										quit = True
										cleanquit=True
										quitter(pid,pid2)
										break
									elif lineD == "!list\n":
										try:
											server.send(line)
										except:
											erreur_rep_server()
									elif lineD == "!help\n":
										help(log)
									else:
										os.write(log,"commande inconnue\n".encode('utf-8'))
								else:
									if not(mute):
										line=("!!message "+line.decode()).encode()
										try:
											server.send(line)
										except:
											erreur_rep_server()
									else :
										os.write(log,"Vous êtes mute ...\n".encode())
							else:
								data = server.recv(MAXBYTES)
								if len(data) == 0:
									# run = False
									continue
								elif data.decode() == "!!BAN\n":
									os.write(log,"Vous avez été bannis\nVous allez être déconnecté...\n".encode())
									time.sleep(4)
									quit = True
								elif data.decode() == "!!MUTE\n":
									os.write(log,"Un modérateur vous a mute.\nVous ne pouvez plus écrire dans le chat...\n".encode())
									mute = True
								elif data.decode() == "!!UNMUTE\n":
									os.write(log,"vous avez été pardonné, vous avez de nouveau droit a écrir dans le chat !\n".encode())
									mute = False
								elif data.decode() != "!!BEAT\n":
									os.write(log, data)
									
					help_offline(log)
					offline = True
					
					while offline and not(quit): #boucle client hors-ligne
						line = os.read(fifo, MAXBYTES)
						lineD = line.decode()
						if len(line)==0:
							continue
						elif lineD[0] == '!':
							if lineD == "!quit\n":
								server.close()
								run = False
								server_statut = False
								quit = True
								cleanquit=True
								quitter(pid,pid2)
								break
							elif lineD == "!help\n":
								help_offline(log)
							elif lineD == "!reconnect\n":
								socketlist,server=server_connection()
								offline = False
								socketlist.append(fifo)
								
							else:
								os.write(log,"commande inconnue\n".encode('utf-8'))
				if cleanquit : #Fermeture !quit
					os.close(fifo)
					os.close(log)
					os.system("rm "+pathfifo)
					os.system("rm "+pathlog)
					os.system("rm "+pathcookie)
					os.system("pkill xterm") #ferme tous les processus xterm
					sys.exit(0)
				else :	#Fermeture car terminal cassé
					quitter(pid,pid2)
					os.close(fifo)
					os.close(log)
					os.system("rm "+pathfifo)
					os.system("rm "+pathlog)
					os.system("rm "+pathcookie)
					os.system("pkill xterm") #ferme tous les processus xterm
					sys.exit(0)
	except OSError as e:
		print("Erreure :",e)
		sys.exit(0)

def main():
	socketlist,servert=server_connection()
	lancement_client(socketlist,server)

	
if __name__ == "__main__":
	pseudo = input("Entrez votre identifiant: ")
	pathfifo = "/tmp/"+pseudo+".fifo"
	pathlog = "/tmp/"+pseudo+".log"
	pathcookie="/tmp/"+pseudo+".cookie"
	MAXBYTES = 4096
	run = False
	COOKIE = False
	
	main()
