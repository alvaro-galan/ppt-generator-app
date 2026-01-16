import React, { useEffect } from 'react';
import { useReactMediaRecorder } from 'react-media-recorder';
import { Button } from './ui/button';
import { Mic, Square } from 'lucide-react';

interface AudioRecorderProps {
  onRecordingComplete: (blob: Blob) => void;
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({ onRecordingComplete }) => {
  const { status, startRecording, stopRecording, mediaBlobUrl } = useReactMediaRecorder({ audio: true });

  // Fetch the blob when recording stops
  useEffect(() => {
    if (status === "stopped" && mediaBlobUrl) {
      fetch(mediaBlobUrl)
        .then(res => res.blob())
        .then(blob => onRecordingComplete(blob));
    }
  }, [status, mediaBlobUrl, onRecordingComplete]);

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="text-sm font-medium text-gray-500">
        Status: {status}
      </div>
      <div className="flex gap-2">
        {status !== "recording" ? (
          <Button onClick={startRecording} className="gap-2">
            <Mic className="h-4 w-4" /> Start Recording
          </Button>
        ) : (
          <Button onClick={stopRecording} className="gap-2 bg-red-500 hover:bg-red-600 text-white">
            <Square className="h-4 w-4" /> Stop Recording
          </Button>
        )}
      </div>
      {mediaBlobUrl && (
        <audio src={mediaBlobUrl} controls className="w-full mt-4" />
      )}
    </div>
  );
};

export default AudioRecorder;
