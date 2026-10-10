import { Badge, Button, HStack, Switch, Text, VStack } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { GlassCard } from '../ui/GlassCard';
import type { Intensity, Roast } from '../../types';

interface RoastCardProps {
  roast: Roast;
  onDelete?: (id: number) => void;
  onTogglePublic?: (id: number, isPublic: boolean) => void;
}

const COLORS: Record<Intensity, string> = { mild: 'green', medium: 'orange', spicy: 'red' };

export function RoastCard({ roast, onDelete, onTogglePublic }: RoastCardProps) {
  return (
    <GlassCard mb={4}>
      <VStack align="stretch" spacing={3}>
        <HStack justify="space-between">
          <Text fontWeight="bold">@{roast.github_username}</Text>
          <Badge colorScheme={COLORS[roast.intensity]}>{roast.intensity}</Badge>
        </HStack>
        <Text noOfLines={3}>{roast.roast_text}</Text>
        <HStack justify="space-between" wrap="wrap">
          <Text fontSize="sm" color="gray.500">
            {new Date(roast.created_at).toLocaleDateString()}
          </Text>
          <HStack>
            {onTogglePublic && (
              <HStack>
                <Text fontSize="sm">Public</Text>
                <Switch
                  isChecked={roast.is_public}
                  aria-label="Toggle public"
                  onChange={(e) => onTogglePublic(roast.id, e.target.checked)}
                />
              </HStack>
            )}
            <Button as={RouterLink} to={`/roasts/${roast.id}`} size="sm" colorScheme="purple" variant="outline">
              View
            </Button>
            {onDelete && (
              <Button size="sm" colorScheme="red" variant="ghost" onClick={() => onDelete(roast.id)}>
                Delete
              </Button>
            )}
          </HStack>
        </HStack>
      </VStack>
    </GlassCard>
  );
}
