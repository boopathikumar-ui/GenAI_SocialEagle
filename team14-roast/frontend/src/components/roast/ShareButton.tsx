import { HStack, Input } from '@chakra-ui/react';
import { shareUrl } from '../../services/roastService';
import { CopyButton } from './CopyButton';

interface ShareButtonProps {
  slug: string;
}

export function ShareButton({ slug }: ShareButtonProps) {
  const url = shareUrl(slug);
  return (
    <HStack w="full">
      <Input size="sm" readOnly value={url} aria-label="Share link" onFocus={(e) => e.target.select()} />
      <CopyButton text={url} label="Copy link" />
    </HStack>
  );
}
