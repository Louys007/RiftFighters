main.py -> le fichier qu'on doit executer pour lancer tout le jeu



src/ (-> pour le code donc les fichier .py a hierarchiser également)
    CoreEngine/<BR>
        EngineRender -> contient la classe qui effectue tous les appels aux fonction render de chaque objets(appelé a chaque frame) pour afficher les sprites/animations, contient egallement les fonctions de base ex: créer un cube
        EngineTick -> contient la classe qui effectue tous les appels aux fonctions tick de chaque objets(appelé a chaque frame) pour executer du code



assets/ (-> pour les textures / animations / sons)



Bibliothèques : (a chaque fois que vous voulez utiliser une biblitheque et qui est donc importée ajoutez la ici)



-pygame



