"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth, useUser, UserButton } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import {
  FileText,
  Upload,
  Calendar,
  Layers,
  ArrowRight,
  Loader2,
  FileSearch,
  CheckCircle2,
  ListTodo,
  TrendingUp,
  AlertTriangle,
  Plus,
  Trash2
} from 'lucide-react';
import NavigationPanel from '@/components/NavigationPanel';
import RevealWrapper from '@/components/animations/RevealWrapper';
import Footer from '@/components/Footer';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export default function Home() {
  const router = useRouter();
  const { isLoaded, userId, getToken, signOut } = useAuth();
  const { user } = useUser();

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
  const [visitors, setVisitors] = useState<{ name: string, org: string, date: string }[]>([{ name: '', org: '', date: '' }]);

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
  const [showEvmModal, setShowEvmModal] = useState(false);
  const [isEvmExpanded, setIsEvmExpanded] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error', message: string } | null>(null);
  const [pdfModalUrl, setPdfModalUrl] = useState<string | null>(null);

  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 5000);
  };

  // EVM States
  const [evmWeekNum, setEvmWeekNum] = useState('');
  const [evmStartDate, setEvmStartDate] = useState('');
  const [evmEndDate, setEvmEndDate] = useState('');
  const [existingEvmWeeks, setExistingEvmWeeks] = useState<string[]>([]);
  const [evmComponents, setEvmComponents] = useState([
    { name: 'Particular preliminaries', pctTotal: 0.33, pctContrib: '', pctDone: '' },
    { name: 'General preliminaries', pctTotal: 1.56, pctContrib: '', pctDone: '' },
    { name: 'Project provisions', pctTotal: 1.47, pctContrib: '', pctDone: '' },
    { name: 'Builders work – Block Type B', pctTotal: 29.58, pctContrib: '', pctDone: '' },
    { name: 'Builders work – Block Type C', pctTotal: 27.86, pctContrib: '', pctDone: '' },
    { name: 'Kindergarten', pctTotal: 0.63, pctContrib: '', pctDone: '' },
    { name: 'Commercial stalls', pctTotal: 0.00, pctContrib: '', pctDone: '' },
    { name: 'Guard house', pctTotal: 0.07, pctContrib: '', pctDone: '' },
    { name: 'Club house', pctTotal: 1.07, pctContrib: '', pctDone: '' },
    { name: 'Garbage receptacle', pctTotal: 0.19, pctContrib: '', pctDone: '' },
    { name: 'Power house', pctTotal: 0.07, pctContrib: '', pctDone: '' },
    { name: 'Boundary wall', pctTotal: 0.11, pctContrib: '', pctDone: '' },
    { name: 'Civil works - Roads', pctTotal: 1.23, pctContrib: '', pctDone: '' },
    { name: 'Sewer', pctTotal: 1.48, pctContrib: '', pctDone: '' },
    { name: 'Underground water tank', pctTotal: 0.75, pctContrib: '', pctDone: '' },
    { name: 'Mechanical installations', pctTotal: 4.43, pctContrib: '', pctDone: '' },
    { name: 'Electrical installation', pctTotal: 8.02, pctContrib: '', pctDone: '' },
    { name: 'Provisional sums & P.C. sums', pctTotal: 21.16, pctContrib: '', pctDone: '' },
    { name: 'Contingency', pctTotal: 2.00, pctContrib: '', pctDone: '' },
  ]);
  const [evmBlocks, setEvmBlocks] = useState([
    { name: 'B1', pctDone: '' },
    { name: 'B2', pctDone: '' },
    { name: 'B3', pctDone: '' },
    { name: 'B4', pctDone: '' },
    { name: 'C1', pctDone: '' },
    { name: 'C2', pctDone: '' },
    { name: 'C3', pctDone: '' },
    { name: 'C4', pctDone: '' },
    { name: 'C5', pctDone: '' },
  ]);
  const [evmLoading, setEvmLoading] = useState(false);
  const [evmStatus, setEvmStatus] = useState('');

  // OneDrive States
  const [oneDriveLinked, setOneDriveLinked] = useState(false);
  const [oneDriveFile, setOneDriveFile] = useState<string | null>(null);
  const [oneDriveFiles, setOneDriveFiles] = useState<any[]>([]);
  const [folderPath, setFolderPath] = useState<{id: string, name: string}[]>([]);
  const [showFilePicker, setShowFilePicker] = useState(false);
  const [oneDriveSyncing, setOneDriveSyncing] = useState(false);
  const [oneDriveLoading, setOneDriveLoading] = useState(false);
  const [isEvmSynced, setIsEvmSynced] = useState(false);

  useEffect(() => {
    const num = parseInt(evmWeekNum);
    if (!isNaN(num) && num >= 41) {
      const diffWeeks = num - 41;
      const anchorStart = new Date(2026, 7, 31); // Aug is 7 (0-indexed)
      const anchorEnd = new Date(2026, 8, 6);    // Sept is 8

      const newStart = new Date(anchorStart.getTime() + diffWeeks * 7 * 24 * 60 * 60 * 1000);
      const newEnd = new Date(anchorEnd.getTime() + diffWeeks * 7 * 24 * 60 * 60 * 1000);

      const formatDate = (d: Date) => d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

      setEvmStartDate(formatDate(newStart));
      setEvmEndDate(formatDate(newEnd));
    } else {
      setEvmStartDate('');
      setEvmEndDate('');
    }
  }, [evmWeekNum]);

  const evmWeekName = evmWeekNum ? `Week ${evmWeekNum}` : '';
  const isWeekDuplicate = existingEvmWeeks.includes(evmWeekName);
  const parsedWeekNum = parseInt(evmWeekNum);
  const isValidWeekNum = parsedWeekNum >= 41;

  const existingWeekNums = existingEvmWeeks.map(w => parseInt(w.replace('Week ', ''))).filter(n => !isNaN(n));
  const maxExistingWeek = existingWeekNums.length > 0 ? Math.max(...existingWeekNums) : 40;
  const expectedNextWeek = maxExistingWeek + 1;
  const isSequential = isNaN(parsedWeekNum) || parsedWeekNum === expectedNextWeek;

  let isDateReached = true;
  if (isValidWeekNum) {
    const diffWeeks = parsedWeekNum - 41;
    const anchorEnd = new Date(2026, 8, 6); // Sept 6, 2026
    const newEnd = new Date(anchorEnd.getTime() + diffWeeks * 7 * 24 * 60 * 60 * 1000);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    newEnd.setHours(0, 0, 0, 0);
    isDateReached = today.getTime() >= newEnd.getTime();
  }

  const isEvmReady = isValidWeekNum && !isWeekDuplicate && isSequential && evmStartDate !== '' &&
    evmComponents.every(c => c.pctContrib.trim() !== '' && c.pctDone.trim() !== '') &&
    evmBlocks.every(b => b.pctDone.trim() !== '');
    
  const hasData = evmComponents.some(c => c.pctContrib.trim() !== '' || c.pctDone.trim() !== '') || evmBlocks.some(b => b.pctDone.trim() !== '');

  // Register UI States
  const [activeRegisterTab, setActiveRegisterTab] = useState('contractor'); // contractor | client | general
  const [registerSearchQuery, setRegisterSearchQuery] = useState('');

  const [mounted, setMounted] = useState(false);
  const [isVerifyingAccess, setIsVerifyingAccess] = useState(() => {
    if (typeof window !== 'undefined') {
      return !sessionStorage.getItem('allowed_user');
    }
    return true;
  });

  // Client-side Role Checking
  const userEmail = user?.primaryEmailAddress?.emailAddress;
  const adminEmail = process.env.NEXT_PUBLIC_ADMIN_EMAIL || '';
  const isAdmin = userEmail && adminEmail && userEmail.toLowerCase() === adminEmail.toLowerCase();

  // Validate cached user matches current logged-in Clerk user
  useEffect(() => {
    if (isLoaded) {
      if (!userId) {
        if (typeof window !== 'undefined') {
          sessionStorage.removeItem('allowed_user');
        }
      } else {
        if (typeof window !== 'undefined') {
          const cached = sessionStorage.getItem('allowed_user');
          if (cached && cached !== userId) {
            sessionStorage.removeItem('allowed_user');
            setIsVerifyingAccess(true);
          }
        }
      }
    }
  }, [isLoaded, userId]);

  // Handle client-side mount
  useEffect(() => {
    setMounted(true);
  }, []);

  // Authentication Guard Redirect
  useEffect(() => {
    if (mounted && isLoaded && !userId) {
      router.replace('/login?redirect=/dashboard');
    }
  }, [mounted, isLoaded, userId, router]);

  // Fetch existing correspondence documents on mount
  useEffect(() => {
    if (isLoaded && userId) {
      fetchDocs();
    }
  }, [isLoaded, userId]);

  const fetchDocs = async () => {
    try {
      const token = await getToken();
      const resp = await fetch(`${BACKEND_URL}/api/project-documents`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (resp.status === 403) {
        // Clear cached allowed status on sign-out
        if (typeof window !== 'undefined') {
          sessionStorage.removeItem('allowed_user');
        }
        await signOut({ redirectUrl: '/?error=not-allowed' });
        return;
      }
      if (resp.ok) {
        const data = await resp.json();
        setUploadedDocs(data);
        if (typeof window !== 'undefined' && userId) {
          sessionStorage.setItem('allowed_user', userId);
        }
        setIsVerifyingAccess(false);
      } else {
        setIsVerifyingAccess(false);
      }
    } catch (e) {
      console.error("Failed to fetch documents list", e);
      setIsVerifyingAccess(false);
    }
  };

  useEffect(() => {
    const fetchEvmHistory = async () => {
      try {
        const token = await getToken();
        const res = await fetch(`${BACKEND_URL}/api/contracts-evm`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
          const data = await res.json();
          setExistingEvmWeeks(Object.keys(data));
        }
      } catch (e) { }
    };

    const checkOneDrive = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/onedrive/status`);
        if (res.ok) {
          const data = await res.json();
          setOneDriveLinked(data.is_linked);
          setOneDriveFile(data.selected_file);
        }
      } catch (e) { }
    };

    if (isLoaded && userId) {
      fetchEvmHistory();
      checkOneDrive();
    }
  }, [isLoaded, userId]);

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
      setDocStatus('📡 Connecting to Claims Analysis Engine...');
      const token = await getToken();
      const response = await fetch(`${BACKEND_URL}/api/upload-document`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Server failed to process document');
      }

      setDocStatus('Claims analysis complete!');
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

  const handleViewDocument = async (docId: string) => {
    try {
      const token = await getToken();
      const response = await fetch(`${BACKEND_URL}/api/project-documents/${docId}/view`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        setPdfModalUrl(url);
      } else {
        const errorData = await response.json().catch(() => ({}));
        showToast('error', errorData.detail || 'The linked document could not be found. It may have been moved or deleted.');

        if (response.status === 404) {
          // Update the UI immediately to revert back to the 'Link Local Path' button
          setUploadedDocs(prev => prev.map(d => d.id === docId ? { ...d, external_pdf_path: null } : d));
          // Tell the backend to persistently clear the broken link from the metadata
          fetch(`${BACKEND_URL}/api/project-documents/${docId}/unlink`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}` }
          }).catch(console.error);
        }
      }
    } catch (e) {
      console.error('View failed', e);
      showToast('error', 'Network error while attempting to view the document.');
    }
  };

  const handleLinkDocument = async (docId: string) => {
    try {
      const token = await getToken();
      // This will trigger a native Windows file picker dialog on your machine!
      const response = await fetch(`${BACKEND_URL}/api/project-documents/${docId}/pick-link`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'cancelled') return;
        showToast('success', 'Document linked successfully! You can now view the original PDF.');
        await fetchDocs();
      } else {
        const err = await response.json().catch(() => ({}));
        showToast('error', err.detail || 'Failed to link document.');
      }
    } catch (e) {
      console.error('Link failed', e);
      showToast('error', 'An error occurred while opening the file picker.');
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    try {
      const token = await getToken();
      const response = await fetch(`${BACKEND_URL}/api/project-documents/${docId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
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
          const token = await getToken();
          const resp = await fetch(`${BACKEND_URL}/api/check-duplicate?title=${encodeURIComponent(title)}`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
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
  }, [title, getToken]);

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

    // 1. Sanitization (XSS, SQLi, Length Limits)
    const sanitize = (input: string) => {
      if (!input) return "";
      return input.substring(0, 150).replace(/[<>;=]/g, "").trim();
    };

    const sTitle = sanitize(title);
    const sDates = sanitize(dates);
    const sTimeLapsed = sanitize(timeLapsed);
    const sPctPeriod = sanitize(pctPeriod);
    const sPctWork = sanitize(pctWork);

    // 2. Strict Input Format Validation
    if (sTitle.length < 5) {
      setError('Report Title must be at least 5 characters long.');
      return;
    }

    const months = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER', 'JAN', 'FEB', 'MAR', 'APR', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
    if (!months.some(m => sDates.toUpperCase().includes(m)) || !/\d{4}/.test(sDates)) {
      setError(`Reporting Period must include a valid month and a 4-digit year. Example: ${mode === 'weekly' ? '6TH - 12TH APRIL 2026' : 'APRIL 2026'}`);
      return;
    }

    if (!/^\d+(\.\d+)?\s*Weeks?$/i.test(sTimeLapsed)) {
      setError('Time Lapsed must be in the format: "X Weeks" (e.g. "20 Weeks").');
      return;
    }

    if (!/^\d+(\.\d+)?%?$/.test(sPctPeriod)) {
      setError('% Period Elapsed must be a valid number with an optional % sign (e.g. "19.43%").');
      return;
    }

    if (!/^\d+(\.\d+)?%?$/.test(sPctWork)) {
      setError('% Work Done must be a valid number with an optional % sign (e.g. "7.29%").');
      return;
    }

    setLoading(true);
    setError('');

    // Phase 1: Uploading
    setStatus('📦 Uploading reports to server...');

    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    formData.append('title', sTitle);
    formData.append('report_date', sDates);
    formData.append('time_elapsed', sTimeLapsed);
    formData.append('pct_period', sPctPeriod);
    formData.append('pct_work', sPctWork);

    if (mode === 'monthly') {
      formData.append('visitors_data', JSON.stringify(visitors));
    }

    try {
      const token = await getToken();
      const endpoint = mode === 'weekly' ? '/api/generate-weekly-stream' : '/api/generate-monthly-stream';
      setStatus('📡 Connecting to Vision Engine...');

      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
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
        window.location.href = `${BACKEND_URL}/api/download-session/${session_id}`;
        setTimeout(() => {
          setStatus(`✨ Success! ${mode === 'weekly' ? 'Weekly' : 'Monthly'} Report Ready.`);
          setTitle('');
          setDates('');
          setTimeLapsed('');
          setPctPeriod('');
          setPctWork('');
          setVisitors([{ name: '', org: '', date: '' }]);
          setFiles([]);
        }, 2000);
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

  const handleSaveEVM = async () => {
    if (!isEvmReady) return;
    setEvmLoading(true);
    setEvmStatus('Saving EVM Data...');
    try {
      const token = await getToken();
      const response = await fetch(`${BACKEND_URL}/api/contracts-evm`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          week_name: evmWeekName,
          data: {
            start_date: evmStartDate,
            end_date: evmEndDate,
            components: evmComponents,
            blocks: evmBlocks
          }
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save EVM data');
      }

      setEvmStatus('✅ EVM Data Saved successfully! It is now available in the Contracts & EVM page.');
      setExistingEvmWeeks(prev => [...prev, evmWeekName]);

      // Clear form
      setEvmWeekNum('');
      setEvmComponents(prev => prev.map(c => ({ ...c, pctContrib: '', pctDone: '' })));
      setEvmBlocks(prev => prev.map(b => ({ ...b, pctDone: '' })));

      setShowEvmModal(true);
    } catch (err: any) {
      setEvmStatus('❌ Error saving EVM Data');
      setShowEvmModal(true);
    } finally {
      setEvmLoading(false);
    }
  };

  const handleOneDriveLink = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/onedrive/auth-url`);
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (e) {
      showToast('error', 'Failed to get OneDrive auth URL');
    }
  };

  const openOneDriveFilePicker = async (folderId?: string, folderName?: string) => {
    try {
      setOneDriveLoading(true);
      const url = folderId ? `${BACKEND_URL}/api/onedrive/files?folder_id=${folderId}` : `${BACKEND_URL}/api/onedrive/files`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setOneDriveFiles(data);
        if (folderId && folderName) {
           setFolderPath(prev => {
             const idx = prev.findIndex(f => f.id === folderId);
             if (idx !== -1) return prev.slice(0, idx + 1);
             return [...prev, { id: folderId, name: folderName }];
           });
        } else if (!folderId) {
           setFolderPath([]);
        }
        setShowFilePicker(true);
      } else {
        showToast('error', 'Failed to fetch OneDrive files');
      }
    } catch (e) {
      showToast('error', 'Network error while fetching OneDrive files');
    } finally {
      setOneDriveLoading(false);
    }
  };

  const handleSelectOneDriveFile = async (fileId: string, fileName: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/onedrive/select-file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: fileId, file_name: fileName })
      });
      if (res.ok) {
        setOneDriveFile(fileName);
        setShowFilePicker(false);
        showToast('success', `Linked file: ${fileName}`);
      }
    } catch (e) {
      showToast('error', 'Failed to save file selection');
    }
  };

  const normalizeStr = (s: string) => (s || '').replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
  const formatVal = (v: any) => {
    if (v === null || v === undefined || v === '') return '';
    const num = parseFloat(v);
    if (isNaN(num)) return v;
    return (num * 100).toFixed(2);
  };

  const handleClearEvmData = () => {
    setEvmComponents(prev => prev.map(c => ({ ...c, pctContrib: '', pctDone: '' })));
    setEvmBlocks(prev => prev.map(b => ({ ...b, pctDone: '' })));
    setIsEvmSynced(false);
    setEvmStatus('');
    showToast('success', 'EVM Data cleared.');
  };

  const handleOneDriveSync = async () => {
    if (!evmWeekNum) {
      showToast('error', 'Please enter a Week Number first before syncing.');
      return;
    }
    if (hasData) {
      showToast('error', 'Please clear existing data before syncing.');
      return;
    }
    try {
      setOneDriveSyncing(true);
      setEvmStatus('Syncing from OneDrive...');
      const res = await fetch(`${BACKEND_URL}/api/onedrive/sync-evm`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to sync');
      }

      const data = await res.json();

      // Update components
      if (data.main_table && data.main_table.length > 0) {
        setEvmComponents(prev => prev.map(comp => {
          const nComp = normalizeStr(comp.name);
          const matched = data.main_table.find((t: any) => {
            const nT = normalizeStr(t.description);
            return nT.includes(nComp) || nComp.includes(nT);
          });
          if (matched) {
            return {
              ...comp,
              pctContrib: formatVal(matched.contribution_to_contract),
              pctDone: formatVal(matched.component_done)
            };
          }
          return comp;
        }));
      }

      // Update blocks
      if (data.blocks_table && data.blocks_table.length > 0) {
        setEvmBlocks(prev => prev.map(block => {
          const nBlock = normalizeStr(block.name);
          const matched = data.blocks_table.find((t: any) => {
            const nT = normalizeStr(t.block);
            return nT === nBlock || nT.includes(nBlock);
          });
          if (matched) {
            return {
              ...block,
              pctDone: formatVal(matched.done_per_block)
            };
          }
          return block;
        }));
      }

      setIsEvmSynced(true);
      setEvmStatus('✅ Sync complete! Please review the populated data before saving.');
      showToast('success', 'EVM Data synced successfully from OneDrive');
    } catch (e: any) {
      showToast('error', `Sync failed: ${e.message}`);
      setEvmStatus(`❌ Sync failed: ${e.message}`);
    } finally {
      setOneDriveSyncing(false);
    }
  };

  if (!mounted || !isLoaded || isVerifyingAccess) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white">
        <div className="w-16 h-16 border-4 border-vivid-tangerine-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest animate-pulse">Loading Security Context...</p>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-vanilla-custard-50 text-vivid-tangerine-955 font-sans">
      <NavigationPanel />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4 sm:pt-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold py-2 bg-gradient-to-r from-sunflower-gold-600 to-vivid-tangerine-600 bg-clip-text text-transparent font-serif leading-none">
              Vektra
            </h1>
            <p className="text-vivid-tangerine-800 text-sm font-medium mt-1">Field Reporting &amp; Analytics</p>
          </div>
        </div>

        {/* Mode Selector */}
        <RevealWrapper direction="up" delay={0.1}>
          <div className="flex gap-4 mb-8">
            <button
              onClick={() => { setMode('weekly'); setFiles([]); }}
              className={`px-6 py-2.5 rounded-none font-semibold transition-all shadow-md ${mode === 'weekly' ? 'bg-vivid-tangerine-600 text-white' : 'bg-white/80 backdrop-blur-sm text-vivid-tangerine-700 hover:bg-vanilla-custard-100'}`}
            >
              Weekly Report
            </button>
            <button
              onClick={() => { setMode('monthly'); setFiles([]); }}
              className={`px-6 py-2.5 rounded-none font-semibold transition-all shadow-md ${mode === 'monthly' ? 'bg-sunflower-gold-600 text-white' : 'bg-white/80 backdrop-blur-sm text-vivid-tangerine-700 hover:bg-vanilla-custard-100'}`}
            >
              Monthly Report
            </button>
          </div>
        </RevealWrapper>

        {/* Manual Input Grid */}
        <RevealWrapper direction="up" delay={0.2}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 sm:gap-6 mb-8 bg-white/90 backdrop-blur-sm p-4 sm:p-8 rounded-none shadow-xl shadow-vanilla-custard-200/40 border border-vanilla-custard-200">
            <div className="md:col-span-2">
              <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Report Title</label>
              <input
                value={title} onChange={(e) => setTitle(e.target.value)}
                disabled={!isAdmin}
                className={`w-full bg-vanilla-custard-50 border-2 ${isDuplicate ? 'border-sunflower-gold-400' : 'border-vanilla-custard-100'} rounded-none px-4 py-3 focus:border-vivid-tangerine-500 outline-none transition-colors text-vivid-tangerine-950 ${!isAdmin ? 'opacity-60 bg-slate-100/50 cursor-not-allowed' : ''}`}
                placeholder={mode === 'weekly' ? "e.g. WEEK 20 PROGRESS REPORT" : "e.g. MONTHLY REPORT (APRIL 2026)"}
              />
              {isDuplicate && (
                <div className="mt-2 text-vivid-tangerine-700 text-sm flex items-center gap-2 bg-vivid-tangerine-50 p-3 rounded-none border border-vivid-tangerine-200">
                  <span>⚡</span>
                  <span>A report for "<strong>{title}</strong>" already exists. This will create an update.</span>
                </div>
              )}
            </div>
            <div>
              <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Reporting Period</label>
              <input
                value={dates} onChange={(e) => setDates(e.target.value)}
                disabled={!isAdmin}
                className={`w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-none px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950 ${!isAdmin ? 'opacity-60 bg-slate-100/50 cursor-not-allowed' : ''}`}
                placeholder={mode === 'weekly' ? "e.g. 6TH – 12TH APRIL 2026" : "e.g. APRIL 2026"}
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Time Lapsed (Weeks)</label>
              <input
                value={timeLapsed} onChange={(e) => setTimeLapsed(e.target.value)}
                disabled={!isAdmin}
                className={`w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-none px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950 ${!isAdmin ? 'opacity-60 bg-slate-100/50 cursor-not-allowed' : ''}`}
                placeholder="e.g. 20 Weeks"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">% Period Elapsed</label>
              <input
                value={pctPeriod} onChange={(e) => setPctPeriod(e.target.value)}
                disabled={!isAdmin}
                className={`w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-none px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950 ${!isAdmin ? 'opacity-60 bg-slate-100/50 cursor-not-allowed' : ''}`}
                placeholder="e.g. 19.43%"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">% Work Done</label>
              <input
                value={pctWork} onChange={(e) => setPctWork(e.target.value)}
                disabled={!isAdmin}
                className={`w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-none px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950 ${!isAdmin ? 'opacity-60 bg-slate-100/50 cursor-not-allowed' : ''}`}
                placeholder="e.g. 7.29%"
              />
            </div>
          </div>
        </RevealWrapper>

        {/* Visitors Form */}
        {mode === 'monthly' && (
          <div className="mb-8 bg-white p-4 sm:p-8 rounded-none shadow-xl shadow-vanilla-custard-200/40 border border-vanilla-custard-200">
            <h3 className="text-lg font-bold text-vivid-tangerine-800 mb-4 uppercase tracking-widest">Visitors / Consultants on Site (Optional)</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b-2 border-vanilla-custard-200 text-xs text-vivid-tangerine-600 uppercase tracking-wider">
                    <th className="pb-3 pl-2">S/N</th>
                    <th className="pb-3">Name</th>
                    <th className="pb-3">Organisation</th>
                    <th className="pb-3">Date on Site</th>
                    <th className="pb-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {visitors.map((v, i) => (
                    <tr key={i} className="border-b border-vanilla-custard-100 last:border-0 hover:bg-vanilla-custard-50/50 transition-colors">
                      <td className="py-3 pl-2 text-sm font-medium text-slate-500">{i + 1}</td>
                      <td className="py-3 pr-2">
                        <input
                          value={v.name}
                          onChange={(e) => {
                            const newV = [...visitors];
                            newV[i].name = e.target.value;
                            setVisitors(newV);
                          }}
                          disabled={!isAdmin}
                          placeholder="Name"
                          className="w-full bg-transparent border-b border-dashed border-vanilla-custard-200 focus:border-vivid-tangerine-400 outline-none px-1 py-1 text-sm text-vivid-tangerine-950"
                        />
                      </td>
                      <td className="py-3 pr-2">
                        <input
                          value={v.org}
                          onChange={(e) => {
                            const newV = [...visitors];
                            newV[i].org = e.target.value;
                            setVisitors(newV);
                          }}
                          disabled={!isAdmin}
                          placeholder="Organisation"
                          className="w-full bg-transparent border-b border-dashed border-vanilla-custard-200 focus:border-vivid-tangerine-400 outline-none px-1 py-1 text-sm text-vivid-tangerine-950"
                        />
                      </td>
                      <td className="py-3 pr-2">
                        <input
                          type="date"
                          value={v.date}
                          onChange={(e) => {
                            const newV = [...visitors];
                            newV[i].date = e.target.value;
                            setVisitors(newV);
                          }}
                          disabled={!isAdmin}
                          className="w-full bg-transparent border-b border-dashed border-vanilla-custard-200 focus:border-vivid-tangerine-400 outline-none px-1 py-1 text-sm text-vivid-tangerine-950"
                        />
                      </td>
                      <td className="py-3 text-right">
                        <button
                          onClick={() => {
                            const newV = visitors.filter((_, idx) => idx !== i);
                            setVisitors(newV.length ? newV : [{ name: '', org: '', date: '' }]);
                          }}
                          disabled={!isAdmin}
                          className="text-vivid-tangerine-400 hover:text-red-500 transition-colors p-1"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {isAdmin && (
              <button
                onClick={() => setVisitors([...visitors, { name: '', org: '', date: '' }])}
                className="mt-4 flex items-center gap-2 text-xs font-bold text-sunflower-gold-600 hover:text-sunflower-gold-700 bg-sunflower-gold-50 px-3 py-2 rounded-none transition-colors border border-sunflower-gold-100"
              >
                <Plus className="w-4 h-4" /> Add Visitor
              </button>
            )}
          </div>
        )}

        {/* Upload Zone */}
        <div className="space-y-4">
          <div className={`bg-white border-2 border-dashed rounded-none p-4 sm:p-10 text-center transition-all shadow-lg ${isAdmin
            ? 'border-vanilla-custard-200 hover:border-vivid-tangerine-500 hover:bg-vanilla-custard-50 group'
            : 'border-slate-200 bg-slate-50/50 cursor-not-allowed'
            }`}>
            <input
              type="file" multiple accept=".pdf"
              onChange={(e) => isAdmin && handleFileChange(e.target.files)}
              className="hidden" id="file-upload"
              disabled={!isAdmin || loading}
            />
            {isAdmin ? (
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
            ) : (
              <div className="flex flex-col items-center justify-center py-4">
                <div className="text-5xl mb-3 grayscale opacity-60">🔒</div>
                <div className="text-base font-bold text-slate-400 mb-1">Upload Site Logs Locked</div>
                <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed mb-3">
                  This account is restricted to read-only viewer permissions. Log upload features are locked.
                </p>
                <div className="text-[10px] text-amber-600 uppercase tracking-widest font-bold bg-amber-50 border border-amber-100 px-3 py-1 rounded-full inline-block">
                  🔒 Requires Admin Account
                </div>
              </div>
            )}
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="bg-white rounded-none p-4 shadow-md border border-vanilla-custard-100 space-y-2">
              {files.map((file, idx) => (
                <div key={idx} className="flex justify-between items-center text-sm bg-vanilla-custard-50 p-3 rounded-none border border-vanilla-custard-100">
                  <span className="truncate max-w-[80%] font-medium text-vivid-tangerine-800">📄 {file.name}</span>
                  <button onClick={() => removeFile(idx)} disabled={loading} className={`p-1.5 rounded-none transition-colors ${loading ? 'opacity-50 cursor-not-allowed text-slate-400' : 'bg-vivid-tangerine-50 text-vivid-tangerine-600 hover:bg-vivid-tangerine-100'}`}>✕</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Status and Errors */}
        <div className="mt-8 space-y-4">
          {status && (
            <div className="bg-sunflower-gold-50 border border-sunflower-gold-200 text-vivid-tangerine-900 p-4 rounded-none animate-pulse font-semibold text-center shadow-sm text-sm">
              {status}
            </div>
          )}
          {error && (
            <div className="bg-vivid-tangerine-50 border border-vivid-tangerine-200 text-vivid-tangerine-900 p-4 rounded-none flex items-start gap-4 shadow-md text-sm">
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
          {!isReady && !loading && isAdmin && (
            <div className="text-vivid-tangerine-400 font-bold bg-vanilla-custard-100/50 px-4 py-2 rounded-full text-xs uppercase tracking-wider">
              {mode === 'weekly' ? `Missing ${7 - files.length} more reports...` : `Upload 4-6 weekly reports`}
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={loading || !isReady || !isAdmin}
            className={`w-full max-w-md py-4 rounded-none font-bold text-lg transition-all shadow-xl ${!isAdmin
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
              : isReady && !loading
                ? 'bg-gradient-to-r from-sunflower-gold-500 to-vivid-tangerine-600 text-white hover:scale-[1.01] active:scale-95'
                : 'bg-vanilla-custard-200 text-vanilla-custard-400 cursor-not-allowed'
              }`}
          >
            {!isAdmin
              ? '🔒 Execution & Generation Locked'
              : loading
                ? 'Processing Vision Data...'
                : isReady
                  ? '🚀 Execute & Generate'
                  : 'Waiting for Files'}
          </button>

          {isReady && !loading && isAdmin && (
            <p className="text-vivid-tangerine-400 text-xs font-semibold uppercase tracking-widest">Document Integrity Verified</p>
          )}
        </div>

        {/* EVM Section Separator */}
        <div className="border-t-2 border-vanilla-custard-200/60 my-16" />

        {/* EVM Section */}
        <div className="mb-8 text-left flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-deep-space-blue-600 to-vivid-tangerine-600 bg-clip-text text-transparent font-serif">
              Earned Value Management Data Weekly
            </h2>
            <p className="text-vivid-tangerine-800 text-sm font-medium mt-1">
              Input weekly EVM data.
            </p>
          </div>
          {isAdmin && (
            <button
              onClick={() => setIsEvmExpanded(!isEvmExpanded)}
              className="text-xs font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors bg-white border border-vanilla-custard-200 px-4 py-2 rounded-none shadow-sm"
            >
              {isEvmExpanded ? 'Collapse Form' : 'Expand Form'}
            </button>
          )}
        </div>

        {isAdmin && isEvmExpanded && (
          <div className="bg-white p-4 sm:p-8 rounded-none shadow-xl shadow-vanilla-custard-200/40 border border-vanilla-custard-200 mb-10 text-left max-h-[600px] overflow-y-auto custom-scrollbar relative">
            {/* OneDrive Integration Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center bg-vanilla-custard-50 p-4 border border-vanilla-custard-200 mb-6 gap-4">
              <div>
                <h4 className="font-bold text-sm text-vivid-tangerine-900">OneDrive Integration</h4>
                <p className="text-xs text-vivid-tangerine-700">Sync EVM Data automatically from Excel</p>
                {oneDriveLinked && (
                  <p className="text-[10px] font-bold text-green-600 mt-1 uppercase tracking-widest">
                    ✓ Linked {oneDriveFile ? `- ${oneDriveFile}` : ''}
                  </p>
                )}
              </div>
              <div className="flex flex-col items-end gap-2">
                <div className="flex gap-2">
                  {!oneDriveLinked ? (
                    <button onClick={handleOneDriveLink} className="px-4 py-2 bg-blue-600 text-white text-xs font-bold uppercase tracking-wider hover:bg-blue-700 transition-colors shadow-sm">
                      Link OneDrive
                    </button>
                  ) : (
                    <>
                      <button onClick={() => openOneDriveFilePicker()} disabled={oneDriveLoading} className="px-4 py-2 bg-white border border-vanilla-custard-300 text-vivid-tangerine-700 text-xs font-bold uppercase tracking-wider hover:bg-vanilla-custard-100 transition-colors shadow-sm">
                        {oneDriveLoading ? 'Loading...' : oneDriveFile ? 'Change File' : 'Select File'}
                      </button>
                      <button onClick={handleOneDriveSync} disabled={!oneDriveFile || oneDriveSyncing || !evmWeekNum || !isValidWeekNum || isWeekDuplicate || !isSequential || !isDateReached} className={`px-4 py-2 text-xs font-bold uppercase tracking-wider transition-colors shadow-sm ${(!oneDriveFile || oneDriveSyncing || !evmWeekNum || !isValidWeekNum || isWeekDuplicate || !isSequential || !isDateReached) ? 'bg-vanilla-custard-200 text-vanilla-custard-500 cursor-not-allowed' : 'bg-green-600 text-white hover:bg-green-700'}`}>
                        {oneDriveSyncing ? 'Syncing...' : 'Sync Data'}
                      </button>
                    </>
                  )}
                </div>
                {oneDriveLinked && (!oneDriveFile || !evmWeekNum || !isValidWeekNum || isWeekDuplicate || !isSequential || !isDateReached) && (
                  <div className="text-[10px] text-vivid-tangerine-600 font-bold bg-vivid-tangerine-50 px-3 py-1.5 rounded-sm border border-vivid-tangerine-200 shadow-sm animate-in fade-in text-right max-w-sm">
                    {!oneDriveFile ? 'Please select an Excel file to sync from.' :
                     !evmWeekNum ? 'Please enter a Week Number in the form.' :
                     !isValidWeekNum ? 'Week Number must be 41 or greater.' :
                     isWeekDuplicate ? 'Data for this week has already been synced and saved.' :
                     !isSequential ? `Week must be sequential (Expected: Week ${expectedNextWeek}).` :
                     !isDateReached ? `Cannot sync yet. Week ${evmWeekNum} ends on ${evmEndDate}. Available from this date onwards.` : ''}
                  </div>
                )}
              </div>
            </div>

            {/* File Picker Modal */}
            {showFilePicker && (
              <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center p-4 z-[100] animate-in fade-in">
                <div className="bg-slate-900 rounded-2xl max-w-2xl w-full p-6 md:p-8 shadow-2xl border border-slate-700/50 max-h-[90vh] flex flex-col relative overflow-hidden">
                  <div className="flex justify-between items-center mb-6">
                    <div>
                      <h2 className="text-xl font-bold text-white mb-1 tracking-tight">Select OneDrive File</h2>
                      <p className="text-xs text-slate-400 font-medium">Choose the Excel file containing your EVM data</p>
                    </div>
                    <button onClick={() => setShowFilePicker(false)} className="text-slate-400 hover:text-white transition-colors bg-slate-800/50 hover:bg-slate-700 p-2 rounded-xl">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>

                  <div className="mb-4 bg-indigo-900/20 border border-indigo-500/30 rounded-lg p-2.5 text-xs text-indigo-200 leading-relaxed">
                    <span className="font-bold">OneDrive Format:</span> Microsoft OneDrive integration only supports native Excel Workbooks (<code className="font-mono bg-indigo-950 px-1 rounded text-[11px] text-indigo-300">.xlsx</code>). CSV files are not supported and are hidden from this list.
                  </div>

                  <div className="mb-4 text-[11px] flex flex-wrap items-center gap-1.5 px-2">
                    <span className="font-semibold text-slate-500">Path:</span>
                    <span
                      onClick={() => openOneDriveFilePicker()}
                      className="font-semibold text-slate-300 cursor-pointer hover:text-indigo-400 transition-colors"
                    >
                      Home
                    </span>
                    {folderPath.map((folder) => (
                      <React.Fragment key={folder.id}>
                        <span className="text-slate-600">/</span>
                        <span
                          onClick={() => openOneDriveFilePicker(folder.id, folder.name)}
                          className="font-semibold text-slate-300 cursor-pointer hover:text-indigo-400 transition-colors"
                        >
                          {folder.name}
                        </span>
                      </React.Fragment>
                    ))}
                  </div>

                  <div className="w-full h-64 border border-slate-700/50 rounded-xl overflow-y-auto divide-y divide-slate-700/50 bg-slate-900/50 custom-scrollbar relative">
                    {oneDriveLoading && (
                      <div className="absolute inset-0 bg-slate-900/50 flex flex-col items-center justify-center text-slate-400 space-y-2 z-10 backdrop-blur-sm">
                        <svg className="w-6 h-6 animate-spin text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                        <span className="text-xs font-medium">Scanning folder...</span>
                      </div>
                    )}
                    
                    {!oneDriveLoading && oneDriveFiles.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center text-xs text-slate-500 p-6 text-center space-y-2">
                        <span className="font-semibold text-slate-400">No supported files found in this folder.</span>
                      </div>
                    ) : (
                      oneDriveFiles.map((file) => {
                        const isFolder = file.type === 'folder';
                        return (
                          <div
                            key={file.id}
                            onClick={() => isFolder ? openOneDriveFilePicker(file.id, file.name) : handleSelectOneDriveFile(file.id, file.name)}
                            className="flex items-center justify-between p-3 transition-all duration-150 hover:bg-slate-800/50 text-slate-300 font-medium cursor-pointer"
                          >
                            <div className="flex-1 flex items-center space-x-3 min-w-0">
                              {isFolder ? (
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-amber-500 fill-amber-100 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                              ) : (
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 flex-shrink-0 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="8" y1="13" x2="16" y2="13"></line><line x1="8" y1="17" x2="16" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                              )}
                              <span className="text-xs truncate">{file.name}</span>
                            </div>
                            {isFolder && (
                              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-slate-500 hover:text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div>
                <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Week Number</label>
                <div className="relative">
                  <span className="absolute left-4 top-3 text-vivid-tangerine-500 font-bold">Week</span>
                  <input
                    type="number"
                    min="41"
                    value={evmWeekNum}
                    onChange={(e) => setEvmWeekNum(e.target.value)}
                    className={`w-full bg-vanilla-custard-50 border-2 ${isWeekDuplicate ? 'border-red-400' : 'border-vanilla-custard-100'} rounded-none pl-16 pr-4 py-3 focus:border-vivid-tangerine-500 outline-none transition-colors text-vivid-tangerine-950`}
                    placeholder="41"
                  />
                </div>
                {isWeekDuplicate && (
                  <p className="text-[10px] text-red-500 font-bold mt-1 uppercase tracking-wider">⚠️ Duplicate: {evmWeekName} is already saved.</p>
                )}
                {!isValidWeekNum && evmWeekNum && (
                  <p className="text-[10px] text-amber-500 font-bold mt-1 uppercase tracking-wider">⚠️ Minimum week is 41.</p>
                )}
                {isValidWeekNum && !isWeekDuplicate && !isSequential && evmWeekNum && (
                  <p className="text-[10px] text-amber-600 font-bold mt-1 uppercase tracking-wider">
                    ⚠️ Sequential Entry Required: Please enter Week {expectedNextWeek} first.
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2 uppercase tracking-widest">Calculated Start Date</label>
                <input
                  value={evmStartDate}
                  disabled
                  className="w-full bg-slate-100/50 border-2 border-slate-100 rounded-none px-4 py-3 cursor-not-allowed text-slate-500 font-medium"
                  placeholder="e.g. 31 Aug 2026"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 mb-2 uppercase tracking-widest">Calculated End Date</label>
                <input
                  value={evmEndDate}
                  disabled
                  className="w-full bg-slate-100/50 border-2 border-slate-100 rounded-none px-4 py-3 cursor-not-allowed text-slate-500 font-medium"
                  placeholder="e.g. 6 Sep 2026"
                />
              </div>
            </div>

            <div className="mb-8 overflow-x-auto">
              <h3 className="text-sm font-bold text-vivid-tangerine-800 mb-4 uppercase tracking-widest">Component Progress</h3>
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b-2 border-vanilla-custard-200 text-xs text-vivid-tangerine-600 uppercase tracking-wider">
                    <th className="pb-3 pl-2">Component</th>
                    <th className="pb-3">% of Component to Total</th>
                    <th className="pb-3">% Contribution of Work Done to Contract Value</th>
                    <th className="pb-3">% of Component Done to Respective Value</th>
                  </tr>
                </thead>
                <tbody>
                  {evmComponents.map((comp, idx) => (
                    <tr key={idx} className="border-b border-vanilla-custard-100 hover:bg-vanilla-custard-50 transition-colors">
                      <td className="py-2 pl-2 font-medium text-slate-700">{comp.name}</td>
                      <td className="py-2 text-slate-500 font-semibold">{comp.pctTotal}%</td>
                      <td className="py-2 pr-2">
                        <input
                          value={comp.pctContrib}
                          disabled={oneDriveSyncing}
                          onChange={(e) => {
                            const newArr = [...evmComponents];
                            newArr[idx].pctContrib = e.target.value.replace(/%/g, '');
                            setEvmComponents(newArr);
                          }}
                          placeholder="e.g. 0.00"
                          className={`w-24 bg-transparent border-b border-dashed border-vanilla-custard-200 focus:border-vivid-tangerine-400 outline-none px-1 py-1 text-vivid-tangerine-950 ${oneDriveSyncing ? 'opacity-70 cursor-not-allowed' : ''}`}
                        />
                      </td>
                      <td className="py-2 pr-2">
                        <input
                          value={comp.pctDone}
                          disabled={oneDriveSyncing}
                          onChange={(e) => {
                            const newArr = [...evmComponents];
                            newArr[idx].pctDone = e.target.value.replace(/%/g, '');
                            setEvmComponents(newArr);
                          }}
                          placeholder="e.g. 0.00"
                          className={`w-24 bg-transparent border-b border-dashed border-vanilla-custard-200 focus:border-vivid-tangerine-400 outline-none px-1 py-1 text-vivid-tangerine-950 ${oneDriveSyncing ? 'opacity-70 cursor-not-allowed' : ''}`}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mb-8 overflow-x-auto">
              <h3 className="text-sm font-bold text-vivid-tangerine-800 mb-4 uppercase tracking-widest">Block Progress</h3>
              <table className="w-full md:w-1/2 text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b-2 border-vanilla-custard-200 text-xs text-vivid-tangerine-600 uppercase tracking-wider">
                    <th className="pb-3 pl-2">Block</th>
                    <th className="pb-3">% Done Per Block</th>
                  </tr>
                </thead>
                <tbody>
                  {evmBlocks.map((blk, idx) => (
                    <tr key={idx} className="border-b border-vanilla-custard-100 hover:bg-vanilla-custard-50 transition-colors">
                      <td className="py-2 pl-2 font-medium text-slate-700">{blk.name}</td>
                      <td className="py-2 pr-2">
                        <input
                          value={blk.pctDone}
                          disabled={oneDriveSyncing}
                          onChange={(e) => {
                            const newArr = [...evmBlocks];
                            newArr[idx].pctDone = e.target.value.replace(/%/g, '');
                            setEvmBlocks(newArr);
                          }}
                          placeholder="e.g. 0.00"
                          className={`w-24 bg-transparent border-b border-dashed border-vanilla-custard-200 focus:border-vivid-tangerine-400 outline-none px-1 py-1 text-vivid-tangerine-950 ${oneDriveSyncing ? 'opacity-70 cursor-not-allowed' : ''}`}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col gap-3">
              {!isEvmReady && !evmLoading && (
                <p className="text-[10px] text-amber-600 uppercase tracking-widest font-bold">⚠️ Enter a valid new week (&gt;=41) and fill all percentage fields to save.</p>
              )}
              <div className="flex gap-4">
                <button
                  onClick={handleSaveEVM}
                  disabled={evmLoading || !isEvmReady}
                  className={`self-start px-8 py-3 rounded-none font-bold transition-all shadow-md ${(!isEvmReady || evmLoading) ? 'bg-vanilla-custard-300 text-vanilla-custard-500 cursor-not-allowed' : 'bg-vivid-tangerine-600 text-white hover:bg-vivid-tangerine-700 active:scale-95'}`}
                >
                  {evmLoading ? 'Saving...' : 'Save EVM Data'}
                </button>
                {hasData && (
                  <button
                    onClick={handleClearEvmData}
                    disabled={evmLoading}
                    className="self-start px-8 py-3 bg-white border border-red-200 text-red-600 font-bold hover:bg-red-50 hover:text-red-700 transition-colors shadow-sm rounded-none uppercase tracking-widest text-xs flex items-center h-[48px]"
                  >
                    Clear Data
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
        {!isAdmin && (
          <div className="flex flex-col items-center justify-center py-10 bg-white rounded-none shadow-md border border-vanilla-custard-100 mb-10">
            <div className="text-5xl mb-3 grayscale opacity-60">🔒</div>
            <div className="text-base font-bold text-slate-400 mb-1">EVM Data Entry Locked</div>
            <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed text-center">
              This account is restricted to read-only viewer permissions. Data entry features are locked.
            </p>
          </div>
        )}

        {/* Correspondence Separator */}
        <div className="border-t-2 border-vanilla-custard-200/60 my-16" />

        {/* Correspondence Section */}
        <div className="mb-8 text-left">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-deep-space-blue-600 to-vivid-tangerine-600 bg-clip-text text-transparent font-serif">
            Project Correspondence & Claims Ingestion
          </h2>
          <p className="text-vivid-tangerine-800 text-sm font-medium mt-1">
            Upload contractor letters, client instructions, EOT requests, or meeting minutes. The system will extract key claims and EOT risks to enrich your final reports.
          </p>
        </div>

        {/* Correspondence Ingestion Form Card */}
        {isAdmin ? (
          <div className="bg-white p-4 sm:p-8 rounded-none shadow-xl shadow-vanilla-custard-200/40 border border-vanilla-custard-200 mb-10 text-left">
            {/* Doc Category Selector */}
            <div className="flex gap-2 mb-6 p-1 bg-vanilla-custard-50 rounded-none border border-vanilla-custard-200">
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
                  className={`flex-1 py-2 rounded-none font-bold text-xs uppercase tracking-wider transition-all ${docCategory === cat
                    ? 'bg-vivid-tangerine-600 text-white shadow-md'
                    : 'text-vivid-tangerine-700 hover:bg-vanilla-custard-100'
                    }`}
                >
                  {cat === 'contractor' ? '👷 Contractor' : cat === 'client' ? '🏢 Client / PM' : '📚 General / Info'}
                </button>
              ))}
            </div>

            {/* Form Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 sm:gap-6">
              <div className="md:col-span-2">
                <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Document Title / Subject</label>
                <input
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  className="w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-none px-4 py-3 focus:border-vivid-tangerine-500 outline-none transition-colors text-vivid-tangerine-950"
                  placeholder="e.g. Request for EOT due to rain delays"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Sender (From)</label>
                <input
                  value={docCategory === 'contractor' ? 'Contractor' : docCategory === 'client' ? 'Client / Project Manager' : docSender}
                  onChange={(e) => setDocSender(e.target.value)}
                  disabled={docCategory !== 'general'}
                  className={`w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-none px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950 ${docCategory !== 'general' ? 'opacity-60 cursor-not-allowed bg-vanilla-custard-100/50' : ''}`}
                  placeholder="Sender Name"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Recipient (To)</label>
                <input
                  value={docRecipient}
                  onChange={(e) => setDocRecipient(e.target.value)}
                  className="w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-none px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950"
                  placeholder={docCategory === 'contractor' ? "Client / Project Manager" : docCategory === 'client' ? "Contractor" : "Recipient Name"}
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Date Sent / Received</label>
                <input
                  type="date"
                  value={docDateSent}
                  onChange={(e) => setDocDateSent(e.target.value)}
                  className="w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-none px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Date Uploaded</label>
                <input
                  value={new Date().toLocaleDateString()}
                  disabled
                  className="w-full bg-vanilla-custard-100/50 opacity-60 border-2 border-vanilla-custard-100 rounded-none px-4 py-3 cursor-not-allowed text-vivid-tangerine-950"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-bold text-vivid-tangerine-800 mb-2 uppercase tracking-widest">Brief Summary (Optional)</label>
                <textarea
                  value={docSummary}
                  onChange={(e) => setDocSummary(e.target.value)}
                  rows={3}
                  className="w-full bg-vanilla-custard-50 border-2 border-vanilla-custard-100 rounded-none px-4 py-3 focus:border-vivid-tangerine-500 outline-none text-vivid-tangerine-950 text-sm resize-none"
                  placeholder="Leave blank to let the system scan the PDF and automatically summarize and analyze all key requests and EOT impacts."
                />
              </div>
            </div>

            {/* File Dropzone */}
            <div className="mt-6">
              <div className="bg-vanilla-custard-50/50 border-2 border-dashed border-vanilla-custard-200 rounded-none p-4 sm:p-6 text-center hover:border-vivid-tangerine-500 hover:bg-vanilla-custard-50 transition-all cursor-pointer relative">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => handleDocFileChange(e.target.files)}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  disabled={docLoading || loading}
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
              <div className="mt-6 bg-sunflower-gold-50 border border-sunflower-gold-200 text-vivid-tangerine-900 p-4 rounded-none animate-pulse font-semibold text-center text-xs">
                {docStatus}
              </div>
            )}
            {docError && (
              <div className="mt-6 bg-vivid-tangerine-50 border border-vivid-tangerine-200 text-vivid-tangerine-900 p-4 rounded-none text-xs font-bold">
                ⚠️ {docError}
              </div>
            )}

            {/* Action Button */}
            <button
              type="button"
              onClick={handleUploadDocument}
              disabled={docLoading || !docFile}
              className={`w-full mt-6 py-4 rounded-none font-bold text-sm uppercase tracking-widest transition-all shadow-md ${docFile && !docLoading
                ? 'bg-gradient-to-r from-deep-space-blue-600 to-vivid-tangerine-600 hover:scale-[1.01] active:scale-95 text-white'
                : 'bg-vanilla-custard-200 text-vanilla-custard-400 cursor-not-allowed'
                }`}
            >
              {docLoading ? '🔄 Analysis Active...' : '🚀 Ingest Correspondence & Analyse'}
            </button>
          </div>
        ) : (
          <div className="bg-slate-900/10 border-2 border-dashed border-slate-200 rounded-none p-10 text-center shadow-lg mb-10">
            <div className="text-4xl mb-4">🔒</div>
            <h3 className="text-lg font-bold text-slate-800 font-serif mb-2">Read-Only Access: Correspondence Ingestion Locked</h3>
            <p className="text-xs text-slate-500 max-w-lg mx-auto leading-relaxed mb-4 font-medium">
              Uploads of contractor letters, client instructions, or site reports for Claims scanning are locked for this account. Only designated Administrators can ingest new correspondence.
            </p>
            <div className="text-[10px] text-amber-600 font-bold uppercase tracking-widest bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-full inline-block shadow-sm">
              🔒 Requires Admin Account
            </div>
          </div>
        )}

        {/* Correspondence Register */}
        <div className="space-y-4 mb-16 text-left">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
            <h3 className="text-sm font-bold text-vivid-tangerine-800 uppercase tracking-widest">Ingested Correspondence Register</h3>
            {uploadedDocs.length > 0 && (
              <div className="relative w-full sm:w-64">
                <input
                  type="text"
                  value={registerSearchQuery}
                  onChange={(e) => setRegisterSearchQuery(e.target.value)}
                  placeholder="Search documents..."
                  className="w-full bg-white border border-vanilla-custard-200 rounded-none pl-4 pr-10 py-2 text-sm text-vivid-tangerine-950 focus:border-vivid-tangerine-500 outline-none transition-colors"
                />
                <span className="absolute right-3 top-2.5 opacity-40">🔍</span>
              </div>
            )}
          </div>

          {uploadedDocs.length > 0 ? (
            <>
              {/* Category Tabs */}
              <div className="flex gap-2 mb-4 p-1 bg-vanilla-custard-50 rounded-none border border-vanilla-custard-200 w-full sm:w-fit">
                {(['contractor', 'client', 'general'] as const).map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setActiveRegisterTab(cat)}
                    className={`px-4 py-2 rounded-none font-bold text-xs uppercase tracking-wider transition-all ${activeRegisterTab === cat
                        ? 'bg-white text-vivid-tangerine-700 shadow-sm border border-vanilla-custard-200'
                        : 'text-vivid-tangerine-600/70 hover:bg-vanilla-custard-100 hover:text-vivid-tangerine-800'
                      }`}
                  >
                    {cat === 'contractor' ? '👷 Contractor' : cat === 'client' ? '🏢 Client / PM' : '📚 General'}
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-1 gap-1 sm:gap-4 max-h-[600px] overflow-y-auto custom-scrollbar pr-1 sm:pr-2">
                {[...uploadedDocs]
                  .filter(doc => doc.category === activeRegisterTab)
                  .filter(doc => {
                    if (!registerSearchQuery) return true;
                    const q = registerSearchQuery.toLowerCase();
                    const searchTitle = (doc.title || doc.ai_analysis?.title || "").toLowerCase();
                    const sender = (doc.sender || "").toLowerCase();
                    return searchTitle.includes(q) || sender.includes(q);
                  })
                  .sort((a, b) => new Date(b.date_sent || b.date_uploaded).getTime() - new Date(a.date_sent || a.date_uploaded).getTime())
                  .map((doc) => (
                    <div key={doc.id} className="bg-white p-4 sm:p-6 rounded-none border border-vanilla-custard-100 shadow-md flex flex-col md:flex-row justify-between gap-2 sm:gap-4 transition-all hover:shadow-lg text-left">
                      <div className="flex-1">
                        <div className="flex items-center gap-1 sm:gap-2 mb-2 flex-wrap">
                          <span className={`text-[9px] font-black uppercase px-2 py-0.5 rounded-full border ${doc.category === 'contractor'
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

                        <h4 className="font-bold text-vivid-tangerine-955 text-sm sm:text-base mb-1 break-words select-text">
                          {doc.title || doc.ai_analysis?.title || "Untitled Document"}
                        </h4>
                        <p className="text-[10px] sm:text-xs text-vivid-tangerine-600 font-bold uppercase tracking-wider mb-2 break-words select-text">
                          From: <span className="text-vivid-tangerine-900 select-text">{doc.sender}</span> &rarr; To: <span className="text-vivid-tangerine-900 select-text">{doc.recipient}</span>
                        </p>
                        <div className="mt-3 bg-vanilla-custard-50/50 p-3.5 rounded-none border border-vanilla-custard-100 shadow-inner">
                          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 mb-2 pb-2 border-b border-vanilla-custard-200/60">
                            <span className="text-xs font-bold text-slate-800 font-serif select-text break-words">
                              Document: {doc.title || doc.ai_analysis?.title || "Untitled Document"}
                            </span>
                            <span className="text-[8px] font-black uppercase text-vivid-tangerine-600 tracking-widest whitespace-nowrap">
                              Summary Preview
                            </span>
                          </div>
                          <p className="text-xs text-vivid-tangerine-900 leading-relaxed font-medium line-clamp-3 md:line-clamp-4">
                            {doc.summary || "No summary preview available."}
                          </p>
                        </div>
                      </div>

                      <div className="flex md:flex-col justify-end items-stretch gap-2 min-w-[150px]">
                        {!doc.external_pdf_path ? (
                          <button
                            onClick={() => handleLinkDocument(doc.id)}
                            className="px-4 py-2 bg-vanilla-custard-50 border border-vanilla-custard-200 rounded-none font-bold text-xs text-vivid-tangerine-700 hover:bg-vanilla-custard-100 hover:text-vivid-tangerine-900 transition-colors text-center w-full"
                          >
                            🔗 Link Local Path
                          </button>
                        ) : (
                          <button
                            onClick={() => handleViewDocument(doc.id)}
                            className="px-4 py-2 bg-vanilla-custard-50 border border-vanilla-custard-200 rounded-none font-bold text-xs text-vivid-tangerine-700 hover:bg-vanilla-custard-100 hover:text-vivid-tangerine-900 transition-colors text-center w-full"
                          >
                            📄 View Linked PDF
                          </button>
                        )}
                        <button
                          onClick={() => setActiveDocDetail(doc)}
                          className="px-4 py-2 bg-vanilla-custard-50 border border-vanilla-custard-200 rounded-none font-bold text-xs text-vivid-tangerine-700 hover:bg-vanilla-custard-100 hover:text-vivid-tangerine-900 transition-colors text-center w-full"
                        >
                          🔍 View Claims Analysis
                        </button>
                        {isAdmin && (
                          <button
                            onClick={() => setDocToDelete(doc)}
                            className="px-4 py-2 bg-vivid-tangerine-50 border border-vivid-tangerine-200 rounded-none font-bold text-xs text-vivid-tangerine-600 hover:bg-vivid-tangerine-100 hover:text-vivid-tangerine-750 transition-colors text-center w-full"
                          >
                            🗑️ Delete Document
                          </button>
                        )}
                      </div>
                    </div>
                  ))}

                {[...uploadedDocs].filter(doc => doc.category === activeRegisterTab).length === 0 && (
                  <div className="bg-vanilla-custard-50/50 border border-dashed border-vanilla-custard-200 rounded-none p-8 text-center text-vivid-tangerine-800 text-sm font-medium">
                    No documents found in this category.
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="bg-slate-50 border border-dashed border-slate-200 rounded-none p-8 text-center text-slate-500 text-sm font-medium">
              No correspondence uploaded yet.
            </div>
          )}
        </div>

        {/* AI Claims Overlay Modal */}
        {activeDocDetail && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-md">
            <div className="bg-white rounded-none max-w-2xl w-full max-h-[85vh] overflow-y-auto border border-vanilla-custard-200 shadow-2xl relative flex flex-col text-left">

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
                  className="p-1.5 bg-vanilla-custard-50 hover:bg-vanilla-custard-100 rounded-none border border-vanilla-custard-200 text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors text-lg font-black leading-none"
                >
                  ✕
                </button>
              </div>

              {/* Content */}
              <div className="p-6 space-y-6 flex-1 text-sm text-vivid-tangerine-900 leading-relaxed overflow-y-auto">

                <div>
                  <h4 className="font-bold text-vivid-tangerine-950 uppercase tracking-widest text-xs mb-2">📜 Document Summary</h4>
                  <div className="bg-vanilla-custard-50 p-4 rounded-none border border-vanilla-custard-100 font-medium">
                    {activeDocDetail.summary}
                  </div>
                </div>

                <div>
                  <h4 className="font-bold text-vivid-tangerine-950 uppercase tracking-widest text-xs mb-2">🧠 Detailed Analysis</h4>
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
                        <li key={i} className="flex gap-2 items-start bg-sunflower-gold-50/40 p-2.5 rounded-none border border-sunflower-gold-100/60 font-medium text-vivid-tangerine-900">
                          <span className="text-sunflower-gold-600 font-black">✔</span>
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div>
                  <h4 className="font-bold text-vivid-tangerine-950 uppercase tracking-widest text-xs mb-2">⚖️ Contractual Implications & Risks</h4>
                  <div className="bg-vivid-tangerine-50/50 p-4 rounded-none border border-vivid-tangerine-100/60 font-medium text-vivid-tangerine-900">
                    {activeDocDetail.ai_analysis?.contractual_implications || "No specific implications noted."}
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="p-4 bg-vanilla-custard-50 border-t border-vanilla-custard-150 flex justify-end">
                <button
                  onClick={() => setActiveDocDetail(null)}
                  className="px-6 py-2.5 bg-vivid-tangerine-600 hover:bg-vivid-tangerine-700 text-white font-bold rounded-none text-xs transition-colors"
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
            <div className="bg-white rounded-none max-w-md w-full overflow-hidden border border-vivid-tangerine-200/50 shadow-2xl relative flex flex-col text-left animate-in fade-in zoom-in duration-200">

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
                <div className="bg-vivid-tangerine-50/70 p-4 rounded-none border border-vivid-tangerine-100 text-xs font-semibold text-vivid-tangerine-950 italic">
                  "{docToDelete.title}"
                </div>
                <p className="text-xs text-vivid-tangerine-600 font-medium leading-relaxed">
                  This action is **irreversible**. Deleting this document will permanently purge its parsed text content, contractor EOT requests, action items, and contractual delay risks from the cache.
                </p>
                <p className="text-xs text-red-600 font-black uppercase tracking-wider bg-red-50 p-3 rounded-none border border-red-100 text-center">
                  ⚠️ This document's system insights will no longer be included in weekly/monthly report aggregation.
                </p>
              </div>

              {/* Action Footer Buttons */}
              <div className="p-4 bg-vanilla-custard-50 border-t border-vanilla-custard-150 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setDocToDelete(null)}
                  className="px-5 py-2.5 bg-vanilla-custard-200 hover:bg-vanilla-custard-300 text-vivid-tangerine-900 font-bold rounded-none text-xs transition-all uppercase tracking-wider"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleDeleteDocument(docToDelete.id)}
                  className="px-5 py-2.5 bg-red-600 hover:bg-red-700 active:scale-95 text-white font-bold rounded-none text-xs transition-all uppercase tracking-wider shadow-md hover:shadow-lg"
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
            <div className="bg-white rounded-none max-w-sm w-full overflow-hidden border border-sunflower-gold-200/40 shadow-2xl relative flex flex-col text-left p-6 animate-in fade-in zoom-in duration-200">
              <h3 className="text-lg font-bold text-vivid-tangerine-950 mb-2 font-serif">Document Upload Successful</h3>
              <p className="text-xs text-vivid-tangerine-800 mb-6 leading-relaxed">
                View your analysed document in the register below, or upload a new document for scanning.
              </p>
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => setShowSuccessModal(false)}
                  className="px-6 py-2.5 bg-gradient-to-r from-sunflower-gold-500 to-vivid-tangerine-600 text-white font-bold rounded-none text-xs uppercase tracking-wider shadow-md hover:scale-[1.02] active:scale-98 transition-all"
                >
                  OK
                </button>
              </div>
            </div>
          </div>
        )}

        {/* EVM Alert Modal */}
        {showEvmModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm transition-all duration-300">
            <div className="bg-white rounded-none max-w-sm w-full overflow-hidden border shadow-2xl relative flex flex-col text-left p-6 animate-in fade-in zoom-in duration-200">
              <h3 className={`text-lg font-bold mb-2 font-serif ${evmStatus.includes('✅') ? 'text-green-600' : 'text-red-600'}`}>
                {evmStatus.includes('✅') ? 'Success!' : 'Error'}
              </h3>
              <p className="text-xs text-vivid-tangerine-800 mb-6 leading-relaxed">
                {evmStatus}
              </p>
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => setShowEvmModal(false)}
                  className="px-6 py-2.5 bg-gradient-to-r from-sunflower-gold-500 to-vivid-tangerine-600 text-white font-bold rounded-none text-xs uppercase tracking-wider shadow-md hover:scale-[1.02] active:scale-98 transition-all"
                >
                  OK
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Panel */}
      <Footer />
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-5 fade-in duration-300">
          <div className={`px-6 py-4 rounded-none shadow-2xl border flex items-center gap-3 ${toast.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
            }`}>
            <span className="text-xl">{toast.type === 'success' ? '✅' : '⚠️'}</span>
            <p className="text-sm font-bold">{toast.message}</p>
            <button
              onClick={() => setToast(null)}
              className={`ml-4 p-1 hover:bg-black/5 rounded transition-colors ${toast.type === 'success' ? 'text-green-600' : 'text-red-600'}`}
            >
              ✕
            </button>
          </div>
        </div>
      )}
      {/* PDF Viewer Modal */}
      {pdfModalUrl && (
        <div className="fixed inset-0 z-[60] bg-black/80 flex items-center justify-center p-4 sm:p-8 animate-in fade-in duration-200">
          <div className="bg-white w-full h-full max-w-7xl max-h-[90vh] rounded-none shadow-2xl flex flex-col overflow-hidden">
            <div className="flex justify-between items-center p-4 border-b border-slate-100 bg-slate-50">
              <h3 className="font-bold text-slate-800 flex items-center gap-2">
                <span className="text-xl">📄</span> Document Preview
              </h3>
              <div className="flex items-center gap-4">
                <a
                  href={pdfModalUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[10px] uppercase tracking-wider font-bold text-vivid-tangerine-600 hover:text-vivid-tangerine-800 transition-colors bg-vivid-tangerine-50 px-3 py-1.5"
                >
                  Open External ↗
                </a>
                <button
                  onClick={() => setPdfModalUrl(null)}
                  className="p-1.5 hover:bg-slate-200 transition-colors text-slate-600"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
              </div>
            </div>
            <div className="flex-1 w-full bg-slate-100">
              <iframe
                src={`${pdfModalUrl}#toolbar=0`}
                className="w-full h-full border-0"
                title="PDF Document Viewer"
              />
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
