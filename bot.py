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
    VOICE_CHANNEL_ID = int(os.environ.get("VOICE_CHANNEL_ID", "0"))
    if VOICE_CHANNEL_ID == 0:
        raise ValueError("VOICE_CHANNEL_ID no está configurado o es 0")
except ValueError as e:
    print(f"--- ERROR: {e} ---")
    print("Asegúrate de haber configurado VOICE_CHANNEL_ID en Render con un ID numérico válido.")
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


# --- CORRECCIÓN 1: Cargar la RUTA de FFmpeg UNA SOLA VEZ ---
print("Obteniendo la ruta de FFmpeg...")
try:
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    print("Ruta de FFmpeg encontrada.")
except Exception as e:
    print(f"Error CRÍTICO al cargar FFmpeg: {e}")
    exit() # Salir si no podemos encontrar ffmpeg


# --- CORRECCIÓN 2: 'play_silence' debe RE-CREAR el stream de audio ---
def play_silence(vc):
    """Crea un NUEVO stream de audio silencioso y lo reproduce."""
    try:
        if not vc.is_connected():
            print("VC no conectado, no se puede reproducir silencio.")
            return

        # ESTA ES LA LÍNEA CLAVE:
        # Creamos un *nuevo* objeto FFmpegPCMAudio CADA VEZ que se llama la función.
        # Los streams de audio no se pueden re-usar.
        audio_source = discord.FFmpegPCMAudio('silence.mp3', executable=ffmpeg_path)
        
        # El 'after' ahora llama a esta misma función, creando un bucle infinito
        vc.play(audio_source, after=lambda e: play_silence(vc) if e is None else print(f"Error en 'after' de play: {e}"))
    
    except Exception as e:
        print(f"Error al reproducir silencio: {e}")

# Tarea en bucle que revisa la conexión cada 15 segundos
# Esto es un "vigilante" por si el bucle de 'play_silence' falla
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
            play_silence(vc) # Empezamos el bucle de silencio
        
        elif not voice_client.is_connected():
            # Estaba conectado pero se cayó, reconectamos.
            print(f"Reconectando a {channel.name}...")
            vc = await voice_client.connect() # connect() maneja la reconexión
            play_silence(vc) # Reiniciamos el bucle de silencio

        elif not voice_client.is_playing():
            # Está conectado PERO no está reproduciendo (el bucle se rompió)
            print("Audio silencioso no estaba sonando. Reiniciando bucle...")
            play_silence(voice_client)

    except Exception as e:
        print(f"Error en el bucle de conexión: {e}")

# Evento que se dispara cuando el bot se inicia y conecta a Discord
@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    print('Iniciando tarea de conexión a voz...')
    check_voice_connection.start() # Inicia la tarea en bucle


# --- Inicio del Servidor y el Bot ---
if __name__ == "__main__":
    
    # Asegúrate de que 'silence.mp3' existe antes de empezar
    if not os.path.exists('silence.mp3'):
        print("--- ERROR CRÍTICO: No se encuentra el archivo 'silence.mp3' ---")
        print("Asegúrate de que 'silence.mp3' esté en tu repositorio de GitHub.")
        exit()
        
    # Inicia el servidor web en un hilo
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

