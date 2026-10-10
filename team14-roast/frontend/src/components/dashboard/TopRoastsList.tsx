import { Badge, Box, Flex, Link, Text, VStack } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import type { TopRoast } from '../../types/dashboard';
import { ChartCard } from './ChartCard';

interface Props {
  roasts: TopRoast[];
}

export function TopRoastsList({ roasts }: Props) {
  return (
    <ChartCard
      title="Top roasts"
      summary={roasts.length === 0 ? 'No roasts yet.' : 'Your most reacted-to roasts.'}
    >
      <VStack as="ul" align="stretch" spacing={3} listStyleType="none">
        {roasts.map((r) => (
          <Flex as="li" key={r.id} justify="space-between" align="center" gap={3} wrap="wrap">
            <Box>
              <Link as={RouterLink} to={`/roasts/${r.id}`} fontWeight="semibold" color="purple.700">
                {r.github_username}
              </Link>
              <Text fontSize="sm" color="gray.600">
                {r.intensity} · {r.reaction_total} reactions · {r.is_public ? 'Public' : 'Private'}
              </Text>
            </Box>
            {r.is_public ? (
              <Link as={RouterLink} to={`/r/${r.share_slug}`} fontSize="sm" color="purple.700">
                Public page
              </Link>
            ) : (
              <Badge>Private</Badge>
            )}
          </Flex>
        ))}
      </VStack>
    </ChartCard>
  );
}
