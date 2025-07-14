# ────────────────────────────────────────────────────────────────────────────────
# 📌 competence_active.py — Commande interactive !!ca pour activer la compétence active selon la classe
# Objectif : Activer la compétence active selon la classe du joueur avec cooldown global
# Catégorie : VAACT
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from datetime import datetime, timedelta

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Fonctions simulées pour accès base de données (à remplacer par ton ORM ou requêtes)
# ────────────────────────────────────────────────────────────────────────────────

def db_get_player_class_and_cd(user_id):
    """
    Simule la récupération en base de la classe et du cooldown comp_cd du joueur.
    Retour : (classe_str, comp_cd_datetime_or_None)
    """
    # Exemple statique pour test
    # Remplacer par une vraie requête SQL / ORM ici
    # Exemple : ("Voleur", datetime.now() - timedelta(hours=1)) => cooldown passé
    return "Voleur", None

def db_update_comp_cd(user_id, new_cd):
    """
    Met à jour le cooldown en base.
    """
    print(f"[DB] Set comp_cd for {user_id} to {new_cd}")

def db_set_flag(user_id, flag_name, value=True):
    """
    Enregistre un flag (ex : vol_garanti) en base lié au joueur.
    """
    print(f"[DB] Set flag {flag_name}={value} for {user_id}")

def db_place_fake_reiatsu(user_id):
    """
    Place un piège reiatsu (illusionniste)
    """
    print(f"[DB] Fake reiatsu placed by {user_id}")

def lancer_pari(user_id):
    """
    Simule le pari du parieur, retourne gain (ou perte)
    """
    import random
    chance = random.random()
    if chance < 0.5:
        return -10  # perte de la mise
    else:
        gain = random.randint(5, 50)
        return gain

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CompetenceActive(commands.Cog):
    """
    Commande !!ca — Active la compétence active de la classe du joueur (avec cooldown)
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="ca",
        help="Active la compétence active de ta classe (cooldown 8h à 12h selon la compétence).",
        description="Commande pour activer ta compétence active selon ta classe."
    )
    async def ca_command(self, ctx: commands.Context):
        user_id = ctx.author.id
        try:
            classe, comp_cd = db_get_player_class_and_cd(user_id)
            now = datetime.now()

            if comp_cd and now < comp_cd:
                remaining = comp_cd - now
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                await ctx.send(f"⏳ Ta compétence active est en cooldown, disponible dans {hours}h {minutes}min.")
                return

            if classe == "Voleur":
                db_set_flag(user_id, "vol_garanti", True)
                new_cd = now + timedelta(hours=12)
                message = "🗡️ Vol garanti activé, valable pour ton prochain vol."

            elif classe == "Absorbeur":
                db_set_flag(user_id, "super_absorption", True)
                new_cd = now + timedelta(hours=12)
                message = "💥 Super absorption activée pour ta prochaine absorption."

            elif classe == "Illusionniste":
                db_place_fake_reiatsu(user_id)
                new_cd = now + timedelta(hours=8)
                message = "🎭 Piège reiatsu placé, attention aux prochains joueurs."

            elif classe == "Parieur":
                gain = lancer_pari(user_id)
                new_cd = now + timedelta(hours=12)
                if gain > 0:
                    message = f"🎲 Pari réussi ! Tu as gagné {gain} reiatsu."
                else:
                    message = f"🎲 Pari perdu ! Tu as perdu 10 reiatsu."

            else:
                await ctx.send("❌ Tu n'as pas de classe valide ou pas de compétence active.")
                return

            db_update_comp_cd(user_id, new_cd)
            await ctx.send(message)

        except Exception as e:
            print(f"[ERREUR !!ca] {e}")
            await ctx.send("❌ Une erreur est survenue lors de l'activation de ta compétence.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CompetenceActive(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
