

import os, socket, sys, select, time,signal
pathfifo = "/tmp/killer.fifo"
pathlog = "/tmp/killer.log"

MAXBYTES = 4096
if len(sys.argv) == 3:
    pseudo = input("Entrez votre pseudo: ")
elif len(sys.argv) == 4:
    pseudo = sys.argv[3]
else:
    print('Usage:', sys.argv[0], 'hote port')
    sys.exit(1)
HOST = sys.argv[1]
PORT = int(sys.argv[2])
sockaddr = (HOST, PORT)

try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPv4, TCP
    server.connect(sockaddr)
    server.send(str('!pseudo ' + pseudo).encode())
except socket.error as e:
    print('erreur connexion:', e)
    sys.exit(1)

print('connected to:', sockaddr)

def help(fd):
    os.write(fd,"liste des commandes: \n".encode('utf-8'))
    os.write(fd,"	!quit pour quitter \n".encode('utf-8'))
    os.write(fd,"	!list pour lister les utilisateurs \n".encode('utf-8'))
    os.write(fd,"	!pseudo pour changer de pseudo \n".encode('utf-8'))
    os.write(fd,"	!help pour afficher la liste des commandes \n".encode('utf-8'))
    os.write(fd,"	@pseudo message pour envoyer un message privé à :pseudo: \n".encode('utf-8'))
    os.write(fd,"	message pour envoyer un message public \n".encode('utf-8'))

socketlist = [server]
run = True

try :
	os.mkfifo(pathfifo) #tube nommé pour communication entre terminal de saisie et superviseur
except :
	print("erreur fifo")
	try :
		sys.exit(0)
	except: 
		print("erreur d'exit")




pid = os.fork()

if pid == 0:
	print("cat fifo")
	argv=["xterm","-e","cat > "+pathfifo]
	#os.system('xterm -e "cat >/tmp/killer.fifo"')
	os.execvp("xterm",argv) #lance le terminal ou entree standard > fifo

else :
	fifo=os.open(pathfifo,os.O_RDONLY) #descripteur de fichier fifo readonly
	socketlist.append(fifo)
	log=os.open(pathlog, os.O_APPEND|os.O_TRUNC|os.O_CREAT|os.O_WRONLY) #descripteur de fichier log append, create if not exist, supprime le contenu à l'ouverture
	pid2= os.fork()
	if pid2== 0:
		argv1 =["xterm","-e","tail -f "+pathlog]
		os.execvp("xterm",argv1)
	else:
		help(log)
		while run:
			(activesockets, _, _) = select.select(socketlist, [], [])
			for s in activesockets:
				
				if s == fifo:

					line = os.read(fifo, MAXBYTES)
					
					if len(line) == 0:
						continue
						"""
						print("run finito")
						server.close()
						# s.shutdown(socket.SHUT_WR)
						run = False
						break"""
					lineD = line.decode()
					if lineD[0] == '!':
						if lineD == "!quit\n":
						    server.close()
						    run = False
						    break
						elif lineD == "!list\n":
						    server.send(line)
						elif lineD == "!help\n":
						    help(log)
						elif lineD[:7] == "!pseudo":
						    server.send(line)
						else:
						    print("commande inconnue")
					else:
			   			 server.send(line)
				else:
					data = server.recv(MAXBYTES)
					if len(data) == 0:
						# run = False
						break
					os.write(log, data)

