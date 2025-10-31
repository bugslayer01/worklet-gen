import { useState, useEffect } from 'react';
import { Plus, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';

interface WebQueryModalProps {
  open: boolean;
  queries: string[];
  onSubmit: (queries: string[]) => void;
}

export const WebQueryModal = ({ open, queries: initialQueries, onSubmit }: WebQueryModalProps) => {
  const [queries, setQueries] = useState<string[]>(initialQueries);

  useEffect(() => {
    if (open) {
      setQueries(initialQueries);
    }
  }, [initialQueries, open]);

  const addQuery = () => {
    setQueries([...queries, '']);
  };

  const removeQuery = (index: number) => {
    setQueries(queries.filter((_, i) => i !== index));
  };

  const updateQuery = (index: number, value: string) => {
    const newQueries = [...queries];
    newQueries[index] = value;
    setQueries(newQueries);
  };

  const handleSubmit = () => {
    const filteredQueries = queries.filter(q => q.trim() !== '');
    onSubmit(filteredQueries);
  };

  return (
    <Dialog open={open}>
      {/* Align modal layout with scrollable middle section */}
      <DialogContent hideClose className="max-w-2xl max-h-[80vh] bg-card border-border grid-rows-[auto,1fr,auto]">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Web Queries
          </DialogTitle>
        </DialogHeader>
        
        <ScrollArea className="min-h-0 pr-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-muted-foreground">
                Review and modify web search queries
              </p>
              <Button
                type="button"
                onClick={addQuery}
                size="sm"
                variant="outline"
                className="border-border"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Query
              </Button>
            </div>

            <div className="space-y-3">
              {queries.map((query, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    value={query}
                    onChange={(e) => updateQuery(index, e.target.value)}
                    placeholder="Enter search query"
                    className="bg-input border-border"
                  />
                  <Button
                    type="button"
                    onClick={() => removeQuery(index)}
                    size="icon"
                    variant="ghost"
                    className="hover:bg-destructive/10 hover:text-destructive"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </ScrollArea>

        <div className="flex justify-end mt-4">
          <Button
            onClick={handleSubmit}
            className="gradient-primary hover:opacity-90 transition-smooth"
          >
            Next
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
