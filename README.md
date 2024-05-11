# ProjetS2

URL du repo : https://github.com/ClaveilleH/ProjetS2

Partie Client : Vincent AUGER 22102678

Points amélioré depuis la démo :	- La commande !reconnect fonctionne

(DONE)			Un client qui lance deux terminaux avec les bonnes commandes et les bonnes redirections, et qu'on peut tester sans connection avec un serveur (le superviseur ne se détache pas de son terminal, il lit et écrit dans le terminal au lieu de communiquer avec le serveur): 6/20

(DONE)			Un client qui se connecte au serveur et échange des messages en alternance : 8/20

(DONE)			Un client qui se connecte et échange des messages sans alternance prédéfinie : 10/20

(DONE)			Gestion de pseudo, de messages privés, et de la commande !list: 12/20

  (Gestion des commandes !suspend, !ban, et !forgive: 14/20))

(DONE)			Tolérance aux pannes des terminaux qui exécutent les commandes tail -f LOG et cat > TUBE, relance des terminaux et des commandes : 16/20

(DONE)			Gestion des cookies lors du redémarage du client après une panne: 18/20

(DONE)			Tolérances aux pannes de serveur (détection par échec d'envoi de message au serveur), commande !reconnect : 19/20

(DONE)			Heartbeat et détection de panne du serveur: 20/20

Auto-évaluation : 20/20

Commentaires(CLIENT) :

- les pseudos fonctionnent comme des identifiants : afin de gérer les cookies de plusieurs clients sur une seule machine, le fichier est "pseudo.cookie". Pour vous reconnecter après un crash, il faut rentrer le meme pseudo.
- !quit est une déconnexion "propre" qui supprime pseudo.fifo, pseudo.log, pseudo.cookie
- si il y a un crash server et que le client quitte en etant hors-ligne, le server peut crash si le client tente de se reconnecter avec le meme pseudo.



________________________________________________________________________________________________________________________

Partie Serveur : CLAVEILLE Hugo 22204830

Points amélioré depuis la démo : Le serveur est maintenant stable.


(DONE) Un serveur qui accepte un client et échange des messages en alternance : 3/20

(DONE) Un serveur qui accepte un client et échange des messages sans alternance prédéfinie : 5/20

(DONE) Un serveur qui accepte plusieurs client et échange des messages public sans alternance prédéfinie : 8/20

(DONE) Gestion des messages privés et de pseudo : 11/20

(DONE) Gestion des pseudos, commande `!list` : 13/20

(DONE) Tolérance aux pannes de client (détection par échec d'envoi de message au serveur), gestion des cookie: 16/20

(DONE) Heartbeat et détection de pannes du client sans envoi de message utilisateur: 18/20

(DONE) Tolérance aux pannes côté serveur (sauvegarde de l'état du serveur à intervalle de temps régulier et chargement de la sauvegarde au redémarrage du serveur): 20/20
