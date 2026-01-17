import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import AudioRecorder from './components/AudioRecorder';
import FileUpload from './components/FileUpload';
import { Download, Loader2, Clock } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [file, setFile] = useState<File | Blob | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'error'>('idle');
  const [downloadFilename, setDownloadFilename] = useState<string | null>(null);
  const [pdfFilename, setPdfFilename] = useState<string | null>(null);
  const [interpretation, setInterpretation] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  // Progress State
  const [statusMessage, setStatusMessage] = useState<string>('Initializing AI...');
  const [progress, setProgress] = useState<number>(0);
  const [secondsElapsed, setSecondsElapsed] = useState<number>(0);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setErrorMsg(null);
    setDownloadFilename(null);
    setPdfFilename(null);
    setInterpretation(null);
    setProgress(0);
    setSecondsElapsed(0);
  };

  const handleRecordingComplete = (blob: Blob) => {
    setFile(blob);
    setErrorMsg(null);
    setDownloadFilename(null);
    setPdfFilename(null);
    setInterpretation(null);
    setProgress(0);
    setSecondsElapsed(0);
  };

  const handleSubmit = async () => {
    if (!file) return;

    setStatus('uploading');
    setErrorMsg(null);
    setProgress(0);
    setSecondsElapsed(0);

    const formData = new FormData();
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

  // Timer Effect
  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    if (status === 'processing') {
      timer = setInterval(() => {
        setSecondsElapsed(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [status]);

  // Polling Effect
  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval>;

    if (status === 'processing' && taskId) {
      intervalId = setInterval(async () => {
        try {
          const response = await axios.get(`${API_URL}/task/${taskId}`);
          const { status: taskStatus, result, info } = response.data;

          if (taskStatus === 'PROGRESS' && info) {
             if (info.status) setStatusMessage(info.status);
             if (info.progress) setProgress(info.progress);
             if (info.interpretation) setInterpretation(info.interpretation);
          }
          else if (taskStatus === 'SUCCESS') {
            if (result.status === 'success') {
              setStatus('completed');
              setDownloadFilename(result.filename);
              if (result.pdf_filename) setPdfFilename(result.pdf_filename);
              if (result.interpretation) setInterpretation(result.interpretation);
              setProgress(100);
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

        {/* Dynamic Interpretation Box (Shows during processing too) */}
        {interpretation && (status === 'processing' || status === 'completed') && (
          <Card className="bg-blue-900/10 border-blue-900/50 text-slate-50 animate-in fade-in duration-500">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg text-blue-400 flex items-center gap-2">
                 AI Interpretation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-300 italic text-lg">"{interpretation}"</p>
            </CardContent>
          </Card>
        )}

        <div className="flex justify-center w-full">
            {status === 'processing' ? (
                <Card className="w-full bg-slate-900 border-slate-800">
                    <CardContent className="p-6 space-y-4">
                        <div className="flex justify-between items-center text-blue-300">
                            <span className="flex items-center gap-2 font-medium animate-pulse">
                                <Loader2 className="h-5 w-5 animate-spin" />
                                {statusMessage}
                            </span>
                            <span className="flex items-center gap-2 text-slate-400 font-mono">
                                <Clock className="h-4 w-4" />
                                {secondsElapsed}s
                            </span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                            <div 
                                className="bg-gradient-to-r from-blue-600 to-cyan-500 h-full rounded-full transition-all duration-500 ease-out" 
                                style={{ width: `${Math.max(5, progress)}%` }}
                            ></div>
                        </div>
                    </CardContent>
                </Card>
            ) : (
                <Button 
                    className="w-full md:w-auto min-w-[200px] text-lg h-12"
                    disabled={!file || status === 'uploading'}
                    onClick={handleSubmit}
                >
                    {status === 'uploading' ? (
                    <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Uploading...</>
                    ) : (
                    'Generate Presentation'
                    )}
                </Button>
            )}
        </div>

        {status === 'completed' && (
          <Card className="bg-green-900/10 border-green-900/50 text-slate-50 animate-in zoom-in-95 duration-300">
            <CardContent className="p-8 flex flex-col items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-green-500/20 flex items-center justify-center text-green-500 mb-2">
                <Download className="h-8 w-8" />
              </div>
              <div className="text-center">
                <h3 className="text-2xl font-bold text-green-500">Presentation Ready!</h3>
                <p className="text-slate-400 mt-1">Generated in {secondsElapsed} seconds.</p>
              </div>
              <div className="flex flex-col sm:flex-row gap-4 w-full justify-center mt-4">
                <Button onClick={handleDownload} className="bg-green-600 hover:bg-green-700 text-white h-12 px-8 text-lg w-full sm:w-auto">
                  Download PowerPoint (.pptx)
                </Button>
                {pdfFilename && (
                  <Button onClick={handleDownloadPdf} className="bg-red-600 hover:bg-red-700 text-white h-12 px-8 text-lg w-full sm:w-auto">
                    Download PDF (.pdf)
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
