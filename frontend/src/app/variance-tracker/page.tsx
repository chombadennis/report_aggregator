"use client";
import React, { useState, useEffect } from 'react';
import NavigationPanel from '@/components/NavigationPanel';
import Footer from '@/components/Footer';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const API_BASE = `${BACKEND_URL}/api/variance`;

export default function VarianceTracker() {
  const { isLoaded, userId, getToken } = useAuth();
  const router = useRouter();

  const [selectedWeek, setSelectedWeek] = useState(44);

  const [selectedComponent, setSelectedComponent] = useState('Block_B1');
  const [isInitialized, setIsInitialized] = useState(false);

  // Sync with localStorage on mount (client-side only) to prevent hydration errors
  useEffect(() => {
    const saved = localStorage.getItem('lastSelectedComponent');
    if (saved) {
      setSelectedComponent(saved);
    }
    setIsInitialized(true);
  }, []);

  // Sync to localStorage whenever it changes, but ONLY after initialization
  useEffect(() => {
    if (isInitialized && typeof window !== 'undefined') {
      localStorage.setItem('lastSelectedComponent', selectedComponent);
    }
  }, [selectedComponent, isInitialized]);

  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Input states
  const [selectedTasks, setSelectedTasks] = useState<{ task_name: string, percentage: number, path?: string, variance_days?: number | string, min_percentage?: number }[]>([]);
  const [notes, setNotes] = useState('');

  const [toast, setToast] = useState<{ message: string, type: 'success' | 'error' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const [lastSavedRecord, setLastSavedRecord] = useState<any>(null);
  const [existingSnapshot, setExistingSnapshot] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(true);
  const [submitDisabled, setSubmitDisabled] = useState(false);
  const [reportModalOpen, setReportModalOpen] = useState(false);

  const handleEditClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsEditing(true);
    setSubmitDisabled(true);
    setTimeout(() => setSubmitDisabled(false), 500);
  };

  // Ref to hold unsaved drafts so they persist across component switches without causing infinite re-renders
  const draftsRef = React.useRef<Record<string, { tasks: any[], notes: string }>>({});

  // Review states
  const [allWeekSnapshots, setAllWeekSnapshots] = useState<any[]>([]);
  const [lockedWeeks, setLockedWeeks] = useState<number[]>([]);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [missingComponents, setMissingComponents] = useState<any[]>([]);
  const [currentMissingIndex, setCurrentMissingIndex] = useState(0);
  const [reviewModalNotes, setReviewModalNotes] = useState("");

  // Finalize Review states
  const [finalizeModalOpen, setFinalizeModalOpen] = useState(false);
  const [finalizeReviewIndex, setFinalizeReviewIndex] = useState(0);
  const [reviewEditModeActive, setReviewEditModeActive] = useState(false);
  const [lockConfirmOpen, setLockConfirmOpen] = useState(false);

  const components = [
    { id: 'Block_B1', sourceId: 'Makindu_AHP_B1_B2_Programme_from_15-Sep-2026', name: 'Block B1' },
    { id: 'Block_B2', sourceId: 'Makindu_AHP_B1_B2_Programme_from_15-Sep-2026', name: 'Block B2' },
    { id: 'Block_B3', sourceId: 'Makindu_AHP_B3_B4_Revised_Programme_from_15-Sep-2026', name: 'Block B3' },
    { id: 'Block_B4', sourceId: 'Makindu_AHP_B3_B4_Revised_Programme_from_15-Sep-2026', name: 'Block B4' },
    { id: 'Block_C1', sourceId: 'Makindu_AHP_C1_C3_Programme_from_04-Sep-2026', name: 'Block C1' },
    { id: 'Block_C3', sourceId: 'Makindu_AHP_C1_C3_Programme_from_04-Sep-2026', name: 'Block C3' },
    { id: 'Block_C2', sourceId: 'Makindu_AHP_C2_C5_Programme_from_13-Sep-2026', name: 'Block C2' },
    { id: 'Block_C5', sourceId: 'Makindu_AHP_C2_C5_Programme_from_13-Sep-2026', name: 'Block C5' },
    { id: 'Block_C4', sourceId: 'Makindu_AHP_C4_Programme_from_05-Nov-2026', name: 'Block C4' },
    { id: 'Auxiliary_Facilities', sourceId: 'Makindu_AHP_Auxiliary_Facilities_Programme', name: 'Auxiliary Facilities' },
    { id: 'Club_House', sourceId: 'Makindu_AHP_Club_House_Programme_from_15-Jan-2027', name: 'Club House' },
    { id: 'Kindergarten', sourceId: 'Makindu_AHP_Kindergarten_Programme_from_09-Aug-2026', name: 'Kindergarten' }
  ];

  useEffect(() => {
    if (isLoaded && !userId) {
      router.push('/login');
    }
  }, [isLoaded, userId, router]);

  useEffect(() => {
    const fetchScheduleAndSnapshot = async () => {
      setLoading(true);
      try {
        const token = await getToken();

        // Fetch locked weeks
        const locksRes = await fetch(`${API_BASE}/locked_weeks`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (locksRes.ok) {
          setLockedWeeks(await locksRes.json());
        }

        // 1. Fetch Schedule using sourceId
        const activeComp = components.find(c => c.id === selectedComponent);
        const sourceId = activeComp ? activeComp.sourceId : selectedComponent;

        let fetchedData: any[] = [];
        const res = await fetch(`${API_BASE}/schedules/${sourceId}?week_number=${selectedWeek}&component_id=${selectedComponent}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (res.ok) {
          fetchedData = await res.json();
          setTasks(fetchedData);
        } else {
          setTasks([]);
        }

        // 2. Fetch Snapshots for the selected week
        const snapRes = await fetch(`${API_BASE}/snapshots/${selectedWeek}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (snapRes.ok) {
          const snapshotsArray = await snapRes.json();
          setAllWeekSnapshots(snapshotsArray);
          const currentSnapshot = snapshotsArray.find((s: any) => s.component === selectedComponent);
          const draftKey = `${selectedWeek}-${selectedComponent}`;
          const currentDraft = draftsRef.current[draftKey];

          if (currentDraft && (currentDraft.tasks.length > 0 || currentDraft.notes)) {
            // Restore from unsaved draft if it exists and has content
            setExistingSnapshot(currentSnapshot || null);

            const getPrevPct = (tasks: any[], name: string, targetPath: string, currentPath = ""): number => {
              for (const t of tasks) {
                if (t.name === name && (currentPath || "") === (targetPath || "")) return t.previous_percentage || 0;
                if (t.children) {
                  const newPath = currentPath ? `${currentPath} > ${t.name}` : t.name;
                  const found = getPrevPct(t.children, name, targetPath, newPath);
                  if (found !== -1) return found;
                }
              }
              return -1;
            };

            const filteredTasks = currentDraft.tasks.filter((t: any) => {
              const prev = getPrevPct(fetchedData, t.task_name, t.path || "");
              return prev < 100;
            });

            setSelectedTasks(filteredTasks);
            setNotes(currentDraft.notes);
            setIsEditing(true);
          } else if (currentSnapshot) {
            setExistingSnapshot(currentSnapshot);

            // Exclude tasks that were already 100% before this week by cross-referencing with fetchedData
            const getPrevPct = (tasks: any[], name: string, targetPath: string, currentPath = ""): number => {
              for (const t of tasks) {
                if (t.name === name && (currentPath || "") === (targetPath || "")) return t.previous_percentage || 0;
                if (t.children) {
                  const newPath = currentPath ? `${currentPath} > ${t.name}` : t.name;
                  const found = getPrevPct(t.children, name, targetPath, newPath);
                  if (found !== -1) return found;
                }
              }
              return -1;
            };

            const filteredTasks = (currentSnapshot.tasks || []).filter((t: any) => {
              const prev = getPrevPct(fetchedData, t.task_name, t.path || "");
              return prev < 100;
            });

            setSelectedTasks(filteredTasks);
            setNotes(currentSnapshot.notes || '');
            setIsEditing(false); // Locked by default if it exists
          } else {
            setExistingSnapshot(null);

            // Pre-fill from previous weeks' progress
            const prefilled: any[] = [];
            const extractPrev = (nodes: any[], path = "") => {
              nodes.forEach(n => {
                const currentPath = path ? `${path} > ${n.name}` : n.name;
                if (n.previous_percentage > 0 && n.previous_percentage < 100) {
                  prefilled.push({
                    task_name: n.name,
                    percentage: n.previous_percentage,
                    min_percentage: n.previous_percentage,
                    path: path // Correctly assigns the parent path without gluing the task name to it
                  });
                }
                if (n.children) extractPrev(n.children, currentPath);
              });
            };
            extractPrev(fetchedData);
            setSelectedTasks(prefilled);

            setNotes('');
            setIsEditing(true); // Open for editing if it doesn't exist
          }
        }
      } catch (err) {
        console.error("Failed to load schedule or snapshots", err);
        setTasks([]);
      }
      setLoading(false);
    };
    fetchScheduleAndSnapshot();
  }, [selectedComponent, selectedWeek]);

  const getSundayForWeek = (weekNum: number) => {
    const diffWeeks = weekNum - 41;
    // Week 41 ends on Sept 6, 2026 (Month is 0-indexed, so 8 is September)
    const anchorEnd = new Date(2026, 8, 6);
    const newEnd = new Date(anchorEnd.getTime() + diffWeeks * 7 * 24 * 60 * 60 * 1000);

    const yyyy = newEnd.getFullYear();
    const mm = String(newEnd.getMonth() + 1).padStart(2, '0');
    const dd = String(newEnd.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  };

  const getDisplayDateForWeek = (weekNum: number) => {
    const diffWeeks = weekNum - 41;
    const anchorEnd = new Date(2026, 8, 6);
    const newEnd = new Date(anchorEnd.getTime() + diffWeeks * 7 * 24 * 60 * 60 * 1000);
    return newEnd.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const startReview = () => {
    const missing = components.filter(c => !allWeekSnapshots.some(s => s.component === c.id));
    if (missing.length === 0) {
      showToast("All components have been recorded for this week!", "success");
      return;
    }
    setMissingComponents(missing);
    setCurrentMissingIndex(0);
    setReviewModalNotes("");
    setReviewModalOpen(true);
  };

  const handleReviewYes = async () => {
    const compToSave = missingComponents[currentMissingIndex];
    const payload = {
      week_number: selectedWeek,
      report_date_str: getSundayForWeek(selectedWeek),
      component: compToSave.id,
      source_id: compToSave.sourceId,
      tasks: [],
      notes: reviewModalNotes.trim() || "No activity recorded."
    };

    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/snapshot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setAllWeekSnapshots(prev => [...prev, data.record]);
        if (compToSave.id === selectedComponent) {
          setExistingSnapshot(data.record);
          setSelectedTasks([]);
          setNotes("No activity recorded.");
          setIsEditing(false);
        }
        if (currentMissingIndex + 1 < missingComponents.length) {
          setCurrentMissingIndex(currentMissingIndex + 1);
          setReviewModalNotes("");
        } else {
          showToast("All missing components have been reviewed!", "success");
          setReviewModalOpen(false);
        }
      } else {
        showToast("Error saving snapshot.", "error");
      }
    } catch (err) {
      showToast("Error saving empty snapshot.", "error");
    }
  };

  const handleReviewNo = () => {
    const compToNavigate = missingComponents[currentMissingIndex];
    setSelectedComponent(compToNavigate.id);
    setReviewModalOpen(false);
  };

  const startFinalizeReview = () => {
    // Block finalization if there are unsaved drafts
    const hasUnsavedDrafts = Object.keys(draftsRef.current).some(key => {
      if (key.startsWith(`${selectedWeek}-`)) {
        const draft = draftsRef.current[key];
        // Check if the draft has actual unsaved modifications
        return draft.tasks.length > 0 || draft.notes.trim() !== '';
      }
      return false;
    });

    if (hasUnsavedDrafts) {
      showToast("You have checked activities or entered notes in one or more components that have not been saved. Please return to them and click 'Save Snapshot' before finalizing the week.", "error");
      return;
    }

    setFinalizeReviewIndex(0);
    setFinalizeModalOpen(true);
  };

  const promptFinalizeWeek = () => {
    setLockConfirmOpen(true);
  };

  const confirmFinalizeWeek = async () => {
    setLockConfirmOpen(false);
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/lock_week/${selectedWeek}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setLockedWeeks(await res.json());
        setFinalizeModalOpen(false);
        showToast("Week has been finalized and locked!", "success");
      }
    } catch (err) {
      showToast("Error locking week.", "error");
    }
  };

  const handleFinalizeEdit = () => {
    const compToEdit = components[finalizeReviewIndex].id;
    const currentSnapshot = allWeekSnapshots.find(s => s.component === compToEdit);

    // Clear current state to avoid visual mix-ups while fetching
    setTasks([]);
    setSelectedTasks([]);
    setNotes('');

    // Seed the draft so the fetcher knows we want to edit this component
    if (currentSnapshot) {
      draftsRef.current[`${selectedWeek}-${compToEdit}`] = {
        tasks: currentSnapshot.tasks || [],
        notes: currentSnapshot.notes || ''
      };
    }

    setFinalizeModalOpen(false);
    setSelectedComponent(compToEdit);
    setIsEditing(true);
    setReviewEditModeActive(true);
  };

  const resumeFinalizeReview = () => {
    setReviewEditModeActive(false);
    setFinalizeModalOpen(true);
  };

  const discardFinalizeEdit = () => {
    const currentSnapshot = allWeekSnapshots.find(s => s.component === selectedComponent);
    if (currentSnapshot) {
      setExistingSnapshot(currentSnapshot);
      setSelectedTasks(currentSnapshot.tasks || []);
      setNotes(currentSnapshot.notes || '');
      setIsEditing(false);
    } else {
      setExistingSnapshot(null);
      setSelectedTasks([]);
      setNotes('');
      setIsEditing(true);
    }
    resumeFinalizeReview();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedTasks.length === 0 && !notes.trim()) {
      showToast("Please select at least one task or provide a note explaining the lack of activity.", "error");
      return;
    }

    const activeComp = components.find(c => c.id === selectedComponent);
    const sourceId = activeComp ? activeComp.sourceId : selectedComponent;

    const payload = {
      week_number: selectedWeek,
      report_date_str: getSundayForWeek(selectedWeek),
      component: selectedComponent,
      source_id: sourceId,
      tasks: selectedTasks,
      notes: notes
    };

    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/snapshot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        // Clear the draft upon successful save
        delete draftsRef.current[`${selectedWeek}-${selectedComponent}`];

        setLastSavedRecord(data.record);
        setExistingSnapshot(data.record);
        setSelectedTasks(data.record.tasks || []);
        setIsEditing(false);
        setAllWeekSnapshots(prev => {
          const idx = prev.findIndex(s => s.component === data.record.component);
          if (idx >= 0) {
            const newArr = [...prev];
            newArr[idx] = data.record;
            return newArr;
          }
          return [...prev, data.record];
        });
        showToast("Snapshot saved successfully!", "success");
      } else {
        showToast("Error saving snapshot.", "error");
      }
    } catch (err) {
      showToast("Error communicating with backend.", "error");
      console.error(err);
    }
  };

  const renderTasks = (nodes: any[], depth = 0, currentPath = "") => {
    return nodes.map((task, idx) => {
      const taskPath = currentPath ? `${currentPath} > ${task.name}` : task.name;
      const displayPath = currentPath;
      const isLeaf = !task.children || task.children.length === 0;
      const selectedTask = selectedTasks.find(t => t.task_name === task.name && (t.path || "") === (displayPath || ""));
      const isSelected = !!selectedTask;
      const isPreviouslyStarted = (task.previous_percentage || 0) > 0;
      const displayPercentage = selectedTask ? selectedTask.percentage : task.previous_percentage;

      const handleToggle = () => {
        if (!isLeaf) return;
        if (isPreviouslyStarted) return; // Cannot uncheck tasks from previous weeks

        if (isSelected) {
          const newTasks = selectedTasks.filter(t => !(t.task_name === task.name && (t.path || "") === (displayPath || "")));
          setSelectedTasks(newTasks);
          draftsRef.current[`${selectedWeek}-${selectedComponent}`] = { tasks: newTasks, notes };
        } else {
          const startPct = task.previous_percentage || 1;
          const newTasks = [...selectedTasks, { task_name: task.name, percentage: startPct, min_percentage: startPct, path: displayPath }];
          setSelectedTasks(newTasks);
          draftsRef.current[`${selectedWeek}-${selectedComponent}`] = { tasks: newTasks, notes };
        }
      };

      return (
        <div key={`${taskPath}-${idx}`}>
          <div
            className={`flex items-center gap-3 p-2 hover:bg-slate-50 border-b border-slate-50`}
            style={{ paddingLeft: `${depth * 1.5 + 0.5}rem` }}
          >
            {isLeaf ? (
              <input
                type="checkbox"
                name={`task-${taskPath}`}
                checked={isSelected || isPreviouslyStarted}
                onChange={handleToggle}
                disabled={!isEditing || lockedWeeks.includes(selectedWeek) || isPreviouslyStarted}
                className="w-4 h-4 accent-vivid-tangerine-500 disabled:opacity-50 cursor-pointer"
              />
            ) : (
              <div className="w-4 h-4"></div>
            )}
            <span className={`text-sm ${depth === 0 ? 'font-bold' : depth === 1 ? 'font-semibold text-slate-700' : 'text-slate-600'}`}>
              {task.name} {displayPercentage ? <span className="text-xs text-vivid-tangerine-600 ml-2">({displayPercentage}% done)</span> : ''}
            </span>
            <span className="ml-auto text-xs text-slate-400">
              {task.start_date} to {task.finish_date}
            </span>
          </div>
          {!isLeaf && renderTasks(task.children, depth + 1, taskPath)}
        </div>
      );
    });
  };

  if (!isLoaded || !userId) return null;

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      <NavigationPanel />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-20">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Schedule Variance Tracker</h1>
          <p className="text-slate-500 mt-2">Track time-based schedule performance per component</p>
        </div>

        {reviewEditModeActive && (
          <div className="bg-amber-100 border-l-4 border-amber-500 p-4 mb-8 flex flex-wrap justify-between items-center shadow-sm gap-4">
            <div>
              <h3 className="text-amber-800 font-bold">Review Edit Mode Active</h3>
              <p className="text-amber-700 text-sm">You are editing <strong className="text-amber-900">{components.find(c => c.id === selectedComponent)?.name}</strong> during the final review process.</p>
            </div>
            <div className="flex gap-4">
              <button onClick={resumeFinalizeReview} className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm">
                Save & Resume Review
              </button>
              <button onClick={discardFinalizeEdit} className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold text-xs uppercase tracking-wider transition-colors shadow-sm">
                Discard Changes
              </button>
            </div>
          </div>
        )}

        <div className="bg-white p-6 rounded-none shadow-sm border border-slate-200 mb-8 flex flex-wrap gap-6 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Select Week</label>
            <select
              value={selectedWeek}
              onChange={(e) => setSelectedWeek(Number(e.target.value))}
              className="w-full p-2.5 bg-slate-50 border border-slate-200 focus:outline-none focus:border-vivid-tangerine-500"
            >
              {[44, 45, 46, 47, 48, 49, 50].map(w => (
                <option key={w} value={w}>
                  Week {w} (Ending {getDisplayDateForWeek(w)}) {lockedWeeks.includes(w) ? '— Locked' : ''}
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1 min-w-[250px]">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Select Component</label>
            <select
              value={selectedComponent}
              onChange={(e) => setSelectedComponent(e.target.value)}
              className="w-full p-2.5 bg-slate-50 border border-slate-200 focus:outline-none focus:border-vivid-tangerine-500"
            >
              {components.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div>
            <button
              onClick={startReview}
              className="px-6 py-2.5 bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm mr-4"
            >
              Review Missing Components
            </button>
            {lockedWeeks.includes(selectedWeek) ? (
              <button
                onClick={() => setReportModalOpen(true)}
                className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                View Weekly Report
              </button>
            ) : (
              <button
                onClick={startFinalizeReview}
                disabled={reviewEditModeActive}
                className="px-6 py-2.5 bg-red-600 hover:bg-red-700 disabled:bg-slate-300 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                Finalize & Lock Week
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Submission Form */}
          <div className="lg:col-span-1">
            <div className="bg-white p-6 shadow-sm border border-slate-200 sticky top-24">
              <h2 className="text-lg font-bold text-vivid-tangerine-700 border-b border-slate-100 pb-4 mb-4">Record Progress</h2>
              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Selected Tasks</label>
                  {selectedTasks.length === 0 ? (
                    <div className="p-3 bg-slate-50 border border-slate-200 text-sm text-slate-600 font-medium min-h-[42px]">
                      Select tasks from the list ➔
                    </div>
                  ) : !isEditing ? (
                    <div className="border border-slate-200 overflow-y-auto max-h-[60vh]">
                      <table className="w-full text-left border-collapse text-sm">
                        <thead className="bg-slate-50 text-slate-600 text-[10px] uppercase tracking-wider">
                          <tr>
                            <th className="p-3 border-b border-slate-200 font-bold">Task</th>
                            <th className="p-3 border-b border-slate-200 font-bold text-right">%</th>
                            <th className="p-3 border-b border-slate-200 font-bold text-right">Variance</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white">
                          {selectedTasks.map((t, idx) => (
                            <tr key={`${t.path || ''}-${t.task_name}-${idx}`} className="border-b border-slate-100 last:border-none">
                              <td className="p-3">
                                {t.path && <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-0.5">{t.path.replace(/ > /g, ' • ')}</div>}
                                <span className="font-semibold text-slate-800">{t.task_name}</span>
                              </td>
                              <td className="p-3 text-right font-bold text-slate-700">{t.percentage}%</td>
                              <td className="p-3 text-right text-xs font-bold whitespace-nowrap">
                                {t.variance_days !== undefined ? (
                                  t.variance_days === 'Completed' ? (
                                    <span className="text-emerald-600">Completed</span>
                                  ) : (
                                    <span className={Number(t.variance_days) < 0 ? 'text-red-600' : Number(t.variance_days) > 0 ? 'text-green-600' : 'text-orange-600'}>
                                      {t.variance_days === 0 ? 'On Track' : `${Number(t.variance_days) < 0 ? '-' : '+'}${Math.abs(Number(t.variance_days))} d`}
                                    </span>
                                  )
                                ) : '-'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-2">
                      {selectedTasks.map((t, idx) => (
                        <div key={`${t.path || ''}-${t.task_name}-${idx}`} className="p-3 bg-slate-50 border border-slate-200 text-sm flex flex-col gap-2">
                          <div>
                            {t.path && <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">{t.path}</div>}
                            <span className="font-bold text-slate-700">{t.task_name}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <input
                              type="range"
                              min={t.min_percentage || 1} max="100"
                              value={t.percentage}
                              onChange={(e) => {
                                const newTasks = selectedTasks.map(st =>
                                  st.task_name === t.task_name && (st.path || "") === (t.path || "") ? { ...st, percentage: Number(e.target.value) } : st
                                );
                                setSelectedTasks(newTasks);
                                draftsRef.current[`${selectedWeek}-${selectedComponent}`] = { tasks: newTasks, notes };
                              }}
                              disabled={t.min_percentage === 100}
                              className="flex-1 accent-vivid-tangerine-500"
                            />
                            <span className="font-bold text-slate-700 w-12 text-right">{t.percentage}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Notes / Delays</label>
                  <textarea
                    value={notes}
                    onChange={(e) => {
                      setNotes(e.target.value);
                      draftsRef.current[`${selectedWeek}-${selectedComponent}`] = { tasks: selectedTasks, notes: e.target.value };
                    }}
                    disabled={!isEditing || lockedWeeks.includes(selectedWeek)}
                    className="w-full p-3 bg-slate-50 border border-slate-200 focus:outline-none focus:border-vivid-tangerine-500 resize-none h-24 text-sm disabled:opacity-50"
                    placeholder="E.g. Delayed 2 days due to heavy rain..."
                  />
                </div>

                {!isEditing && !lockedWeeks.includes(selectedWeek) ? (
                  <button
                    type="button"
                    onClick={handleEditClick}
                    className="mt-4 w-full py-3 bg-slate-800 hover:bg-slate-900 text-white font-bold uppercase tracking-widest text-xs transition-colors shadow-sm"
                  >
                    Edit Saved Progress
                  </button>
                ) : !lockedWeeks.includes(selectedWeek) ? (
                  <button
                    type="submit"
                    disabled={submitDisabled}
                    className="mt-4 w-full py-3 bg-vivid-tangerine-600 hover:bg-vivid-tangerine-700 text-white font-bold uppercase tracking-widest text-xs transition-colors shadow-sm disabled:opacity-50"
                  >
                    {existingSnapshot ? "Update Snapshot" : "Save Snapshot"}
                  </button>
                ) : (
                  <div className="mt-4 p-3 bg-slate-100 text-slate-500 text-xs font-bold text-center uppercase tracking-widest">
                    Week is locked
                  </div>
                )}
              </form>
            </div>
          </div>

          {/* Task Hierarchy List */}
          <div className="lg:col-span-2">
            <div className="bg-white p-6 shadow-sm border border-slate-200">
              <h2 className="text-lg font-bold text-slate-800 border-b border-slate-100 pb-4 mb-4 flex justify-between items-center">
                <span>Planned Schedule ({components.find(c => c.id === selectedComponent)?.name})</span>
                <span className="text-xs font-normal text-slate-500 bg-slate-100 px-3 py-1 rounded-full">Select completed/active tasks</span>
              </h2>

              <div className="h-[600px] overflow-y-auto border border-slate-100 p-2 relative">
                {loading ? (
                  <div className="absolute inset-0 flex items-center justify-center bg-white/80">
                    <span className="text-slate-400">Loading schedule...</span>
                  </div>
                ) : tasks.length > 0 ? (
                  <div className="flex flex-col">
                    {renderTasks(tasks)}
                  </div>
                ) : (
                  <div className="p-4 text-center text-slate-400 text-sm">
                    No tasks found or failed to load schedule.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {reviewModalOpen && missingComponents.length > 0 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white p-6 max-w-md w-full shadow-lg border border-slate-200">
            <h2 className="text-xl font-bold text-slate-800 mb-4">Missing Activity</h2>
            <p className="text-slate-600 mb-6">
              You have not inputted any activity for <strong className="text-slate-900">{missingComponents[currentMissingIndex].name}</strong> this week. Do you wish to save activity as None?
            </p>
            <div className="mb-6">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Optional Notes</label>
              <textarea
                value={reviewModalNotes}
                onChange={(e) => setReviewModalNotes(e.target.value)}
                className="w-full p-3 bg-slate-50 border border-slate-200 focus:outline-none focus:border-vivid-tangerine-500 resize-none h-20 text-sm"
                placeholder="E.g. Delayed due to pending approvals..."
              />
            </div>
            <div className="flex gap-4">
              <button
                onClick={handleReviewYes}
                className="flex-1 py-2.5 bg-vivid-tangerine-600 hover:bg-vivid-tangerine-700 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                Yes, Save None
              </button>
              <button
                onClick={handleReviewNo}
                className="flex-1 py-2.5 bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                No, Fill it in
              </button>
            </div>
            <button
              onClick={() => setReviewModalOpen(false)}
              className="w-full mt-4 py-2 text-slate-500 hover:text-slate-700 text-xs font-bold uppercase tracking-wider"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {finalizeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white p-8 max-w-2xl w-full shadow-lg border border-slate-200 flex flex-col max-h-[90vh]">
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Final Review: Week {selectedWeek}</h2>
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100">
              <h3 className="text-lg font-bold text-vivid-tangerine-600">{components[finalizeReviewIndex].name}</h3>
              <span className="text-sm font-bold text-slate-400">Component {finalizeReviewIndex + 1} of {components.length}</span>
            </div>

            <div className="overflow-y-auto flex-1 mb-6 pr-2">
              {(() => {
                const snap = allWeekSnapshots.find(s => s.component === components[finalizeReviewIndex].id);
                if (!snap || !snap.tasks || snap.tasks.length === 0) {
                  return (
                    <div className="p-6 bg-slate-50 border border-slate-200 text-center text-slate-500 font-medium">
                      No activity recorded for this component.
                    </div>
                  );
                }
                return (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Activities Recorded</h4>
                      <div className="border border-slate-200 overflow-hidden">
                        <table className="w-full text-left border-collapse text-sm">
                          <thead className="bg-slate-50 text-slate-600 text-[10px] uppercase tracking-wider">
                            <tr>
                              <th className="p-3 border-b border-slate-200 font-bold">Task</th>
                              <th className="p-3 border-b border-slate-200 font-bold text-right">%</th>
                              <th className="p-3 border-b border-slate-200 font-bold text-right">Variance</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white">
                            {snap.tasks.map((t: any, idx: number) => (
                              <tr key={idx} className="border-b border-slate-100 last:border-none">
                                <td className="p-3">
                                  {t.path && <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-0.5">{t.path.replace(/ > /g, ' • ')}</div>}
                                  <span className="font-semibold text-slate-800">{t.task_name}</span>
                                </td>
                                <td className="p-3 text-right font-bold text-slate-700">{t.percentage}%</td>
                                <td className="p-3 text-right text-xs font-bold whitespace-nowrap">
                                  {t.variance_days !== undefined ? (
                                    t.variance_days === 'Completed' ? (
                                      <span className="text-emerald-600">Completed</span>
                                    ) : (
                                      <span className={Number(t.variance_days) < 0 ? 'text-red-600' : Number(t.variance_days) > 0 ? 'text-green-600' : 'text-orange-600'}>
                                        {t.variance_days === 0 ? 'On Track' : `${Number(t.variance_days) < 0 ? '-' : '+'}${Math.abs(Number(t.variance_days))} d`}
                                      </span>
                                    )
                                  ) : '-'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                    {snap.notes && (
                      <div className="mt-4">
                        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Notes</h4>
                        <div className="p-3 bg-slate-50 border border-slate-200 text-sm text-slate-700 whitespace-pre-wrap">
                          {snap.notes}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-slate-100">
              <button
                onClick={() => setFinalizeReviewIndex(prev => Math.max(0, prev - 1))}
                disabled={finalizeReviewIndex === 0}
                className="px-6 py-2.5 bg-slate-200 hover:bg-slate-300 disabled:opacity-50 text-slate-800 font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                &larr; Previous
              </button>

              <button
                onClick={handleFinalizeEdit}
                className="px-6 py-2.5 bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                Edit Component
              </button>

              {finalizeReviewIndex < components.length - 1 ? (
                <button
                  onClick={() => setFinalizeReviewIndex(prev => prev + 1)}
                  className="px-6 py-2.5 bg-vivid-tangerine-600 hover:bg-vivid-tangerine-700 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
                >
                  Next &rarr;
                </button>
              ) : (
                <button
                  onClick={promptFinalizeWeek}
                  className="px-6 py-2.5 bg-red-600 hover:bg-red-700 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
                >
                  Confirm & Lock Week
                </button>
              )}
            </div>

            <button
              onClick={() => setFinalizeModalOpen(false)}
              className="w-full mt-4 py-2 text-slate-400 hover:text-slate-600 text-xs font-bold uppercase tracking-wider"
            >
              ✕ Close
            </button>
          </div>
        </div>
      )}

      {lockConfirmOpen && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4">
          <div className="bg-white p-8 max-w-sm w-full shadow-lg border border-slate-200 flex flex-col text-center">
            <h2 className="text-xl font-bold text-slate-800 mb-4">Lock Week {selectedWeek}?</h2>
            <p className="text-slate-600 mb-8 text-sm">
              Are you sure you want to lock this week? Once locked, you will not be able to edit any progress for Week {selectedWeek}.
            </p>
            <div className="flex gap-4">
              <button
                onClick={confirmFinalizeWeek}
                className="flex-1 py-3 bg-red-600 hover:bg-red-700 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                Yes, Lock Week
              </button>
              <button
                onClick={() => setLockConfirmOpen(false)}
                className="flex-1 py-3 bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div className={`fixed top-6 right-6 z-[100] max-w-sm w-full p-4 rounded shadow-lg border-l-4 transition-all duration-300 ease-in-out transform translate-y-0 opacity-100 flex items-center justify-between ${toast.type === 'success' ? 'bg-white border-green-500 text-slate-800' : 'bg-red-50 border-red-500 text-red-800'
          }`}>
          <div className="flex items-center gap-3">
            <span className="text-xl">{toast.type === 'success' ? '✅' : '❌'}</span>
            <p className="text-sm font-semibold">{toast.message}</p>
          </div>
          <button onClick={() => setToast(null)} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>
      )}

      {reportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white p-8 max-w-6xl w-full shadow-lg border border-slate-200 flex flex-col max-h-[90vh]">
            <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-800">Weekly Summary Report: Week {selectedWeek} (Ending {getDisplayDateForWeek(selectedWeek)})</h2>
              <button onClick={() => setReportModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-2xl font-bold">&times;</button>
            </div>

            <div className="overflow-y-auto flex-1 mb-6 pr-2">
              <table className="w-full text-left border-collapse text-sm">
                <thead className="bg-slate-100 text-slate-700 text-xs uppercase tracking-wider sticky top-0 z-10 shadow-sm">
                  <tr>
                    <th className="p-3 border-b border-slate-200 font-bold w-1/5">Component</th>
                    <th className="p-3 border-b border-slate-200 font-bold w-2/5">Activity</th>
                    <th className="p-3 border-b border-slate-200 font-bold text-right">Progress</th>
                    <th className="p-3 border-b border-slate-200 font-bold text-right">Remaining</th>
                    <th className="p-3 border-b border-slate-200 font-bold text-right">Variance</th>
                  </tr>
                </thead>
                <tbody className="bg-white">
                  {components.map(comp => {
                    const snap = allWeekSnapshots.find(s => s.component === comp.id);
                    if (!snap || !snap.tasks || snap.tasks.length === 0) {
                      return (
                        <tr key={comp.id} className="border-b border-slate-200">
                          <td className="p-3 font-semibold text-slate-800 bg-slate-50 border-r border-slate-100">{comp.name}</td>
                          <td className="p-3 text-slate-500 italic" colSpan={4}>
                            {snap?.notes ? `No activity: ${snap.notes}` : "No activity recorded"}
                          </td>
                        </tr>
                      );
                    }
                    return snap.tasks.map((t: any, idx: number) => (
                      <tr key={`${comp.id}-${idx}`} className="border-b border-slate-100 last:border-slate-200">
                        {idx === 0 && (
                          <td className="p-3 font-semibold text-slate-800 bg-slate-50 border-r border-slate-100" rowSpan={snap.tasks.length}>
                            {comp.name}
                          </td>
                        )}
                        <td className="p-3">
                          {t.path && <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-0.5">{t.path.replace(/ > /g, ' • ')}</div>}
                          <span className="font-semibold text-slate-800">{t.task_name}</span>
                        </td>
                        <td className="p-3 text-right font-bold text-vivid-tangerine-600">{t.percentage}%</td>
                        <td className="p-3 text-right font-bold text-slate-500">{100 - t.percentage}%</td>
                        <td className="p-3 text-right text-xs font-bold whitespace-nowrap">
                          {t.variance_days !== undefined ? (
                            t.variance_days === 'Completed' ? (
                              <span className="text-emerald-600">Completed</span>
                            ) : (
                              <span className={Number(t.variance_days) < 0 ? 'text-red-600' : Number(t.variance_days) > 0 ? 'text-green-600' : 'text-orange-600'}>
                                {t.variance_days === 0 ? 'On Track' : `${Number(t.variance_days) < 0 ? 'Behind by ' : 'Ahead by '}${Math.abs(Number(t.variance_days))} d`}
                              </span>
                            )
                          ) : '-'}
                        </td>
                      </tr>
                    ));
                  })}
                </tbody>
              </table>
            </div>

            <div className="pt-4 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => window.print()}
                className="px-6 py-2.5 bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm mr-4"
              >
                Print Report
              </button>
              <button
                onClick={() => setReportModalOpen(false)}
                className="px-6 py-2.5 bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer Panel */}
      <Footer />
    </main>
  );
}

