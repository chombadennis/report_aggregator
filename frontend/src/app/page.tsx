"use client";
import React, { useState, useEffect } from 'react';

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

  const targetCount = mode === 'weekly' ? 7 : 4;
  const isReady = files.length === targetCount;

  const handleUpload = async () => {
    if (!isReady) {
      setError(`Wait! You need exactly ${targetCount} reports. You have ${files.length}.`);
      return;
    }

    setLoading(true);
    setError('');

    // Phase 1: Uploading
    setStatus('[1/3] Uploading reports to server...');

    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    formData.append('title', title);
    formData.append('report_date', dates);
    formData.append('time_elapsed', timeLapsed);
    formData.append('pct_period', pctPeriod);
    formData.append('pct_work', pctWork);

    try {
      // Phase 2: AI Vision Scan
      setStatus('[2/3] Deep Scanning PDFs (This takes ~60-90 seconds)...');

      const endpoint = mode === 'weekly' ? '/api/generate-weekly' : '/api/generate-monthly';
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        // Phase 3: Finalizing
        setStatus('[3/3] Compiling Word Document...');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${mode}_report.docx`;
        document.body.appendChild(a);
        a.click();
        setStatus('✨ Success! Your report is ready.');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to generate report.');
        setStatus('');
      }
    } catch (err) {
      setError('Connection failed. Please ensure the backend server is running on port 8000.');
      setStatus('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-vanilla-custard-50 text-vivid-tangerine-950 p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-2 py-2 bg-gradient-to-r from-sunflower-gold-600 to-vivid-tangerine-600 bg-clip-text text-transparent font-serif">
          Construction Report Aggregator
        </h1>
        <p className="text-vivid-tangerine-800 mb-8 text-lg font-medium">Industrial AI reporting for professional site managers.</p>

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
              placeholder="e.g. WEEK 20 PROGRESS REPORT"
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
              placeholder="e.g. 6TH – 12TH APRIL 2026"
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
              type="file" multiple
              onChange={(e) => handleFileChange(e.target.files)}
              className="hidden" id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">📁</div>
              <div className="text-lg font-bold text-vivid-tangerine-900 mb-1">Upload Site Logs</div>
              <div className="text-vivid-tangerine-400 font-medium text-sm">
                {isReady ? `All ${targetCount} documents verified ✅` : `${files.length} of ${targetCount} files ready`}
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
              Missing {targetCount - files.length} more reports...
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
      </div>
    </main>
  );
}
