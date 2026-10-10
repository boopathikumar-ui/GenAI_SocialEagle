import { Box, Text } from '@chakra-ui/react';

interface StatCardProps {
  label: string;
  value: number;
}

export function StatCard({ label, value }: StatCardProps) {
  return (
    <Box
      as="section"
      aria-label={label}
      p={5}
      rounded="xl"
      bg="white"
      border="1px solid"
      borderColor="gray.200"
      shadow="sm"
    >
      <Text fontSize="sm" color="gray.600">
        {label}
      </Text>
      <Text fontSize="3xl" fontWeight="bold" color="gray.800" data-testid="stat-value">
        {value.toLocaleString('en-US')}
      </Text>
    </Box>
  );
}
