import { Box, Heading, Text } from '@chakra-ui/react';
import type { ReactNode } from 'react';

interface ChartCardProps {
  title: string;
  summary: string;
  children: ReactNode;
}

export function ChartCard({ title, summary, children }: ChartCardProps) {
  return (
    <Box as="section" p={5} rounded="xl" bg="white" border="1px solid" borderColor="gray.200">
      <Heading as="h2" size="sm" mb={1}>
        {title}
      </Heading>
      <Text fontSize="sm" color="gray.600" mb={3} data-testid="chart-summary">
        {summary}
      </Text>
      {children}
    </Box>
  );
}
