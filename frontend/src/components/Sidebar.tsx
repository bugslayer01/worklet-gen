import { useState, useEffect } from 'react';
import { Plus, ChevronLeft, ChevronRight, Trash2, X } from 'lucide-react';
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
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  clusterName?: string;
}

export const Sidebar = ({ threads, onNewThread, onSelectThread, selectedThreadId, onDeleteThread, collapsed = false, onToggleCollapse, clusterName }: SidebarProps) => {
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
      className={`h-screen bg-sidebar border-r border-sidebar-border transition-smooth`}
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-4 border-b border-sidebar-border flex items-center justify-between">
          {!collapsed && (
            <div className="flex flex-col">
              <h2 className="text-lg font-semibold text-sidebar-foreground">Threads</h2>
              {clusterName && (
                <span className="text-xs text-muted-foreground mt-1 truncate max-w-[12rem]">{clusterName}</span>
              )}
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleCollapse}
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
                const isSelected = selectedThreadId === thread.thread_id;
                const threadButton = (
                  <button
                    onClick={() => onSelectThread(thread.thread_id)}
                    aria-current={isSelected ? 'true' : undefined}
                    className={`w-full text-left p-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-sidebar-ring ${!collapsed ? 'pr-10' : ''} ${
                      isSelected
                        ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold ring-1 ring-sidebar-ring border-l-4 border-sidebar-primary shadow-glow'
                        : 'hover:bg-sidebar-accent/20'
                    }`}
                  >
                    {!collapsed ? (
                      <>
                        <div className={`whitespace-normal break-words mb-1 pr-8 ${isSelected ? 'text-sidebar-accent-foreground font-semibold' : 'font-medium text-sidebar-foreground'}`}>
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
                  <div key={thread.thread_id} className="relative group min-w-0">
                    {collapsed ? (
                      <Tooltip>
                        <TooltipTrigger asChild>{threadButton}</TooltipTrigger>
                        <TooltipContent side="right">{thread.thread_name}</TooltipContent>
                      </Tooltip>
                    ) : (
                      threadButton
                    )}
                    {/* Delete button - only visible when not collapsed */}
                    {!collapsed && (
                      <AlertDialog open={pendingDelete === thread.thread_id} onOpenChange={(open) => {
                        if (open) openConfirm(thread.thread_id); else if (pendingDelete === thread.thread_id) closeConfirm();
                      }}>
                      <AlertDialogTrigger asChild>
                        <button
                          type="button"
                          onClick={(e) => { e.stopPropagation(); openConfirm(thread.thread_id); }}
                          className={`absolute top-2 right-3 inline-flex items-center justify-center rounded-md transition-smooth text-muted-foreground hover:text-destructive ${
                            collapsed ? 'w-5 h-5' : 'w-6 h-6'
                          }`}
                          aria-label="Delete thread"
                        >
                          {/* no extra padding so hover bg is symmetric; use inline-flex to center icon */}
                          <span className="flex items-center justify-center w-full h-full rounded-md hover:bg-destructive/20">
                            <X className={`${collapsed ? 'h-3 w-3' : 'h-4 w-4'}`} />
                          </span>
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
