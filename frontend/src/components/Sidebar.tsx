import { useState, useEffect } from 'react';
import { Plus, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Thread } from '@/types/thread';
import { formatDistanceToNow } from 'date-fns';
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from '@/components/ui/alert-dialog';
import { useCallback, useState as useReactState } from 'react';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip';

interface SidebarProps {
  threads: Thread[];
  onNewThread: () => void;
  onSelectThread: (threadId: string) => void;
  selectedThreadId: string | null;
  onDeleteThread: (threadId: string) => Promise<void> | void;
}

export const Sidebar = ({ threads, onNewThread, onSelectThread, selectedThreadId, onDeleteThread }: SidebarProps) => {
  const [collapsed, setCollapsed] = useState(false);
  const [pendingDelete, setPendingDelete] = useReactState<string | null>(null);

  const openConfirm = useCallback((id: string) => {
    setPendingDelete(id);
  }, []);

  const closeConfirm = useCallback(() => setPendingDelete(null), []);

  const confirmDelete = useCallback(async () => {
    if (!pendingDelete) return;
    await onDeleteThread(pendingDelete);
    setPendingDelete(null);
  }, [pendingDelete, onDeleteThread]);

  return (
    <div
      className={`h-screen bg-sidebar border-r border-sidebar-border transition-smooth ${
        collapsed ? 'w-16' : 'w-72'
      }`}
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-4 border-b border-sidebar-border flex items-center justify-between">
          {!collapsed && (
            <h2 className="text-lg font-semibold text-sidebar-foreground">Threads</h2>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(!collapsed)}
            className="ml-auto"
          >
            {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
          </Button>
        </div>

        {/* New Thread Button */}
        <div className="p-4">
          <Button
            onClick={onNewThread}
            className="w-full gradient-primary hover:opacity-90 transition-smooth shadow-glow"
            size={collapsed ? 'icon' : 'default'}
          >
            <Plus className="h-5 w-5" />
            {!collapsed && <span className="ml-2">New Thread</span>}
          </Button>
        </div>

        {/* Thread List */}
        <ScrollArea className="flex-1">
          <div className="space-y-2 p-4">
            <TooltipProvider>
              {threads.map((thread) => {
                const threadButton = (
                  <button
                    onClick={() => onSelectThread(thread.thread_id)}
                    className={`w-full text-left p-3 rounded-lg transition-smooth ${!collapsed ? 'pr-10' : ''} ${
                      selectedThreadId === thread.thread_id
                        ? 'bg-sidebar-accent shadow-glow'
                        : 'hover:bg-sidebar-accent/50'
                    } ${collapsed ? 'px-2 pr-2' : ''}`}
                  >
                    {!collapsed ? (
                      <>
                        <div className="font-medium text-sidebar-foreground truncate">
                          {thread.thread_name}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Created {formatDistanceToNow(new Date(thread.created_at), { addSuffix: true })}
                        </div>
                      </>
                    ) : (
                      <div className="w-full h-8 flex items-center justify-center">
                        <div className="w-2 h-2 rounded-full bg-primary" />
                      </div>
                    )}
                  </button>
                );
                return (
                  <div key={thread.thread_id} className="relative group">
                    {collapsed ? (
                      <Tooltip>
                        <TooltipTrigger asChild>{threadButton}</TooltipTrigger>
                        <TooltipContent side="right">{thread.thread_name}</TooltipContent>
                      </Tooltip>
                    ) : (
                      threadButton
                    )}
                    {/* Delete button (only when expanded) */}
                    {!collapsed && (
                      <AlertDialog open={pendingDelete === thread.thread_id} onOpenChange={(open) => {
                        if (open) openConfirm(thread.thread_id); else if (pendingDelete === thread.thread_id) closeConfirm();
                      }}>
                        <AlertDialogTrigger asChild>
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); openConfirm(thread.thread_id); }}
                            className="absolute top-1.5 right-2 p-1 rounded hover:bg-destructive/20 text-muted-foreground hover:text-destructive transition-smooth"
                            aria-label="Delete thread"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete Thread</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to delete "{thread.thread_name}"? This action cannot be undone and all generated worklets for this thread will be lost.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel onClick={closeConfirm}>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={confirmDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">Delete</AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    )}
                  </div>
                );
              })}
            </TooltipProvider>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
};
