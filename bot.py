import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
import asyncio
import os

# Configuration à partir des variables d'environnement
# Ces variables seront configurées dans Railway
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '0'))
MINECRAFT_IP = os.getenv('MINECRAFT_IP')
MINECRAFT_PORT = int(os.getenv('MINECRAFT_PORT', '25565'))

# Configuration des intentions du bot
# Ces intentions sont nécessaires pour que le bot puisse fonctionner correctement
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Variable pour stocker le message de statut
message_status = None

@bot.event
async def on_ready():
    """
    Fonction exécutée quand le bot démarre.
    Elle initialise le message de statut et démarre la vérification périodique.
    """
    print(f'Bot connecté en tant que {bot.user.name}')
    await initialiser_message_status()
    verifier_serveur.start()

async def initialiser_message_status():
    """
    Crée ou retrouve le message de statut dans le canal spécifié.
    Si un ancien message existe, il le réutilise au lieu d'en créer un nouveau.
    """
    global message_status
    channel = bot.get_channel(CHANNEL_ID)

    # Recherche dans les 100 derniers messages si notre message de statut existe déjà
    async for message in channel.history(limit=100):
        if message.author == bot.user and "État du serveur Minecraft" in message.content:
            message_status = message
            return

    # Si aucun message n'est trouvé, en crée un nouveau
    message_status = await channel.send("🔄 État du serveur Minecraft\n*Chargement...*")

@tasks.loop(seconds=30)  # Vérifie toutes les 30 secondes
async def verifier_serveur():
    """
    Vérifie l'état du serveur Minecraft et met à jour le message de statut.
    Cette fonction s'exécute automatiquement toutes les 30 secondes.
    """
    global message_status

    try:
        # Tente de se connecter au serveur Minecraft
        serveur = JavaServer(MINECRAFT_IP, MINECRAFT_PORT)
        status = await serveur.async_status()

        # Prépare le message avec les informations actualisées
        message = (
            "🖥️ **État du serveur Minecraft**\n"
            f"📊 **Statut :** ✅ En ligne\n"
            f"👥 **Joueurs connectés :** {status.players.online}\n"
            f"⏰ Dernière mise à jour : <t:{int(discord.utils.utcnow().timestamp())}:R>"
        )

    except Exception as e:
        # Message si le serveur est hors ligne
        message = (
            "🖥️ **État du serveur Minecraft**\n"
            f"📊 **Statut :** ❌ Hors ligne\n"
            f"⏰ Dernière mise à jour : <t:{int(discord.utils.utcnow().timestamp())}:R>"
        )

    # Met à jour le message
    try:
        await message_status.edit(content=message)
    except discord.NotFound:
        # Si le message a été supprimé, en crée un nouveau
        channel = bot.get_channel(CHANNEL_ID)
        message_status = await channel.send(message)
    except Exception as e:
        print(f"Erreur lors de la mise à jour du message : {e}")

@bot.command(name='rafraichir')
async def rafraichir(ctx):
    """
    Commande pour forcer le rafraîchissement du statut.
    Les utilisateurs peuvent taper !rafraichir pour forcer une mise à jour.
    """
    await initialiser_message_status()
    await verifier_serveur()
    # Ajoute une réaction pour confirmer que la commande a été exécutée
    await ctx.message.add_reaction('✅')

@bot.command(name='status')
async def status(ctx):
    """
    Commande pour vérifier manuellement le statut du serveur.
    Les utilisateurs peuvent taper !status pour obtenir un rapport immédiat.
    """
    try:
        serveur = JavaServer(MINECRAFT_IP, MINECRAFT_PORT)
        status = await serveur.async_status()
        await ctx.send(f"✅ Serveur EN LIGNE\n👥 Joueurs connectés : {status.players.online}")
    except:
        await ctx.send("❌ Le serveur est actuellement HORS LIGNE")

# Démarrage du bot
bot.run(TOKEN)