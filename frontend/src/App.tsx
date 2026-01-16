import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import AudioRecorder from './components/AudioRecorder';
import FileUpload from './components/FileUpload';
import { Download, Loader2 } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [file, setFile] = useState<File | Blob | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'error'>('idle');
  const [downloadFilename, setDownloadFilename] = useState<string | null>(null);
  const [pdfFilename, setPdfFilename] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setErrorMsg(null);
    setDownloadFilename(null);
    setPdfFilename(null);
  };

  const handleRecordingComplete = (blob: Blob) => {
    setFile(blob);
    setErrorMsg(null);
    setDownloadFilename(null);
    setPdfFilename(null);
  };

  const handleSubmit = async () => {
    if (!file) return;

    setStatus('uploading');
    setErrorMsg(null);

    const formData = new FormData();
    // Determine filename
    const filename = file instanceof File ? file.name : 'recording.webm';
    formData.append('file', file, filename);

    try {
      const response = await axios.post(`${API_URL}/upload-audio/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setTaskId(response.data.task_id);
      setStatus('processing');
    } catch (error) {
      console.error(error);
      setStatus('error');
      setErrorMsg('Failed to upload audio.');
    }
  };

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval>;

    if (status === 'processing' && taskId) {
      intervalId = setInterval(async () => {
        try {
          const response = await axios.get(`${API_URL}/task/${taskId}`);
          const { status: taskStatus, result } = response.data;

          if (taskStatus === 'SUCCESS') {
            if (result.status === 'success') {
              setStatus('completed');
              setDownloadFilename(result.filename);
              if (result.pdf_filename) {
                setPdfFilename(result.pdf_filename);
              }
            } else {
              setStatus('error');
              setErrorMsg(result.error || 'Processing failed.');
            }
            clearInterval(intervalId);
          } else if (taskStatus === 'FAILURE') {
            setStatus('error');
            setErrorMsg('Task failed unexpectedly.');
            clearInterval(intervalId);
          }
        } catch (error) {
          console.error(error);
        }
      }, 2000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [status, taskId]);

  const handleDownload = () => {
    if (downloadFilename) {
      window.open(`${API_URL}/download/${downloadFilename}`, '_blank');
    }
  };

  const handleDownloadPdf = () => {
    if (pdfFilename) {
      window.open(`${API_URL}/download/${pdfFilename}`, '_blank');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 py-10 px-4">
      <div className="max-w-3xl mx-auto space-y-8">
        <header className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight text-blue-500">VERSION ACTUALIZADA V2 (DARK MODE)</h1>
          <p className="text-slate-400">Turn your voice into a professional PowerPoint presentation instantly.</p>
        </header>

        <Card className="bg-slate-900 border-slate-800 text-slate-50 shadow-lg">
          <CardHeader>
            <CardTitle>1. Provide Audio</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <h3 className="font-medium text-slate-300">Upload Audio File</h3>
                <FileUpload onFileSelect={handleFileSelect} />
              </div>
              <div className="space-y-2">
                <h3 className="font-medium text-slate-300">Record Voice</h3>
                <div className="h-full border border-slate-800 rounded-lg p-6 flex items-center justify-center bg-slate-950/50">
                  <AudioRecorder onRecordingComplete={handleRecordingComplete} />
                </div>
              </div>
            </div>
            {file && (
              <div className="bg-blue-900/20 text-blue-200 p-3 rounded-md text-center text-sm border border-blue-900/50">
                Selected: {file instanceof File ? file.name : 'Voice Recording'}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex justify-center">
          <Button 
            className="w-full md:w-auto min-w-[200px] text-lg"
            disabled={!file || status === 'uploading' || status === 'processing'}
            onClick={handleSubmit}
          >
            {status === 'uploading' ? (
              <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Uploading...</>
            ) : status === 'processing' ? (
              <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Processing AI...</>
            ) : (
              'Generate Presentation'
            )}
          </Button>
        </div>

        {status === 'completed' && (
          <Card className="bg-green-900/10 border-green-900/50 text-slate-50">
            <CardContent className="p-8 flex flex-col items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-green-500/20 flex items-center justify-center text-green-500">
                <Download className="h-6 w-6" />
              </div>
              <div className="text-center">
                <h3 className="text-xl font-bold text-green-500">Success!</h3>
                <p className="text-slate-400">Your presentation is ready for download.</p>
              </div>
              <div className="flex gap-4">
                <Button onClick={handleDownload} className="bg-green-600 hover:bg-green-700 text-white">
                  Download .PPTX
                </Button>
                {pdfFilename && (
                  <Button onClick={handleDownloadPdf} className="bg-red-600 hover:bg-red-700 text-white">
                    Download .PDF
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {status === 'error' && (
          <div className="bg-red-900/20 border border-red-900/50 text-red-200 p-4 rounded-md text-center">
            Error: {errorMsg}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
