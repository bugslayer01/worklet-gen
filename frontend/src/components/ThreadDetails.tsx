import { Download, FileIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Thread, Worklet } from '@/types/thread';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu';
import { ScrollArea } from '@/components/ui/scroll-area';
import { API_URL } from '@/config';
import { toast } from 'sonner';
import { ApiError, requestBlob, ensureOk } from '@/lib/http';
import { useState } from 'react';

interface ThreadDetailsProps {
  thread: Thread;
  worklets: Worklet[];
}

export const ThreadDetails = ({ thread, worklets }: ThreadDetailsProps) => {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<Worklet | null>(null);

  const handleOpenWorklet = (w: Worklet) => {
    setSelected(w);
    setOpen(true);
  };

  const handleDownload = async (type: 'pdf' | 'ppt') => {
    if (!selected) return;
    try {
      const blob = await requestBlob(`${API_URL}/thread/${thread.thread_id}/download/${selected.worklet_id}/${type}`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selected.title}.${type}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`${type.toUpperCase()} downloaded`);
    } catch (e) {
      console.error(e);
      if (e instanceof ApiError) {
        toast.error(e.message);
      } else {
        toast.error(e instanceof Error ? e.message : 'Download failed');
      }
    }
  };

  const handleDownloadAll = async (type: 'pdf' | 'ppt') => {
    try {
      const res = await fetch(`${API_URL}/thread/${thread.thread_id}/download/all/${type}`);
      await ensureOk(res);

      const disposition = res.headers.get('Content-Disposition');
      let suggestedName = disposition?.match(/filename="?([^";]+)"?/)?.[1];
      if (!suggestedName) {
        // Fallback filename pattern
        suggestedName = `worklets-${type}-bundle.zip`;
      } else if (!/\.zip$/i.test(suggestedName)) {
        // Ensure .zip extension
        suggestedName = suggestedName.replace(/\.[^.]+$/, '') + '.zip';
      }
  const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = suggestedName;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`ZIP with all ${type.toUpperCase()} files downloaded`);
    } catch (e) {
      console.error(e);
      if (e instanceof ApiError) {
        toast.error(e.message);
      } else {
        toast.error(e instanceof Error ? e.message : 'Bulk download failed');
      }
    }
  };

  return (
    <div className="space-y-6 p-6">
      <Card className="p-6 bg-card border-border space-y-4">
        <h3 className="text-xl font-semibold text-foreground mb-4">Thread Details</h3>
        
        <div className="space-y-3">
          <div>
            <p className="text-sm text-muted-foreground">Thread ID</p>
            <p className="text-foreground font-mono">{thread.thread_id}</p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground">Thread Name</p>
            <p className="text-foreground">{thread.thread_name}</p>
          </div>

          {thread.custom_prompt && (
            <div>
              <p className="text-sm text-muted-foreground">Custom Prompt</p>
              <p className="text-foreground">{thread.custom_prompt}</p>
            </div>
          )}

          {thread.links && thread.links.length > 0 && (
            <div>
              <p className="text-sm text-muted-foreground mb-2">Links</p>
              <div className="space-y-1">
                {thread.links.map((link, index) => (
                  <a
                    key={index}
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent hover:underline block"
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
                {thread.files.map((file, index) => {
                  const display = typeof file === 'string' ? file : (file as any)?.name || String(file);
                  return (
                  <div key={index} className="flex items-center gap-2 p-2 bg-muted rounded">
                    <FileIcon className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{display}</span>
                  </div>
                  );
                })}
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
        <Card className="p-6 bg-card border-border space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold text-foreground">Generated Files</h3>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button className="gradient-accent hover:opacity-90 transition-smooth">
                  <Download className="h-4 w-4 mr-2" />
                  Download All
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleDownloadAll('pdf')}>PDF (All)</DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleDownloadAll('ppt')}>PPT (All)</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            {worklets.map((w) => (
              <Button
                key={w.worklet_id}
                variant="outline"
                className="border-border hover:border-primary transition-smooth justify-start"
                onClick={() => handleOpenWorklet(w)}
              >
                <FileIcon className="h-4 w-4 mr-2" />
                {w.title}
              </Button>
            ))}
          </div>
        </Card>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh]">
          {selected && (
            <>
              <DialogHeader>
                <DialogTitle className="text-2xl leading-tight [overflow-wrap:anywhere]">
                  {selected.title}
                </DialogTitle>
              </DialogHeader>
              <ScrollArea className="pr-4 h-[60vh]">
                <div className="space-y-4 text-sm whitespace-pre-wrap [overflow-wrap:anywhere] max-w-full">
                  <DetailField label="Problem Statement" value={selected.problem_statement} />
                  <DetailField label="Description" value={selected.description} />
                  <DetailField label="Challenge / Use Case" value={selected.challenge_use_case} />
                  <DetailField label="Deliverables" value={selected.deliverables} />
                  <ArrayField label="KPIs" values={selected.kpis} />
                  <ArrayField label="Prerequisites" values={selected.prerequisites} />
                  <DetailField label="Infrastructure Requirements" value={selected.infrastructure_requirements} />
                  <DetailField label="Tech Stack" value={selected.tech_stack} />
                  <MilestonesField milestones={selected.milestones} />
                  <ReferencesField references={selected.references} />
                </div>
              </ScrollArea>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => handleDownload('pdf')}>
                  <Download className="h-4 w-4 mr-1" /> PDF
                </Button>
                <Button onClick={() => handleDownload('ppt')}>
                  <Download className="h-4 w-4 mr-1" /> PPT
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Helper subcomponents
const normalizeWrapText = (input: string) => {
  // Replace characters that inhibit wrapping:
  //  - NBSP (\u00A0)
  //  - NARROW NBSP (\u202F)
  //  - WORD JOINER (\u2060)
  //  - ZERO WIDTH NO-BREAK SPACE / BOM (\uFEFF)
  //  - NON-BREAKING HYPHEN (\u2011)
  return (input ?? "")
    .replace(/[\u00A0\u202F\u2060\uFEFF]/g, " ")
    .replace(/[\u2011]/g, "-");
};

const DetailField = ({ label, value }: { label: string; value: string }) => {
  const safe = normalizeWrapText(value ?? "");
  return (
    <div>
      <p className="text-muted-foreground font-medium mb-1">{label}</p>
      <p className="whitespace-pre-wrap leading-relaxed [overflow-wrap:anywhere]">{safe}</p>
    </div>
  );
};

// const DetailField = ({ label, value }: { label: string; value: string }) => (
//   <div>
//     <p className="text-muted-foreground font-medium mb-1">{label}</p>
//     <p className="whitespace-pre-wrap leading-relaxed">{value}</p>
//   </div>
// );

const ArrayField = ({ label, values }: { label: string; values: string[] }) => (
  <div>
    <p className="text-muted-foreground font-medium mb-1">{label}</p>
    <ul className="list-disc list-inside space-y-1">
      {values.map((v, i) => (
        <li key={i} className="[overflow-wrap:anywhere]">
          {normalizeWrapText(v ?? "")}
        </li>
      ))}
    </ul>
  </div>
);

const MilestonesField = ({ milestones }: { milestones: Record<string, any> }) => (
  <div>
    <p className="text-muted-foreground font-medium mb-1">Milestones</p>
    <div className="space-y-2">
      {Object.entries(milestones || {}).map(([k, v]) => (
        <div key={k} className="border border-border rounded p-2">
          <p className="text-sm font-semibold mb-1">{k}</p>
          <pre className="text-xs whitespace-pre-wrap">{typeof v === 'string' ? v : JSON.stringify(v, null, 2)}</pre>
        </div>
      ))}
    </div>
  </div>
);

const ReferencesField = ({ references }: { references: Worklet['references'] }) => (
  <div>
    <p className="text-muted-foreground font-medium mb-1">References</p>
    <div className="space-y-3">
      {references.map((r, i) => (
        <div key={i} className="border border-border rounded p-3">
          <a
            href={r.link}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-primary hover:underline"
          >
            {r.title}
          </a>
          <p className="text-xs mt-1 mb-1">{r.description}</p>
          <span className="inline-block text-[10px] uppercase tracking-wide bg-muted px-2 py-0.5 rounded">{r.tag}</span>
        </div>
      ))}
    </div>
  </div>
);
