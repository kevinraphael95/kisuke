# ────────────────────────────────────────────────────────────────────────────────
# sorting.py — Visualisation d'algorithmes de tri /sorting et !sorting
# Objectif : Visualiser différents algorithmes de tri en temps réel dans Discord
# Catégorie : Fun
# Accès : Tous
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
import random
import asyncio
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# Fonctions de tri (avec yield pour animation)
# ────────────────────────────────────────────────────────────────────────────────
async def bubble_sort(data):
    n = len(data)
    for i in range(n):
        for j in range(0, n - i - 1):
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
            yield data, list(range(n - i, n))

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

async def heap_sort(data):
    n = len(data)
    def heapify(n, i):
        largest = i
        l, r = 2*i + 1, 2*i + 2
        if l < n and data[l] > data[largest]:
            largest = l
        if r < n and data[r] > data[largest]:
            largest = r
        if largest != i:
            data[i], data[largest] = data[largest], data[i]
            heapify(n, largest)
    for i in range(n//2 - 1, -1, -1):
        heapify(n, i)
        yield data, []
    for i in range(n - 1, 0, -1):
        data[i], data[0] = data[0], data[i]
        heapify(i, 0)
        yield data, list(range(i, n))

async def shell_sort(data):
    n = len(data)
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            temp = data[i]
            j = i
            while j >= gap and data[j - gap] > temp:
                data[j] = data[j - gap]
                j -= gap
                yield data, list(range(i + 1))
            data[j] = temp
            yield data, list(range(i + 1))
        gap //= 2

async def cocktail_sort(data):
    n = len(data)
    swapped = True
    start = 0
    end = n - 1
    while swapped:
        swapped = False
        for i in range(start, end):
            if data[i] > data[i + 1]:
                data[i], data[i + 1] = data[i + 1], data[i]
                swapped = True
            yield data, list(range(i + 1))
        if not swapped:
            break
        swapped = False
        end -= 1
        for i in range(end - 1, start - 1, -1):
            if data[i] > data[i + 1]:
                data[i], data[i + 1] = data[i + 1], data[i]
                swapped = True
            yield data, list(range(i + 1))
        start += 1

async def comb_sort(data):
    n = len(data)
    gap = n
    shrink = 1.3
    sorted_ = False
    while not sorted_:
        gap = int(gap / shrink)
        if gap <= 1:
            gap = 1
            sorted_ = True
        i = 0
        while i + gap < n:
            if data[i] > data[i + gap]:
                data[i], data[i + gap] = data[i + gap], data[i]
                sorted_ = False
            yield data, list(range(i + 1))
            i += 1

# ────────────────────────────────────────────────────────────────────────────────
# Visualisation des barres
# ────────────────────────────────────────────────────────────────────────────────
def render_bars(data, sorted_indices=None, max_length=12):
    if sorted_indices is None:
        sorted_indices = []
    max_val = max(data)
    lines = []
    for i, n in enumerate(data):
        height = int((n / max_val) * max_length)
        bar = "▇" * height
        if i in sorted_indices:
            bar = f"{bar} ✅"
        lines.append(bar)
    return "\n".join(lines)

# ────────────────────────────────────────────────────────────────────────────────
# Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Sorting(commands.Cog):
    """Commande /sorting et !sorting — Visualise un algorithme de tri en temps réel"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.algorithms = {
            "Bubble Sort": bubble_sort,
            "Cocktail Sort": cocktail_sort,
            "Comb Sort": comb_sort,
            "Heap Sort": heap_sort,
            "Insertion Sort": insertion_sort,
            "Merge Sort": merge_sort,
            "Quick Sort": quick_sort,
            "Selection Sort": selection_sort,
            "Shell Sort": shell_sort,
        }

    async def visualize_sorting(self, channel_or_interaction, algorithm_name: str):
        data = list(range(1, 13))
        random.shuffle(data)
        algo = self.algorithms[algorithm_name]
        delay = 0.25
        msg = None
        iteration = 0

        async def send(embed):
            nonlocal msg
            if isinstance(channel_or_interaction, discord.Interaction):
                if msg:
                    await msg.edit(embed=embed)
                else:
                    msg = await safe_respond(channel_or_interaction, embed=embed)
            else:
                if msg:
                    await msg.edit(embed=embed)
                else:
                    msg = await safe_send(channel_or_interaction, embed=embed)

        embed = discord.Embed(
            title=f"🔄 {algorithm_name} — En cours...",
            description=f"```\n{render_bars(data)}\n```",
            color=discord.Color.blurple()
        )
        await send(embed)

        async for step, sorted_idx in algo(data.copy()):
            iteration += 1
            await asyncio.sleep(delay)
            embed = discord.Embed(
                title=f"🔄 {algorithm_name} — Étape {iteration}",
                description=f"```\n{render_bars(step, sorted_idx)}\n```",
                color=discord.Color.orange()
            )
            await send(embed)

        sorted_data = sorted(data)
        embed = discord.Embed(
            title=f"✅ {algorithm_name} terminé !",
            description=f"```\n{render_bars(sorted_data, list(range(len(sorted_data))))}\n```",
            color=discord.Color.green()
        )
        embed.add_field(name="🧮 Itérations totales", value=f"{iteration}", inline=False)
        await send(embed)

    # ────────────────────────────────────────────────────────────────────────────
    # Commande SLASH
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
    # Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="sorting")
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_sorting(self, ctx: commands.Context, *, algorithme: str = None):
        await self.handle_sorting(ctx.channel, algorithme)

    # ────────────────────────────────────────────────────────────────────────────
    # Gestion logique commune
    # ────────────────────────────────────────────────────────────────────────────
    async def handle_sorting(self, channel_or_interaction, algorithme: str = None):
        algos_list = sorted(self.algorithms.keys())
        algo_dict = {str(i + 1): name for i, name in enumerate(algos_list)}

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
        if algorithme == "random":
            algo_name = random.choice(algos_list)
        elif algorithme.isdigit() and algorithme in algo_dict:
            algo_name = algo_dict[algorithme]
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
# Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Sorting(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun&Random"
    await bot.add_cog(cog)

