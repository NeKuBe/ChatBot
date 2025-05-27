from faster_whisper import WhisperModel

# Usa el modelo "medium" para buen balance entre calidad y rendimiento
model = WhisperModel("small", device="cuda", compute_type="float32")

def transcribe_audio(audio_path):
    try:
        # Transcripción optimizada para español regional
        segments, info = model.transcribe(
            audio_path,
            language="es",             # Forzar español
            task="transcribe",
            beam_size=15,
            temperature=0.0,
            best_of=5,
            vad_filter=True,
            initial_prompt=(
                "Audio informal de clientes de Culiacán hablando sobre fallas en consolas como PlayStation, Xbox o Nintendo. "
                "Usa expresiones como 'se madreó', 'no jala', 'HDMI', 'control no responde', 'pantalla negra', etc. "
                "Responde en español mexicano con un estilo natural."
            )
        )

        # Validación extra de idioma
        if info.language != "es":
            return {"error": f"Audio no es español (detectado: {info.language})"}

        # Unir texto limpio
        text = " ".join(seg.text.strip() for seg in segments if seg.text)

        return {
            "type": "audio",
            "text": text,
            "language": info.language
        }

    except Exception as e:
        return {"error": str(e)}
