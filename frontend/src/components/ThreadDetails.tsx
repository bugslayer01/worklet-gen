import { type ReactNode, useEffect, useMemo, useState } from 'react';
import {
  Check,
  ChevronLeft,
  ChevronRight,
  Download,
  FileIcon,
  Loader2,
  Pencil,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  ArrayAttribute,
  EnhanceWorkletResponse,
  IterateWorkletResponse,
  ObjectAttribute,
  SelectIterationResponse,
  SelectWorkletIterationResponse,
  StringAttribute,
  Thread,
  WorkletFieldKey,
  WorkletIteration,
  WorkletWithIterations,
} from '@/types/thread';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { API_URL } from '../../config';
import { toast } from 'sonner';
import {
  ApiError,
  ensureOk,
  requestBlob,
  requestJson,
} from '@/lib/http';
import {
  clampToIterations,
  clampWorkletIterationIndex,
  ensureWorkletBundle,
  ensureWorkletIteration,
  getArrayIteration,
  getDefaultWorkletIteration,
  getIterationCount,
  getObjectIteration,
  getSelectedIndex,
  getStringIteration,
  getWorkletIterationAt,
  getWorkletIterationCount,
} from '@/lib/worklet';

interface ThreadDetailsProps {
  thread: Thread;
  worklets: WorkletWithIterations[];
  onUpdateWorklet: (worklet: WorkletWithIterations) => void;
  clusterName?: string;
}

type FieldType = 'string' | 'array' | 'object';

interface FieldConfig {
  key: WorkletFieldKey;
  label: string;
  type: FieldType;
}

const FIELD_CONFIGS: FieldConfig[] = [
  { key: 'title', label: 'Title', type: 'string' },
  { key: 'problem_statement', label: 'Problem Statement', type: 'string' },
  { key: 'description', label: 'Description', type: 'string' },
  { key: 'challenge_use_case', label: 'Challenge / Use Case', type: 'string' },
  { key: 'deliverables', label: 'Deliverables', type: 'array' },
  { key: 'kpis', label: 'KPIs', type: 'array' },
  { key: 'prerequisites', label: 'Prerequisites', type: 'array' },
  {
    key: 'infrastructure_requirements',
    label: 'Infrastructure Requirements',
    type: 'string',
  },
  { key: 'tech_stack', label: 'Tech Stack', type: 'string' },
  { key: 'milestones', label: 'Milestones', type: 'object' },
];

const DEFAULT_FIELD_PROMPT_STATE = {
  open: false,
  field: null as WorkletFieldKey | null,
  prompt: '',
  iterationIndex: 0,
};

const computeInitialIndices = (
  iteration: WorkletIteration,
): Record<WorkletFieldKey, number> => {
  return FIELD_CONFIGS.reduce((acc, field) => {
    const attr = iteration[field.key];
    acc[field.key] = getSelectedIndex(attr);
    return acc;
  }, {} as Record<WorkletFieldKey, number>);
};

const getAttribute = (
  iteration: WorkletIteration,
  key: WorkletFieldKey,
): StringAttribute | ArrayAttribute | ObjectAttribute => iteration[key];

