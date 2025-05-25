import discord
from discord.ext import commands
from bot import get_prefix, bot  # Assure-toi que cette importation est possible dans ton projet

# 📘 Commande : help
# ─────────────────────────────────────────────
@commands.command(name="help", help="Affiche la liste des commandes ou les infos sur une commande spécifique.")
async def help_command(ctx, commande: str = None):
    prefix = get_prefix(bot, ctx.message)

    if commande is None:
        categories = {
            "Général": [],
            "Fun": [],
            "Reiatsu": [],
            "Admin": [],
            "Autres": []
        }

        for cmd in bot.commands:
            if cmd.hidden:
                continue
            cat = getattr(cmd, "category", "Autres")
            categories.setdefault(cat, []).append(cmd)

        embed = discord.Embed(title="📜 Commandes par catégorie", color=discord.Color.blue())

        for cat in ["Général", "Fun", "Reiatsu", "Admin", "Autres"]:
            cmds = categories.get(cat, [])
            if cmds:
                cmds.sort(key=lambda c: c.name)
                liste = "\n".join(f"`{prefix}{cmd.name}` : {cmd.help or 'Pas de description.'}" for cmd in cmds)
                embed.add_field(name=f"📂 {cat}", value=liste, inline=False)

        embed.set_footer(text=f"Utilise {prefix}help <commande> pour plus de détails.")
        await ctx.send(embed=embed)

    else:
        cmd = bot.get_command(commande)
        if cmd is None:
            await ctx.send(f"❌ La commande `{commande}` n'existe pas.")
        else:
            embed = discord.Embed(
                title=f"Aide pour `{prefix}{cmd.name}`",
                color=discord.Color.green()
            )
            embed.add_field(name="Description", value=cmd.help or "Pas de description.", inline=False)
            if cmd.aliases:
                embed.add_field(name="Alias", value=", ".join(f"`{a}`" for a in cmd.aliases), inline=False)
            embed.set_footer(text="Paramètres entre < > sont obligatoires, ceux entre [ ] sont optionnels.")
            await ctx.send(embed=embed)

help_command.category = "Général"

# Chargement automatique du module (async obligatoire)
async def setup(bot):
    bot.add_command(help_command)
    print("✅ Commande help chargée")

