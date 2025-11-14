import { useState } from 'react';
import { Plus, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { DomainsKeywords } from '@/types/thread';
import { ScrollArea } from '@/components/ui/scroll-area';

interface DomainKeywordModalProps {
  open: boolean;
  data: DomainsKeywords;
  onSubmit: (data: DomainsKeywords) => void;
  threadName?: string;
  message?: string;
}

export const DomainKeywordModal = ({ open, data, onSubmit, threadName, message }: DomainKeywordModalProps) => {
  // Ensure we always have the expected shape (defensive in case of future optional changes)
  const [domains, setDomains] = useState<DomainsKeywords['domains']>({
    worklet: data.domains?.worklet ?? [],
    link: data.domains?.link ?? [],
    custom_prompt: data.domains?.custom_prompt ?? [],
    custom: data.domains?.custom ?? []
  });
  const [keywords, setKeywords] = useState<DomainsKeywords['keywords']>({
    worklet: data.keywords?.worklet ?? [],
    link: data.keywords?.link ?? [],
    custom_prompt: data.keywords?.custom_prompt ?? [],
    custom: data.keywords?.custom ?? []
  });
  const [showCustomDomains, setShowCustomDomains] = useState(false);
  const [showCustomKeywords, setShowCustomKeywords] = useState(false);

  type SectionKey = 'worklet' | 'link' | 'custom_prompt' | 'custom';

  const removeItem = (category: 'domains' | 'keywords', section: SectionKey, index: number) => {
    if (category === 'domains') {
      setDomains(prev => {
        const arr = prev[section];
        if (!arr || index < 0 || index >= arr.length) return prev; // safety
        return { ...prev, [section]: arr.filter((_, i) => i !== index) };
      });
    } else {
      setKeywords(prev => {
        const arr = prev[section];
        if (!arr || index < 0 || index >= arr.length) return prev;
        return { ...prev, [section]: arr.filter((_, i) => i !== index) };
      });
    }
  };

  const updateItem = (category: 'domains' | 'keywords', section: SectionKey, index: number, value: string) => {
    if (category === 'domains') {
      setDomains(prev => {
        const arr = prev[section];
        if (!arr || index < 0 || index >= arr.length) return prev;
        const nextArr = [...arr];
        nextArr[index] = value;
        return { ...prev, [section]: nextArr };
      });
    } else {
      setKeywords(prev => {
        const arr = prev[section];
        if (!arr || index < 0 || index >= arr.length) return prev;
        const nextArr = [...arr];
        nextArr[index] = value;
        return { ...prev, [section]: nextArr };
      });
    }
  };

  const addCustomItem = (category: 'domains' | 'keywords') => {
    if (category === 'domains') {
      setShowCustomDomains(true);
      if (!domains.custom) {
        setDomains({ ...domains, custom: [''] });
      } else {
        setDomains({ ...domains, custom: [...domains.custom, ''] });
      }
    } else {
      setShowCustomKeywords(true);
      if (!keywords.custom) {
        setKeywords({ ...keywords, custom: [''] });
      } else {
        setKeywords({ ...keywords, custom: [...keywords.custom, ''] });
      }
    }
  };

  const handleSubmit = () => {
    onSubmit({ domains, keywords });
  };

  const renderSection = (
    title: string,
    items: string[],
    category: 'domains' | 'keywords',
    section: SectionKey
  ) => {
    if (!items || items.length === 0) return null; // hide empty sections per requirement
    return (
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-muted-foreground">{title}</h4>
        <div className="space-y-2">
          {items.map((item, index) => (
            <div key={index} className="flex gap-2">
              <Input
                value={item}
                onChange={(e) => updateItem(category, section, index, e.target.value)}
                className="bg-input border-border"
              />
              <Button
                type="button"
                onClick={() => removeItem(category, section, index)}
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
    );
  };

  return (
    <Dialog open={open}>
      {/* Use grid rows so header/footer are auto-sized and middle content can scroll */}
      <DialogContent hideClose className="max-w-4xl max-h-[80vh] bg-card border-border grid-rows-[auto,1fr,auto]">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            {`Approve Domains & Keywords${threadName ? ` for ${threadName}` : ''}`}
          </DialogTitle>
          {message && (
            <p className="text-sm text-muted-foreground mt-1">{message}</p>
          )}
        </DialogHeader>
        
        {/* Make the middle section scrollable within the dialog's max height */}
        <ScrollArea className="min-h-0 pr-4">
          <div className="grid grid-cols-2 gap-8 p-2">
            {/* Domains Column */}
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-foreground">Domains</h3>
                <Button
                  type="button"
                  onClick={() => addCustomItem('domains')}
                  size="sm"
                  variant="outline"
                  className="border-border"
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Custom
                </Button>
              </div>
              {renderSection('Worklets', domains.worklet, 'domains', 'worklet')}
              {renderSection('Links', domains.link, 'domains', 'link')}
              {renderSection('Custom Prompt', domains.custom_prompt, 'domains', 'custom_prompt')}
              {showCustomDomains && domains.custom && (
                <div className="pb-2">
                  {renderSection('Custom Domains', domains.custom, 'domains', 'custom')}
                </div>
              )}
            </div>

            {/* Keywords Column */}
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-foreground">Keywords</h3>
                <Button
                  type="button"
                  onClick={() => addCustomItem('keywords')}
                  size="sm"
                  variant="outline"
                  className="border-border"
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Custom
                </Button>
              </div>
              {renderSection('Worklets', keywords.worklet, 'keywords', 'worklet')}
              {renderSection('Links', keywords.link, 'keywords', 'link')}
              {renderSection('Custom Prompt', keywords.custom_prompt, 'keywords', 'custom_prompt')}
              {showCustomKeywords && keywords.custom && (
                <div className="pb-2">
                  {renderSection('Custom Keywords', keywords.custom, 'keywords', 'custom')}
                </div>
              )}
            </div>
          </div>
        </ScrollArea>

        <div className="flex justify-end mt-4 pt-2 border-t border-border">
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
