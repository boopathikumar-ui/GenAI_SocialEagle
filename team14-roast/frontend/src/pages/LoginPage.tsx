import { Alert, AlertIcon, Box, Divider, Heading, Link, Text, VStack } from '@chakra-ui/react';
import { Link as RouterLink, Navigate, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { AuthForm } from '../components/auth/AuthForm';
import type { AuthFormValues } from '../components/auth/AuthForm';
import { GoogleLoginButton } from '../components/auth/GoogleLoginButton';
import { useAuth } from '../hooks/useAuth';

interface LocationState {
  from?: string;
}

export default function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const oauthFailed = searchParams.get('error') === 'oauth_failed';
  const from = (location.state as LocationState | null)?.from ?? '/';

  if (!isLoading && isAuthenticated) return <Navigate to={from} replace />;

  const handleSubmit = async (v: AuthFormValues): Promise<void> => {
    await login(v.email, v.password);
    navigate(from, { replace: true });
  };

  return (
    <PageWrapper>
      <Box maxW="md" mx="auto" px={4} py={16}>
        <GlassCard bg="whiteAlpha.800" borderColor="gray.200">
          <VStack spacing={5} align="stretch">
            <Heading size="lg" textAlign="center">
              Welcome back
            </Heading>
            {oauthFailed && (
              <Alert status="error" rounded="md">
                <AlertIcon />
                Google sign-in did not work. Please try again or use your email and password.
              </Alert>
            )}
            <AuthForm mode="login" onSubmit={handleSubmit} />
            <Divider />
            <GoogleLoginButton />
            <Text fontSize="sm" textAlign="center">
              No account?{' '}
              <Link as={RouterLink} to="/register" color="purple.500">
                Sign up
              </Link>
            </Text>
          </VStack>
        </GlassCard>
      </Box>
    </PageWrapper>
  );
}
