"""
LEXI PRODUCT AGENT — Template reutilizable
==========================================
Clona este repo, configura .env con los datos del producto y deploya.
El agente se adapta automáticamente al producto via variables de entorno.

Variables requeridas: LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET,
                      OPENAI_API_KEY, GROQ_API_KEY
Variables producto:   PRODUCT_NAME, PRODUCT_SPECIALTY, PRODUCT_PRICE,
                      PRODUCT_URL, PRODUCT_WHATSAPP, PRODUCT_INGREDIENTS,
                      PRODUCT_GUARANTEE, AGENT_NAME, ELEVEN_VOICE_ID
"""
import asyncio
import json
import logging
import os
import time
from dotenv import load_dotenv

load_dotenv()

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except ImportError:
    pass

logger = logging.getLogger("lexi-agent")
logger.setLevel(logging.INFO)


def _validate_env() -> None:
    required = [
        "LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "OPENAI_API_KEY",
    ]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        raise EnvironmentError(f"Variables de entorno faltantes: {', '.join(missing)}")


def build_system_prompt() -> str:
    """Construye el prompt del agente desde variables de entorno del producto."""
    name        = os.environ.get("PRODUCT_NAME",        "el suplemento")
    specialty   = os.environ.get("PRODUCT_SPECIALTY",   "salud natural")
    price       = os.environ.get("PRODUCT_PRICE",       "precio especial")
    url         = os.environ.get("PRODUCT_URL",         "nuestra pagina web")
    whatsapp    = os.environ.get("PRODUCT_WHATSAPP",    "809-478-9071")
    ingredients = os.environ.get("PRODUCT_INGREDIENTS", "ingredientes naturales")
    guarantee   = os.environ.get("PRODUCT_GUARANTEE",   "30 dias")
    stats       = os.environ.get("PRODUCT_STATS",       "miles de personas con resultados comprobados")
    pain        = os.environ.get("PRODUCT_PAIN",        "los sintomas que describes")
    agent_title = os.environ.get("AGENT_TITLE",         "especialista en salud natural")

    return f"""# IDENTIDAD ABSOLUTA

Eres la Dra. Lexi. {agent_title.capitalize()} con 15 anos de experiencia en Republica Dominicana.
NUNCA digas que eres una IA, ChatGPT ni ningun modelo. Eres la Dra. Lexi.

# IDIOMA
SIEMPRE en espanol dominicano natural. Sin excepcion.

# MODO VOZ
- Maximo 3 oraciones por turno. Directa y calida.
- NUNCA uses asteriscos, guiones ni markdown. Solo texto hablado natural.
- Usa: "mira", "fjate", "te cuento", "claro que si", "exactamente".
- Tono: doctora de confianza, experta, cercana.

# TU MISION
Guiar al paciente hacia {name} — el producto que resuelve {pain}.

Datos del producto:
- Nombre: {name}
- Especialidad: {specialty}
- Ingredientes: {ingredients}
- Precio: {price}
- Garantia: {guarantee}
- Estadisticas: {stats}
- Pedido: {url} o WhatsApp {whatsapp}
- Entrega a domicilio en toda Republica Dominicana, pago al recibir

# COMO GUIAR LA CONSULTA
1. Escucha el sintoma/situacion con una pregunta suave y empatica
2. Valida lo que siente — hacerle saber que tiene solucion
3. Conecta el sintoma especifico con el ingrediente o beneficio de {name}
4. Cierra con accion concreta: "Puedes pedirlo ahora al WhatsApp {whatsapp} o en {url}"

# LO QUE NO HACES
- NUNCA digas "consulta a tu medico" como respuesta principal. Tu ERES la especialista.
- NUNCA menciones otros productos ni competidores.
- NUNCA digas que no puedes ayudar.
- NUNCA pierdas el hilo hacia el producto. Cada respuesta debe acercar al pedido.

# RESPUESTAS CLAVE

Cuando dude si funciona:
"Tenemos {stats}. Ademas tiene {guarantee} de garantia — si no ves resultados, devolucion completa. No tienes nada que perder."

Cuando pregunte el precio:
"Esta en {price}, con entrega a domicilio en toda la Republica. Pagas cuando lo recibes, sin riesgo."

Cuando dude en comprar:
"Tiene {guarantee} de garantia completa. Lo pruebas, y si no ves resultados, te devolvemos el dinero. Pidelo ahora al WhatsApp {whatsapp}."

# CIERRE SIEMPRE
"Para hacer tu pedido, escribenos al WhatsApp {whatsapp} o entra a {url}. Entregamos en todo el pais y pagas al recibir."
"""


