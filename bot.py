import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
import os

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '0'))
MINECRAFT_IP = os.getenv('MINECRAFT_IP')
MINECRAFT_PORT = int(os.getenv('MINECRAFT_PORT', '25565'))
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))

# Configuration minimale des intentions
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

message_status = None
dernier_etat = None

@bot.event
async def on_ready():
    print('Bot prêt')
    await demarrer()
    verifier_serveur.start()

async def demarrer():
    global message_status
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        async for msg in channel.history(limit=5):
            if msg.author == bot.user:
                await msg.delete()
        message_status = await channel.send("**Serveur Minecraft**\n❌ Hors ligne")

@tasks.loop(seconds=CHECK_INTERVAL)
async def verifier_serveur():
    global message_status, dernier_etat
    try:
        serveur = JavaServer(MINECRAFT_IP, MINECRAFT_PORT)
        status = await serveur.async_status()
        nouvel_etat = (True, status.players.online)
    except:
        nouvel_etat = (False, 0)

    if nouvel_etat != dernier_etat:
        try:
            message = f"**Serveur Minecraft**\n{'✅ En ligne - ' + str(nouvel_etat[1]) + ' 👥' if nouvel_etat[0] else '❌ Hors ligne'}"
            if message_status:
                await message_status.edit(content=message)
            dernier_etat = nouvel_etat
        except discord.NotFound:
            channel = bot.get_channel(CHANNEL_ID)
            message_status = await channel.send(message)

@bot.command(name='status')
async def status_check(ctx):
    await verifier_serveur()
    await ctx.message.add_reaction('✅')

bot.run(TOKEN)