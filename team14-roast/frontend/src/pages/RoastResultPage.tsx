import { Button, Container, HStack, Spinner, VStack } from '@chakra-ui/react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { CopyButton } from '../components/roast/CopyButton';
import { RoastDisplay } from '../components/roast/RoastDisplay';
import { RoastError } from '../components/roast/RoastError';
import { ShareButton } from '../components/roast/ShareButton';
import { useNoIndex } from '../hooks/useNoIndex';
import { useRoast } from '../hooks/useRoasts';

export default function RoastResultPage() {
  useNoIndex();
  const { id } = useParams<{ id: string }>();
  const numericId = id !== undefined && /^\d+$/.test(id) ? Number(id) : undefined;
  const { roast, isLoading, error } = useRoast(numericId);

  return (
    <PageWrapper>
      <Container maxW="2xl" py={12}>
        <VStack spacing={6} align="stretch">
          {numericId === undefined && (
            <RoastError error={{ kind: 'not_found', title: 'Not found', message: 'That roast does not exist.' }} />
          )}
          {numericId !== undefined && isLoading && <Spinner alignSelf="center" size="xl" color="purple.400" />}
          {error && <RoastError error={error} />}
          {roast && (
            <GlassCard>
              <VStack align="stretch" spacing={5}>
                <RoastDisplay roast={roast} />
                <HStack>
                  <CopyButton text={roast.roast_text} label="Copy roast" />
                </HStack>
                {roast.is_public ? (
                  <ShareButton slug={roast.share_slug} />
                ) : (
                  <Button as={RouterLink} to="/roasts" size="sm" variant="link">
                    Make it public from your history to share
                  </Button>
                )}
              </VStack>
            </GlassCard>
          )}
          <Button as={RouterLink} to="/" variant="outline">
            Roast someone else
          </Button>
        </VStack>
      </Container>
    </PageWrapper>
  );
}
