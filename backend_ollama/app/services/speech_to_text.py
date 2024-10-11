# speech_to_text.py
from groq import Groq

def transcribe_audio(file_path: str) -> str:
    client = Groq()
    with open(file_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(file_path, file.read()),
            model="whisper-large-v3-turbo",
        )
    return transcription.text
