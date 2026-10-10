import { Button, Container, Spinner, VStack } from '@chakra-ui/react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { RoastDisplay } from '../components/roast/RoastDisplay';
import { RoastError } from '../components/roast/RoastError';
import { useNoIndex } from '../hooks/useNoIndex';
import { useSharedRoast } from '../hooks/useRoasts';

export default function SharedRoastPage() {
  useNoIndex();
  const { slug } = useParams<{ slug: string }>();
  const { roast, isLoading, error } = useSharedRoast(slug);

  return (
    <PageWrapper>
      <Container maxW="2xl" py={12}>
        <VStack spacing={6} align="stretch">
          {isLoading && <Spinner alignSelf="center" size="xl" color="purple.400" />}
          {error && <RoastError error={error} />}
          {roast && (
            <GlassCard>
              <RoastDisplay roast={roast} />
            </GlassCard>
          )}
          <Button as={RouterLink} to="/" colorScheme="purple">
            Get your own GitHub roasted
          </Button>
        </VStack>
      </Container>
    </PageWrapper>
  );
}
