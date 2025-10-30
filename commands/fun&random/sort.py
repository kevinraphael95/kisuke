# ────────────────────────────────────────────────────────────────────────────────
# 📌 sorting.py — Visualisation d'algorithmes de tri /sorting et !sorting
# Objectif : Visualiser différents algorithmes de tri en temps réel dans Discord
# Catégorie : Fun
# Accès : Tous
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
import random
import asyncio
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Fonctions de tri (avec yield pour animation)
# ────────────────────────────────────────────────────────────────────────────────
async def bubble_sort(data):
    n = len(data)
    for i in range(n):
        for j in range(0, n - i - 1):
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
            yield data, list(range(n - i, n))  # barres triées

async def insertion_sort(data):
    for i in range(1, len(data)):
        key = data[i]
        j = i - 1
        while j >= 0 and data[j] > key:
            data[j + 1] = data[j]
            j -= 1
            yield data, list(range(i + 1))
        data[j + 1] = key
        yield data, list(range(i + 1))

async def selection_sort(data):
    n = len(data)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if data[j] < data[min_idx]:
                min_idx = j
        data[i], data[min_idx] = data[min_idx], data[i]
        yield data, list(range(i + 1))

async def quick_sort(data, low=0, high=None):
    if high is None:
        high = len(data) - 1
    if low < high:
        pivot, left, right = data[high], low, high - 1
        while left <= right:
            while left <= right and data[left] < pivot:
                left += 1
            while left <= right and data[right] >= pivot:
                right -= 1
            if left < right:
                data[left], data[right] = data[right], data[left]
            yield data, list(range(low))
        data[left], data[high] = data[high], data[left]
        yield data, list(range(low, left + 1))
        async for step, sorted_idx in quick_sort(data, low, left - 1):
            yield step, sorted_idx
        async for step, sorted_idx in quick_sort(data, left + 1, high):
            yield step, sorted_idx

async def merge_sort(data, start=0, end=None):
    if end is None:
        end = len(data)
    if end - start > 1:
        mid = (start + end) // 2
        async for step, sorted_idx in merge_sort(data, start, mid):
            yield step, sorted_idx
        async for step, sorted_idx in merge_sort(data, mid, end):
            yield step, sorted_idx
        left, right = data[start:mid], data[mid:end]
        i = j = 0
        for k in range(start, end):
            if j >= len(right) or (i < len(left) and left[i] < right[j]):
                data[k] = left[i]
                i += 1
            else:
                data[k] = right[j]
                j += 1
            yield data, list(range(start, k + 1))

# ────────────────────────────────────────────────────────────────────────────────
# 🎨 Visualisation des barres
# ────────────────────────────────────────────────────────────────────────────────
def render_bars(data, sorted_indices=None, max_length=20):
    if sorted_indices is None:
        sorted_indices = []
    max_val = max(data)
    lines = []
    for i, n in enumerate(data):
        height = int((n / max_val) * max_length)
        bar = "▇" * height
        if i in sorted_indices:
            bar = f"✅{bar}"
        lines.append(bar)
    return "\n".join(lines)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Sorting(commands.Cog):
    """
    Commande /sorting et !sorting — Visualise un algorithme de tri en temps réel
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.algorithms = {
            "Bubble Sort": bubble_sort,
            "Insertion Sort": insertion_sort,
            "Merge Sort": merge_sort,
            "Quick Sort": quick_sort,
            "Selection Sort": selection_sort,
        }

    async def visualize_sorting(self, channel_or_interaction, algorithm_name: str):
        data = [random.randint(1, 12) for _ in range(12)]
        algo = self.algorithms[algorithm_name]
        delay = 0.25
        initial_bars = render_bars(data)
        msg = None

        async def send(content):
            nonlocal msg
            if isinstance(channel_or_interaction, discord.Interaction):
                if msg:
                    await msg.edit(content=content)
                else:
                    msg = await safe_respond(channel_or_interaction, content)
            else:
                if msg:
                    await msg.edit(content=content)
                else:
                    msg = await safe_send(channel_or_interaction, content)

        await send(f"🔄 **{algorithm_name}** en cours...\n{initial_bars}")
        async for step, sorted_idx in algo(data.copy()):
            await asyncio.sleep(delay)
            await send(f"🔄 **{algorithm_name}**\n{render_bars(step, sorted_idx)}")
        await send(f"✅ **{algorithm_name} terminé !**\n{render_bars(sorted(data), list(range(len(data))))}")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="sorting",
        description="Visualise un algorithme de tri en temps réel."
    )
    @app_commands.describe(algorithme="Nom, numéro ou 'random' pour un tri aléatoire")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def slash_sorting(self, interaction: discord.Interaction, algorithme: str = None):
        await self.handle_sorting(interaction, algorithme)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="sorting")
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_sorting(self, ctx: commands.Context, *, algorithme: str = None):
        await self.handle_sorting(ctx.channel, algorithme)

    # ────────────────────────────────────────────────────────────────────────────
    # ⚙️ Gestion logique commune
    # ────────────────────────────────────────────────────────────────────────────
    async def handle_sorting(self, channel_or_interaction, algorithme: str = None):
        algos_list = sorted(self.algorithms.keys())
        algo_dict = {str(i + 1): name for i, name in enumerate(algos_list)}

        # Si pas d'argument → embed de présentation
        if not algorithme:
            embed = discord.Embed(
                title="🎨 Visualisation d'algorithmes de tri",
                description="Choisis un algorithme avec son **numéro**, son **nom**, ou tape `random` pour un aléatoire.",
                color=discord.Color.blurple()
            )
            embed.add_field(
                name="📚 Algorithmes disponibles",
                value="\n".join([f"**{i+1}.** {name}" for i, name in enumerate(algos_list)]),
                inline=False
            )
            embed.set_footer(text="Exemples : /sorting 3 | /sorting Bubble Sort | /sorting random")
            if isinstance(channel_or_interaction, discord.Interaction):
                await safe_respond(channel_or_interaction, embed=embed)
            else:
                await safe_send(channel_or_interaction, embed=embed)
            return

        algorithme = algorithme.strip().lower()

        # Si 'random'
        if algorithme == "random":
            algo_name = random.choice(algos_list)
        # Si numéro valide
        elif algorithme.isdigit() and algorithme in algo_dict:
            algo_name = algo_dict[algorithme]
        # Si nom exact (insensible à la casse)
        else:
            matched = next((name for name in algos_list if name.lower() == algorithme), None)
            if not matched:
                algos_str = "\n".join([f"**{i+1}.** {name}" for i, name in enumerate(algos_list)])
                err = discord.Embed(
                    title="❌ Algorithme inconnu",
                    description=f"Choisis un algorithme valide :\n\n{algos_str}",
                    color=discord.Color.red()
                )
                if isinstance(channel_or_interaction, discord.Interaction):
                    await safe_respond(channel_or_interaction, embed=err)
                else:
                    await safe_send(channel_or_interaction, embed=err)
                return
            algo_name = matched

        await self.visualize_sorting(channel_or_interaction, algo_name)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Sorting(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun&Random"
    await bot.add_cog(cog)



