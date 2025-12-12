Lisez ca : notre jeu tourne a 60 fps (sauf si la configuration ne le permet pas mais on va skip ca) donc 60 fois par secondes une image est rendue a l'ecran, cela signifie que a chaque frame on doit aussi mettre a jour les données du personnage cest ce quon appelle le tick. Chaque objet du jeu doit donc etre equipé de deux fonctions tick (pour executer le code) et render qui recoit en argument une reference a la classe engine render (pour afficher quelque chose a l'ecran cest ici). Le EngineRender contient toutes les fonctions de base pour afficher des trucs (ex cube) et si vous avez besoin de dautres fonctions dite le moi (Louis).


main.py -> le fichier qu'on doit executer pour lancer tout le jeu



src/ (-> pour le code donc les fichier .py a hierarchiser également)<BR>
        CoreEngine/<BR>
                EngineRender -> contient la classe qui effectue tous les appels aux fonction render de chaque objets(appelé a chaque frame) pour afficher les sprites/animations, contient egallement les fonctions de base ex: créer un cube<BR>
                EngineTick -> contient la classe qui effectue tous les appels aux fonctions tick de chaque objets(appelé a chaque frame) pour executer du code<BR>



assets/ (-> pour les textures / animations / sons)



Bibliothèques : (a chaque fois que vous voulez utiliser une biblitheque et qui est donc importée ajoutez la ici)



-pygame



