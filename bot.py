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

# Configuration des intentions
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Variables globales
message_status = None
dernier_statut = None  # Initialement None pour forcer la première mise à jour

@bot.event
async def on_ready():
    print('Bot prêt')
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        print(f'Canal trouvé: {channel.name}')
        await initialiser_message_status()
        verifier_serveur.start()
    else:
        print(f'Erreur: Canal {CHANNEL_ID} non trouvé')

async def initialiser_message_status():
    """Crée ou trouve le message de statut"""
    global message_status
    channel = bot.get_channel(CHANNEL_ID)

    # Supprime les anciens messages du bot dans le canal
    async for message in channel.history(limit=10):
        if message.author == bot.user:
            await message.delete()

    # Crée un nouveau message de statut
    message_status = await channel.send("**Serveur Minecraft**\n❌ Hors ligne")
    print('Message de statut initialisé')

@tasks.loop(seconds=CHECK_INTERVAL)
async def verifier_serveur():
    """Vérifie le statut du serveur et met à jour le message"""
    global message_status, dernier_statut
    channel = bot.get_channel(CHANNEL_ID)

    try:
        serveur = JavaServer(MINECRAFT_IP, MINECRAFT_PORT)
        status = await serveur.async_status()
        nouveau_statut = True
        message = f"**Serveur Minecraft**\n✅ En ligne - {status.players.online} 👥"
    except Exception as e:
        nouveau_statut = False
        message = "**Serveur Minecraft**\n❌ Hors ligne"
        print(f'Erreur de connexion au serveur: {str(e)}')

    # Met à jour le message si le statut a changé ou si c'est la première vérification
    if nouveau_statut != dernier_statut or dernier_statut is None:
        try:
            # Si le message n'existe plus, en crée un nouveau
            if not message_status or not await message_exists(message_status):
                message_status = await channel.send(message)
                print('Nouveau message créé')
            else:
                await message_status.edit(content=message)
                print('Message mis à jour')
            dernier_statut = nouveau_statut
        except Exception as e:
            print(f'Erreur lors de la mise à jour du message: {str(e)}')

async def message_exists(message):
    """Vérifie si un message existe toujours"""
    try:
        channel = bot.get_channel(CHANNEL_ID)
        await channel.fetch_message(message.id)
        return True
    except:
        return False

@bot.command(name='status')
async def status_check(ctx):
    """Commande pour vérifier manuellement le statut"""
    await verifier_serveur()
    await ctx.message.add_reaction('✅')

# Démarrage du bot
bot.run(TOKEN)