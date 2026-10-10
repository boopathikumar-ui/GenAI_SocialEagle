import { Box, Button, Container, Heading, Text, VStack } from '@chakra-ui/react';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { IntensityPicker } from '../components/roast/IntensityPicker';
import { LanguagePicker } from '../components/roast/LanguagePicker';
import { LoadingMessages } from '../components/roast/LoadingMessages';
import { RoastDisplay } from '../components/roast/RoastDisplay';
import { RoastError } from '../components/roast/RoastError';
import { ShareButton } from '../components/roast/ShareButton';
import { UrlInput } from '../components/roast/UrlInput';
import { useAuth } from '../hooks/useAuth';
import { useCreateRoast } from '../hooks/useRoasts';
import { validateGithubUrl } from '../services/roastService';
import type { Intensity, Roast, RoastLanguage } from '../types';

export default function LandingPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { create, isLoading, error, clearError } = useCreateRoast();
  const [url, setUrl] = useState('');
  const [intensity, setIntensity] = useState<Intensity>('medium');
  const [language, setLanguage] = useState<RoastLanguage>('english');
  const [urlError, setUrlError] = useState<string | null>(null);
  const [result, setResult] = useState<Roast | null>(null);

  const handleSubmit = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    const validation = validateGithubUrl(url);
    setUrlError(validation);
    if (validation) return;
    clearError();
    const roast = await create({ github_url: url.trim(), intensity, language });
    if (!roast) return;
    if (isAuthenticated) navigate(`/roasts/${roast.id}`);
    else setResult(roast);
  };

  const reset = (): void => {
    setResult(null);
    setUrl('');
  };

  return (
    <PageWrapper>
      <Container maxW="2xl" py={16}>
        <VStack spacing={8} align="stretch">
          <Box textAlign="center">
            <Heading size="2xl" bgGradient="linear(to-r, purple.500, pink.500)" bgClip="text">
              Get your GitHub roasted
            </Heading>
            <Text mt={4} fontSize="lg" color="gray.600">
              Paste a profile or repo URL. Pick your pain level. Try not to cry.
            </Text>
          </Box>

          {result ? (
            <GlassCard>
              <VStack align="stretch" spacing={5}>
                <RoastDisplay roast={result} />
                {result.is_public && <ShareButton slug={result.share_slug} />}
                <Button onClick={reset} variant="outline">
                  Roast another
                </Button>
                <Text fontSize="sm" color="gray.500">
                  This roast is private and is only shown here.{' '}
                  <Button as={RouterLink} to="/register" variant="link" size="sm" colorScheme="purple">
                    Sign up
                  </Button>{' '}
                  to save your roasts and choose which ones to share.
                </Text>
              </VStack>
            </GlassCard>
          ) : (
            <GlassCard>
              {isLoading ? (
                <LoadingMessages />
              ) : (
                <form onSubmit={(e) => void handleSubmit(e)} noValidate>
                  <VStack spacing={5} align="stretch">
                    <UrlInput value={url} onChange={setUrl} error={urlError} />
                    <Box display="flex" justifyContent="center" flexWrap="wrap" gap={3}>
                      <IntensityPicker value={intensity} onChange={setIntensity} />
                      <LanguagePicker value={language} onChange={setLanguage} />
                    </Box>
                    {error && <RoastError error={error} />}
                    <GradientButton type="submit" size="lg">
                      Roast me
                    </GradientButton>
                  </VStack>
                </form>
              )}
            </GlassCard>
          )}
        </VStack>
      </Container>
    </PageWrapper>
  );
}
