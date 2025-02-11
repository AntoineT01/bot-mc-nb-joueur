import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
import os

# Configuration depuis les variables d'environnement
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '0'))
MINECRAFT_IP = os.getenv('MINECRAFT_IP')
MINECRAFT_PORT = int(os.getenv('MINECRAFT_PORT', '25565'))

# Configuration minimale des intentions
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Variable globale unique pour le message
message_status = None
dernier_statut = False

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user.name}')
    await initialiser_message_status()
    verifier_serveur.start()

async def initialiser_message_status():
    global message_status
    channel = bot.get_channel(CHANNEL_ID)
    async for message in channel.history(limit=10):  # Réduit à 10 messages
        if message.author == bot.user and "État du serveur Minecraft" in message.content:
            message_status = message
            return
    message_status = await channel.send("🔄 État du serveur Minecraft\n*Chargement...*")

@tasks.loop(minutes=2)  # Vérifie toutes les 2 minutes au lieu de 30 secondes
async def verifier_serveur():
    global message_status, dernier_statut
    try:
        serveur = JavaServer(MINECRAFT_IP, MINECRAFT_PORT)
        status = await serveur.async_status()

        # Message simplifié
        message = f"🖥️ **Serveur Minecraft**\n✅ En ligne - {status.players.online} joueurs"

        if not dernier_statut:
            channel = bot.get_channel(CHANNEL_ID)
            await channel.send("Le serveur Minecraft est EN LIGNE ! 🎮")
            dernier_statut = True

    except Exception:
        message = "🖥️ **Serveur Minecraft**\n❌ Hors ligne"
        if dernier_statut:
            channel = bot.get_channel(CHANNEL_ID)
            await channel.send("Le serveur Minecraft est HORS LIGNE ⚠️")
            dernier_statut = False

    try:
        await message_status.edit(content=message)
    except discord.NotFound:
        channel = bot.get_channel(CHANNEL_ID)
        message_status = await channel.send(message)

@bot.command(name='status')
async def status(ctx):
    await verifier_serveur()
    await ctx.message.add_reaction('✅')

bot.run(TOKEN)