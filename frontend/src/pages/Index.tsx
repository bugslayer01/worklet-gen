import { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { Sidebar } from '@/components/Sidebar';
import { WelcomeScreen } from '@/components/WelcomeScreen';
import { ThreadForm } from '@/components/ThreadForm';
import { ProgressBar } from '@/components/ProgressBar';
import { DomainKeywordModal } from '@/components/DomainKeywordModal';
import { WebQueryModal } from '@/components/WebQueryModal';
import { ThreadDetails } from '@/components/ThreadDetails';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/resizable';
import { Thread, DomainsKeywords, ProgressMessage, ThreadApiResponse, WorkletPayload, WorkletWithIterations } from '@/types/thread';
import { Cluster } from '@/types/cluster';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip';
import { getSocket } from '@/lib/socket';
import { toast } from 'sonner';
import { API_URL, PROJECT_NAME } from '../../config';
import { ApiError, requestJson, formatValidationDetails } from '@/lib/http';
import { normalizeThreadResponse, ensureWorkletBundle } from '@/lib/worklet';
import { useTheme } from '@/contexts/ThemeContext';
import { Sun, Moon, ArrowLeft } from 'lucide-react';

const Index = () => {
  const navigate = useNavigate();
  const { clusterId, threadId } = useParams<{ clusterId?: string; threadId?: string }>();
  const location = useLocation();
  const isNewRoute = location.pathname.endsWith('/new');
  const { theme, toggleTheme } = useTheme();

  const [threads, setThreads] = useState<Thread[]>([]);
  const [selectedThread, setSelectedThread] = useState<Thread | null>(null);
  const [threadLoading, setThreadLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [progressMessages, setProgressMessages] = useState<ProgressMessage[]>([]);
  const [worklets, setWorklets] = useState<WorkletWithIterations[]>([]);
  const [clusterName, setClusterName] = useState<string>('');
  const [clusterLoading, setClusterLoading] = useState<boolean>(true);
  const [clusterError, setClusterError] = useState<string | null>(null);
  // Initialization placeholder state for brand-new thread creation
  const [isInitializing, setIsInitializing] = useState<boolean>(false);
  const isInitializingRef = useRef<boolean>(false);
  const initTimeoutRef = useRef<number | null>(null);
  // Stores to preserve per-thread progress & worklets when user navigates away
  const [progressStore, setProgressStore] = useState<Record<string, ProgressMessage[]>>({});
  const [workletsStore, setWorkletsStore] = useState<Record<string, WorkletWithIterations[]>>({});
  // Keep track of current socket event bindings for cleanup
  const socketCleanupRef = useRef<() => void>(() => { });

  // Resizable panels state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [layout, setLayout] = useState([19, 81]); // [left, middle] percentages
  const [containerWidth, setContainerWidth] = useState(window.innerWidth);
  const containerRef = useRef<HTMLDivElement>(null);
  const leftPanelRef = useRef<any>(null);
  const middlePanelRef = useRef<any>(null);
  const prevSidebarSizeRef = useRef<number>(19);

  const currentThreadIdRef = useRef<string | null>(null);

  const [domainKeywordModal, setDomainKeywordModal] = useState<{
    open: boolean;
    data: DomainsKeywords | null;
    message?: string;
    threadId?: string;
  }>({ open: false, data: null, threadId: undefined });

  const [webQueryModal, setWebQueryModal] = useState<{
    open: boolean;
    queries: string[];
    threadId?: string;
  }>({ open: false, queries: [], threadId: undefined });

  // Helper to close any approval modals that might be open
  const closeAllModals = () => {
  setDomainKeywordModal({ open: false, data: null, message: undefined, threadId: undefined });
  setWebQueryModal({ open: false, queries: [], threadId: undefined });
  };

  useEffect(() => {
    if (!clusterId) {
      setClusterLoading(false);
      setClusterError('Cluster not specified.');
      setThreads([]);
      setSelectedThread(null);
      return;
    }
    setThreads([]);
    setSelectedThread(null);
    setProgressMessages([]);
    setWorklets([]);
  setProgressStore({});
  setWorkletsStore({});
    socketCleanupRef.current?.();
    stopInitializing();
    closeAllModals();
    fetchCluster(clusterId);
  }, [clusterId]);

  useEffect(() => {
    if (!clusterId || clusterError) {
      return;
    }
    fetchThreads(clusterId);
  }, [clusterId, clusterError]);

  // Update container width on resize
  useEffect(() => {
    const updateWidth = () => {
      setContainerWidth(window.innerWidth);
    };
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  useEffect(() => {
    if (leftPanelRef.current) {
      leftPanelRef.current.resize(19);
    }
  }, []);

  // Calculate collapsed width in percent
  const collapsedPercent = useMemo(() => {
    const width = containerWidth;
    const collapsedPx = 64;
    const percent = (collapsedPx / Math.max(1, width)) * 100;
    return Math.max(2, Math.min(20, percent));
  }, [containerWidth]);

  // Toggle sidebar collapse
  const toggleSidebar = () => {
    if (sidebarCollapsed) {
      // Expand
      leftPanelRef.current?.resize(prevSidebarSizeRef.current);
      setSidebarCollapsed(false);
    } else {
      // Collapse
      prevSidebarSizeRef.current = layout[0];
      leftPanelRef.current?.resize(collapsedPercent);
      setSidebarCollapsed(true);
    }
  };

  // Toggle right panel collapse
  // Handle layout changes
  const handleLayout = (sizes: number[]) => {
    setLayout(sizes);
    localStorage.setItem('dashboard:sidebar:layout', JSON.stringify(sizes));
  };

  useEffect(() => {
    if (!threadId || !clusterId || clusterError) return;
    // If we already have a selectedThread that matches and is local optimistic, skip fetching
    if (selectedThread && selectedThread.thread_id === threadId && selectedThread.local) {
      return;
    }
    fetchThread(threadId);
  }, [threadId, clusterId, clusterError]);

  useEffect(() => {
    currentThreadIdRef.current = threadId || null;
  }, [threadId]);


  useEffect(() => {
    if (isNewRoute) {
      if (!showForm) setShowForm(true);
      if (selectedThread) setSelectedThread(null);
    } else if (showForm) {
      setShowForm(false);
    }
  }, [isNewRoute, showForm, selectedThread]);

  const fetchCluster = async (id: string) => {
    try {
      setClusterLoading(true);
      setClusterError(null);
  const cluster = await requestJson<Cluster>(`${API_URL}/clusters/${id}`);
  setClusterName(cluster.name || id);
      setClusterError(null);
    } catch (error) {
      console.error('Error fetching cluster:', error);
      if (error instanceof ApiError) {
        setClusterError(error.message);
        toast.error(error.message);
      } else {
        setClusterError('Failed to load cluster information');
        toast.error('Failed to load cluster information');
      }
      setClusterName('');
      setThreads([]);
      setSelectedThread(null);
    } finally {
      setClusterLoading(false);
    }
  };

  const fetchThreads = async (targetClusterId?: string) => {
    const resolvedClusterId = targetClusterId ?? clusterId;
    if (!resolvedClusterId) {
      return;
    }
    try {
      const data = await requestJson<{ threads: ThreadApiResponse[] }>(`${API_URL}/thread/all?cluster_id=${encodeURIComponent(resolvedClusterId)}`);
      const fetched: ThreadApiResponse[] = data.threads || [];
      const normalized = fetched.map(normalizeThreadResponse);
      // Sort descending by created_at (most recent first). Guard against invalid dates.
      const sorted = [...normalized].sort((a, b) => {
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
      const apiThread = await requestJson<ThreadApiResponse>(`${API_URL}/thread/${id}`);
      const normalizedThread = normalizeThreadResponse(apiThread);
      if (normalizedThread.cluster_id && clusterId && normalizedThread.cluster_id !== clusterId) {
        toast.error('Thread belongs to a different cluster. Redirecting.');
        navigate(`/cluster/${normalizedThread.cluster_id}/thread/${id}`, { replace: true });
        return;
      }
      setSelectedThread(normalizedThread);

      if (!normalizedThread.generated) {
        setupSocketListeners(id);
        // Do NOT start initializing when navigating to an existing thread
        // Only show initialization for brand-new local thread creation
        setProgressMessages([]);
        setWorklets(workletsStore[id] || []);
      } else {
        if (normalizedThread.worklets && normalizedThread.worklets.length > 0) {
          setWorkletsStore(prev => ({ ...prev, [id]: normalizedThread.worklets }));
          setWorklets(normalizedThread.worklets);
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
  setDomainKeywordModal({ open: true, data, message: data.message, threadId: id });
    };

    const webApprovalHandler = (data: { queries: string[] }) => {
      console.log('Received web approval request:', data);
      setWebQueryModal({ open: true, queries: data.queries, threadId: id });
    };

    const fileGeneratedHandler = (data: { worklet: WorkletPayload }) => {
      const normalized = ensureWorkletBundle(data.worklet);
      setWorkletsStore(prev => {
        const existing = prev[id] || [];
        const updated = [...existing, normalized];
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
    if (clusterError) {
      toast.error(clusterError);
      return;
    }
    if (!clusterId) {
      toast.error('Select a cluster before creating a thread');
      return;
    }
    const creationPath = `/cluster/${clusterId}/new`;
    if (location.pathname !== creationPath) {
      navigate(creationPath, { replace: false });
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
    if (clusterError) {
      toast.error(clusterError);
      return;
    }
    if (!clusterId) {
      toast.error('Select a cluster before creating a thread');
      return;
    }
    const creationPath = `/cluster/${clusterId}/new`;
    if (location.pathname !== creationPath) {
      navigate(creationPath);
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
    if (clusterError) {
      toast.error(clusterError);
      return;
    }
    if (!clusterId) {
      toast.error('Select a cluster before generating worklets');
      return;
    }
    // Preserve form data in case of failure
    const previousFormData = { ...formData };
    const newThreadId = safeUUID().replace(/-/g, '').slice(0, 7);

    // Optimistically create a local thread representation
    const optimisticThread: Thread = {
      thread_id: newThreadId,
      thread_name: formData.thread_name,
      cluster_id: clusterId,
      custom_prompt: formData.custom_prompt,
      links: formData.links,
      // Store only filenames for optimistic UI to match Thread type and avoid rendering File objects
      files: (formData.files || []).map((f: File) => f.name),
      count: formData.count,
      generated: false,
      created_at: new Date().toISOString(),
      worklets: [],
      local: true,
    };

    setSelectedThread(optimisticThread);
    // Optimistically insert at top of sidebar list
    setThreads(prev => {
      const filtered = prev.filter(t => t.thread_id !== newThreadId);
      return [optimisticThread, ...filtered];
    });
    setShowForm(false);
    setProgressMessages([]);
    setWorklets([]);
    setProgressStore(prev => ({ ...prev, [newThreadId]: [] }));
    setWorkletsStore(prev => ({ ...prev, [newThreadId]: [] }));

    // Navigate to the new thread URL
  navigate(`/cluster/${clusterId}/thread/${newThreadId}`);

    // Start listening for updates BEFORE sending request
    setupSocketListeners(newThreadId);
    // Show initializing placeholder immediately for brand-new thread
    startInitializing(newThreadId);

    const body = new FormData();
    body.append('thread_id', newThreadId);
    body.append('thread_name', formData.thread_name);
  body.append('cluster_id', clusterId);
    body.append('custom_prompt', formData.custom_prompt);
    body.append('count', formData.count.toString());
    body.append('links', JSON.stringify(formData.links));
    formData.files.forEach((file: File) => body.append('files', file));

    try {
      await requestJson<{ worklets: WorkletPayload[] }>(`${API_URL}/generate`, {
        method: 'POST',
        body,
      });
      // Mark thread as generated & not local so the progress bar disappears while we refetch canonical data
      setSelectedThread(prev => prev ? {
        ...prev,
        local: false,
        generated: true,
      } : prev);
      // Hide progress box by marking thread as generated above; do not append more progress UI entries
      setProgressMessages([]);
      stopInitializing();
  fetchThreads(clusterId);
      toast.success('Worklets generated successfully');
      await fetchThread(newThreadId);
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

      navigate(`/cluster/${clusterId}/new`, { state: { previousFormData } });
      setShowForm(true);
      setSelectedThread(null);
      setProgressMessages([]);
      stopInitializing();
      setWorklets([]);
      // Close any open modals on error
      closeAllModals();
    }
  };

  const handleWorkletUpdate = (updatedWorklet: WorkletWithIterations) => {
    let nextWorklets: WorkletWithIterations[] = [];
    setWorklets((prev) => {
      const exists = prev.some((worklet) => worklet.worklet_id === updatedWorklet.worklet_id);
      nextWorklets = exists
        ? prev.map((worklet) =>
            worklet.worklet_id === updatedWorklet.worklet_id ? updatedWorklet : worklet,
          )
        : [...prev, updatedWorklet];
      return nextWorklets;
    });

    const activeThreadId = selectedThread?.thread_id;
    if (!activeThreadId) {
      return;
    }

    if (nextWorklets.length === 0) {
      nextWorklets = [updatedWorklet];
    }

    setWorkletsStore((prev) => ({
      ...prev,
      [activeThreadId]: nextWorklets,
    }));

    setSelectedThread((prev) =>
      prev ? { ...prev, worklets: nextWorklets } : prev,
    );

    setThreads((prev) =>
      prev.map((thread) =>
        thread.thread_id === activeThreadId
          ? { ...thread, worklets: nextWorklets }
          : thread,
      ),
    );
  };

  const handleSelectThread = (id: string) => {
    if (clusterError) {
      toast.error(clusterError);
      return;
    }
    if (!clusterId) {
      toast.error('Select a cluster first');
      return;
    }
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
    navigate(`/cluster/${clusterId}/thread/${id}`);
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
        if (clusterId) {
          navigate(`/cluster/${clusterId}`);
        } else {
          navigate('/');
        }
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
    const targetThreadId = domainKeywordModal.threadId ?? threadId;
    if (!targetThreadId) {
      console.warn('Unable to emit topic response: missing target thread id');
      return;
    }

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
    socket.emit(`${targetThreadId}/topic_response`, sanitized);
    setDomainKeywordModal({ open: false, data: null, message: undefined, threadId: undefined });
  };

  const handleWebQuerySubmit = (queries: string[]) => {
    const targetThreadId = webQueryModal.threadId ?? threadId;
    if (!targetThreadId) {
      console.warn('Unable to emit web response: missing target thread id');
      return;
    }

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
    socket.emit(`${targetThreadId}/web_response`, { queries: cleaned });
    setWebQueryModal({ open: false, queries: [], threadId: undefined });
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

  const modalThreadName = domainKeywordModal.threadId
    ? threads.find(t => t.thread_id === domainKeywordModal.threadId)?.thread_name
    : selectedThread?.thread_name;

  return (
    <div ref={containerRef} className="h-screen w-full bg-background">
      <ResizablePanelGroup direction="horizontal" onLayout={handleLayout}>
        <ResizablePanel
          ref={leftPanelRef}
          defaultSize={layout[0]}
          minSize={sidebarCollapsed ? collapsedPercent : 19}
          maxSize={sidebarCollapsed ? collapsedPercent : 40}
        >
          <Sidebar
            threads={threads}
            onNewThread={handleNewThread}
            onSelectThread={handleSelectThread}
            selectedThreadId={threadId || null}
            onDeleteThread={handleDeleteThread}
            collapsed={sidebarCollapsed}
            onToggleCollapse={toggleSidebar}
            clusterName={clusterName || clusterId || ''}
          />
        </ResizablePanel>
        <ResizableHandle withHandle={!sidebarCollapsed} />
        <ResizablePanel
          ref={middlePanelRef}
          defaultSize={layout[1]}
          minSize={40}
        >
          <main className="h-full overflow-auto">
        <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
          <div className="p-6 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-6">
              <img src="/prism_logo.png" alt="Prism Logo" className="h-16 w-auto" />
              <button
                type="button"
                onClick={handleHeaderClick}
                className="text-left focus:outline-none"
              >
                <h1 className="text-3xl font-bold text-foreground">
                  {PROJECT_NAME}
                </h1>
              </button>
              <div className="flex flex-col">
                <span className="text-xs uppercase tracking-wide text-muted-foreground">Cluster</span>
                <span className="text-lg font-semibold text-foreground">
                  {clusterLoading ? 'Loading...' : clusterError ? 'Unavailable' : clusterName || clusterId || 'Unknown'}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={handleHeaderClick} className="hidden sm:inline-flex">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Clusters
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleHeaderClick}
                className="sm:hidden"
                aria-label="Back to clusters"
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={toggleTheme}
                      className="ml-0"
                    >
                      {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    Switch to {theme === 'dark' ? 'light' : 'dark'} mode
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        </header>

        <div className="p-6">
          {clusterError && (
            <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
              <p className="text-lg text-destructive">{clusterError}</p>
              <Button variant="outline" onClick={handleHeaderClick}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to clusters
              </Button>
            </div>
          )}

          {!clusterError && clusterId && showForm && !selectedThread && isNewRoute && (
            <ThreadForm onGenerate={handleGenerate} clusterName={clusterName || clusterId || ''} />
          )}

          {!clusterError && clusterId && !showForm && !selectedThread && !threadId && !clusterLoading && (
            <WelcomeScreen onStartGenerating={handleStartGenerating} />
          )}

          {!clusterError && clusterLoading && !selectedThread && !showForm && (
            <div className="py-24 text-center text-muted-foreground">Loading threads...</div>
          )}

          {threadLoading && !clusterError && (
            <div className="space-y-6">
              <CardSkeleton />
              <CardSkeleton />
            </div>
          )}
          {!threadLoading && !clusterError && selectedThread && (
            <>
              {!selectedThread.generated && (
                <ProgressBar messages={progressMessages} />
              )}
              <ThreadDetails
                thread={selectedThread}
                worklets={worklets}
                onUpdateWorklet={handleWorkletUpdate}
                clusterName={clusterName || clusterId || ''}
              />
            </>
          )}
            </div>
          </main>
        </ResizablePanel>
      </ResizablePanelGroup>

      {domainKeywordModal.data && (
        <DomainKeywordModal
          open={domainKeywordModal.open}
          data={domainKeywordModal.data}
          threadName={modalThreadName}
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
