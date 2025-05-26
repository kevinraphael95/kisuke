import discord
from discord.ext import commands
import hashlib
import random

class GayCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gay", help="Analyse ton taux de gaytitude (ou celui de quelqu’un d’autre). Résultat fixe et fun.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def gay(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id).encode()

        # Score déterministe basé sur hash
        hash_val = hashlib.md5(user_id).digest()
        score = int.from_bytes(hash_val, 'big') % 101

        niveaux = [
            {
                "min": 90,
                "emoji": "🌈",
                "titre": "Légende arc-en-ciel",
                "couleur": discord.Color.magenta(),
                "descriptions": [
                    "Ton existence même est un dégradé de couleurs.",
                    "Tu fais des playlists plus gays que RuPaul en finale.",
                    "On t’a vu danser sur Dua Lipa un mardi à 8h."
                ]
            },
            {
                "min": 70,
                "emoji": "💖",
                "titre": "Icône en liberté",
                "couleur": discord.Color.pink(),
                "descriptions": [
                    "Ton eyeliner est plus stable que ta sexualité.",
                    "Tu es l’ambiance d’une soirée sans même parler.",
                    "Les gens t’appellent juste pour décorer leur feed."
                ]
            },
            {
                "min": 50,
                "emoji": "😏",
                "titre": "Phase expérimentale",
                "couleur": discord.Color.blurple(),
                "descriptions": [
                    "Tu dis ‘no homo’ mais ton historique Chrome parle.",
                    "T'as liké un reel un peu trop expressif hier.",
                    "Tu joues à ‘et si ?’ dans ta tête depuis 2017."
                ]
            },
            {
                "min": 30,
                "emoji": "🤨",
                "titre": "Ambiance suspecte",
                "couleur": discord.Color.gold(),
                "descriptions": [
                    "Personne ne te croit hétéro sauf toi.",
                    "Tu regardes Mamma Mia seul, souvent.",
                    "Ton parfum s'appelle ‘curiosité florale’."
                ]
            },
            {
                "min": 0,
                "emoji": "🧍",
                "titre": "Droit dans ses bottes",
                "couleur": discord.Color.dark_gray(),
                "descriptions": [
                    "Tu penses que Pride c’est un détergent.",
                    "Tes emojis sont toujours 🧱 ou 🛠️.",
                    "Ton plat préféré, c’est ‘protéine + riz’."
                ]
            }
        ]

        niveau = next(n for n in niveaux if score >= n["min"])
        commentaire = random.choice(niveau["descriptions"])

        embed = discord.Embed(
            title="🌈 Gayomètre 3000",
            description=f"{niveau['emoji']} **{niveau['titre']}**",
            color=niveau["couleur"]
        )
        embed.add_field(name="👤 Candidat", value=member.mention, inline=True)
        embed.add_field(name="📊 Taux de gaytitude", value=f"**{score}%**", inline=True)
        embed.add_field(name="💬 Analyse", value=commentaire, inline=False)
        embed.set_footer(text="Test semi-scientifique. Ne pas utiliser pour se marier en mairie.")

        await ctx.send(embed=embed)

# Chargement automatique
async def setup(bot):
    cog = GayCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
