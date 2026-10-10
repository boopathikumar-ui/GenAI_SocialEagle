import { Button, HStack, Link, Text, useToast } from '@chakra-ui/react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { addReaction, removeReaction } from '../../services/galleryService';
import type { ReactionEmoji } from '../../types';
import { REACTION_EMOJIS, REACTION_GLYPHS } from '../../types/gallery';
import type { ReactionCounts, ReactionState } from '../../types/gallery';

interface ReactionBarProps {
  roastId: number;
  counts: ReactionCounts;
  mine: ReactionEmoji[];
}

export function ReactionBar({ roastId, counts, mine }: ReactionBarProps) {
  const { isAuthenticated } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [state, setState] = useState<ReactionState>({ reaction_counts: counts, my_reactions: mine });
  const [pending, setPending] = useState<ReactionEmoji | null>(null);

  const toggle = async (emoji: ReactionEmoji): Promise<void> => {
    if (!isAuthenticated) {
      if (!toast.isActive('gallery-login')) {
        toast({
          id: 'gallery-login',
          status: 'info',
          duration: 5000,
          isClosable: true,
          description: (
            <Text>
              <Link
                href="/login"
                textDecoration="underline"
                onClick={(e) => {
                  e.preventDefault();
                  navigate('/login');
                }}
              >
                Log in
              </Link>{' '}
              to react to roasts.
            </Text>
          ),
        });
      }
      return;
    }
    if (pending) return;
    const previous = state;
    const active = previous.my_reactions.includes(emoji);
    const delta = active ? -1 : 1;
    setState({
      reaction_counts: {
        ...previous.reaction_counts,
        [emoji]: Math.max(0, previous.reaction_counts[emoji] + delta),
      },
      my_reactions: active ? previous.my_reactions.filter((e) => e !== emoji) : [...previous.my_reactions, emoji],
    });
    setPending(emoji);
    try {
      const next = active ? await removeReaction(roastId, emoji) : await addReaction(roastId, emoji);
      setState(next);
    } catch {
      setState(previous);
      toast({ status: 'error', description: 'Could not save your reaction. Please try again.', duration: 4000 });
    } finally {
      setPending(null);
    }
  };

  return (
    <HStack spacing={2} role="group" aria-label="Reactions" flexWrap="wrap">
      {REACTION_EMOJIS.map((emoji) => {
        const count = state.reaction_counts[emoji];
        const active = state.my_reactions.includes(emoji);
        return (
          <Button
            key={emoji}
            size="sm"
            variant={active ? 'solid' : 'outline'}
            colorScheme={active ? 'purple' : 'gray'}
            aria-pressed={active}
            aria-label={`${emoji} reaction, ${count}`}
            onClick={() => void toggle(emoji)}
          >
            <span aria-hidden="true">{REACTION_GLYPHS[emoji]}</span>
            <Text as="span" ml={1} aria-hidden="true">
              {count}
            </Text>
          </Button>
        );
      })}
    </HStack>
  );
}
