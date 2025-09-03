class JardinView(discord.ui.View):
    def __init__(self, garden: dict, user_id: int, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.garden = garden
        self.user_id = user_id
        # ───────── Grille des fleurs ─────────
        self.create_grid_buttons()
        # ───────── Boutons de contrôle ─────────
        self.add_control_buttons()

    # ───────── Création de la grille interactive ─────────
    def create_grid_buttons(self):
        self.clear_items()  # supprime tous les boutons existants
        for row_idx, row in enumerate(self.garden["garden_grid"]):
            for col_idx, emoji in enumerate(row):
                button = discord.ui.Button(
                    label=emoji,
                    style=discord.ButtonStyle.secondary,
                    row=row_idx,
                    custom_id=f"grid-{row_idx}-{col_idx}"
                )
                button.callback = self.make_cut_callback(row_idx, col_idx)
                self.add_item(button)

    # ───────── Callback pour chaque bouton de la grille ─────────
    def make_cut_callback(self, row_idx, col_idx):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message(
                    "❌ Ce jardin n'est pas à toi !", ephemeral=True
                )

            cell = self.garden["garden_grid"][row_idx][col_idx]
            for key, emoji in FLEUR_EMOJIS.items():
                if cell == emoji:
                    # Ajouter à l'inventaire
                    self.garden["inventory"][key] = self.garden["inventory"].get(key, 0) + 1
                    # Remplacer par 🌱
                    self.garden["garden_grid"][row_idx] = (
                        self.garden["garden_grid"][row_idx][:col_idx] + "🌱" +
                        self.garden["garden_grid"][row_idx][col_idx+1:]
                    )
                    break

            # Mise à jour Supabase
            await supabase.table(TABLE_NAME).update({
                "garden_grid": self.garden["garden_grid"],
                "inventory": self.garden["inventory"]
            }).eq("user_id", self.user_id).execute()

            # Recréer la grille pour refléter les changements
            self.create_grid_buttons()
            embed = build_garden_embed(self.garden, self.user_id)
            await interaction.response.edit_message(embed=embed, view=self)
        return callback

    # ───────── Boutons de contrôle (Engrais, Alchimie, Potions) ─────────
    def add_control_buttons(self):
        # Engrais
        engrais_btn = discord.ui.Button(label="Engrais", emoji="💩", style=discord.ButtonStyle.green)
        engrais_btn.callback = self.engrais
        self.add_item(engrais_btn)

        # Alchimie
        alchimie_btn = discord.ui.Button(label="Alchimie", emoji="⚗️", style=discord.ButtonStyle.blurple)
        alchimie_btn.callback = self.alchimie
        self.add_item(alchimie_btn)

        # Potions
        potions_btn = discord.ui.Button(label="Potions", emoji="🧪", style=discord.ButtonStyle.green)
        potions_btn.callback = self.potions
        self.add_item(potions_btn)

    # ───────── Actions des boutons de contrôle ─────────
    async def engrais(self, interaction: discord.Interaction):
        last = self.garden.get("last_fertilize")
        if last:
            last_dt = datetime.datetime.fromisoformat(last)
            now = datetime.datetime.now(datetime.timezone.utc)
            if now < last_dt + FERTILIZE_COOLDOWN:
                remain = last_dt + FERTILIZE_COOLDOWN - now
                total_seconds = int(remain.total_seconds())
                minutes, seconds = divmod(total_seconds, 60)
                hours, minutes = divmod(minutes, 60)
                return await interaction.response.send_message(
                    f"⏳ Tu dois attendre {hours}h {minutes}m {seconds}s avant d'utiliser de l'engrais !",
                    ephemeral=True
                )

        self.garden["garden_grid"] = pousser_fleurs(self.garden["garden_grid"])
        self.garden["last_fertilize"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        await supabase.table(TABLE_NAME).update({
            "garden_grid": self.garden["garden_grid"],
            "last_fertilize": self.garden["last_fertilize"]
        }).eq("user_id", self.user_id).execute()

        # Recréer la grille et afficher le jardin
        self.create_grid_buttons()
        embed = build_garden_embed(self.garden, self.user_id)
        await interaction.response.edit_message(embed=embed, view=self)

    async def alchimie(self, interaction: discord.Interaction):
        view = AlchimieView(self.garden, self.user_id)
        embed = view.build_embed()
        await interaction.response.send_message(embed=embed, view=view)

    async def potions(self, interaction: discord.Interaction):
        user_data = supabase.table(TABLE_NAME).select("potions").eq("user_id", self.user_id).execute()
        potions_data = {}
        if user_data.data and user_data.data[0].get("potions"):
            potions_data = user_data.data[0]["potions"]
        embed = build_potions_embed(potions_data)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.user_id
