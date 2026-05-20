"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Home() {
  const [mode, setMode] = useState('weekly');
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  // Manual Input States
  const [title, setTitle] = useState('');
  const [dates, setDates] = useState('');
  const [timeLapsed, setTimeLapsed] = useState('');
  const [pctPeriod, setPctPeriod] = useState('');
  const [pctWork, setPctWork] = useState('');
  const [isDuplicate, setIsDuplicate] = useState(false);

  // Correspondence & Document States
  const [docCategory, setDocCategory] = useState('contractor'); // contractor | client | general
  const [docTitle, setDocTitle] = useState('');
  const [docSummary, setDocSummary] = useState('');
  const [docDateSent, setDocDateSent] = useState('');
  const [docSender, setDocSender] = useState('');
  const [docRecipient, setDocRecipient] = useState('');
  const [docFile, setDocFile] = useState<File | null>(null);
  
  const [docLoading, setDocLoading] = useState(false);
  const [docStatus, setDocStatus] = useState('');
  const [docError, setDocError] = useState('');
  const [uploadedDocs, setUploadedDocs] = useState<any[]>([]);
  const [activeDocDetail, setActiveDocDetail] = useState<any | null>(null);
  const [docToDelete, setDocToDelete] = useState<any | null>(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  // Fetch existing correspondence documents on mount
  useEffect(() => {
    fetchDocs();
  }, []);

  const fetchDocs = async () => {
    try {
      const resp = await fetch('http://localhost:8000/api/project-documents');
      if (resp.ok) {
        const data = await resp.json();
        setUploadedDocs(data);
      }
    } catch (e) {
      console.error("Failed to fetch documents list", e);
    }
  };

  const handleDocFileChange = (newFiles: FileList | null) => {
    if (!newFiles || newFiles.length === 0) return;
    setDocFile(newFiles[0]);
    setDocError('');
  };

  const handleUploadDocument = async () => {
    if (!docFile) {
      setDocError('Please choose a PDF document to upload.');
      return;
    }

    setDocLoading(true);
    setDocError('');
    setDocStatus('📦 Reading and uploading document to server...');

    const formData = new FormData();
    formData.append('file', docFile);
    formData.append('title', docTitle);
    formData.append('summary', docSummary);
    formData.append('date_sent', docDateSent);
    formData.append('category', docCategory);
    
    // Smart auto-fill
    const finalSender = docCategory === 'contractor' 
      ? 'Contractor' 
      : docCategory === 'client' 
        ? 'Client / Project Manager' 
        : docSender;
        
    const finalRecipient = docCategory === 'contractor' && !docRecipient
      ? 'Client / Project Manager'
      : docCategory === 'client' && !docRecipient
        ? 'Contractor'
        : docRecipient;

    formData.append('sender', finalSender);
    formData.append('recipient', finalRecipient);

    try {
      setDocStatus('📡 Connecting to Claims Analysis AI Engine...');
      const response = await fetch('http://localhost:8000/api/upload-document', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Server failed to process document');
      }

      setDocStatus('Claims AI analysis complete!');
      setDocFile(null);
      setDocTitle('');
      setDocSummary('');
      setDocDateSent('');
      setDocSender('');
      setDocRecipient('');
      
      // Refresh documents list
      await fetchDocs();
      
      setDocStatus('');
      setShowSuccessModal(true);
    } catch (err: any) {
      setDocError(err.message || 'An error occurred during document parsing.');
      setDocStatus('');
    } finally {
      setDocLoading(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/project-documents/${docId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        await fetchDocs();
        if (activeDocDetail && activeDocDetail.id === docId) {
          setActiveDocDetail(null);
        }
        setDocToDelete(null);
      } else {
        alert('Failed to delete document');
      }
    } catch (e) {
      console.error('Delete failed', e);
    }
  };

  // Check for existing report title in history
  useEffect(() => {
    const checkTitle = async () => {
      if (title.length > 3) {
        try {
          const resp = await fetch(`http://localhost:8000/api/check-duplicate?title=${encodeURIComponent(title)}`);
          const data = await resp.json();
          setIsDuplicate(data.exists);
        } catch (e) {
          console.error("Duplicate check failed", e);
        }
      } else {
        setIsDuplicate(false);
      }
    };
    const timer = setTimeout(checkTitle, 500); // Debounce
    return () => clearTimeout(timer);
  }, [title]);

  // File Handling
  const handleFileChange = (newFiles: FileList | null) => {
    if (!newFiles) return;
    const array = Array.from(newFiles);
    setFiles(prev => [...prev, ...array]);
    setError('');
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const isReady = mode === 'weekly' ? files.length === 7 : (files.length >= 4 && files.length <= 6);

  const handleUpload = async () => {
    if (!isReady) {
      const msg = mode === 'weekly' ? "exactly 7 daily reports" : "between 4 and 6 weekly reports";
      setError(`Wait! You need ${msg}. You have ${files.length}.`);
      return;
    }

    setLoading(true);
    setError('');

    // Phase 1: Uploading
    setStatus('📦 Uploading reports to server...');

    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    formData.append('title', title);
    formData.append('report_date', dates);
    formData.append('time_elapsed', timeLapsed);
    formData.append('pct_period', pctPeriod);
    formData.append('pct_work', pctWork);

    try {
      const endpoint = mode === 'weekly' ? '/api/generate-weekly-stream' : '/api/generate-monthly-stream';
      setStatus('📡 Connecting to AI Vision Engine...');
      
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
         const errorData = await response.json();
         throw new Error(errorData.detail || "Server Error");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let session_id = "";

      while (true) {
        const { value, done } = await reader!.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              setStatus(data.msg);
              if (data.status === 'done') {
                session_id = data.session_id;
              }
              if (data.status === 'error') {
                throw new Error(data.msg);
              }
            } catch (e) {
              console.error("JSON parse error on line", line);
            }
          }
        }
      }

      if (session_id) {
        setStatus('📥 Downloading final document...');
        window.location.href = `http://localhost:8000/api/download-session/${session_id}`;
        setTimeout(() => setStatus(`✨ Success! ${mode === 'weekly' ? 'Weekly' : 'Monthly'} Report Ready.`), 2000);
      }
    } catch (err: any) {
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        setError('🌐 Network Error: The connection was lost. Please ensure you have a stable internet connection and try again.');
      } else {
        setError(err.message || 'An unexpected error occurred during processing.');
      }
      setStatus('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-vanilla-custard-50 text-vivid-tangerine-950 p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-start mb-2">
          <h1 className="text-3xl font-bold py-2 bg-gradient-to-r from-sunflower-gold-600 to-vivid-tangerine-600 bg-clip-text text-transparent font-serif">
            Makindu Affordable Housing Project
          </h1>
          <Link href="/" className="text-[10px] font-black text-vivid-tangerine-600 uppercase tracking-widest bg-vivid-tangerine-50 px-3 py-1.5 rounded-full hover:bg-vivid-tangerine-100 transition-colors border border-vivid-tangerine-200">
            ← Exit to Home
          </Link>
        </div>
        <p className="text-vivid-tangerine-800 mb-8 text-lg font-medium">Industrial AI reporting for professional site managers.</p>

        {/* Dashboard Navigation */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
          <a href="/contract" className="group bg-white p-6 rounded-3xl shadow-lg border border-vanilla-custard-100 hover:border-sunflower-gold-400 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-3xl">📝</span>
              <span className="text-vivid-tangerine-400 group-hover:translate-x-1 transition-transform">→</span>
            </div>
            <h3 className="font-bold text-vivid-tangerine-950">Contract Summary</h3>
            <p className="text-xs text-vivid-tangerine-600">Project details and scope of works</p>
          </a>
          <a href="/trends" className="group bg-white p-6 rounded-3xl shadow-lg border border-vanilla-custard-100 hover:border-vivid-tangerine-400 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-3xl">📈</span>
              <span className="text-vivid-tangerine-400 group-hover:translate-x-1 transition-transform">→</span>
            </div>
            <h3 className="font-bold text-vivid-tangerine-950">Trends & Risks</h3>
            <p className="text-xs text-vivid-tangerine-600">Visual performance & risk analysis</p>
          </a>
        </div>

        {/* Mode Selector */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={() => { setMode('weekly'); setFiles([]); }}
            className={`px-6 py-2.5 rounded-xl font-semibold transition-all shadow-md ${mode === 'weekly' ? 'bg-vivid-tangerine-600 text-white' : 'bg-white text-vivid-tangerine-700 hover:bg-vanilla-custard-100'}`}
          >
            Weekly Report
          </button>
          <button
            onClick={() => { setMode('monthly'); setFiles([]); }}
            className={`px-6 py-2.5 rounded-xl font-semibold transition-all shadow-md ${mode === 'monthly' ? 'bg-sunflower-gold-600 text-white' : 'bg-white text-vivid-tangerine-700 hover:bg-vanilla-custard-100'}`}
          >
            Monthly Report
          </button>
        </div>

        {/* Manual Input Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 bg-white p-8 rounded-3xl shadow-xl shadow-vanilla-custard-200/40 border border-vanilla-custard-200">
          <div className="md:col-span-2">
            <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Report Title</label>
            <input
              value={title} onChange={(e) => setTitle(e.target.value)}
              className={`w-full bg-vanilla-custard-50 border-2 ${isDuplicate ? 'border-sunflower-gold-400' : 'border-vanilla-custard-100'} rounded-xl px-4 py-3 focus:border-vivid-tangerine-500 outline-none transition-colors text-vivid-tangerine-950`}
              placeholder={mode === 'weekly' ? "e.g. WEEK 20 PROGRESS REPORT" : "e.g. MONTHLY REPORT (APRIL 2026)"}
            />
            {isDuplicate && (
              <div className="mt-2 text-vivid-tangerine-700 text-sm flex items-center gap-2 bg-vivid-tangerine-50 p-3 rounded-lg border border-vivid-tangerine-200">
                <span>⚡</span>
                <span>A report for "<strong>{title}</strong>" already exists. This will create an update.</span>
              </div>
            )}
          </div>
          <div>
            <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Reporting Period</label>
            <input
              value={dates} onChange={(e) => setDates(e.target.value)}
              className="w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-xl px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950"
              placeholder={mode === 'weekly' ? "e.g. 6TH – 12TH APRIL 2026" : "e.g. APRIL 2026"}
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Time Lapsed (Weeks)</label>
            <input
              value={timeLapsed} onChange={(e) => setTimeLapsed(e.target.value)}
              className="w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-xl px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950"
              placeholder="e.g. 20 Weeks"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">% Period Elapsed</label>
            <input
              value={pctPeriod} onChange={(e) => setPctPeriod(e.target.value)}
              className="w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-xl px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950"
              placeholder="e.g. 19.43%"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">% Work Done</label>
            <input
              value={pctWork} onChange={(e) => setPctWork(e.target.value)}
              className="w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-xl px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950"
              placeholder="e.g. 7.29%"
            />
          </div>
        </div>

        {/* Upload Zone */}
        <div className="space-y-4">
          <div className="bg-white border-2 border-dashed border-vanilla-custard-200 rounded-3xl p-10 text-center transition-all hover:border-vivid-tangerine-500 hover:bg-vanilla-custard-50 group shadow-lg">
            <input
              type="file" multiple accept=".pdf"
              onChange={(e) => handleFileChange(e.target.files)}
              className="hidden" id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">📁</div>
              <div className="text-lg font-bold text-vivid-tangerine-900 mb-1">Upload Site Logs</div>
              <div className="text-vivid-tangerine-400 font-medium text-sm mb-2">
                {isReady ? `Documents verified ✅` : mode === 'weekly' ? `${files.length} of 7 files ready` : `${files.length} of 4-6 files ready`}
              </div>
              <div className="text-[10px] text-vivid-tangerine-400 uppercase tracking-widest font-bold bg-vanilla-custard-100 py-1 px-3 rounded-full inline-block">
                ⚡ Stable Internet Connection Required
              </div>
            </label>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="bg-white rounded-2xl p-4 shadow-md border border-vanilla-custard-100 space-y-2">
              {files.map((file, idx) => (
                <div key={idx} className="flex justify-between items-center text-sm bg-vanilla-custard-50 p-3 rounded-xl border border-vanilla-custard-100">
                  <span className="truncate max-w-[80%] font-medium text-vivid-tangerine-800">📄 {file.name}</span>
                  <button onClick={() => removeFile(idx)} className="bg-vivid-tangerine-50 text-vivid-tangerine-600 hover:bg-vivid-tangerine-100 p-1.5 rounded-lg transition-colors">✕</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Status and Errors */}
        <div className="mt-8 space-y-4">
          {status && (
            <div className="bg-sunflower-gold-50 border border-sunflower-gold-200 text-vivid-tangerine-900 p-4 rounded-2xl animate-pulse font-semibold text-center shadow-sm text-sm">
              {status}
            </div>
          )}
          {error && (
            <div className="bg-vivid-tangerine-50 border border-vivid-tangerine-200 text-vivid-tangerine-900 p-4 rounded-2xl flex items-start gap-4 shadow-md text-sm">
              <span className="text-xl">🛠️</span>
              <div>
                <p className="font-bold">System Notification</p>
                <p className="opacity-90">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Action Area */}
        <div className="mt-8 flex flex-col items-center gap-4">
          {!isReady && !loading && (
            <div className="text-vivid-tangerine-400 font-bold bg-vanilla-custard-100/50 px-4 py-2 rounded-full text-xs uppercase tracking-wider">
              {mode === 'weekly' ? `Missing ${7 - files.length} more reports...` : `Upload 4-6 weekly reports`}
            </div>
          )}
          
          <button
            onClick={handleUpload}
            disabled={loading || !isReady}
            className={`w-full max-w-md py-4 rounded-2xl font-bold text-lg transition-all shadow-xl ${
              isReady && !loading 
                ? 'bg-gradient-to-r from-sunflower-gold-500 to-vivid-tangerine-600 text-white hover:scale-[1.01] active:scale-95' 
                : 'bg-vanilla-custard-200 text-vanilla-custard-400 cursor-not-allowed'
            }`}
          >
            {loading ? 'Processing Vision Data...' : isReady ? '🚀 Execute & Generate' : 'Waiting for Files'}
          </button>
          
          {isReady && !loading && (
            <p className="text-vivid-tangerine-400 text-xs font-semibold uppercase tracking-widest">Document Integrity Verified</p>
          )}
        </div>
        {/* Correspondence Separator */}
        <div className="border-t-2 border-vanilla-custard-200/60 my-16" />

        {/* Correspondence Section */}
        <div className="mb-8 text-left">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-deep-space-blue-600 to-vivid-tangerine-600 bg-clip-text text-transparent font-serif">
            Project Correspondence & Claims Ingestion
          </h2>
          <p className="text-vivid-tangerine-800 text-sm font-medium mt-1">
            Upload contractor letters, client instructions, EOT requests, or meeting minutes. Gemini AI will extract key claims and EOT risks to enrich your final reports.
          </p>
        </div>

        {/* Correspondence Ingestion Form Card */}
        <div className="bg-white p-8 rounded-3xl shadow-xl shadow-vanilla-custard-200/40 border border-vanilla-custard-200 mb-10 text-left">
          {/* Doc Category Selector */}
          <div className="flex gap-2 mb-6 p-1 bg-vanilla-custard-50 rounded-xl border border-vanilla-custard-200">
            {(['contractor', 'client', 'general'] as const).map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => {
                  setDocCategory(cat);
                  setDocTitle('');
                  setDocSummary('');
                  setDocDateSent('');
                  setDocSender(cat === 'general' ? '' : '');
                  setDocRecipient(cat === 'contractor' ? 'Client / Project Manager' : cat === 'client' ? 'Contractor' : '');
                }}
                className={`flex-1 py-2 rounded-lg font-bold text-xs uppercase tracking-wider transition-all ${
                  docCategory === cat 
                    ? 'bg-vivid-tangerine-600 text-white shadow-md' 
                    : 'text-vivid-tangerine-700 hover:bg-vanilla-custard-100'
                }`}
              >
                {cat === 'contractor' ? '👷 Contractor' : cat === 'client' ? '🏢 Client / PM' : '📚 General / Info'}
              </button>
            ))}
          </div>

          {/* Form Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Document Title / Subject</label>
              <input
                value={docTitle}
                onChange={(e) => setDocTitle(e.target.value)}
                className="w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-xl px-4 py-3 focus:border-vivid-tangerine-500 outline-none transition-colors text-vivid-tangerine-950"
                placeholder="e.g. Request for EOT due to rain delays"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Sender (From)</label>
              <input
                value={docCategory === 'contractor' ? 'Contractor' : docCategory === 'client' ? 'Client / Project Manager' : docSender}
                onChange={(e) => setDocSender(e.target.value)}
                disabled={docCategory !== 'general'}
                className={`w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-xl px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950 ${docCategory !== 'general' ? 'opacity-60 cursor-not-allowed bg-vanilla-custard-100/50' : ''}`}
                placeholder="Sender Name"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Recipient (To)</label>
              <input
                value={docRecipient}
                onChange={(e) => setDocRecipient(e.target.value)}
                className="w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-xl px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950"
                placeholder={docCategory === 'contractor' ? "Client / Project Manager" : docCategory === 'client' ? "Contractor" : "Recipient Name"}
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Date Sent / Received</label>
              <input
                type="date"
                value={docDateSent}
                onChange={(e) => setDocDateSent(e.target.value)}
                className="w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-xl px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Date Uploaded</label>
              <input
                value={new Date().toLocaleDateString()}
                disabled
                className="w-full bg-vanilla-custard-100/50 opacity-60 border-2 border-vanilla-custard-100 rounded-xl px-4 py-3 cursor-not-allowed text-vivid-tangerine-950"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Brief Summary (Optional)</label>
              <textarea
                value={docSummary}
                onChange={(e) => setDocSummary(e.target.value)}
                rows={3}
                className="w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-xl px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950 text-sm resize-none"
                placeholder="Leave blank to let Gemini scan the PDF and automatically summarize and analyze all key requests and EOT impacts."
              />
            </div>
          </div>

          {/* File Dropzone */}
          <div className="mt-6">
            <div className="bg-vanilla-custard-50/50 border-2 border-dashed border-vanilla-custard-200 rounded-2xl p-6 text-center hover:border-vivid-tangerine-500 hover:bg-vanilla-custard-50 transition-all cursor-pointer relative">
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => handleDocFileChange(e.target.files)}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="text-3xl mb-2">📁</div>
              <div className="text-xs font-bold text-vivid-tangerine-900 mb-1">
                {docFile ? `Selected: ${docFile.name}` : 'Upload PDF Correspondence'}
              </div>
              <div className="text-[10px] text-vivid-tangerine-400 uppercase tracking-widest font-black">
                {docFile ? 'Click to change file' : 'PDF files only'}
              </div>
            </div>
          </div>

          {/* Status and Errors */}
          {docStatus && (
            <div className="mt-6 bg-sunflower-gold-50 border border-sunflower-gold-200 text-vivid-tangerine-900 p-4 rounded-xl animate-pulse font-semibold text-center text-xs">
              {docStatus}
            </div>
          )}
          {docError && (
            <div className="mt-6 bg-vivid-tangerine-50 border border-vivid-tangerine-200 text-vivid-tangerine-900 p-4 rounded-xl text-xs font-bold">
              ⚠️ {docError}
            </div>
          )}

          {/* Action Button */}
          <button
            type="button"
            onClick={handleUploadDocument}
            disabled={docLoading || !docFile}
            className={`w-full mt-6 py-4 rounded-xl font-bold text-sm uppercase tracking-widest transition-all shadow-md ${
              docFile && !docLoading 
                ? 'bg-gradient-to-r from-deep-space-blue-600 to-vivid-tangerine-600 hover:scale-[1.01] active:scale-95 text-white' 
                : 'bg-vanilla-custard-200 text-vanilla-custard-400 cursor-not-allowed'
           }`}
          >
            {docLoading ? '🔄 AI Claims Analysis Active...' : '🚀 Ingest Correspondence & Run AI'}
          </button>
        </div>

        {/* Correspondence Register */}
        {uploadedDocs.length > 0 && (
          <div className="space-y-4 mb-16 text-left">
            <h3 className="text-sm font-bold text-vivid-tangerine-800 uppercase tracking-widest mb-4">Ingested Correspondence Register</h3>
            <div className="grid grid-cols-1 gap-4">
              {uploadedDocs.map((doc) => (
                <div key={doc.id} className="bg-white p-6 rounded-2xl border border-vanilla-custard-100 shadow-md flex flex-col md:flex-row justify-between gap-4 transition-all hover:shadow-lg text-left">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <span className={`text-[9px] font-black uppercase px-2 py-0.5 rounded-full border ${
                        doc.category === 'contractor' 
                          ? 'bg-vivid-tangerine-50 border-vivid-tangerine-200 text-vivid-tangerine-700' 
                          : doc.category === 'client' 
                            ? 'bg-deep-space-blue-50 border-deep-space-blue-200 text-deep-space-blue-700' 
                            : 'bg-vanilla-custard-50 border-vanilla-custard-200 text-vanilla-custard-700'
                      }`}>
                        {doc.category === 'contractor' ? '👷 Contractor' : doc.category === 'client' ? '🏢 Client / PM' : '📚 General'}
                      </span>
                      <span className="text-[10px] text-vivid-tangerine-400 font-bold bg-vanilla-custard-50 px-2 py-0.5 rounded-full">
                        📅 Sent: {doc.date_sent}
                      </span>
                      <span className="text-[10px] text-vivid-tangerine-400 font-bold bg-vanilla-custard-50 px-2 py-0.5 rounded-full">
                        📤 Uploaded: {doc.date_uploaded.split(' ')[0]}
                      </span>
                    </div>

                    <h4 className="font-bold text-vivid-tangerine-950 text-base mb-1">{doc.title}</h4>
                    <p className="text-xs text-vivid-tangerine-600 font-bold uppercase tracking-wider mb-2">
                      From: <span className="text-vivid-tangerine-900">{doc.sender}</span> &rarr; To: <span className="text-vivid-tangerine-900">{doc.recipient}</span>
                    </p>
                    <p className="text-xs text-vivid-tangerine-750 line-clamp-2">{doc.summary}</p>
                  </div>

                  <div className="flex md:flex-col justify-end items-stretch gap-2 min-w-[150px]">
                    <button
                      onClick={() => setActiveDocDetail(doc)}
                      className="px-4 py-2 bg-vanilla-custard-50 border border-vanilla-custard-200 rounded-xl font-bold text-xs text-vivid-tangerine-700 hover:bg-vanilla-custard-100 hover:text-vivid-tangerine-900 transition-colors text-center"
                    >
                      🔍 View Claims Analysis
                    </button>
                    <button
                      onClick={() => setDocToDelete(doc)}
                      className="px-4 py-2 bg-vivid-tangerine-50 border border-vivid-tangerine-200 rounded-xl font-bold text-xs text-vivid-tangerine-600 hover:bg-vivid-tangerine-100 hover:text-vivid-tangerine-750 transition-colors text-center"
                    >
                      🗑️ Delete Document
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Claims Overlay Modal */}
        {activeDocDetail && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-md">
            <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[85vh] overflow-y-auto border border-vanilla-custard-200 shadow-2xl relative flex flex-col text-left">
              
              {/* Header */}
              <div className="p-6 border-b border-vanilla-custard-150 flex justify-between items-start">
                <div>
                  <span className="text-[10px] font-black uppercase px-3 py-1 rounded-full border bg-vivid-tangerine-50 border-vivid-tangerine-200 text-vivid-tangerine-700 mb-2 inline-block">
                    {activeDocDetail.category.toUpperCase()} Claims Analysis
                  </span>
                  <h3 className="text-xl font-bold text-vivid-tangerine-950 font-serif leading-tight">{activeDocDetail.title}</h3>
                  <p className="text-xs text-vivid-tangerine-400 font-bold uppercase tracking-wider mt-1">
                    Sent: {activeDocDetail.date_sent} | From: {activeDocDetail.sender} to {activeDocDetail.recipient}
                  </p>
                </div>
                <button 
                  onClick={() => setActiveDocDetail(null)} 
                  className="p-1.5 bg-vanilla-custard-50 hover:bg-vanilla-custard-100 rounded-xl border border-vanilla-custard-200 text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors text-lg font-black leading-none"
                >
                  ✕
                </button>
              </div>

              {/* Content */}
              <div className="p-6 space-y-6 flex-1 text-sm text-vivid-tangerine-900 leading-relaxed overflow-y-auto">
                
                <div>
                  <h4 className="font-bold text-vivid-tangerine-950 uppercase tracking-widest text-xs mb-2">📜 Document Summary</h4>
                  <div className="bg-vanilla-custard-50 p-4 rounded-2xl border border-vanilla-custard-100 font-medium">
                    {activeDocDetail.summary}
                  </div>
                </div>

                <div>
                  <h4 className="font-bold text-vivid-tangerine-950 uppercase tracking-widest text-xs mb-2">🧠 AI Detailed Analysis</h4>
                  <p className="whitespace-pre-wrap text-vivid-tangerine-800">{activeDocDetail.ai_analysis?.detailed_analysis || "No detailed analysis available."}</p>
                </div>

                {activeDocDetail.ai_analysis?.requests_made?.length > 0 && (
                  <div>
                    <h4 className="font-bold text-vivid-tangerine-950 uppercase tracking-widest text-xs mb-2">💸 Extracted Requests</h4>
                    <ul className="space-y-1.5">
                      {activeDocDetail.ai_analysis.requests_made.map((req: string, i: number) => (
                        <li key={i} className="flex gap-2 items-start">
                          <span className="text-vivid-tangerine-600 font-black">&bull;</span>
                          <span className="text-vivid-tangerine-800">{req}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {activeDocDetail.ai_analysis?.action_items?.length > 0 && (
                  <div>
                    <h4 className="font-bold text-vivid-tangerine-950 uppercase tracking-widest text-xs mb-2">⚙️ Required Action Items</h4>
                    <ul className="space-y-1.5">
                      {activeDocDetail.ai_analysis.action_items.map((action: string, i: number) => (
                        <li key={i} className="flex gap-2 items-start bg-sunflower-gold-50/40 p-2.5 rounded-xl border border-sunflower-gold-100/60 font-medium text-vivid-tangerine-900">
                          <span className="text-sunflower-gold-600 font-black">✔</span>
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div>
                  <h4 className="font-bold text-vivid-tangerine-950 uppercase tracking-widest text-xs mb-2">⚖️ Contractual Implications & Risks</h4>
                  <div className="bg-vivid-tangerine-50/50 p-4 rounded-2xl border border-vivid-tangerine-100/60 font-medium text-vivid-tangerine-900">
                    {activeDocDetail.ai_analysis?.contractual_implications || "No specific implications noted."}
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="p-4 bg-vanilla-custard-50 border-t border-vanilla-custard-150 flex justify-end">
                <button
                  onClick={() => setActiveDocDetail(null)}
                  className="px-6 py-2.5 bg-vivid-tangerine-600 hover:bg-vivid-tangerine-700 text-white font-bold rounded-xl text-xs transition-colors"
                >
                  Close Claims Window
                </button>
              </div>

            </div>
          </div>
        )}

        {/* Custom Premium Delete Warning Modal */}
        {docToDelete && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/70 backdrop-blur-md transition-all duration-300">
            <div className="bg-white rounded-3xl max-w-md w-full overflow-hidden border border-vivid-tangerine-200/50 shadow-2xl relative flex flex-col text-left animate-in fade-in zoom-in duration-200">
              
              {/* Alert Header Banner */}
              <div className="bg-gradient-to-r from-red-600 to-vivid-tangerine-600 p-6 text-white flex items-center gap-4">
                <span className="text-4xl">⚠️</span>
                <div>
                  <h3 className="text-lg font-black uppercase tracking-widest leading-none mb-1">Critical Warning</h3>
                  <p className="text-[10px] text-white/90 font-bold uppercase tracking-wider">Permanent Deletion Action</p>
                </div>
              </div>

              {/* Warning Content */}
              <div className="p-6 space-y-4">
                <p className="text-sm font-bold text-vivid-tangerine-950">
                  You are about to delete a critical project correspondence document:
                </p>
                <div className="bg-vivid-tangerine-50/70 p-4 rounded-xl border border-vivid-tangerine-100 text-xs font-semibold text-vivid-tangerine-950 italic">
                  "{docToDelete.title}"
                </div>
                <p className="text-xs text-vivid-tangerine-600 font-medium leading-relaxed">
                  This action is **irreversible**. Deleting this document will permanently purge its parsed text content, contractor EOT requests, action items, and contractual delay risks from the cache. 
                </p>
                <p className="text-xs text-red-600 font-black uppercase tracking-wider bg-red-50 p-3 rounded-lg border border-red-100 text-center">
                  ⚠️ This document's AI insights will no longer be included in weekly/monthly report aggregation.
                </p>
              </div>

              {/* Action Footer Buttons */}
              <div className="p-4 bg-vanilla-custard-50 border-t border-vanilla-custard-150 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setDocToDelete(null)}
                  className="px-5 py-2.5 bg-vanilla-custard-200 hover:bg-vanilla-custard-300 text-vivid-tangerine-900 font-bold rounded-xl text-xs transition-all uppercase tracking-wider"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleDeleteDocument(docToDelete.id)}
                  className="px-5 py-2.5 bg-red-600 hover:bg-red-700 active:scale-95 text-white font-bold rounded-xl text-xs transition-all uppercase tracking-wider shadow-md hover:shadow-lg"
                >
                  Yes, Delete Document
                </button>
              </div>

            </div>
          </div>
        )}

        {/* Success Modal */}
        {showSuccessModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm transition-all duration-300">
            <div className="bg-white rounded-3xl max-w-sm w-full overflow-hidden border border-sunflower-gold-200/40 shadow-2xl relative flex flex-col text-left p-6 animate-in fade-in zoom-in duration-200">
              <h3 className="text-lg font-bold text-vivid-tangerine-950 mb-2 font-serif">Document Upload Successful</h3>
              <p className="text-xs text-vivid-tangerine-800 mb-6 leading-relaxed">
                View your analysed document in the register below, or upload a new document for scanning.
              </p>
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => setShowSuccessModal(false)}
                  className="px-6 py-2.5 bg-gradient-to-r from-sunflower-gold-500 to-vivid-tangerine-600 text-white font-bold rounded-xl text-xs uppercase tracking-wider shadow-md hover:scale-[1.02] active:scale-98 transition-all"
                >
                  OK
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Footer Panel */}
      <footer className="mt-20 border-t border-vanilla-custard-200 pt-12 pb-8 max-w-4xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="text-left">
            <p className="text-xs font-black text-vivid-tangerine-950 uppercase tracking-widest mb-1">Makindu Affordable Housing Project</p>
            <p className="text-[10px] text-vivid-tangerine-400 font-bold uppercase tracking-tighter mb-4 md:mb-0">Field Intelligence & Reporting</p>
            
            {/* NeuralAxis Labs Branding Logo */}
            <div className="flex items-center gap-2.5 mt-4">
              <span className="text-[10px] font-black uppercase text-vivid-tangerine-600 tracking-wider">Developed by</span>
              <img src="/neuralaxis-logo.png" alt="NeuralAxis Labs Logo" className="h-7 w-7 rounded-full aspect-square object-cover shadow-sm" />
              <span className="text-xs font-black text-vivid-tangerine-950 tracking-tight">NeuralAxis Labs</span>
            </div>
          </div>
          <div className="flex flex-col items-stretch md:items-end gap-3">
            <div className="flex justify-center md:justify-end gap-4">
              <Link href="/" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Home</Link>
              <Link href="/contract" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Contract</Link>
              <Link href="/trends" className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors">Trends</Link>
            </div>
            <div className="flex justify-center md:justify-end gap-3">
              <Link href="/terms" className="text-[10px] font-black text-vivid-tangerine-500 uppercase tracking-widest hover:text-vivid-tangerine-800 transition-colors bg-vanilla-custard-100/30 border border-vanilla-custard-200 px-3 py-1 rounded-full">Terms</Link>
              <Link href="/privacy" className="text-[10px] font-black text-vivid-tangerine-500 uppercase tracking-widest hover:text-vivid-tangerine-800 transition-colors bg-vanilla-custard-100/30 border border-vanilla-custard-200 px-3 py-1 rounded-full">Privacy</Link>
            </div>
          </div>
        </div>
        <div className="mt-8 text-center border-t border-vanilla-custard-100 pt-6">
          <p className="text-[10px] text-vanilla-custard-400 font-bold uppercase tracking-widest">&copy; 2026 Makindu Affordable Housing Project. All Rights Reserved.</p>
        </div>
      </footer>
    </main>
  );
}
