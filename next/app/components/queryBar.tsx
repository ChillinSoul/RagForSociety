// app/components/queryBar.tsx
import React, { useState, useRef } from "react";
import { Send, Mic, MicOff } from "lucide-react";
import Score from "./score";

interface QueryBarProps {
  query: string;
  setQuery: (query: string) => void;
  handleSubmit: (e: React.FormEvent) => void;
  responseMutation: any;
  responseBNFMutation: any;
  queryId: string;
}

const QueryBar = ({
  query,
  setQuery,
  handleSubmit,
  responseMutation,
  responseBNFMutation,
  queryId,
}: QueryBarProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const mediaStreamRef = useRef<MediaStream | null>(null); // Keep track of the media stream

  const handleMicClick = () => {
    if (!isRecording) {
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          mediaStreamRef.current = stream; // Store the media stream
          const mediaRecorder = new MediaRecorder(stream);
          mediaRecorderRef.current = mediaRecorder;
          mediaRecorder.start();
          setIsRecording(true);
          audioChunksRef.current = [];

          mediaRecorder.ondataavailable = (event) => {
            audioChunksRef.current.push(event.data);
          };

          mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunksRef.current, {
              type: "audio/webm",
            });
            sendAudioToBackend(audioBlob);
            setIsRecording(false);

            // Stop all tracks to release the microphone
            if (mediaStreamRef.current) {
              mediaStreamRef.current
                .getTracks()
                .forEach((track) => track.stop());
            }
          };
        })
        .catch((error) => {
          console.error("Error accessing microphone", error);
        });
    } else {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
        setIsRecording(false);

        // Stop all tracks immediately
        if (mediaStreamRef.current) {
          mediaStreamRef.current.getTracks().forEach((track) => track.stop());
        }
      }
    }
  };

  const sendAudioToBackend = (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    fetch("http://127.0.0.1:8000/transcribe/", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        setQuery(data.transcription);
      })
      .catch((error) => {
        console.error("Error transcribing audio", error);
      });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="absolute bottom-0 z-40 flex flex-row w-full gap-4 p-8"
    >
      <div className="form-control grow">
        <label htmlFor="query" className="label"></label>
        <input
          type="text"
          id="query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Comment puis-je vous aider?"
          required
          className="input input-bordered input-secondary w-full"
        />
      </div>

      <button
        type="button"
        aria-label="Activer/Désactiver le microphone"
        className={`btn ${isRecording ? "btn-error" : "btn-secondary"} mt-4`}
        onClick={handleMicClick}
        tabIndex={0}
        disabled={responseMutation.isPending || responseBNFMutation.isPending}
      >
        {isRecording ? <MicOff className="animate-pulse" /> : <Mic />}
      </button>

      <button
        type="submit"
        aria-label="Envoyer la requête"
        className="btn btn-secondary mt-4"
        tabIndex={0}
        disabled={responseMutation.isPending || responseBNFMutation.isPending}
      >
        <Send />
      </button>
      <Score queryId={queryId} />
    </form>
  );
};

export default QueryBar;
