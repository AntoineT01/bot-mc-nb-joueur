import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
import asyncio

# === Configuration du bot ===
# Remplacez ces valeurs par les vôtres
TOKEN = 'MTMzODQ0Njc4MjU4MTA1MTQxMg.GXZYZg.53KSGBt5gW2z61agM_NcPGLj77iePmpEXiZx0o'  # Le token de votre bot Discord
CHANNEL_ID = 1338451009156153374  # L'ID du canal où le bot enverra les messages
MINECRAFT_IP = '212.195.167.183'  # L'adresse IP de votre serveur Minecraft
MINECRAFT_PORT = 25565  # Le port de votre serveur Minecraft (25565 par défaut)

# Configuration des intentions du bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Variable pour stocker l'ID du message de statut
message_status = None

@bot.event
async def on_ready():
    """Fonction exécutée quand le bot démarre"""
    print(f'Bot connecté en tant que {bot.user.name}')
    await initialiser_message_status()
    verifier_serveur.start()

async def initialiser_message_status():
    """Crée ou retrouve le message de statut"""
    global message_status
    channel = bot.get_channel(CHANNEL_ID)
    
    # Recherche dans les 100 derniers messages si notre message de statut existe déjà
    async for message in channel.history(limit=100):
        if message.author == bot.user and "État du serveur Minecraft" in message.content:
            message_status = message
            return

    # Si aucun message n'est trouvé, en crée un nouveau
    message_status = await channel.send("🔄 État du serveur Minecraft\n*Chargement...*")

@tasks.loop(seconds=30)
async def verifier_serveur():
    """Vérifie l'état du serveur et met à jour le message de statut"""
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
        )
    
    # Met à jour le message
    try:
        await message_status.edit(content=message)
    except discord.NotFound:
        # Si le message a été supprimé, en crée un nouveau
        channel = bot.get_channel(CHANNEL_ID)
        message_status = await channel.send(message)

@bot.command(name='rafraichir')
async def rafraichir(ctx):
    """Commande pour forcer le rafraîchissement du statut"""
    await initialiser_message_status()
    await verifier_serveur()
    await ctx.message.add_reaction('✅')

# Démarrage du bot
bot.run(TOKEN)