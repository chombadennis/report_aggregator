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

  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Input states
  const [selectedTasks, setSelectedTasks] = useState<{task_name: string, percentage: number, path?: string, variance_days?: number, min_percentage?: number}[]>([]);
  const [notes, setNotes] = useState('');

  const [lastSavedRecord, setLastSavedRecord] = useState<any>(null);
  const [existingSnapshot, setExistingSnapshot] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(true);

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

  const components = [
    { id: 'Block_B1', sourceId: 'Makindu_AHP_B1_B2_Programme_from_15-Sep-2026', name: 'Block B1' },
    { id: 'Block_B2', sourceId: 'Makindu_AHP_B1_B2_Programme_from_15-Sep-2026', name: 'Block B2' },
    { id: 'Block_B3', sourceId: 'Makindu_AHP_B3_B4_Programme_from_15-Sep-2026', name: 'Block B3' },
    { id: 'Block_B4', sourceId: 'Makindu_AHP_B3_B4_Programme_from_15-Sep-2026', name: 'Block B4' },
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

        const res = await fetch(`${API_BASE}/schedules/${sourceId}?week_number=${selectedWeek}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (res.ok) {
          const data = await res.json();
          setTasks(data);
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
          if (currentSnapshot) {
            setExistingSnapshot(currentSnapshot);
            setSelectedTasks(currentSnapshot.tasks || []);
            setNotes(currentSnapshot.notes || '');
            setIsEditing(false); // Locked by default if it exists
          } else {
            setExistingSnapshot(null);
            setSelectedTasks([]);
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
      alert("All components have been recorded for this week!");
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
          alert("All missing components have been reviewed!");
          setReviewModalOpen(false);
        }
      } else {
        alert("Error saving snapshot.");
      }
    } catch (err) {
      alert("Error saving empty snapshot.");
    }
  };

  const handleReviewNo = () => {
    const compToNavigate = missingComponents[currentMissingIndex];
    setSelectedComponent(compToNavigate.id);
    setReviewModalOpen(false);
  };

  const startFinalizeReview = () => {
    setFinalizeReviewIndex(0);
    setFinalizeModalOpen(true);
  };

  const confirmFinalizeWeek = async () => {
    if (!confirm("Are you sure you want to lock this week?")) return;
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/lock_week/${selectedWeek}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setLockedWeeks(await res.json());
        setFinalizeModalOpen(false);
        alert("Week has been finalized and locked!");
      }
    } catch (err) {
      alert("Error locking week.");
    }
  };

  const handleFinalizeEdit = () => {
    setFinalizeModalOpen(false);
    setSelectedComponent(components[finalizeReviewIndex].id);
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
    if (selectedTasks.length === 0) {
      alert("Please select at least one task from the list below.");
      return;
    }

    const payload = {
      week_number: selectedWeek,
      report_date_str: getSundayForWeek(selectedWeek),
      component: selectedComponent,
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
        alert(`Success! Overall Schedule Variance is: ${data.record.variance_days} days.`);
      } else {
        alert("Error saving snapshot: " + JSON.stringify(data));
      }
    } catch (err) {
      alert("Error communicating with backend.");
      console.error(err);
    }
  };

  const renderTasks = (nodes: any[], depth = 0, currentPath = "") => {
    return nodes.map((task, idx) => {
      if (task.previous_percentage === 100) return null; // hide fully completed tasks

      const taskPath = currentPath ? `${currentPath} > ${task.name}` : task.name;
      const displayPath = currentPath;
      const isLeaf = !task.children || task.children.length === 0;
      const isSelected = selectedTasks.some(t => t.task_name === task.name && (t.path || "") === (displayPath || ""));
      
      const handleToggle = () => {
        if (!isLeaf) return;
        if (isSelected) {
          setSelectedTasks(selectedTasks.filter(t => !(t.task_name === task.name && (t.path || "") === (displayPath || ""))));
        } else {
          const startPct = task.previous_percentage || 1;
          setSelectedTasks([...selectedTasks, { task_name: task.name, percentage: startPct, min_percentage: startPct, path: displayPath }]);
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
              checked={isSelected}
              onChange={handleToggle}
              disabled={!isEditing || lockedWeeks.includes(selectedWeek)}
              className="w-4 h-4 accent-vivid-tangerine-500 disabled:opacity-50 cursor-pointer"
            />
          ) : (
            <div className="w-4 h-4"></div>
          )}
          <span className={`text-sm ${depth === 0 ? 'font-bold' : depth === 1 ? 'font-semibold text-slate-700' : 'text-slate-600'}`}>
            {task.name} {task.previous_percentage ? <span className="text-xs text-vivid-tangerine-600 ml-2">({task.previous_percentage}% done)</span> : ''}
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

        {lastSavedRecord && (
          <div className={`mb-8 p-4 rounded shadow-sm flex items-center gap-4 ${lastSavedRecord.variance_days < 0 ? 'bg-red-50 border border-red-200 text-red-800' : 'bg-green-50 border border-green-200 text-green-800'
            }`}>
            <span className="text-2xl">{lastSavedRecord.variance_days < 0 ? '🔴' : '🟢'}</span>
            <div>
              <h3 className="font-bold text-lg">
                {Math.abs(lastSavedRecord.variance_days)} Days {lastSavedRecord.variance_days < 0 ? 'Behind' : 'Ahead'}
              </h3>
              <p className="text-sm opacity-80">Saved for Week {lastSavedRecord.week_number} ({lastSavedRecord.component})</p>
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
              {[41, 42, 43, 44, 45, 46, 47, 48, 49, 50].map(w => (
                <option key={w} value={w} disabled={w < 44}>
                  Week {w} (Ending {getDisplayDateForWeek(w)}) {w < 44 ? '- Locked' : ''}
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
            <button 
              onClick={startFinalizeReview}
              disabled={lockedWeeks.includes(selectedWeek) || reviewEditModeActive}
              className="px-6 py-2.5 bg-red-600 hover:bg-red-700 disabled:bg-slate-300 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
            >
              {lockedWeeks.includes(selectedWeek) ? "Week Locked" : "Finalize & Lock Week"}
            </button>
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
                  ) : (
                    <div className="space-y-3">
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
                              }}
                              disabled={!isEditing || lockedWeeks.includes(selectedWeek)}
                              className="flex-1 accent-vivid-tangerine-500 disabled:opacity-50"
                            />
                            <span className="font-bold text-slate-700 w-12 text-right">{t.percentage}%</span>
                          </div>
                          {t.variance_days !== undefined && !isEditing && (
                            <div className={`text-xs font-bold ${t.variance_days < 0 ? 'text-red-600' : 'text-green-600'}`}>
                              Variance: {Math.abs(t.variance_days)} days {t.variance_days < 0 ? 'Behind' : 'Ahead'}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Notes / Delays</label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    disabled={!isEditing || lockedWeeks.includes(selectedWeek)}
                    className="w-full p-3 bg-slate-50 border border-slate-200 focus:outline-none focus:border-vivid-tangerine-500 resize-none h-24 text-sm disabled:opacity-50"
                    placeholder="E.g. Delayed 2 days due to heavy rain..."
                  />
                </div>

                {!isEditing && !lockedWeeks.includes(selectedWeek) ? (
                  <button type="button" onClick={() => setIsEditing(true)} className="mt-4 w-full py-3 bg-slate-800 hover:bg-slate-900 text-white font-bold uppercase tracking-widest text-xs transition-colors shadow-sm">
                    Unlock for Editing
                  </button>
                ) : !lockedWeeks.includes(selectedWeek) ? (
                  <button type="submit" className="mt-4 w-full py-3 bg-vivid-tangerine-600 hover:bg-vivid-tangerine-700 text-white font-bold uppercase tracking-widest text-xs transition-colors shadow-sm">
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
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Activities Recorded</h4>
                      {snap.tasks.map((t: any, idx: number) => (
                        <div key={idx} className="p-3 bg-slate-50 border border-slate-200 text-sm flex justify-between items-center">
                          <div>
                            {t.path && <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">{t.path}</div>}
                            <span className="font-bold text-slate-700">{t.task_name}</span>
                          </div>
                          <div className="font-bold text-vivid-tangerine-600 bg-vivid-tangerine-50 px-3 py-1 rounded">
                            {t.percentage}%
                          </div>
                        </div>
                      ))}
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
                  onClick={confirmFinalizeWeek}
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

      {/* Footer Panel */}
      <Footer />
    </main>
  );
}
