import { Button, useToast } from '@chakra-ui/react';
import { useState } from 'react';

interface CopyButtonProps {
  text: string;
  label?: string;
}

export function CopyButton({ text, label = 'Copy' }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);
  const toast = useToast();

  const handleCopy = async (): Promise<void> => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      toast({ title: 'Could not copy to clipboard', status: 'error', duration: 3000 });
    }
  };

  return (
    <Button size="sm" variant="outline" onClick={() => void handleCopy()}>
      {copied ? 'Copied!' : label}
    </Button>
  );
}