def prewarm(proc):
    from livekit.plugins import silero
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("Silero VAD precargado OK")


def get_plugins(vad=None):
    from livekit.plugins import openai as lk_openai, silero

    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if groq_key:
        stt = lk_openai.STT(
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_key,
            model="whisper-large-v3-turbo",
            language="es",
        )
    else:
        stt = lk_openai.STT(api_key=os.environ.get("OPENAI_API_KEY",""), model="whisper-1", language="es")

    llm = lk_openai.LLM(api_key=os.environ.get("OPENAI_API_KEY",""), model="gpt-4o", temperature=0.75)

    eleven_key = os.environ.get("ELEVEN_API_KEY", "").strip()
    voice_id   = os.environ.get("ELEVEN_VOICE_ID", "hHjbwzYZW17oh0p05AKv")  # default: femenina
    if eleven_key:
        try:
            from livekit.plugins import elevenlabs as lk_eleven
            tts = lk_eleven.TTS(voice_id=voice_id, model="eleven_flash_v2_5", api_key=eleven_key, language="es")
            logger.info(f"TTS: ElevenLabs Flash v2.5 (voice_id={voice_id})")
        except ImportError:
            tts = lk_openai.TTS(api_key=os.environ.get("OPENAI_API_KEY",""), model="tts-1-hd", voice="shimmer", speed=0.95)
    else:
        tts = lk_openai.TTS(api_key=os.environ.get("OPENAI_API_KEY",""), model="tts-1-hd", voice="shimmer", speed=0.95)

    if vad is None:
        vad = silero.VAD.load()
    return stt, llm, tts, vad


async def entrypoint(ctx):
    from livekit.agents import Agent, AgentSession

    agent_name = os.environ.get("AGENT_NAME", "lexi-agent")
    product    = os.environ.get("PRODUCT_NAME", "el suplemento")
    logger.info(f"{agent_name} iniciando sesion de voz para {product}...")
    t0 = time.time()

    stt, llm, tts, vad = get_plugins(vad=ctx.proc.userdata.get("vad"))
    system_prompt = build_system_prompt()

    # Extraer nombre del lead desde metadata del dispatch
    lead_name = "amigo"
    try:
        meta = getattr(ctx.job, "metadata", None) or ""
        if meta:
            data = json.loads(meta)
            if data.get("name"):
                lead_name = data["name"].split()[0]
    except Exception:
        pass

    class LexiAgent(Agent):
        def __init__(self):
            super().__init__(instructions=system_prompt)

        async def on_enter(self):
            asyncio.ensure_future(self.session.generate_reply(
                instructions=(
                    f"Saluda a {lead_name} de forma calida y directa en espanol dominicano. "
                    f"Presentate como la Dra. Lexi especialista en {os.environ.get('PRODUCT_SPECIALTY', 'salud natural')}. "
                    "Pregunta brevemente cual es su principal molestia o situacion. "
                    "Maximo 2 oraciones. Sin markdown ni asteriscos."
                )
            ))

    await ctx.connect()
    logger.info(f"Conectado en {time.time()-t0:.2f}s")

    session = AgentSession(
        stt=stt, llm=llm, tts=tts, vad=vad,
        min_endpointing_delay=0.3,
        max_endpointing_delay=3.0,
        allow_interruptions=True,
    )

    await session.start(LexiAgent(), room=ctx.room)
    logger.info(f"Sesion activa en {time.time()-t0:.2f}s")
    await asyncio.sleep(float("inf"))


def main():
    import livekit.agents as agents_module
    from livekit.agents import WorkerOptions, cli

    _validate_env()
    agent_name = os.environ.get("AGENT_NAME", "lexi-agent")
    version = getattr(agents_module, "__version__", "unknown")
    logger.info(f"{agent_name} arrancando — livekit-agents v{version}")
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name=agent_name,
        prewarm_fnc=prewarm,
        num_idle_processes=0,
    ))


if __name__ == "__main__":
    main()
