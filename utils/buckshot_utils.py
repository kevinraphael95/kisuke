import random

CHAMBRE_COUNT = 6
MIN_BULLETS = 1
MAX_BULLETS = 5

# crée un barillet aléatoire
def make_barillet(min_bullets=MIN_BULLETS, max_bullets=MAX_BULLETS, chamber_count=CHAMBRE_COUNT):
    bullets = random.randint(min_bullets, max_bullets)
    barillet = [True]*bullets + [False]*(chamber_count - bullets)
    random.shuffle(barillet)
    return barillet

# applique l'effet d'un objet sur le joueur et retourne texte descriptif
def apply_item(player_state: dict, item: str, barillet: list, opponent_id=None):
    note = ""
    alter = None
    hp = player_state["hp"]

    if item == "cigarette":
        player_state["hp"] = min(5, hp + 1)
        note = f"{player_state['user'].display_name} fume une cigarette et récupère ❤️1."
    elif item == "biere":
        if True in barillet:
            barillet[barillet.index(True)] = False
            note = f"{player_state['user'].display_name} boit une bière et retire une balle du barillet."
            alter = True
        else:
            note = "La bière n'a rien retiré (barillet déjà sûr)."
    elif item == "loupe":
        note = f"{player_state['user'].display_name} regarde la prochaine chambre."
        alter = "peek"
    elif item == "menottes" and opponent_id:
        note = f"{player_state['user'].display_name} menotte l'adversaire ({opponent_id}) pour qu'il perde son prochain tour."
        alter = "menotte"
    elif item == "scie":
        note = f"{player_state['user'].display_name} prépare la scie (+1 dégât prochain tir)."
        alter = "scie"
    elif item == "adrenaline":
        note = f"{player_state['user'].display_name} prend de l'adrénaline (action supplémentaire)."
        alter = "adrenaline"
    else:
        note = f"{player_state['user'].display_name} a tenté d'utiliser un objet inconnu."
    return note, alter
