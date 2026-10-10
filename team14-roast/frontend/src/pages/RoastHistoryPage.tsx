import { Button, Container, Heading, HStack, Spinner, Text, VStack } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { AnimatedList } from '../components/ui/AnimatedList';
import { RoastCard } from '../components/roast/RoastCard';
import { RoastError } from '../components/roast/RoastError';
import { useRoastList } from '../hooks/useRoasts';

export default function RoastHistoryPage() {
  const { items, total, page, pageSize, setPage, isLoading, error, remove, togglePublic } = useRoastList();
  const hasNext = page * pageSize < total;

  return (
    <PageWrapper>
      <Container maxW="3xl" py={12}>
        <VStack spacing={6} align="stretch">
          <HStack justify="space-between">
            <Heading size="lg">Your roasts</Heading>
            <Button as={RouterLink} to="/" colorScheme="purple" size="sm">
              New roast
            </Button>
          </HStack>
          {isLoading && <Spinner alignSelf="center" size="xl" color="purple.400" />}
          {error && <RoastError error={error} />}
          {!isLoading && !error && items.length === 0 && <Text>No roasts yet. Go roast someone.</Text>}
          {items.length > 0 && (
            <AnimatedList>
              {items.map((r) => (
                <RoastCard
                  key={r.id}
                  roast={r}
                  onDelete={(id) => void remove(id)}
                  onTogglePublic={(id, v) => void togglePublic(id, v)}
                />
              ))}
            </AnimatedList>
          )}
          <HStack justify="center">
            <Button size="sm" isDisabled={page <= 1} onClick={() => setPage(page - 1)}>
              Previous
            </Button>
            <Button size="sm" isDisabled={!hasNext} onClick={() => setPage(page + 1)}>
              Next
            </Button>
          </HStack>
        </VStack>
      </Container>
    </PageWrapper>
  );
}
