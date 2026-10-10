import { Box, Button, ButtonGroup, Container, Heading, SimpleGrid, Skeleton, Text, VStack } from '@chakra-ui/react';
import { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { GalleryCard } from '../components/gallery/GalleryCard';
import { PageWrapper } from '../components/layout/PageWrapper';
import { RoastError } from '../components/roast/RoastError';
import { useGallery } from '../hooks/useGallery';
import type { GallerySort } from '../types/gallery';

const SORTS: { value: GallerySort; label: string }[] = [
  { value: 'new', label: 'Newest' },
  { value: 'top', label: 'Top' },
];

export default function GalleryPage() {
  const [sort, setSort] = useState<GallerySort>('new');
  const { items, isLoading, isLoadingMore, error, hasMore, loadMore, retry } = useGallery(sort);

  return (
    <PageWrapper>
      <Container maxW="6xl" py={12}>
        <VStack spacing={8} align="stretch">
          <VStack spacing={3} textAlign="center">
            <Heading size="2xl">Roast Gallery</Heading>
            <Text color="whiteAlpha.800">The best burns from the community. React to your favorites.</Text>
            <ButtonGroup isAttached role="group" aria-label="Sort roasts">
              {SORTS.map((s) => (
                <Button
                  key={s.value}
                  onClick={() => setSort(s.value)}
                  aria-pressed={sort === s.value}
                  colorScheme={sort === s.value ? 'purple' : 'gray'}
                  variant={sort === s.value ? 'solid' : 'outline'}
                >
                  {s.label}
                </Button>
              ))}
            </ButtonGroup>
          </VStack>

          {error && (
            <VStack spacing={3}>
              <RoastError error={error} />
              <Button onClick={retry} colorScheme="purple">
                Try again
              </Button>
            </VStack>
          )}

          {isLoading && (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6} aria-busy="true" data-testid="gallery-skeleton">
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} h="220px" rounded="2xl" />
              ))}
            </SimpleGrid>
          )}

          {!isLoading && !error && items.length === 0 && (
            <VStack spacing={4} py={10}>
              <Text fontSize="lg">No public roasts yet. Be the first!</Text>
              <Button as={RouterLink} to="/" colorScheme="purple">
                Roast a GitHub profile
              </Button>
            </VStack>
          )}

          {!isLoading && items.length > 0 && (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
              {items.map((roast) => (
                <Box key={roast.id}>
                  <GalleryCard roast={roast} />
                </Box>
              ))}
            </SimpleGrid>
          )}

          {!isLoading && hasMore && !error && (
            <Button onClick={loadMore} isLoading={isLoadingMore} alignSelf="center" colorScheme="purple" variant="outline">
              Load more
            </Button>
          )}
        </VStack>
      </Container>
    </PageWrapper>
  );
}
