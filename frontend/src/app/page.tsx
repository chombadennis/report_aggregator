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
    <main className="min-h-screen bg-slate-900 text-white p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          Construction Report Aggregator
        </h1>
        <p className="text-slate-400 mb-8 text-lg">Turn daily logs into professional summaries instantly.</p>

        {/* Mode Selector */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={() => { setMode('weekly'); setFiles([]); }}
            className={`px-6 py-3 rounded-xl font-semibold transition-all ${mode === 'weekly' ? 'bg-blue-600 shadow-lg shadow-blue-900' : 'bg-slate-800 hover:bg-slate-700'}`}
          >
            Weekly Report (7 Dailies)
          </button>
          <button
            onClick={() => { setMode('monthly'); setFiles([]); }}
            className={`px-6 py-3 rounded-xl font-semibold transition-all ${mode === 'monthly' ? 'bg-emerald-600 shadow-lg shadow-emerald-900' : 'bg-slate-800 hover:bg-slate-700'}`}
          >
            Monthly Report (4 Weeklies)
          </button>
        </div>

        {/* Manual Input Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 bg-slate-800/50 p-6 rounded-3xl border border-slate-700/50">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-400 mb-2">Report Title (e.g. WEEK 20 PROGRESS REPORT)</label>
            <input
              value={title} onChange={(e) => setTitle(e.target.value)}
              className={`w-full bg-slate-900 border ${isDuplicate ? 'border-yellow-500' : 'border-slate-700'} rounded-xl px-4 py-3 focus:border-blue-500 outline-none`}
              placeholder="Enter title..."
            />
            {isDuplicate && (
              <div className="mt-2 text-yellow-500 text-sm flex items-center gap-2 bg-yellow-500/10 p-2 rounded-lg border border-yellow-500/20">
                <span>⚠️</span>
                <span>A report for "<strong>{title}</strong>" already exists. Generating this will create a new version.</span>
              </div>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Dates / Reporting Period</label>
            <input
              value={dates} onChange={(e) => setDates(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:border-blue-500 outline-none"
              placeholder="e.g. 6TH – 12TH APRIL 2026"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Time Lapsed in Weeks</label>
            <input
              value={timeLapsed} onChange={(e) => setTimeLapsed(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:border-blue-500 outline-none"
              placeholder="e.g. 20 Weeks"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">% Contract Period Elapsed</label>
            <input
              value={pctPeriod} onChange={(e) => setPctPeriod(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:border-blue-500 outline-none"
              placeholder="e.g. 19.43%"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">% Work Done</label>
            <input
              value={pctWork} onChange={(e) => setPctWork(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 focus:border-blue-500 outline-none"
              placeholder="e.g. 7.29%"
            />
          </div>
        </div>

        {/* Upload Zone */}
        <div className="space-y-4">
          <div className="bg-slate-800 border-2 border-dashed border-slate-700 rounded-3xl p-10 text-center transition-all hover:border-blue-500 group">
            <input
              type="file" multiple
              onChange={(e) => handleFileChange(e.target.files)}
              className="hidden" id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="text-5xl mb-3 group-hover:scale-110 transition-transform">📄</div>
              <div className="text-lg font-medium mb-1">Click to add reports</div>
              <div className="text-slate-500">
                {isReady ? `All ${targetCount} files selected ✅` : `Selected: ${files.length} / ${targetCount}`}
              </div>
            </label>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="bg-slate-800/30 rounded-2xl p-4 border border-slate-700/50 space-y-2">
              {files.map((file, idx) => (
                <div key={idx} className="flex justify-between items-center text-sm bg-slate-900/50 p-2 rounded-lg">
                  <span className="truncate max-w-[80%]">📄 {file.name}</span>
                  <button onClick={() => removeFile(idx)} className="text-red-400 hover:text-red-300 px-2">✕</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Status and Errors */}
        <div className="mt-8 space-y-4">
          {status && (
            <div className="bg-blue-900/20 border border-blue-500/30 text-blue-300 p-4 rounded-2xl animate-pulse">
              {status}
            </div>
          )}
          {error && (
            <div className="bg-red-900/20 border border-red-500/50 text-red-400 p-4 rounded-2xl flex items-start gap-3">
              <span className="text-xl">⚠️</span>
              <div>
                <p className="font-bold">Error</p>
                <p className="text-sm opacity-90">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Action Area */}
        <div className="mt-8 flex flex-col items-center gap-4">
          {!isReady && !loading && (
            <div className="text-slate-500 font-medium">
              Waiting for {targetCount - files.length} more {mode === 'weekly' ? 'daily' : 'weekly'} reports...
            </div>
          )}
          
          <button
            onClick={handleUpload}
            disabled={loading || !isReady}
            className={`w-full py-5 rounded-2xl font-bold text-xl transition-all shadow-xl ${
              isReady && !loading 
                ? 'bg-gradient-to-r from-blue-600 to-emerald-600 hover:scale-[1.02] active:scale-95' 
                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
            }`}
          >
            {loading ? 'Executing Vision Scan...' : isReady ? '🚀 Execute & Generate' : 'Waiting for files...'}
          </button>
          
          {isReady && !loading && (
            <p className="text-slate-400 text-sm">All files accounted for. Click above to begin aggregation.</p>
          )}
        </div>
      </div>
    </main>
  );
}
