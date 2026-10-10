import { Badge, Box, Heading, HStack, Text } from '@chakra-ui/react';
import type { Roast } from '../../types';

interface RoastDisplayProps {
  roast: Roast;
}

const COLORS = { mild: 'green', medium: 'orange', spicy: 'red' } as const;

export function RoastDisplay({ roast }: RoastDisplayProps) {
  return (
    <Box>
      <HStack mb={3} wrap="wrap">
        <Heading size="md">@{roast.github_username}</Heading>
        <Badge colorScheme={COLORS[roast.intensity]}>{roast.intensity}</Badge>
        <Badge>{roast.target_type}</Badge>
      </HStack>
      <Text whiteSpace="pre-wrap" fontSize="lg" lineHeight="tall">
        {roast.roast_text}
      </Text>
    </Box>
  );
}
