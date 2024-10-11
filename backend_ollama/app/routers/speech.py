# app/routers/speech.py
import io
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from app.services.speech_to_text import transcribe_audio
from app.services.text_to_speech import synthesize_speech
import os
import uuid

router = APIRouter()

@router.post("/transcribe/")
async def transcribe(file: UploadFile = File(...)):
    contents = await file.read()
    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    with open(temp_filename, "wb") as f:
        f.write(contents)
    try:
        transcription = transcribe_audio(temp_filename)
    finally:
        os.remove(temp_filename)
    return {"transcription": transcription}

@router.post("/tts/")
async def tts(request: Request):
    data = await request.json()
    text = data.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    try:
        audio_content = synthesize_speech(text)
        return StreamingResponse(io.BytesIO(audio_content), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))