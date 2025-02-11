import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
import os

# Configuration depuis les variables d'environnement
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '0'))
MINECRAFT_IP = os.getenv('MINECRAFT_IP')
MINECRAFT_PORT = int(os.getenv('MINECRAFT_PORT', '25565'))
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))  # 5 minutes par défaut

# Configuration minimale des intentions
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Variables globales minimales
message_status = None
dernier_statut = False

@bot.event
async def on_ready():
    print('Bot prêt')
    await initialiser_message_status()
    verifier_serveur.start()

async def initialiser_message_status():
    """Initialise ou trouve le message de statut existant"""
    global message_status
    channel = bot.get_channel(CHANNEL_ID)
    try:
        message_status = await channel.fetch_message(channel.last_message_id)
        if not (message_status.author == bot.user and "Serveur Minecraft" in message_status.content):
            message_status = await channel.send("🎮 **Serveur Minecraft**\n*Vérification...*")
    except:
        message_status = await channel.send("🎮 **Serveur Minecraft**\n*Vérification...*")

@tasks.loop(seconds=CHECK_INTERVAL)
async def verifier_serveur():
    """Vérifie l'état du serveur et met à jour le message de statut"""
    global message_status, dernier_statut
    try:
        # Vérifie le serveur Minecraft
        serveur = JavaServer(MINECRAFT_IP, MINECRAFT_PORT)
        status = await serveur.async_status()

        # Message avec émojis pour meilleure visibilité
        message = (
            "🎮 **Serveur Minecraft**\n"
            f"✅ En ligne - {status.players.online} 👥"
        )
        nouveau_statut = True
    except Exception:
        # Message d'erreur avec émoji
        message = (
            "🎮 **Serveur Minecraft**\n"
            "❌ Hors ligne"
        )
        nouveau_statut = False

    # Met à jour le message uniquement si le statut a changé
    if nouveau_statut != dernier_statut:
        try:
            await message_status.edit(content=message)
        except:
            channel = bot.get_channel(CHANNEL_ID)
            message_status = await channel.send(message)
        dernier_statut = nouveau_statut

@bot.command(name='status')
async def status_check(ctx):
    """Commande pour vérifier manuellement le statut"""
    await verifier_serveur()
    await ctx.message.add_reaction('✅')

# Démarrage du bot
bot.run(TOKEN)