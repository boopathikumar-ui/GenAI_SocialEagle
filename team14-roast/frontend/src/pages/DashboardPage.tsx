import {
  Alert,
  AlertIcon,
  Box,
  Button,
  Flex,
  Heading,
  Link,
  SimpleGrid,
  Skeleton,
  Text,
  VStack,
} from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { IntensityChart } from '../components/dashboard/IntensityChart';
import { LanguagesChart } from '../components/dashboard/LanguagesChart';
import { RangeSelector } from '../components/dashboard/RangeSelector';
import { RoastsPerDayChart } from '../components/dashboard/RoastsPerDayChart';
import { StatCard } from '../components/dashboard/StatCard';
import { TopRoastsList } from '../components/dashboard/TopRoastsList';
import { useDashboard } from '../hooks/useDashboard';

export default function DashboardPage() {
  const { stats, isLoading, error, days, setDays, retry } = useDashboard(30);
  const isEmpty = stats !== null && stats.totals.roasts === 0;

  return (
    <PageWrapper>
      <Box maxW="4xl" mx="auto" px={4} py={12}>
        <Flex justify="space-between" align="center" wrap="wrap" gap={3} mb={6}>
          <Heading size="lg">Dashboard</Heading>
          <Flex align="center" gap={3}>
            <RangeSelector value={days} onChange={setDays} />
            <Link as={RouterLink} to="/settings" color="purple.700">
              Settings
            </Link>
          </Flex>
        </Flex>

        {error && (
          <Alert status="error" rounded="md" mb={4}>
            <AlertIcon />
            <Text flex="1">{error}</Text>
            <Button size="sm" onClick={retry}>
              Retry
            </Button>
          </Alert>
        )}

        {isLoading && !stats && (
          <VStack spacing={4} align="stretch" data-testid="dashboard-skeleton">
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
              <Skeleton h="90px" rounded="xl" />
              <Skeleton h="90px" rounded="xl" />
              <Skeleton h="90px" rounded="xl" />
            </SimpleGrid>
            <Skeleton h="220px" rounded="xl" />
            <Skeleton h="120px" rounded="xl" />
          </VStack>
        )}

        {stats && isEmpty && !error && (
          <VStack spacing={4} py={12} role="status">
            <Heading size="md">Nothing here yet</Heading>
            <Text color="gray.600">Roast something first and your stats will show up here.</Text>
            <Button as={RouterLink} to="/" colorScheme="purple">
              Roast something first
            </Button>
          </VStack>
        )}

        {stats && !isEmpty && (
          <VStack spacing={4} align="stretch" opacity={isLoading ? 0.6 : 1} aria-busy={isLoading}>
            <Text fontSize="sm" color="gray.600">
              The range selector applies to the daily chart. All other figures cover all time.
            </Text>
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
              <StatCard label="Roasts" value={stats.totals.roasts} />
              <StatCard label="Public roasts" value={stats.totals.public_roasts} />
              <StatCard label="Reactions received" value={stats.totals.reactions_received} />
            </SimpleGrid>
            <RoastsPerDayChart data={stats.roasts_per_day} />
            <IntensityChart data={stats.intensity_split} />
            <LanguagesChart data={stats.top_languages} />
            <TopRoastsList roasts={stats.top_roasts} />
          </VStack>
        )}
      </Box>
    </PageWrapper>
  );
}
