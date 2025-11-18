import { useEffect, useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { ProgressMessage } from '@/types/thread';

interface ProgressBarProps {
  messages: ProgressMessage[];
}

// Simplified progress: show only the latest message; no queue/rotation, but with a small fade.
export const ProgressBar = ({ messages }: ProgressBarProps) => {
  const [currentMessage, setCurrentMessage] = useState<string>('');
  const [isFading, setIsFading] = useState<boolean>(true);
  const FADE_DURATION = 120; // ms
  const swapTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    if (!messages || messages.length === 0) {
      // No messages: hide the progress bar
      if (currentMessage) setCurrentMessage('');
      return;
    }
    const last = messages[messages.length - 1];

    // First message: set and fade in
    if (!currentMessage) {
      setCurrentMessage(last.message);
      requestAnimationFrame(() => setIsFading(false));
      return;
    }

    // If message changed, perform a quick fade-out then swap then fade-in
    if (last.message !== currentMessage) {
      setIsFading(true);
      if (swapTimeoutRef.current) {
        clearTimeout(swapTimeoutRef.current);
      }
      swapTimeoutRef.current = window.setTimeout(() => {
        setCurrentMessage(last.message);
        setIsFading(false);
        swapTimeoutRef.current = null;
      }, FADE_DURATION);
    }
  }, [messages, currentMessage]);

  useEffect(() => {
    return () => {
      if (swapTimeoutRef.current) {
        clearTimeout(swapTimeoutRef.current);
      }
    };
  }, []);

  if (!currentMessage) return null;

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-card border border-border rounded-lg p-4 shadow-glow">
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 text-primary animate-spin" />
          <div className="flex-1">
            <p
              className={`text-sm font-medium text-foreground transition-opacity ${isFading ? 'opacity-0' : 'opacity-100'}`}
              style={{ transitionDuration: `${FADE_DURATION}ms` }}
            >
              {currentMessage}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
