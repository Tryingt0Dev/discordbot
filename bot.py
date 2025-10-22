import discord
from discord.ext import tasks
import os
from flask import Flask
from markupsafe import Markup # Importamos Markup
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
    # --- TU CÓDIGO HTML CON EL VIDEO DE YOUTUBE IMPLEMENTADO ---
    return Markup("""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EDUARDOYT666 | Presentación</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            min-height: 100vh;
            margin: 0;
            padding: 0;
            background: linear-gradient(120deg, #232526 0%, #414345 100%);
            overflow-x: hidden;
        }
        .animated-bg {
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            z-index: 0;
            pointer-events: none;
        }
        .presentation-card {
            position: relative;
            z-index: 2;
            background: rgba(44, 62, 80, 0.92);
            border-radius: 18px;
            padding: 2.5rem 2rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            max-width: 480px;
            margin: 4rem auto;
        }
        .profile-img {
            width: 120px;
            height: 120px;
            object-fit: cover;
            border-radius: 50%;
            border: 4px solid #fff;
            margin-bottom: 1rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        }
        .yt-btn {
            background: #ff0000;
            color: #fff;
            border: none;
            font-size: 1.2rem;
            padding: 0.75rem 2rem;
            border-radius: 50px;
            margin-top: 1.5rem;
            transition: background 0.2s;
        }
        .yt-btn:hover {
            background: #c20000;
            color: #fff;
        }
        
        /* CSS para el video de YouTube responsivo */
        .video-container {
            margin: 2rem 0 1rem 0;
            position: relative;
            overflow: hidden;
            width: 100%;
            padding-top: 56.25%; /* Proporción 16:9 */
            border-radius: 12px;
            box-shadow: 0 2px 16px rgba(0,0,0,0.3);
        }
        .video-container iframe {
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            width: 100%;
            height: 100%;
            border: none;
        }
        
        h1 {
            font-family: 'Montserrat', sans-serif;
            font-weight: 700;
            letter-spacing: 2px;
            color: #ffffff;
        }
        .subtitle {
            font-size: 1.1rem;
            color: #e0e0e0;
        }
    </style>
</head>
<body>
    <svg class="animated-bg" viewBox="0 0 1920 1080" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="400" cy="200" r="180" fill="#ff0000" fill-opacity="0.08">
            <animate attributeName="cx" values="400;1600;400" dur="12s" repeatCount="indefinite"/>
        </circle>
        <circle cx="1600" cy="900" r="220" fill="#00ffea" fill-opacity="0.07">
            <animate attributeName="cy" values="900;200;900" dur="10s" repeatCount="indefinite"/>
        </circle>
        <circle cx="960" cy="540" r="320" fill="#fff700" fill-opacity="0.04">
            <animate attributeName="r" values="320;180;320" dur="14s" repeatCount="indefinite"/>
        </circle>
    </svg>
    <div class="container">
        <div class="presentation-card text-center">
            
            <img src="https://raw.githubusercontent.com/Tryingt0Dev/discordbot/main/eduardoyt666.jpg" alt="EDUARDOYT666" class="profile-img">
            
            <h1>EDUARDOYT666</h1>
            <div class="subtitle mb-3">¡Bienvenido a la morada digital de <b>EDUARDOYT666</b>! Disfruta el video y conoce su contenido.</div>
            
            <!-- Video de YouTube Embebido con tu ID -->
            <div class="video-container">
                <iframe 
                    src="https://www.youtube.com/embed/c7ZGtZCFQGo?autoplay=1&mute=1&loop=1&playsinline=1&playlist=c7ZGtZCFQGo" 
                    title="YouTube video player" 
                    allow="autoplay; encrypted-media" 
                    allowfullscreen>
                </iframe>
            </div>

            <a href="https://youtube.com/@eduardoyt666" target="_blank" class="yt-btn">
                <i class="bi bi-youtube"></i> Ver canal de YouTube
            </a>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
</body>
</html>
""")

def run_web_server():
  # Añadimos use_reloader=False para evitar que se inicie dos veces
  app.run(host='0.0.0.0', port=8080, use_reloader=False)


# --- Configuración del Cliente de Discord ---
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True 

client = discord.Client(intents=intents)


# --- Lógica del Bot ---
print("Obteniendo la ruta de FFmpeg...")
try:
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    print("Ruta de FFmpeg encontrada.")
except Exception as e:
    print(f"Error CRÍTICO al cargar FFmpeg: {e}")
    exit() # Salir si no podemos encontrar ffmpeg

def play_silence(vc):
    """Crea un NUEVO stream de audio silencioso y lo reproduce."""
    try:
        if not vc.is_connected():
            print("VC no conectado, no se puede reproducir silencio.")
            return

        # Re-creamos el stream CADA VEZ para el bucle
        audio_source = discord.FFmpegPCMAudio('silence.mp3', executable=ffmpeg_path)
        vc.play(audio_source, after=lambda e: play_silence(vc) if e is None else print(f"Error en 'after' de play: {e}"))
    
    except Exception as e:
        print(f"Error al reproducir silencio: {e}")

@tasks.loop(seconds=15)
async def check_voice_connection():
    await client.wait_until_ready()

    try:
        channel = client.get_channel(VOICE_CHANNEL_ID)
        if not channel:
            print(f"Error: No se encontró el canal con ID {VOICE_CHANNEL_ID}")
            return

        guild = channel.guild
        voice_client = discord.utils.get(client.voice_clients, guild=guild)

        if voice_client is None:
            print(f"Conectando a {channel.name}...")
            vc = await channel.connect()
            play_silence(vc)
        
        elif not voice_client.is_connected():
            print(f"Reconectando a {channel.name}...")
            vc = await voice_client.connect()
            play_silence(vc)

        elif not voice_client.is_playing():
            print("Audio silencioso no estaba sonando. Reiniciando bucle...")
            play_silence(voice_client)

    except Exception as e:
        print(f"Error en el bucle de conexión: {e}")

@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    print('Iniciando tarea de conexión a voz...')
    check_voice_connection.start()


# --- Inicio del Servidor y el Bot ---
if __name__ == "__main__":
    
    if not os.path.exists('silence.mp3'):
        print("--- ERROR CRÍTICO: No se encuentra el archivo 'silence.mp3' ---")
        print("Asegúrate de que 'silence.mp3' esté en tu repositorio de GitHub.")
        exit()
        
    print("Iniciando servidor web...")
    t_web = Thread(target=run_web_server)
    t_web.daemon = True # Permite que el hilo se cierre si el script principal se detiene
    t_web.start()
    
    print("Iniciando el bot de Discord...")
    try:
        client.run(TOKEN)
    except discord.errors.LoginFailure:
        print("\n--- ERROR: TOKEN INVÁLIDO ---")
        print("Revisa la variable de entorno DISCORD_TOKEN en Render.")
    except Exception as e:
        print(f"Error desconocido al ejecutar el bot: {e}")