export const ThreadDetails = ({ thread, worklets, onUpdateWorklet, clusterName }: ThreadDetailsProps) => {
  const [activeWorkletId, setActiveWorkletId] = useState<string | null>(null);
  const [activeIterationIndex, setActiveIterationIndex] = useState(0);
  const [fieldViewIndices, setFieldViewIndices] = useState<Record<WorkletFieldKey, number>>({} as Record<WorkletFieldKey, number>);
  const [selectingField, setSelectingField] = useState<WorkletFieldKey | null>(null);
  const [iteratingField, setIteratingField] = useState<WorkletFieldKey | null>(null);
  const [fieldPromptState, setFieldPromptState] = useState(DEFAULT_FIELD_PROMPT_STATE);
  const [enhanceDialogOpen, setEnhanceDialogOpen] = useState(false);
  const [enhancePrompt, setEnhancePrompt] = useState('');
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [defaultSelecting, setDefaultSelecting] = useState(false);

  const activeWorklet = useMemo(
    () => worklets.find((w) => w.worklet_id === activeWorkletId) ?? null,
    [worklets, activeWorkletId],
  );

  useEffect(() => {
    if (!activeWorklet) {
      setActiveIterationIndex(0);
      setFieldViewIndices({} as Record<WorkletFieldKey, number>);
      return;
    }

    const defaultIndex = clampWorkletIterationIndex(
      activeWorklet,
      activeWorklet.selected_iteration_index,
    );
    setActiveIterationIndex(defaultIndex);
  }, [activeWorklet?.worklet_id, activeWorklet?.selected_iteration_index]);

  const activeIteration = useMemo(() => {
    if (!activeWorklet) return null;
    return getWorkletIterationAt(activeWorklet, activeIterationIndex);
  }, [activeWorklet, activeIterationIndex]);

  useEffect(() => {
    if (!activeIteration) return;
    setFieldViewIndices(computeInitialIndices(activeIteration));
  }, [activeIteration?.iteration_id]);

  const isDialogOpen = Boolean(activeWorklet);
  const isIterating = iteratingField !== null;

  const totalWorkletIterations = activeWorklet ? getWorkletIterationCount(activeWorklet) : 0;

  const getViewIndex = (key: WorkletFieldKey): number => {
    if (!activeIteration) return 0;
    const attr = getAttribute(activeIteration, key);
    const fallback = getSelectedIndex(attr);
    const requested = fieldViewIndices[key];
    return clampToIterations(attr, typeof requested === 'number' ? requested : fallback);
  };

  const closeFieldPrompt = () => {
    if (isIterating) return;
    setFieldPromptState(DEFAULT_FIELD_PROMPT_STATE);
  };

  const handleDialogOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) {
      if (isIterating || isEnhancing) return;
      setActiveWorkletId(null);
      setFieldPromptState(DEFAULT_FIELD_PROMPT_STATE);
      setEnhanceDialogOpen(false);
      setEnhancePrompt('');
    }
  };

  const handleOpenWorklet = (worklet: WorkletWithIterations) => {
    setActiveWorkletId(worklet.worklet_id);
    const defaultIndex = clampWorkletIterationIndex(
      worklet,
      worklet.selected_iteration_index,
    );
    setActiveIterationIndex(defaultIndex);
  };

  const getActiveTitle = (): string => {
    if (!activeIteration) return '';
    const index = getViewIndex('title');
    const value = getStringIteration(activeIteration.title, index).trim();
    return value.length > 0 ? value : 'Worklet';
  };

  const sanitizeFilename = (raw: string): string => {
    const safe = raw.replace(/[\\/:*?"<>|]/g, '-').trim();
    return safe.length > 0 ? safe : 'worklet';
  };

  const handleDownload = async (type: 'pdf' | 'pptx') => {
    if (!activeWorklet) return;
    try {
      const blob = await requestBlob(
        `${API_URL}/thread/${thread.thread_id}/download/${activeWorklet.worklet_id}/${type}`,
      );
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${sanitizeFilename(getActiveTitle())}.${type}`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`${type.toUpperCase()} downloaded`);
    } catch (error) {
      console.error(error);
      if (error instanceof ApiError) {
        toast.error(error.message);
      } else {
        toast.error(error instanceof Error ? error.message : 'Download failed');
      }
    }
  };

  const handleDownloadAll = async (type: 'pdf' | 'pptx') => {
    try {
      const response = await fetch(`${API_URL}/thread/${thread.thread_id}/download/all/${type}`);
      await ensureOk(response);
      const blob = await response.blob();
      const disposition = response.headers.get('Content-Disposition');
      let suggestedName = disposition?.match(/filename="?([^";]+)"?/i)?.[1];
      if (!suggestedName) {
        suggestedName = `worklets-${type}-bundle.zip`;
      } else if (!/\.zip$/i.test(suggestedName)) {
        suggestedName = suggestedName.replace(/\.[^.]+$/, '') + '.zip';
      }
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = suggestedName;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`ZIP with all ${type.toUpperCase()} files downloaded`);
    } catch (error) {
      console.error(error);
      if (error instanceof ApiError) {
        toast.error(error.message);
      } else {
        toast.error(error instanceof Error ? error.message : 'Bulk download failed');
      }
    }
  };

  const handleNavigateField = (field: WorkletFieldKey, delta: number) => {
    if (!activeIteration) return;
    const attr = getAttribute(activeIteration, field);
    const total = getIterationCount(attr);
    if (total <= 1) return;
    const current = getViewIndex(field);
    const next = clampToIterations(attr, current + delta);
    if (next === current) return;
    setFieldViewIndices((prev) => ({ ...prev, [field]: next }));
  };

  const handleSelectFieldIteration = async (field: WorkletFieldKey, index: number) => {
    if (!activeWorklet || !activeIteration) return;
    const attr = getAttribute(activeIteration, field);
    const selected = getSelectedIndex(attr);
    if (index === selected) return;
    setSelectingField(field);
    try {
      const payload = {
        worklet_id: activeWorklet.worklet_id,
        worklet_iteration_id: activeIteration.iteration_id,
        field,
        selected_index: index,
      };
      await requestJson<SelectIterationResponse>(`${API_URL}/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const updatedIteration: WorkletIteration = {
        ...activeIteration,
        [field]: {
          ...attr,
          selected_index: index,
        },
      };

      const updatedWorklet = ensureWorkletBundle({
        ...activeWorklet,
        iterations: activeWorklet.iterations.map((iteration) =>
          iteration.iteration_id === activeIteration.iteration_id ? updatedIteration : iteration,
        ),
      });

      onUpdateWorklet(updatedWorklet);
      setFieldViewIndices((prev) => ({ ...prev, [field]: index }));
      toast.success('Default iteration updated');
    } catch (error) {
      console.error(error);
      if (error instanceof ApiError) {
        toast.error(error.message ?? 'Selection failed');
      } else {
        toast.error(error instanceof Error ? error.message : 'Selection failed');
      }
    } finally {
      setSelectingField(null);
    }
  };

  const handleOpenFieldPrompt = (field: WorkletFieldKey, index: number) => {
    if (isIterating) return;
    setFieldPromptState({ open: true, field, prompt: '', iterationIndex: index });
  };

  const handleFieldPromptSubmit = async () => {
    if (!activeWorklet || !activeIteration || !fieldPromptState.field) return;
    const trimmed = fieldPromptState.prompt.trim();
    if (!trimmed) {
      toast.error('Please enter a prompt to iterate this field');
      return;
    }

    setIteratingField(fieldPromptState.field);
    try {
      const payload = {
        worklet_id: activeWorklet.worklet_id,
        worklet_iteration_id: activeIteration.iteration_id,
        field: fieldPromptState.field,
        index: fieldPromptState.iterationIndex,
        prompt: trimmed,
      };

      const response = await requestJson<IterateWorkletResponse>(`${API_URL}/iterate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const attr = getAttribute(activeIteration, fieldPromptState.field);
      const updatedIteration: WorkletIteration = {
        ...activeIteration,
        [fieldPromptState.field]: {
          ...attr,
          selected_index: response.selected_index,
          iterations: response.iterations as any,
        },
      };

      const updatedWorklet = ensureWorkletBundle({
        ...activeWorklet,
        iterations: activeWorklet.iterations.map((iteration) =>
          iteration.iteration_id === activeIteration.iteration_id ? updatedIteration : iteration,
        ),
      });

      onUpdateWorklet(updatedWorklet);
      setFieldViewIndices((prev) => ({
        ...prev,
        [fieldPromptState.field as WorkletFieldKey]: response.selected_index,
      }));
      toast.success('Iteration applied');
      setFieldPromptState(DEFAULT_FIELD_PROMPT_STATE);
    } catch (error) {
      console.error(error);
      if (error instanceof ApiError) {
        toast.error(error.message ?? 'Iteration failed');
      } else {
        toast.error(error instanceof Error ? error.message : 'Iteration failed');
      }
    } finally {
      setIteratingField(null);
    }
  };

  const handleIterationNavigate = (delta: number) => {
    if (!activeWorklet) return;
    if (totalWorkletIterations <= 1) return;
    const next = clampWorkletIterationIndex(activeWorklet, activeIterationIndex + delta);
    if (next === activeIterationIndex) return;
    setActiveIterationIndex(next);
  };

  const handleSelectDefaultIteration = async () => {
    if (!activeWorklet || !activeIteration) return;
    const currentDefault = getWorkletIterationAt(activeWorklet, activeWorklet.selected_iteration_index);
    if (currentDefault.iteration_id === activeIteration.iteration_id) {
      return;
    }
    setDefaultSelecting(true);
    try {
      const response = await requestJson<SelectWorkletIterationResponse>(
        `${API_URL}/worklet-iterations/select-default`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            worklet_id: activeWorklet.worklet_id,
            worklet_iteration_id: activeIteration.iteration_id,
          }),
        },
      );

      const updatedWorklet = ensureWorkletBundle({
        ...activeWorklet,
        selected_iteration_index: response.selected_iteration_index,
      });

      onUpdateWorklet(updatedWorklet);
      setActiveIterationIndex(response.selected_iteration_index);
      toast.success('Default worklet iteration updated');
    } catch (error) {
      console.error(error);
      if (error instanceof ApiError) {
        toast.error(error.message ?? 'Failed to update default iteration');
      } else {
        toast.error(error instanceof Error ? error.message : 'Failed to update default iteration');
      }
    } finally {
      setDefaultSelecting(false);
    }
  };

  const handleEnhanceSubmit = async () => {
    if (!activeWorklet || !activeIteration) return;
    const trimmed = enhancePrompt.trim();
    if (!trimmed) {
      toast.error('Please provide a prompt to enhance the worklet');
      return;
    }
    setIsEnhancing(true);
    try {
      const response = await requestJson<EnhanceWorkletResponse>(
        `${API_URL}/worklet-iterations/enhance`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            worklet_id: activeWorklet.worklet_id,
            worklet_iteration_id: activeIteration.iteration_id,
            prompt: trimmed,
          }),
        },
      );

      const newIteration = ensureWorkletIteration(response.iteration as any);
      const updatedWorklet = ensureWorkletBundle({
        ...activeWorklet,
        iterations: [...activeWorklet.iterations, newIteration],
        selected_iteration_index: response.selected_iteration_index,
      });

      onUpdateWorklet(updatedWorklet);
      setActiveIterationIndex(response.selected_iteration_index);
      setEnhancePrompt('');
      setEnhanceDialogOpen(false);
      toast.success('Worklet enhanced');
    } catch (error) {
      console.error(error);
      if (error instanceof ApiError) {
        toast.error(error.message ?? 'Enhancement failed');
      } else {
        toast.error(error instanceof Error ? error.message : 'Enhancement failed');
      }
    } finally {
      setIsEnhancing(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <Card className="space-y-4 border-border bg-card p-6">
        <h3 className="text-xl font-semibold text-foreground">Thread Details</h3>
        <div className="space-y-3">
          {clusterName && (
            <div>
              <p className="text-sm text-muted-foreground">Cluster</p>
              <p className="text-foreground">{clusterName}</p>
            </div>
          )}
          <div>
            <p className="text-sm text-muted-foreground">Thread ID</p>
            <p className="font-mono text-foreground">{thread.thread_id}</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground">Thread Name</p>
            <p className="text-foreground">{thread.thread_name}</p>
          </div>

          {thread.custom_prompt && (
            <div>
              <p className="text-sm text-muted-foreground">Custom Prompt</p>
              <p className="text-foreground [overflow-wrap:anywhere]">{thread.custom_prompt}</p>
            </div>
          )}

          {thread.links && thread.links.length > 0 && (
            <div>
              <p className="text-sm text-muted-foreground mb-2">Links</p>
              <div className="space-y-1">
                {thread.links.map((link) => (
                  <a
                    key={link}
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-accent hover:underline"
                  >
                    {link}
                  </a>
                ))}
              </div>
            </div>
          )}

          {thread.files && thread.files.length > 0 && (
            <div>
              <p className="text-sm text-muted-foreground mb-2">Uploaded Files</p>
              <div className="space-y-2">
                {thread.files.map((file) => (
                  <div key={file} className="flex items-center gap-2 rounded border border-border bg-muted p-2">
                    <FileIcon className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm [overflow-wrap:anywhere]">{file}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <p className="text-sm text-muted-foreground">Count</p>
            <p className="text-foreground">{thread.count}</p>
          </div>
        </div>
      </Card>

      {worklets.length > 0 && (
        <Card className="space-y-4 border-border bg-card p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-xl font-semibold text-foreground">Generated Files</h3>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button className="gradient-primary text-primary-foreground transition-colors hover:opacity-90">
                  <Download className="mr-2 h-4 w-4" />
                  Download All
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleDownloadAll('pdf')}>
                  PDF (All)
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleDownloadAll('pptx')}>
                  PPTX (All)
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {worklets.map((worklet) => {
              const iteration = getDefaultWorkletIteration(worklet);
              const rawTitle = getStringIteration(iteration.title);
              const buttonTitle = rawTitle.trim().length > 0 ? rawTitle : 'Untitled Worklet';
              return (
                <Button
                  key={worklet.worklet_id}
                  variant="outline"
                  className="h-auto justify-start border-border transition-colors hover:border-primary whitespace-normal py-3 text-left"
                  onClick={() => handleOpenWorklet(worklet)}
                >
                  <FileIcon className="mr-2 h-4 w-4" />
                  <span className="text-left [overflow-wrap:anywhere]">
                    {buttonTitle}
                  </span>
                </Button>
              );
            })}
          </div>
        </Card>
      )}

      <Dialog open={isDialogOpen} onOpenChange={handleDialogOpenChange}>
        <DialogContent className="max-h-[90vh] max-w-3xl">
          {activeWorklet && activeIteration && (
            <>
              <DialogHeader>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex-1">
                    <DialogTitle className="text-2xl leading-tight [overflow-wrap:anywhere]">
                      {getActiveTitle()}
                    </DialogTitle>
                    {isIterating && (
                      <DialogDescription className="text-sm text-muted-foreground">
                        Iteration in progress. Please wait...
                      </DialogDescription>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => handleIterationNavigate(-1)}
                      disabled={isIterating || isEnhancing || totalWorkletIterations <= 1 || activeIterationIndex <= 0}
                      aria-label="Previous worklet iteration"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <span className="min-w-[3rem] text-center text-xs font-mono text-foreground">
                      {totalWorkletIterations > 0
                        ? `${activeIterationIndex + 1}/${totalWorkletIterations}`
                        : '0/0'}
                    </span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => handleIterationNavigate(1)}
                      disabled={
                        isIterating ||
                        isEnhancing ||
                        totalWorkletIterations <= 1 ||
                        activeIterationIndex >= totalWorkletIterations - 1
                      }
                      aria-label="Next worklet iteration"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={handleSelectDefaultIteration}
                      disabled={
                        isIterating ||
                        isEnhancing ||
                        defaultSelecting ||
                        activeWorklet.selected_iteration_index === activeIterationIndex
                      }
                      aria-label="Set default worklet iteration"
                    >
                      {defaultSelecting ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => setEnhanceDialogOpen(true)}
                      disabled={isIterating || isEnhancing}
                      aria-label="Enhance worklet"
                    >
                      {isEnhancing ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Pencil className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </DialogHeader>
              <ScrollArea className="h-[60vh] pr-4">
                <div className="space-y-6">
                  {FIELD_CONFIGS.map((field) => {
                    const attr = getAttribute(activeIteration, field.key);
                    const total = getIterationCount(attr);
                    const viewIndex = getViewIndex(field.key);
                    const selectedIndex = getSelectedIndex(attr);
                    const isSelected = total > 0 && viewIndex === selectedIndex;
                    const showSelect = total > 0 && !isSelected;

                    let content: ReactNode;
                    if (field.type === 'array') {
                      const values = getArrayIteration(attr as ArrayAttribute, viewIndex);
                      content = <ArrayContent values={values} />;
                    } else if (field.type === 'object') {
                      const values = getObjectIteration(attr as ObjectAttribute, viewIndex);
                      content = <MilestonesContent milestones={values} />;
                    } else {
                      const value = getStringIteration(attr as StringAttribute, viewIndex);
                      content = <StringContent value={value} />;
                    }

                    return (
                      <section key={field.key} className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <h4 className="text-sm font-semibold text-foreground">
                            {field.label}
                          </h4>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              onClick={() => handleNavigateField(field.key, -1)}
                              disabled={isIterating || total <= 1 || viewIndex <= 0}
                              aria-label={`Previous iteration for ${field.label}`}
                            >
                              <ChevronLeft className="h-4 w-4" />
                            </Button>
                            <span className="min-w-[3rem] text-center font-mono text-foreground">
                              {total > 0 ? `${viewIndex + 1}/${total}` : '0/0'}
                            </span>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              onClick={() => handleNavigateField(field.key, 1)}
                              disabled={isIterating || total <= 1 || viewIndex >= total - 1}
                              aria-label={`Next iteration for ${field.label}`}
                            >
                              <ChevronRight className="h-4 w-4" />
                            </Button>
                          </div>
                          {showSelect && (
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              onClick={() => handleSelectFieldIteration(field.key, viewIndex)}
                              disabled={isIterating || selectingField === field.key}
                              aria-label={`Select iteration ${viewIndex + 1} for ${field.label}`}
                            >
                              {selectingField === field.key ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Check className="h-4 w-4" />
                              )}
                            </Button>
                          )}
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7"
                            onClick={() => handleOpenFieldPrompt(field.key, viewIndex)}
                            disabled={isIterating || isEnhancing}
                            aria-label={`Iterate ${field.label}`}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          {isSelected && (
                            <span className="rounded bg-muted px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-primary">
                              Selected
                            </span>
                          )}
                        </div>
                        <div className="rounded border border-border bg-muted/20 p-3">
                          {content}
                        </div>
                      </section>
                    );
                  })}

                  <ReasoningField reasoning={activeIteration.reasoning} />
                  <ReferencesField references={activeIteration.references} />
                </div>
              </ScrollArea>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => handleDownload('pdf')} disabled={isIterating || isEnhancing}>
                  <Download className="mr-1 h-4 w-4" /> PDF
                </Button>
                <Button onClick={() => handleDownload('pptx')} disabled={isIterating || isEnhancing}>
                  <Download className="mr-1 h-4 w-4" /> PPTX
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={fieldPromptState.open} onOpenChange={(open) => (!open ? closeFieldPrompt() : null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Provide iteration prompt</DialogTitle>
            {fieldPromptState.field && (
              <DialogDescription>
                Field: {FIELD_CONFIGS.find((f) => f.key === fieldPromptState.field)?.label} · Iteration {fieldPromptState.iterationIndex + 1}
              </DialogDescription>
            )}
          </DialogHeader>
          <div className="space-y-3">
            <Textarea
              value={fieldPromptState.prompt}
              onChange={(event) =>
                setFieldPromptState((prev) => ({ ...prev, prompt: event.target.value }))
              }
              placeholder="Describe how you would like to change this iteration..."
              disabled={isIterating}
              className="min-h-[120px]"
            />
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={closeFieldPrompt}
              disabled={isIterating}
            >
              Cancel
            </Button>
            <Button type="button" onClick={handleFieldPromptSubmit} disabled={isIterating}>
              {isIterating ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Pencil className="mr-2 h-4 w-4" />
              )}
              Iterate
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={enhanceDialogOpen} onOpenChange={(open) => {
        if (!open && !isEnhancing) {
          setEnhanceDialogOpen(false);
          setEnhancePrompt('');
        } else if (open) {
          setEnhanceDialogOpen(true);
        }
      }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Enhance worklet</DialogTitle>
            <DialogDescription>
              Provide instructions to refine the entire worklet iteration.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Textarea
              value={enhancePrompt}
              onChange={(event) => setEnhancePrompt(event.target.value)}
              placeholder="Describe how you would like to enhance this worklet..."
              disabled={isEnhancing}
              className="min-h-[140px]"
            />
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                if (isEnhancing) return;
                setEnhanceDialogOpen(false);
                setEnhancePrompt('');
              }}
              disabled={isEnhancing}
            >
              Cancel
            </Button>
            <Button type="button" onClick={handleEnhanceSubmit} disabled={isEnhancing}>
              {isEnhancing ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Pencil className="mr-2 h-4 w-4" />
              )}
              Enhance
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const normalizeWrapText = (input: string) => {
  return (input ?? '')
    .replace(/[\u00A0\u202F\u2060\uFEFF]/g, ' ')
    .replace(/[\u2011]/g, '-');
};

const StringContent = ({ value }: { value: string }) => {
  const safe = normalizeWrapText(value ?? '');
  if (!safe.trim()) {
    return <p className="text-sm text-muted-foreground">No content for this iteration.</p>;
  }
  return <p className="whitespace-pre-wrap leading-relaxed [overflow-wrap:anywhere]">{safe}</p>;
};

const ArrayContent = ({ values }: { values: string[] }) => {
  if (!values || values.length === 0) {
    return <p className="text-sm text-muted-foreground">No entries for this iteration.</p>;
  }
  return (
    <ul className="list-disc space-y-1 pl-4">
      {values.map((value, index) => (
        <li key={`${value}-${index}`} className="[overflow-wrap:anywhere]">
          {normalizeWrapText(value ?? '')}
        </li>
      ))}
    </ul>
  );
};

const MilestonesContent = ({ milestones }: { milestones: Record<string, unknown> }) => {
  const entries = Object.entries(milestones ?? {});
  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No milestones for this iteration.</p>;
  }
  return (
    <div className="space-y-2">
      {entries.map(([key, value]) => (
        <div key={key} className="rounded border border-border bg-background p-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {normalizeWrapText(key)}
          </p>
          <pre className="mt-1 whitespace-pre-wrap text-xs [overflow-wrap:anywhere]">
            {typeof value === 'string' ? normalizeWrapText(value) : JSON.stringify(value, null, 2)}
          </pre>
        </div>
      ))}
    </div>
  );
};

const ReasoningField = ({ reasoning }: { reasoning: string }) => {
  const safe = normalizeWrapText(reasoning ?? '');
  const hasContent = safe.trim().length > 0;
  return (
    <section className="space-y-2">
      <div className="flex items-center gap-2">
        <h4 className="text-sm font-semibold text-foreground">Reasoning</h4>
      </div>
      <div className="rounded border border-border bg-muted/20 p-3">
        {hasContent ? (
          <p className="whitespace-pre-wrap leading-relaxed [overflow-wrap:anywhere]">{safe}</p>
        ) : (
          <p className="text-sm text-muted-foreground">No reasoning provided for this worklet.</p>
        )}
      </div>
    </section>
  );
};

const ReferencesField = ({ references }: { references: WorkletIteration['references'] }) => {
  if (!references || references.length === 0) {
    return null;
  }
  return (
    <section className="space-y-2">
      <h4 className="text-sm font-semibold text-foreground">References</h4>
      <div className="space-y-3">
        {references.map((reference) => (
          <article
            key={`${reference.link}-${reference.title}`}
            className="rounded border border-border bg-background p-3"
          >
            <a
              href={reference.link}
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-primary hover:underline"
            >
              {reference.title}
            </a>
            <p className="mt-1 text-xs text-muted-foreground">
              {normalizeWrapText(reference.description)}
            </p>
            <span className="mt-2 inline-block rounded bg-muted px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              {reference.tag}
            </span>
          </article>
        ))}
      </div>
    </section>
  );
};
