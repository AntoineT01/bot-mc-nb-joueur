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

# Variables globales pour le suivi
message_status = None
dernier_statut = None
dernier_nombre_joueurs = None  # Ajout d'une variable pour suivre le nombre de joueurs

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

    # Nettoyage des anciens messages
    async for message in channel.history(limit=10):
        if message.author == bot.user:
            await message.delete()

    # Création du message initial
    message_status = await channel.send("**Serveur Minecraft**\n❌ Hors ligne")
    print('Message de statut initialisé')

@tasks.loop(seconds=CHECK_INTERVAL)
async def verifier_serveur():
    """Vérifie le statut du serveur et met à jour le message"""
    global message_status, dernier_statut, dernier_nombre_joueurs
    channel = bot.get_channel(CHANNEL_ID)

    try:
        # Tentative de connexion au serveur Minecraft
        serveur = JavaServer(MINECRAFT_IP, MINECRAFT_PORT)
        status = await serveur.async_status()
        nombre_joueurs = status.players.online
        nouveau_statut = True
        message = f"**Serveur Minecraft**\n✅ En ligne - {nombre_joueurs} 👥"

        # Mise à jour uniquement si le statut ou le nombre de joueurs change
        if nouveau_statut != dernier_statut or nombre_joueurs != dernier_nombre_joueurs:
            print(f'Changement détecté - Joueurs: {nombre_joueurs}')
            dernier_statut = nouveau_statut
            dernier_nombre_joueurs = nombre_joueurs

            if not message_status or not await message_exists(message_status):
                message_status = await channel.send(message)
                print('Nouveau message créé')
            else:
                await message_status.edit(content=message)
                print(f'Message mis à jour - {nombre_joueurs} joueurs')

    except Exception as e:
        nouveau_statut = False
        message = "**Serveur Minecraft**\n❌ Hors ligne"
        print(f'Erreur de connexion au serveur: {str(e)}')

        # Mise à jour uniquement si le statut change
        if nouveau_statut != dernier_statut:
            dernier_statut = nouveau_statut
            dernier_nombre_joueurs = 0

            if not message_status or not await message_exists(message_status):
                message_status = await channel.send(message)
                print('Nouveau message créé (hors ligne)')
            else:
                await message_status.edit(content=message)
                print('Message mis à jour (hors ligne)')

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