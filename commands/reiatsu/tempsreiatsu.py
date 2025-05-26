@commands.command(name="tempsreiatsu", aliases = ["tpsreiatsu"], help="Affiche le temps restant avant le prochain Reiatsu.")
@commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
async def tempsreiatsu(self, ctx):
    guild_id = str(ctx.guild.id)
    data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()

    if not data.data:
        await ctx.send("❌ Ce serveur n’a pas de salon Reiatsu configuré.")
        return

    conf = data.data[0]
    if conf.get("en_attente"):
        spawn_msg_id = conf.get("spawn_message_id")
        if spawn_msg_id:
            try:
                channel = ctx.guild.get_channel(int(conf["channel_id"]))
                spawn_msg = await channel.fetch_message(int(spawn_msg_id))
                await ctx.send(f"💠 Un Reiatsu est **déjà apparu** !", reference=spawn_msg)
            except:
                await ctx.send("💠 Un Reiatsu est **déjà apparu**, mais impossible de retrouver le message.")
        else:
            await ctx.send("💠 Un Reiatsu est **déjà apparu** et attend d’être absorbé.")
        return

    # ... suite avec délai sinon ...
