import { Box, Divider, Heading, Link, Text, VStack } from '@chakra-ui/react';
import { Link as RouterLink, Navigate, useNavigate } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { AuthForm } from '../components/auth/AuthForm';
import type { AuthFormValues } from '../components/auth/AuthForm';
import { GoogleLoginButton } from '../components/auth/GoogleLoginButton';
import { useAuth } from '../hooks/useAuth';

export default function RegisterPage() {
  const { register, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  if (!isLoading && isAuthenticated) return <Navigate to="/" replace />;

  const handleSubmit = async (v: AuthFormValues): Promise<void> => {
    await register(v.email, v.password, v.fullName);
    navigate('/', { replace: true });
  };

  return (
    <PageWrapper>
      <Box maxW="md" mx="auto" px={4} py={16}>
        <GlassCard bg="whiteAlpha.800" borderColor="gray.200">
          <VStack spacing={5} align="stretch">
            <Heading size="lg" textAlign="center">
              Create your account
            </Heading>
            <AuthForm mode="register" onSubmit={handleSubmit} />
            <Divider />
            <GoogleLoginButton label="Sign up with Google" />
            <Text fontSize="sm" textAlign="center">
              Already registered?{' '}
              <Link as={RouterLink} to="/login" color="purple.500">
                Log in
              </Link>
            </Text>
          </VStack>
        </GlassCard>
      </Box>
    </PageWrapper>
  );
}
