import os
from io import BytesIO
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def synthesize_speech(text: str) -> bytes:
    ELEVENLABS_API_KEY = os.getenv("ELEVEN_API_KEY")
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVEN_API_KEY not set in environment variables.")

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    # Choose a voice (e.g., Adam pre-made voice)
    voice_id = "pNInz6obpgDQGcFmaJgB"  # Replace with desired voice ID

    # Define voice settings
    voice_settings = VoiceSettings(
        stability=0.75,
        similarity_boost=0.75,
    )

    # Perform the text-to-speech conversion
    response = client.text_to_speech.convert(
        voice_id=voice_id,
        output_format="mp3_44100_128",  # You can adjust the output format as needed
        text=text,
        model_id="eleven_multilingual_v1",  # Or "eleven_multilingual_v1" for multiple languages
        voice_settings=voice_settings,
    )

    # Create a BytesIO object to hold the audio data in memory
    audio_stream = BytesIO()

    # Write each chunk of audio data to the stream
    for chunk in response:
        if chunk:
            audio_stream.write(chunk)

    # Reset stream position to the beginning
    audio_stream.seek(0)

    # Return the audio content as bytes
    return audio_stream.read()
