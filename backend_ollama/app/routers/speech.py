# app/routers/speech.py
import io
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from app.services.speech_to_text import transcribe_audio
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