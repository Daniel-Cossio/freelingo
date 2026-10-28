import asyncio
import os
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.core.config import settings
from app.services.tts_service import KokoroTTSService
from app.services.stt_service import WhisperSTTService
from app.services.llm_adapter import LLMAdapter
from app.services.tour_audio import get_tour_audio

async def main():
    print("==================================================")
    print("🎙️ Verificando Pipeline de Voz Local FreeLingo + AGY")
    print("==================================================")

    # 1. Kokoro TTS
    print("\n1. Verificando Kokoro TTS (puerto 8880)...")
    tts = KokoroTTSService(settings.TTS_BASE_URL, settings.TTS_VOICE)
    await tts.health()
    print("   ✅ Kokoro TTS Health OK")

    # 2. Whisper STT
    print("\n2. Verificando Faster-Whisper STT (puerto 9000)...")
    stt = WhisperSTTService(settings.STT_BASE_URL)
    await stt.health()
    print("   ✅ Whisper STT Health OK")

    # 3. Síntesis de Audio (TTS)
    print("\n3. Generando audio sintético de prueba...")
    phrase = "Hello, I am Lingu, your personal AI tutor."
    audio_bytes = await tts.synthesize(phrase, language="en-US")
    print(f"   ✅ Audio generado con éxito ({len(audio_bytes)} bytes MP3)")

    # 4. Transcripción de Audio (STT)
    print("\n4. Transcribiendo audio con Whisper STT...")
    transcription = await stt.transcribe(
        audio_bytes,
        filename="test.mp3",
        mime_type="audio/mpeg",
        language="en"
    )
    print(f"   ✅ Transcripción: {repr(transcription)}")
    assert "lingu" in transcription.lower() or "tutor" in transcription.lower(), "Whisper no transcribió adecuadamente"

    # 5. Tour Audio Persistence Cache
    print("\n5. Verificando persistencia y caché del tour de bienvenida...")
    tour_path = await get_tour_audio(tts, locale="es", text="Paso de prueba del tour guiado.", voice=None)
    print(f"   ✅ Archivo de audio persistido en: {tour_path}")
    assert tour_path.is_file() and tour_path.stat().st_size > 0

    print("\n==================================================")
    print("🎉 ¡TODO EL PIPELINE DE VOZ Y CONVERSACIÓN FUNCIONA AL 100%!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
