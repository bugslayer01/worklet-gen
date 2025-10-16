import { useEffect, useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { ProgressMessage } from '@/types/thread';

interface ProgressBarProps {
  messages: ProgressMessage[];
}

export const ProgressBar = ({ messages }: ProgressBarProps) => {
  const [currentMessage, setCurrentMessage] = useState<string>('');
  const [messageQueue, setMessageQueue] = useState<ProgressMessage[]>([]); // only pending (not yet displayed) messages
  const [isFading, setIsFading] = useState<boolean>(true); // start faded, then fade in initial

  const FADE_DURATION = 100; // ms

  // Track last processed (displayed) message timestamp to avoid re-adding old messages
  const lastProcessedRef = useRef<number>(0);
  const rotationTimeoutRef = useRef<number | null>(null);

  // Ingest only new messages (those with a timestamp greater than last processed)
  useEffect(() => {
    if (!messages || messages.length === 0) return;

    const newMessages = messages.filter(m => m.timestamp > lastProcessedRef.current);
    if (newMessages.length === 0) return; // nothing new

    setMessageQueue(prev => {
      // If there's no current message being displayed, show the first new one immediately
      if (!currentMessage) {
        const [first, ...rest] = newMessages;
        setCurrentMessage(first.message);
        lastProcessedRef.current = first.timestamp;
        // trigger fade-in for initial
        requestAnimationFrame(() => setIsFading(false));
        return [...prev, ...rest];
      }
      // Current message stays until we rotate; queue the new ones
      return [...prev, ...newMessages];
    });
  }, [messages, currentMessage]);

  // Rotate to next queued message ONLY if a next one exists; otherwise keep current message indefinitely
  useEffect(() => {
    if (!currentMessage) return; // nothing displayed yet

    // If there are pending messages and no timer running, schedule rotation
    if (messageQueue.length > 0 && rotationTimeoutRef.current == null) {
      rotationTimeoutRef.current = window.setTimeout(() => {
        const next = messageQueue[0];
        if (next) {
          // Fade out first
            setIsFading(true);
            // After fade duration, swap message & fade back in
            window.setTimeout(() => {
              setCurrentMessage(next.message);
              lastProcessedRef.current = next.timestamp;
              setMessageQueue(prev => prev.slice(1)); // remove consumed
              setIsFading(false);
            }, FADE_DURATION);
        }
        // Clear rotation timeout so future rotations can be scheduled (even while inner fade timers may still run)
        rotationTimeoutRef.current = null;
      }, 700);
    }

    // If queue becomes empty while timer exists (shouldn't happen often), clear it
    if (messageQueue.length === 0 && rotationTimeoutRef.current != null) {
      clearTimeout(rotationTimeoutRef.current);
      rotationTimeoutRef.current = null;
    }
  }, [messageQueue, currentMessage]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (rotationTimeoutRef.current != null) {
        clearTimeout(rotationTimeoutRef.current);
      }
    };
  }, []);

  // If no message ever displayed yet, render nothing
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
