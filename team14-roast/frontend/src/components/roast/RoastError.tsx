import { Alert, AlertDescription, AlertIcon, AlertTitle, Box } from '@chakra-ui/react';
import type { RoastError as RoastErrorValue } from '../../services/roastService';

interface RoastErrorProps {
  error: RoastErrorValue;
}

export function RoastError({ error }: RoastErrorProps) {
  return (
    <Alert status={error.kind === 'rate_limited' ? 'warning' : 'error'} rounded="xl" alignItems="flex-start">
      <AlertIcon />
      <Box>
        <AlertTitle>{error.title}</AlertTitle>
        <AlertDescription>{error.message}</AlertDescription>
      </Box>
    </Alert>
  );
}
