import { Spinner, Text, VStack } from '@chakra-ui/react';
import { useEffect, useState } from 'react';

const MESSAGES: string[] = [
  'Reading your commit messages...',
  'Judging your variable names...',
  'Counting your TODO comments...',
  'Sharpening the roasting fork...',
  'Asking your README for an apology...',
  'Finding the 3am "fix stuff" commits...',
];

export function LoadingMessages() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => setIndex((i) => (i + 1) % MESSAGES.length), 2200);
    return () => window.clearInterval(id);
  }, []);

  return (
    <VStack py={8} spacing={4} role="status" aria-live="polite">
      <Spinner size="xl" color="purple.400" />
      <Text fontSize="lg">{MESSAGES[index]}</Text>
    </VStack>
  );
}
