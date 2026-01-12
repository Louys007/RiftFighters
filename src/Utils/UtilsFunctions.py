# fichier qui contient toute sortes de fonction utilitaires

def lerp(start, end, t):
    """
    fonction qui donne une valeur smooth entre start et end en fonction d'un facteur t
    plus t est proche de 1 plus ca ira vite vers end

    !! la fonction n'a pas été designé pour un jeu avec une frequence de raffraichissement variable (absence du delta time)
    """
    return start + (end - start) * t