import { Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WelcomeScreenProps {
  onStartGenerating: () => void;
}

export const WelcomeScreen = ({ onStartGenerating }: WelcomeScreenProps) => {
  return (
    <div className="flex flex-col items-center justify-center h-full space-y-8">
      <div className="text-center space-y-4">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full gradient-primary shadow-glow mb-4">
          <Sparkles className="h-10 w-10 text-primary-foreground" />
        </div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
          Welcome to Worklet Generator Agent
        </h1>
        <p className="text-muted-foreground text-lg max-w-md mx-auto">
          Create powerful worklets with AI assistance. Upload files, add links, and let our agent do the magic.
        </p>
      </div>
      
      <Button
        onClick={onStartGenerating}
        size="lg"
        className="gradient-primary hover:opacity-90 transition-smooth shadow-glow text-lg px-8 py-6"
      >
        <Sparkles className="mr-2 h-5 w-5" />
        Start Generating Worklets
      </Button>
    </div>
  );
};
