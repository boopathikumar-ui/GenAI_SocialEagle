import {
  Alert,
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  AlertIcon,
  Box,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Text,
  VStack,
  useToast,
} from '@chakra-ui/react';
import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GradientButton } from '../components/ui/GradientButton';
import { useAuth } from '../hooks/useAuth';
import { authService, getErrorMessage } from '../services/authService';
import { dashboardService } from '../services/dashboardService';

export default function SettingsPage() {
  const { user, refreshUser, logout } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const cancelRef = useRef<HTMLButtonElement>(null);
  const [fullName, setFullName] = useState<string>(user?.full_name ?? '');
  const [saving, setSaving] = useState<boolean>(false);
  const [nameError, setNameError] = useState<string | null>(null);
  const [pending, setPending] = useState<boolean | null>(null);
  const [bulkBusy, setBulkBusy] = useState<boolean>(false);
  const [bulkError, setBulkError] = useState<string | null>(null);

  const handleSave = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (fullName.trim().length < 2) {
      setNameError('Name must be at least 2 characters');
      return;
    }
    setNameError(null);
    setSaving(true);
    try {
      await authService.updateMe({ full_name: fullName.trim() });
      await refreshUser();
      toast({ title: 'Name updated', status: 'success', duration: 3000 });
    } catch (err: unknown) {
      setNameError(getErrorMessage(err, 'Could not update name'));
    } finally {
      setSaving(false);
    }
  };

  const confirmVisibility = async (): Promise<void> => {
    if (pending === null || bulkBusy) return;
    const target = pending;
    setBulkBusy(true);
    setBulkError(null);
    try {
      const { updated } = await dashboardService.setAllRoastsVisibility(target);
      toast({
        title: `${updated} roasts made ${target ? 'public' : 'private'}`,
        status: 'success',
        duration: 4000,
      });
    } catch (err: unknown) {
      setBulkError(getErrorMessage(err, 'Could not update roast visibility'));
    } finally {
      setBulkBusy(false);
      setPending(null);
    }
  };

  const handleLogout = async (): Promise<void> => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <PageWrapper>
      <Box maxW="md" mx="auto" px={4} py={12}>
        <VStack spacing={8} align="stretch">
          <Heading size="lg">Settings</Heading>

          <Box as="section" aria-labelledby="settings-name">
            <Heading as="h2" size="md" id="settings-name" mb={3}>
              Display name
            </Heading>
            <form onSubmit={(e) => void handleSave(e)} noValidate>
              <VStack spacing={4} align="stretch">
                {nameError && (
                  <Alert status="error" rounded="md">
                    <AlertIcon />
                    {nameError}
                  </Alert>
                )}
                <FormControl>
                  <FormLabel>Full name</FormLabel>
                  <Input value={fullName} onChange={(e) => setFullName(e.target.value)} />
                </FormControl>
                <GradientButton type="submit" isLoading={saving}>
                  Save name
                </GradientButton>
              </VStack>
            </form>
          </Box>

          <Box as="section" aria-labelledby="settings-visibility">
            <Heading as="h2" size="md" id="settings-visibility" mb={3}>
              Roast visibility
            </Heading>
            {bulkError && (
              <Alert status="error" rounded="md" mb={3}>
                <AlertIcon />
                {bulkError}
              </Alert>
            )}
            <VStack spacing={3} align="stretch">
              <Button variant="outline" onClick={() => setPending(false)}>
                Make all my roasts private
              </Button>
              <Button variant="outline" onClick={() => setPending(true)}>
                Make all my roasts public
              </Button>
            </VStack>
          </Box>

          <Box as="section" aria-labelledby="settings-session">
            <Heading as="h2" size="md" id="settings-session" mb={3}>
              Session
            </Heading>
            <VStack spacing={3} align="stretch">
              <Button variant="outline" onClick={() => void handleLogout()}>
                Log out
              </Button>
              <Button as={RouterLink} to="/profile" variant="link">
                Back to profile
              </Button>
            </VStack>
          </Box>
        </VStack>

        <AlertDialog
          isOpen={pending !== null}
          leastDestructiveRef={cancelRef}
          onClose={() => setPending(null)}
          isCentered
        >
          <AlertDialogOverlay>
            <AlertDialogContent>
              <AlertDialogHeader>
                {pending ? 'Make all roasts public?' : 'Make all roasts private?'}
              </AlertDialogHeader>
              <AlertDialogBody>
                <Text>
                  This changes every roast you have created.
                  {pending
                    ? ' Anyone with a link will be able to see them.'
                    : ' Existing share links will stop working.'}
                </Text>
              </AlertDialogBody>
              <AlertDialogFooter gap={3}>
                <Button ref={cancelRef} onClick={() => setPending(null)}>
                  Cancel
                </Button>
                <Button
                  colorScheme="purple"
                  isLoading={bulkBusy}
                  onClick={() => void confirmVisibility()}
                >
                  Confirm
                </Button>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialogOverlay>
        </AlertDialog>
      </Box>
    </PageWrapper>
  );
}
