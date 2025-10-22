import discord
from discord.ext import tasks
import os
from flask import Flask
from threading import Thread
import imageio_ffmpeg  # Asegúrate de que esto esté en requirements.txt

# --- Configuración del Bot ---
TOKEN = os.environ.get("DISCORD_TOKEN")

if not TOKEN:
    print("--- ERROR: No se encontró la variable de entorno DISCORD_TOKEN ---")
    print("Asegúrate de haberla configurado en el dashboard de Render.")
    exit()

try:
    # Convertimos el ID a un entero
    VOICE_CHANNEL_ID = int(os.environ.get("VOICE_CHANNEL_ID", "TU_ID_DE_CANAL_POR_DEFECTO_SI_FALLA"))
except ValueError:
    print("--- ERROR: VOICE_CHANNEL_ID no es un número válido ---")
    print("Asegúrate de haberla configurado en el dashboard de Render.")
    exit()


# --- Configuración del Servidor Web (para UptimeRobot) ---
app = Flask('')

@app.route('/')
def home():
    return "¡El bot está vivo!"

def run_web_server():
  # Añadimos use_reloader=False para evitar que se inicie dos veces
  app.run(host='0.0.0.0', port=8080, use_reloader=False)


# --- Configuración del Cliente de Discord ---
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True 

client = discord.Client(intents=intents)


# --- CORRECCIÓN 1: Cargar FFmpeg y el audio UNA SOLA VEZ al inicio ---
print("Cargando FFmpeg...")
try:
    # 1. Obtener la ruta de ffmpeg
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    
    # 2. Crear la fuente de audio silencioso UNA SOLA VEZ
    # Asegúrate de que 'silence.mp3' esté en tu repositorio de GitHub
    silent_audio_source = discord.FFmpegPCMAudio('silence.mp3', executable=ffmpeg_path)
    print("Fuente de audio silencioso cargada.")

except Exception as e:
    print(f"Error CRÍTICO al cargar FFmpeg o silence.mp3: {e}")
    print("Asegúrate de que 'silence.mp3' está en el repositorio.")
    exit() # Salir si no podemos cargar el audio


# --- CORRECCIÓN 2: 'play_silence' ahora solo REPRODUCE, no recarga ---
def play_silence(vc):
    """Reproduce la fuente de audio silencioso (ya cargada) en bucle."""
    try:
        if not vc.is_connected():
            print("VC no conectado, no se puede reproducir silencio.")
            return

        vc.play(silent_audio_source, after=lambda e: play_silence(vc) if e is None else print(f"Error en 'after' de play: {e}"))
    
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
            vc = await voice_client.connect() # connect() maneja la reconexión
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


# --- CORRECCIÓN 3: Iniciar el servidor web y el bot JUNTOS al final ---
if __name__ == "__main__":
    
    # Inicia el servidor web en un hilo (UNA SOLA VEZ)
    print("Iniciando servidor web...")
    t_web = Thread(target=run_web_server)
    t_web.daemon = True # Permite que el programa se cierre si solo queda este hilo
    t_web.start()
    
    # Ejecuta el bot
    print("Iniciando el bot de Discord...")
    try:
        client.run(TOKEN)
    except discord.errors.LoginFailure:
        print("\n--- ERROR: TOKEN INVÁLIDO ---")
        print("Revisa la variable de entorno DISCORD_TOKEN en Render.")
    except Exception as e:
        print(f"Error desconocido al ejecutar el bot: {e}")
