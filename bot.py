import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
import os

# Configuration depuis les variables d'environnement
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '0'))
MINECRAFT_IP = os.getenv('MINECRAFT_IP')
MINECRAFT_PORT = int(os.getenv('MINECRAFT_PORT', '25565'))
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))

# Configuration minimale des intentions
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Variables globales minimales
message_status = None
dernier_statut = False

async def get_server_status_message(en_ligne, joueurs=0):
    """Génère le message de statut formaté"""
    if en_ligne:
        return f"**Serveur Minecraft**\n✅ En ligne - {joueurs} 👥"
    return "**Serveur Minecraft**\n❌ Hors ligne"

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
            message_status = await channel.send(await get_server_status_message(False))
    except:
        message_status = await channel.send(await get_server_status_message(False))

@tasks.loop(seconds=CHECK_INTERVAL)
async def verifier_serveur():
    """Vérifie l'état du serveur et met à jour le message de statut"""
    global message_status, dernier_statut
    try:
        serveur = JavaServer(MINECRAFT_IP, MINECRAFT_PORT)
        status = await serveur.async_status()
        message = await get_server_status_message(True, status.players.online)
        nouveau_statut = True
    except Exception:
        message = await get_server_status_message(False)
        nouveau_statut = False

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