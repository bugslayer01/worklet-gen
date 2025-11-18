import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { Sidebar } from '@/components/Sidebar';
import { WelcomeScreen } from '@/components/WelcomeScreen';
import { ThreadForm } from '@/components/ThreadForm';
import { ProgressBar } from '@/components/ProgressBar';
import { DomainKeywordModal } from '@/components/DomainKeywordModal';
import { WebQueryModal } from '@/components/WebQueryModal';
import { ThreadDetails } from '@/components/ThreadDetails';
import { Thread, DomainsKeywords, ProgressMessage, Worklet } from '@/types/thread';
import { Skeleton } from '@/components/ui/skeleton';
import { getSocket } from '@/lib/socket';
import { toast } from 'sonner';
import { API_URL } from '@/config';
import { ApiError, requestJson, formatValidationDetails } from '@/lib/http';

const Index = () => {
  const navigate = useNavigate();
  const { threadId } = useParams();
  const location = useLocation();

  const [threads, setThreads] = useState<Thread[]>([]);
  const [selectedThread, setSelectedThread] = useState<Thread | null>(null);
  const [threadLoading, setThreadLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [progressMessages, setProgressMessages] = useState<ProgressMessage[]>([]);
  const [worklets, setWorklets] = useState<Worklet[]>([]);
  // Initialization placeholder state for brand-new thread creation
  const [isInitializing, setIsInitializing] = useState<boolean>(false);
  const isInitializingRef = useRef<boolean>(false);
  const initTimeoutRef = useRef<number | null>(null);
  // Stores to preserve per-thread progress & worklets when user navigates away
  const [progressStore, setProgressStore] = useState<Record<string, ProgressMessage[]>>({});
  const [workletsStore, setWorkletsStore] = useState<Record<string, Worklet[]>>({});
  // Keep track of current socket event bindings for cleanup
  const socketCleanupRef = useRef<() => void>(() => { });


  const currentThreadIdRef = useRef<string | null>(null);

  const [domainKeywordModal, setDomainKeywordModal] = useState<{
    open: boolean;
    data: DomainsKeywords | null;
    message?: string;
  }>({ open: false, data: null });

  const [webQueryModal, setWebQueryModal] = useState<{
    open: boolean;
    queries: string[];
  }>({ open: false, queries: [] });

  // Helper to close any approval modals that might be open
  const closeAllModals = () => {
    setDomainKeywordModal({ open: false, data: null, message: undefined });
    setWebQueryModal({ open: false, queries: [] });
  };

  useEffect(() => {
    fetchThreads();
  }, []);

  useEffect(() => {
    if (!threadId) return;
    // If we already have a selectedThread that matches and is local optimistic, skip fetching
    if (selectedThread && selectedThread.thread_id === threadId && selectedThread.local) {
      return;
    }
    fetchThread(threadId);
  }, [threadId]);

  useEffect(() => {
    currentThreadIdRef.current = threadId || null;
  }, [threadId]);


  useEffect(() => {
    if (location.pathname === '/new') {
      if (!showForm) setShowForm(true);
      if (selectedThread) setSelectedThread(null);
    } else {
      // Leaving /new should hide the form unless explicitly re-opened
      if (showForm && location.pathname !== '/new') {
        setShowForm(false);
      }
    }
  }, [location.pathname]);

  const fetchThreads = async () => {
    try {
      const data = await requestJson<{ threads: Thread[] }>(`${API_URL}/thread/all`);
      const fetched: Thread[] = data.threads || [];
      // Sort descending by created_at (most recent first). Guard against invalid dates.
      const sorted = [...fetched].sort((a, b) => {
        const aTime = a?.created_at ? new Date(a.created_at).getTime() : 0;
        const bTime = b?.created_at ? new Date(b.created_at).getTime() : 0;
        return bTime - aTime; // descending
      });
      setThreads(sorted);
    } catch (error) {
      console.error('Error fetching threads:', error);
      if (error instanceof ApiError) {
        toast.error(error.message);
      } else {
        toast.error('Failed to fetch threads');
      }
      // Close any open modals on error
      closeAllModals();
    }
  };

  const fetchThread = async (id: string) => {
    try {
      setThreadLoading(true);
      const data = await requestJson<Thread>(`${API_URL}/thread/${id}`);
      setSelectedThread(data);

      if (!data.generated) {
        setupSocketListeners(id);
        // Do NOT start initializing when navigating to an existing thread
        // Only show initialization for brand-new local thread creation
        setProgressMessages([]);
        setWorklets(workletsStore[id] || []);
      } else {
        if (data.worklets && data.worklets.length > 0) {
          setWorkletsStore(prev => ({ ...prev, [id]: data.worklets }));
          setWorklets(data.worklets);
        } else {
          // use any stored worklets if available
          setWorklets(workletsStore[id] || []);
        }
        // also restore any stored progress (may be empty)
        setProgressMessages(progressStore[id] || []);
      }
    } catch (error) {
      console.error('Error fetching thread:', error);
      if (error instanceof ApiError) {
        if (error.status === 404) {
          // Navigate to NotFound and show backend message
          toast.error(error.message || 'Thread not found');
          navigate('/not-found', { replace: true, state: { code: error.status, message: error.message, path: error.path || `/thread/${id}` } });
        } else {
          toast.error(error.message);
        }
      } else {
        toast.error('Failed to fetch thread');
      }
      // Close any open modals on error
      closeAllModals();
    }
    finally {
      setThreadLoading(false);
    }
  };

  const stopInitializing = () => {
    setIsInitializing(false);
    isInitializingRef.current = false;
    if (initTimeoutRef.current) {
      clearTimeout(initTimeoutRef.current);
      initTimeoutRef.current = null;
    }
  };

  const startInitializing = (id: string) => {
    stopInitializing();
    setIsInitializing(true);
    isInitializingRef.current = true;
    // Immediately show the placeholder message
    setProgressMessages([{ message: 'Initializing pipeline', timestamp: Date.now() }]);
    // Guard timeout to auto-hide after 10s if nothing arrives
    initTimeoutRef.current = window.setTimeout(() => {
      // Only clear if still on the same thread and still initializing
      if (currentThreadIdRef.current === id) {
        setProgressMessages([]);
        setIsInitializing(false);
        isInitializingRef.current = false;
      }
      initTimeoutRef.current = null;
    }, 10000);
  };

  const setupSocketListeners = (id: string) => {
    // Always tear down previous listeners before setting new ones
    socketCleanupRef.current?.();

    const socket = getSocket();

    const statusHandler = (data: { message: string }) => {
      const timestamp = Date.now();
      console.log(`[${new Date(timestamp).toISOString()}] Progress:`, data.message);

      // Store latest message for this thread; keep history per-thread if needed
      setProgressStore(prev => {
        const existing = prev[id] || [];
        const updated = [...existing, { message: data.message, timestamp }];
        return { ...prev, [id]: updated };
      });

      // Only update UI if we're on the same thread; keep only the last message in UI state
      if (currentThreadIdRef.current === id) {
        // First real message arrived; stop showing initialization placeholder
        if (isInitializingRef.current) {
          stopInitializing();
        }
        setProgressMessages([{ message: data.message, timestamp }]);
      }
    };

    const topicApprovalHandler = (data: DomainsKeywords & { message?: string }) => {
      console.log('Received topic approval request:', data);
      setDomainKeywordModal({ open: true, data, message: data.message });
    };

    const webApprovalHandler = (data: { queries: string[] }) => {
      console.log('Received web approval request:', data);
      setWebQueryModal({ open: true, queries: data.queries });
    };

    const fileGeneratedHandler = (data: { worklet: Worklet }) => {
      setWorkletsStore(prev => {
        const existing = prev[id] || [];
        const updated = [...existing, data.worklet];
        if (threadId === id) setWorklets(updated);
        return { ...prev, [id]: updated };
      });
    };

    socket.on(`${id}/status_update`, statusHandler);
    socket.on(`${id}/topic_approval`, topicApprovalHandler);
    socket.on(`${id}/web_approval`, webApprovalHandler);
    socket.on(`${id}/file_generated`, fileGeneratedHandler);

    // Register cleanup for these specific listeners
    socketCleanupRef.current = () => {
      try {
        socket.off(`${id}/status_update`, statusHandler);
        socket.off(`${id}/topic_approval`, topicApprovalHandler);
        socket.off(`${id}/web_approval`, webApprovalHandler);
        socket.off(`${id}/file_generated`, fileGeneratedHandler);
      } catch { }
    };
  };

  const handleNewThread = () => {
    // Navigate to /new to reflect new thread creation intent
    if (location.pathname !== '/new') {
      navigate('/new', { replace: false });
    }
    // Stop listening to any previous thread updates
    socketCleanupRef.current?.();
    stopInitializing();
    setShowForm(true);
    setSelectedThread(null);
    setProgressMessages([]);
    setWorklets([]);
  };

  const handleStartGenerating = () => {
    if (location.pathname !== '/new') {
      navigate('/new');
    }
    // Stop listening to any previous thread updates
    socketCleanupRef.current?.();
    stopInitializing();
    setShowForm(true);
  };
  function safeUUID() {
    if (typeof window !== "undefined" && window.crypto?.randomUUID) {
      return window.crypto.randomUUID();
    }
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
  }

  const handleGenerate = async (formData: any) => {
    // Preserve form data in case of failure
    const previousFormData = { ...formData };
    const newThreadId = safeUUID();

    // Optimistically create a local thread representation
    const optimisticThread = {
      thread_id: newThreadId,
      thread_name: formData.thread_name,
      custom_prompt: formData.custom_prompt,
      links: formData.links,
      // Store only filenames for optimistic UI to match Thread type and avoid rendering File objects
      files: (formData.files || []).map((f: File) => f.name),
      count: formData.count,
      generated: false,
      created_at: new Date().toISOString(),
      worklets: [] as Worklet[],
      local: true,
    };

    setSelectedThread(optimisticThread);
    // Optimistically insert at top of sidebar list
    setThreads(prev => {
      const filtered = prev.filter(t => t.thread_id !== newThreadId);
      return [optimisticThread as Thread, ...filtered];
    });
    setShowForm(false);
    setProgressMessages([]);
    setWorklets([]);
    setProgressStore(prev => ({ ...prev, [newThreadId]: [] }));
    setWorkletsStore(prev => ({ ...prev, [newThreadId]: [] }));

    // Navigate to the new thread URL
    navigate(`/thread/${newThreadId}`);

    // Start listening for updates BEFORE sending request
    setupSocketListeners(newThreadId);
    // Show initializing placeholder immediately for brand-new thread
    startInitializing(newThreadId);

    const body = new FormData();
    body.append('thread_id', newThreadId);
    body.append('thread_name', formData.thread_name);
    body.append('custom_prompt', formData.custom_prompt);
    body.append('count', formData.count.toString());
    body.append('links', JSON.stringify(formData.links));
    formData.files.forEach((file: File) => body.append('files', file));

    try {
      const data = await requestJson<{ worklets: Worklet[] }>(`${API_URL}/generate`, {
        method: 'POST',
        body,
      });
      setWorklets(data.worklets || []);
      // Mark thread as generated & not local anymore so the progress bar disappears
      setSelectedThread(prev => prev ? {
        ...prev,
        local: false,
        generated: true,
        worklets: data.worklets || prev.worklets
      } : prev);
      if (data.worklets) {
        setWorkletsStore(prev => ({ ...prev, [newThreadId]: data.worklets }));
      }
      // Hide progress box by marking thread as generated above; do not append more progress UI entries
      setProgressMessages([]);
      stopInitializing();
      fetchThreads();
      toast.success('Worklets generated successfully');
    } catch (error) {
      console.error('Error generating worklets:', error);
      if (error instanceof ApiError) {
        if (error.status === 409) {
          toast.error(error.message || 'Thread ID already exists');
        } else if (error.status === 422) {
          const hint = formatValidationDetails(error.details);
          toast.error([error.message, hint].filter(Boolean).join('\n'));
        } else {
          toast.error(error.message);
        }
      } else {
        toast.error('Failed to generate worklets');
      }

      navigate('/new', { state: { previousFormData } });
      setShowForm(true);
      setSelectedThread(null);
      setProgressMessages([]);
      stopInitializing();
      setWorklets([]);
      // Close any open modals on error
      closeAllModals();
    }
  };

  const handleSelectThread = (id: string) => {
    // If the user clicks the already selected thread, do nothing
    if (id === threadId) return;
    // Persist current thread's progress/worklets before switching
    if (selectedThread) {
      setProgressStore(prev => ({ ...prev, [selectedThread.thread_id]: progressMessages }));
      setWorkletsStore(prev => ({ ...prev, [selectedThread.thread_id]: worklets }));
    }

    setSelectedThread(null);
    setProgressMessages([]);
    setWorklets([]);
    stopInitializing();
    setThreadLoading(true);
    navigate(`/thread/${id}`);
  };

  const handleHeaderClick = () => {
    // Return to welcome screen
    navigate('/');
    // Stop listening to any previous thread updates
    socketCleanupRef.current?.();
    stopInitializing();
    setShowForm(false);
    setSelectedThread(null);
    setProgressMessages([]);
    setWorklets([]);
  };

  const handleDeleteThread = async (id: string) => {
    try {
      await requestJson(`${API_URL}/thread/delete/${id}`, { method: 'DELETE' });
      setThreads(prev => prev.filter(t => t.thread_id !== id));
      // Clean stores
      setProgressStore(prev => { const { [id]: _, ...rest } = prev; return rest; });
      setWorkletsStore(prev => { const { [id]: _, ...rest } = prev; return rest; });
      // If deleted thread is selected or currently in route, navigate away
      if (threadId === id) {
        navigate('/');
        setSelectedThread(null);
        setProgressMessages([]);
        stopInitializing();
        setWorklets([]);
      }
      toast.success('Thread deleted');
    } catch (e) {
      console.error(e);
      if (e instanceof ApiError) {
        toast.error(e.message);
      } else {
        toast.error(e instanceof Error ? e.message : 'Failed to delete thread');
      }
      // Close any open modals on error
      closeAllModals();
    }
  };

  const handleDomainKeywordSubmit = (data: DomainsKeywords) => {
    if (!threadId) return;

    const socket = getSocket();
    // Sanitize payload: remove empty/whitespace-only strings & trim duplicates (case-insensitive) preserving first occurrence
    const sanitize = (arr: string[]) => {
      const seen = new Set<string>();
      const result: string[] = [];
      for (const raw of arr) {
        if (!raw) continue;
        const trimmed = raw.trim();
        if (!trimmed) continue;
        const key = trimmed.toLowerCase();
        if (seen.has(key)) continue;
        seen.add(key);
        result.push(trimmed);
      }
      return result;
    };
    const sanitized: DomainsKeywords = {
      domains: {
        worklet: sanitize(data.domains.worklet),
        link: sanitize(data.domains.link),
        custom_prompt: sanitize(data.domains.custom_prompt),
        custom: sanitize(data.domains.custom),
      },
      keywords: {
        worklet: sanitize(data.keywords.worklet),
        link: sanitize(data.keywords.link),
        custom_prompt: sanitize(data.keywords.custom_prompt),
        custom: sanitize(data.keywords.custom),
      },
    };
    socket.emit(`${threadId}/topic_response`, sanitized);
    setDomainKeywordModal({ open: false, data: null, message: undefined });
  };

  const handleWebQuerySubmit = (queries: string[]) => {
    if (!threadId) return;

    const socket = getSocket();
    // Normalize queries more aggressively to avoid duplicates that differ only by
    // case, extra internal whitespace, or trailing punctuation like '?', '!' or '.'.
    const normalize = (q: string) =>
      q
        .trim()
        .replace(/\s+/g, ' ')            // collapse whitespace
        .replace(/[?!.,;:]+$/g, '')        // strip trailing punctuation that often varies
        .toLowerCase();                    // case-insensitive comparison

    const seen = new Set<string>();
    const cleaned = queries
      .map(q => q.trim())
      .filter(q => q.length > 0)
      .map(q => q.replace(/\s+/g, ' ')) // user-facing cleaned spacing
      .filter(original => {
        const key = normalize(original);
        if (!key) return false;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
    socket.emit(`${threadId}/web_response`, { queries: cleaned });
    setWebQueryModal({ open: false, queries: [] });
  };

  useEffect(() => {
    if (!threadId) return;
    const found = threads.find(t => t.thread_id === threadId);
    if (!found) return;

    // If thread already generated, ensure progress UI is hidden.
    if (found.generated) {
      setProgressMessages([]);
      return;
    }
    // If not generated and there are stored messages, show only the latest.
    const list = progressStore[threadId] || [];
    if (list.length > 0) {
      const last = list[list.length - 1];
      setProgressMessages([last]);
    }
  }, [threadId, progressStore, threads]);

  // On unmount, ensure we cleanup any socket listeners
  useEffect(() => {
    return () => {
      socketCleanupRef.current?.();
      // Clear any pending init timeout on unmount
      if (initTimeoutRef.current) {
        clearTimeout(initTimeoutRef.current);
        initTimeoutRef.current = null;
      }
    };
  }, []);

  return (
    <div className="flex h-screen w-full bg-background">
      <Sidebar
        threads={threads}
        onNewThread={handleNewThread}
        onSelectThread={handleSelectThread}
        selectedThreadId={threadId || null}
        onDeleteThread={handleDeleteThread}
      />

      <main className="flex-1 overflow-auto">
        <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
          <div className="p-6">
            <button
              type="button"
              onClick={handleHeaderClick}
              className="text-left focus:outline-none"
            >
              <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Worklet Generator Agent
              </h1>
            </button>
          </div>
        </header>

        <div className="p-6">
          {/* Show welcome screen only on root path ("/") with no thread selected and not in /new */}
          {!showForm && !selectedThread && location.pathname === '/' && (
            <WelcomeScreen onStartGenerating={handleStartGenerating} />
          )}

          {/* Show form when /new route is active and no thread selected */}
          {showForm && !selectedThread && location.pathname === '/new' && (
            <ThreadForm onGenerate={handleGenerate} />
          )}

          {threadLoading && (
            <div className="space-y-6">
              <CardSkeleton />
              <CardSkeleton />
            </div>
          )}
          {!threadLoading && selectedThread && (
            <>
              {!selectedThread.generated && (
                <ProgressBar messages={progressMessages} />
              )}
              <ThreadDetails
                thread={selectedThread}
                worklets={worklets}
              />
            </>
          )}
        </div>
      </main>

      {domainKeywordModal.data && (
        <DomainKeywordModal
          open={domainKeywordModal.open}
          data={domainKeywordModal.data}
          threadName={selectedThread?.thread_name}
          message={domainKeywordModal.message}
          onSubmit={handleDomainKeywordSubmit}
        />
      )}

      <WebQueryModal
        open={webQueryModal.open}
        queries={webQueryModal.queries}
        onSubmit={handleWebQuerySubmit}
      />
    </div>
  );
};

export default Index;

// Lightweight card skeleton for loading state
const CardSkeleton = () => (
  <div className="p-6 border border-border rounded-lg bg-card space-y-4 animate-pulse">
    <Skeleton className="h-6 w-1/3" />
    <div className="space-y-2">
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-4 w-1/3" />
    </div>
    <div className="grid grid-cols-2 gap-2 pt-2">
      <Skeleton className="h-9 w-full" />
      <Skeleton className="h-9 w-full" />
    </div>
  </div>
);
