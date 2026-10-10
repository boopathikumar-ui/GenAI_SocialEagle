import { Alert, AlertIcon, Box, Center, Link, Spinner, Text, VStack } from '@chakra-ui/react';
import { useEffect, useRef, useState } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { useAuth } from '../hooks/useAuth';
import { setTokens } from '../services/api';

const MISSING_TOKENS = 'Google sign-in failed. Missing tokens.';

function clearHash(): void {
  window.history.replaceState(null, '', window.location.pathname + window.location.search);
}

export default function AuthCallbackPage() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const [error, setError] = useState<string | null>(null);
  // Tokens are captured once: StrictMode re-runs effects after the hash is cleared.
  const captured = useRef<{ access: string | null; refresh: string | null } | null>(null);

  useEffect(() => {
    if (captured.current === null) {
      const fragment = new URLSearchParams(window.location.hash.replace(/^#/, ''));
      captured.current = {
        access: fragment.get('access_token'),
        refresh: fragment.get('refresh_token'),
      };
    }
    clearHash();
    const { access, refresh } = captured.current;
    if (!access || !refresh) {
      setError(MISSING_TOKENS);
      return;
    }
    setTokens({ access_token: access, refresh_token: refresh });
    let active = true;
    void refreshUser()
      .then(() => {
        if (active) navigate('/', { replace: true });
      })
      .catch(() => {
        if (active) setError('Google sign-in failed. Please try again.');
      });
    return () => {
      active = false;
    };
  }, [navigate, refreshUser]);

  return (
    <PageWrapper>
      <Center minH="100vh">
        {error ? (
          <Box maxW="md" px={4}>
            <Alert status="error" rounded="md">
              <AlertIcon />
              <VStack align="start" spacing={1}>
                <Text>{error}</Text>
                <Link as={RouterLink} to="/login" color="purple.500">
                  Back to login
                </Link>
              </VStack>
            </Alert>
          </Box>
        ) : (
          <Spinner size="xl" color="purple.500" />
        )}
      </Center>
    </PageWrapper>
  );
}
