import {
  Alert,
  AlertIcon,
  Box,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Text,
  VStack,
  useToast,
} from '@chakra-ui/react';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { useAuth } from '../hooks/useAuth';
import { authService, getErrorMessage } from '../services/authService';

export default function ProfilePage() {
  const { user, refreshUser, logout } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const [fullName, setFullName] = useState<string>(user?.full_name ?? '');
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (fullName.trim().length < 2) {
      setError('Name must be at least 2 characters');
      return;
    }
    setError(null);
    setSaving(true);
    try {
      await authService.updateMe({ full_name: fullName.trim() });
      await refreshUser();
      toast({ title: 'Profile updated', status: 'success', duration: 3000 });
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Could not update profile'));
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = async (): Promise<void> => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <PageWrapper>
      <Box maxW="md" mx="auto" px={4} py={16}>
        <GlassCard bg="whiteAlpha.800" borderColor="gray.200">
          <VStack spacing={5} align="stretch">
            <Heading size="lg">Your profile</Heading>
            <Text color="gray.600">{user?.email}</Text>
            <form onSubmit={(e) => void handleSave(e)} noValidate>
              <VStack spacing={4}>
                {error && (
                  <Alert status="error" rounded="md">
                    <AlertIcon />
                    {error}
                  </Alert>
                )}
                <FormControl>
                  <FormLabel>Full name</FormLabel>
                  <Input value={fullName} onChange={(e) => setFullName(e.target.value)} />
                </FormControl>
                <GradientButton type="submit" w="full" isLoading={saving}>
                  Save changes
                </GradientButton>
              </VStack>
            </form>
            <GradientButton variant="outline" onClick={() => void handleLogout()}>
              Log out
            </GradientButton>
          </VStack>
        </GlassCard>
      </Box>
    </PageWrapper>
  );
}
