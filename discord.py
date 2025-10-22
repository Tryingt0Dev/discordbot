import discordbot.discord as discord
from discord.ext import tasks
from flask import Flask
from threading import Thread
import os

# --- Configuración ---
# Reemplaza con tus propios IDs
TOKEN = "551e73b1220b8db7e6aa04a6a79c7f79e39e31350dc5627bd9940c7d1e523c2c"
VOICE_CHANNEL_ID = 1428203094138814584 # ID del canal de voz al que quieres que se una
app = Flask('')

@app.route('/')
# ---------------------
def home():
    return "¡El bot está vivo!"

def run_web_server():
  app.run(host='0.0.0.0', port=8080)

# Inicia el servidor web en un hilo separado
Thread(target=run_web_server).start()
# Configura los "intents" (permisos) que tu bot necesita
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True 

client = discord.Client(intents=intents)

# Esta es la fuente de audio silencioso que se reproducirá en bucle
# Asegúrate de tener 'silence.mp3' y 'ffmpeg.exe' en la misma carpeta
# o que ffmpeg esté en tu PATH.
silent_audio_source = discord.FFmpegPCMAudio('silence.mp3')

# Función para reproducir el silencio. Se llama a sí misma cuando termina.
def play_silence(vc):
    try:
        vc.play(silent_audio_source, after=lambda e: play_silence(vc) if vc.is_connected() else None)
    except Exception as e:
        print(f"Error al reproducir silencio: {e}")

# Tarea en bucle que revisa la conexión cada 15 segundos
@tasks.loop(seconds=15)
async def check_voice_connection():
    await client.wait_until_ready()  # Espera a que el bot esté conectado a Discord

    try:
        channel = client.get_channel(VOICE_CHANNEL_ID)
        if not channel:
            print(f"Error: No se encontró el canal con ID {VOICE_CHANNEL_ID}")
            return

        guild = channel.guild
        voice_client = discord.utils.get(client.voice_clients, guild=guild)

        if voice_client is None:
            # No está conectado, así que nos conectamos.
            print(f"Conectando a {channel.name}...")
            vc = await channel.connect()
            play_silence(vc) # Empezamos a reproducir silencio
        
        elif not voice_client.is_connected():
            # Estaba conectado pero se cayó, reconectamos.
            print(f"Reconectando a {channel.name}...")
            vc = await voice_client.connect()
            play_silence(vc) # Reiniciamos el silencio

        elif not voice_client.is_playing():
            # Está conectado pero no reproduciendo (raro, pero por si acaso)
            print("Audio silencioso no estaba sonando. Reiniciando...")
            play_silence(voice_client)

    except Exception as e:
        print(f"Error en el bucle de conexión: {e}")

# Evento que se dispara cuando el bot se inicia y conecta a Discord
@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    print('Iniciando tarea de conexión a voz...')
    check_voice_connection.start() # Inicia la tarea en bucle


Thread(target=run_web_server).start()


# Ejecuta el bot
try:
    client.run(TOKEN)
except discord.errors.LoginFailure:
    print("\n--- ERROR: TOKEN INVÁLIDO ---")
    