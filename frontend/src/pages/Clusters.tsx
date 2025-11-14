import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Plus, Pencil, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useTheme } from '@/contexts/ThemeContext';
import { Sun, Moon } from 'lucide-react';
import { toast } from 'sonner';
import { API_URL, PROJECT_NAME } from '../../config';
import { ApiError, requestJson } from '@/lib/http';
import { Cluster } from '@/types/cluster';

const NEW_CLUSTER_BOX_ID = '__creating__';

const ClustersPage = () => {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();

  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [sortOption, setSortOption] = useState<'created' | 'updated' | 'alphabetical'>('updated');
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    fetchClusters();
  }, []);

  // Persist sort preference
  useEffect(() => {
    try {
      const saved = window.localStorage.getItem('clusters:sort');
      if (saved === 'created' || saved === 'updated' || saved === 'alphabetical') {
        setSortOption(saved);
      }
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    if ((creating && !editingId) || editingId) {
      const timeout = window.setTimeout(() => inputRef.current?.focus(), 10);
      return () => window.clearTimeout(timeout);
    }
    return undefined;
  }, [creating, editingId]);

  const hasNoClusters = useMemo(() => !loading && clusters.length === 0 && !creating, [loading, clusters.length, creating]);

  const fetchClusters = async () => {
    try {
      setLoading(true);
      const data = await requestJson<{ clusters: Cluster[] }>(`${API_URL}/clusters`);
      setClusters(data.clusters || []);
    } catch (error) {
      console.error('Error fetching clusters:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to load clusters';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const sortedClusters = useMemo(() => {
    const copy = [...clusters];
    if (sortOption === 'alphabetical') {
      return copy.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
    }
    if (sortOption === 'updated') {
      return copy.sort((a, b) => {
        const aTime = a.updated_at ? new Date(a.updated_at).getTime() : 0;
        const bTime = b.updated_at ? new Date(b.updated_at).getTime() : 0;
        return bTime - aTime; // most recently updated first
      });
    }
    // default: created (most recent first)
    return copy.sort((a, b) => {
      const aTime = a.created_at ? new Date(a.created_at).getTime() : 0;
      const bTime = b.created_at ? new Date(b.created_at).getTime() : 0;
      return bTime - aTime;
    });
  }, [clusters, sortOption]);

  const handleStartCreating = () => {
    setCreating(true);
    setNewName('');
    setEditingId(null);
  };

  const resetCreatingState = () => {
    setCreating(false);
    setNewName('');
  };

  const handleCreateCluster = async (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = newName.trim();
    if (!trimmed) {
      toast.error('Please enter a cluster name');
      return;
    }
    setBusyId(NEW_CLUSTER_BOX_ID);
    try {
      const created = await requestJson<Cluster>(`${API_URL}/clusters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmed }),
      });
      setClusters((prev) => [created, ...prev]);
      toast.success('Cluster created');
      resetCreatingState();
      navigate(`/cluster/${created.cluster_id}`);
    } catch (error) {
      console.error('Error creating cluster:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to create cluster';
      toast.error(message);
    } finally {
      setBusyId(null);
    }
  };

  const handleRenameClick = (cluster: Cluster) => {
    setEditingId(cluster.cluster_id);
    setEditingName(cluster.name);
    setCreating(false);
    setConfirmDeleteId(null);
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditingName('');
  };

  const handleRenameSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!editingId) return;
    const trimmed = editingName.trim();
    if (!trimmed) {
      toast.error('Please enter a cluster name');
      return;
    }
    setBusyId(editingId);
    try {
      const updated = await requestJson<Cluster>(`${API_URL}/clusters/${editingId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmed }),
      });
      setClusters((prev) => prev.map((cluster) => (cluster.cluster_id === updated.cluster_id ? updated : cluster)));
      toast.success('Cluster renamed');
      cancelEditing();
    } catch (error) {
      console.error('Error renaming cluster:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to rename cluster';
      toast.error(message);
    } finally {
      setBusyId(null);
    }
  };

  const location = useLocation();

  const handleDeleteCluster = async (clusterId: string) => {
    setBusyId(clusterId);
    try {
      await requestJson(`${API_URL}/clusters/${clusterId}`, { method: 'DELETE' });
      setClusters((prev) => prev.filter((cluster) => cluster.cluster_id !== clusterId));
      toast.success('Cluster deleted');
      if (confirmDeleteId === clusterId) setConfirmDeleteId(null);

      // If the user is currently viewing the deleted cluster, navigate back to the root
      // This avoids showing stale/404 cluster pages after deletion.
      const path = location.pathname || '';
      if (path.startsWith(`/cluster/${clusterId}`) || path === `/cluster/${clusterId}`) {
        navigate('/');
      }
    } catch (error) {
      console.error('Error deleting cluster:', error);
      const message = error instanceof ApiError ? error.message : 'Failed to delete cluster';
      toast.error(message);
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="min-h-screen w-full bg-background">
      <div className="fixed top-4 left-4 z-50">
        <img src="/prism_logo.png" alt="Prism Logo" className="h-20 w-auto" />
      </div>
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">{PROJECT_NAME}</h1>
            <p className="text-muted-foreground mt-1">Choose or create a cluster to start creating worklets.</p>
          </div>
          <div className="flex items-center gap-3">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    className="hidden sm:inline-flex"
                    onClick={handleStartCreating}
                    disabled={creating && !hasNoClusters}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add cluster
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Add a new cluster</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            {/* Sort dropdown (styled) */}
            <div className="ml-2">
              <label className="sr-only">Sort clusters</label>
              <Select value={sortOption} onValueChange={(v) => {
                const val = v as 'created' | 'updated' | 'alphabetical';
                setSortOption(val);
                try { window.localStorage.setItem('clusters:sort', val); } catch { }
              }}>
                <SelectTrigger className="w-56 sm:w-44 md:w-56">
                  <SelectValue placeholder="Sort clusters" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="alphabetical">Alphabetical (A–Z)</SelectItem>
                  <SelectItem value="created">Date created (newest)</SelectItem>
                  <SelectItem value="updated">Last updated (newest)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleStartCreating}
              className="sm:hidden"
              disabled={creating && !hasNoClusters}
              aria-label="Add cluster"
            >
              <Plus className="h-5 w-5" />
            </Button>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" onClick={toggleTheme}>
                    {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Switch to {theme === 'dark' ? 'light' : 'dark'} mode</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12">
        {hasNoClusters && (
          <div className="flex flex-col items-center justify-center py-24 gap-6">
            <p className="text-lg text-muted-foreground">No clusters yet. Create your first cluster to get started.</p>
            <Button
              size="lg"
              className="gradient-primary shadow-glow px-10 py-6 text-lg"
              onClick={handleStartCreating}
            >
              <Plus className="mr-2 h-5 w-5" />
              Add cluster
            </Button>
          </div>
        )}

        <div className="grid gap-8 justify-center" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))' }}>
          {creating && (
            <Card className="relative h-80 w-60 mx-auto flex flex-col justify-between border-dashed border-2 border-primary/60 overflow-hidden">
              {/* subtle, semi-transparent gradient overlay (less opaque than full gradient) */}
              <div
                aria-hidden
                className="absolute inset-0"
                style={{ background: 'linear-gradient(135deg, hsl(var(--primary) / 0.75), hsl(var(--accent) / 0.55))', pointerEvents: 'none' }}
              />
              <div className="relative z-10 flex flex-1 flex-col">
                <form onSubmit={handleCreateCluster} className="flex flex-1 flex-col">
                  <div className="p-6 flex-1 flex flex-col gap-4">
                    <h2 className="text-lg font-semibold text-primary-foreground">New cluster</h2>
                  <Input
                    ref={inputRef}
                    value={newName}
                    onChange={(event) => setNewName(event.target.value)}
                    placeholder="Cluster name"
                    className="bg-input border-border"
                    disabled={busyId === NEW_CLUSTER_BOX_ID}
                  />
                </div>
                <div className="p-6 pt-0 space-y-3">
                  <Button
                    type="submit"
                    className="w-full gradient-primary"
                    disabled={busyId === NEW_CLUSTER_BOX_ID}
                  >
                    Create cluster
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    className="w-full"
                    onClick={resetCreatingState}
                    disabled={busyId === NEW_CLUSTER_BOX_ID}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
              </div>
            </Card>
          )}

          {sortedClusters.map((cluster) => {
            const isEditing = editingId === cluster.cluster_id;
            const handleOpenCluster = () => {
              // If any delete confirmation is open, don't navigate — clicking outside the
              // dialog should dismiss it, not cause navigation into the card below.
              if (isEditing || confirmDeleteId) return;
              navigate(`/cluster/${cluster.cluster_id}`);
            };
            const handleKeyActivate = (event: KeyboardEvent<HTMLDivElement>) => {
              if (isEditing || confirmDeleteId || event.target !== event.currentTarget) return;
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                handleOpenCluster();
              }
            };

            return (
              <Card
                key={cluster.cluster_id}
                role={isEditing ? undefined : 'button'}
                tabIndex={isEditing ? -1 : 0}
                onClick={handleOpenCluster}
                onKeyDown={handleKeyActivate}
                // Ensure the card hides overflow and allows inner flex children to constrain height
                className={`relative h-80 w-60 mx-auto flex flex-col items-center justify-center border-border transition-smooth focus:outline-none focus:ring-2 focus:ring-primary/50 overflow-hidden ${isEditing ? '' : 'hover:brightness-105 cursor-pointer'}`}
              >
                {/* toned-down semi-transparent gradient overlay */}
                <div
                  aria-hidden
                  className="absolute inset-0"
                  style={{ background: 'linear-gradient(135deg, hsl(var(--primary) / 0.7), hsl(var(--accent) / 0.5))', pointerEvents: 'none' }}
                />
                <div className="relative z-10 flex-1 flex flex-col items-center justify-center w-full">
                <div className="absolute top-3 right-3 flex items-center gap-2">
                  <button
                    type="button"
                    className="rounded-full p-2 text-white hover:bg-muted/20 transition-smooth"
                    onClick={(event) => {
                      event.stopPropagation();
                      handleRenameClick(cluster);
                    }}
                    aria-label="Rename cluster"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <AlertDialog open={confirmDeleteId === cluster.cluster_id} onOpenChange={(open) => setConfirmDeleteId(open ? cluster.cluster_id : null)}>
                    <AlertDialogTrigger asChild>
                      <button
                        type="button"
                        className="rounded-full p-2 text-white hover:bg-destructive/10 transition-smooth"
                        onClick={(event) => {
                          event.stopPropagation();
                          setConfirmDeleteId(cluster.cluster_id);
                        }}
                        aria-label="Delete cluster"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete cluster</AlertDialogTitle>
                        <AlertDialogDescription>
                          Deleting this cluster will remove all threads associated with it. This action cannot be undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                          onClick={(e: React.MouseEvent) => {
                            // Prevent this click from bubbling to the underlying card which
                            // would trigger navigation to the cluster page.
                            e.stopPropagation();
                            handleDeleteCluster(cluster.cluster_id);
                          }}
                          disabled={busyId === cluster.cluster_id}
                        >
                          Delete
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>

                {isEditing ? (
                  <form
                    onSubmit={handleRenameSubmit}
                    onClick={(event) => event.stopPropagation()}
                    className="flex flex-1 min-h-0 flex-col items-center justify-center gap-4 px-6 text-center w-full"
                  >
                    <Input
                      ref={inputRef}
                      value={editingName}
                      onChange={(event) => setEditingName(event.target.value)}
                      className="bg-input border-border"
                      disabled={busyId === cluster.cluster_id}
                    />
                    <div className="w-full space-y-3">
                      <Button type="submit" className="w-full" disabled={busyId === cluster.cluster_id}>Save</Button>
                      <Button type="button" variant="ghost" className="w-full" onClick={cancelEditing} disabled={busyId === cluster.cluster_id}>Cancel</Button>
                    </div>
                  </form>
                ) : (
                  // The outer flex child must allow its children to shrink (min-h-0) so the inner
                  // scroll container can constrain its height. The scroll container then uses
                  // overflow-y-auto to keep long names inside the card.
                  <div className="flex-1 min-h-0 flex flex-col items-center justify-center px-6 text-center w-full">
                    <div className="min-h-0 max-h-full w-full overflow-y-auto">
                        <h2 className="text-xl font-semibold text-primary-foreground break-words whitespace-pre-wrap leading-snug">{cluster.name}</h2>
                      </div>
                  </div>
                )}
                  </div>
                </Card>
            );
          })}
        </div>
      </main>
    </div>
  );
};

export default ClustersPage;
