import { Badge, Box, HStack, Link, Text, VStack } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { GlassCard } from '../ui/GlassCard';
import { ReactionBar } from './ReactionBar';
import type { GalleryRoast } from '../../types/gallery';

const MAX_CHARS = 220;

function truncate(text: string, max: number): string {
  return text.length <= max ? text : `${text.slice(0, max).trimEnd()}…`;
}

const INTENSITY_COLOR = { mild: 'green', medium: 'orange', spicy: 'red' } as const;

interface GalleryCardProps {
  roast: GalleryRoast;
}

export function GalleryCard({ roast }: GalleryCardProps) {
  return (
    <GlassCard as="article" h="100%">
      <VStack align="stretch" spacing={4} h="100%">
        <HStack justify="space-between">
          <Text fontWeight="bold" noOfLines={1}>
            @{roast.github_username}
          </Text>
          <Badge colorScheme={INTENSITY_COLOR[roast.intensity]}>{roast.intensity}</Badge>
        </HStack>
        <Box flex="1">
          <Text whiteSpace="pre-wrap" wordBreak="break-word">
            {truncate(roast.roast_text, MAX_CHARS)}
          </Text>
          <Link as={RouterLink} to={`/r/${roast.share_slug}`} color="purple.300" fontSize="sm">
            Read full roast
          </Link>
        </Box>
        <ReactionBar roastId={roast.id} counts={roast.reaction_counts} mine={roast.my_reactions} />
      </VStack>
    </GlassCard>
  );
}
