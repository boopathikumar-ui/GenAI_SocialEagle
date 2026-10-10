import { FormControl, FormErrorMessage, Input } from '@chakra-ui/react';

interface UrlInputProps {
  value: string;
  onChange: (value: string) => void;
  error: string | null;
  isDisabled?: boolean;
}

export function UrlInput({ value, onChange, error, isDisabled }: UrlInputProps) {
  return (
    <FormControl isInvalid={error !== null}>
      <Input
        size="lg"
        rounded="full"
        bg="whiteAlpha.800"
        placeholder="https://github.com/username"
        aria-label="GitHub URL"
        value={value}
        isDisabled={isDisabled}
        onChange={(e) => onChange(e.target.value)}
      />
      <FormErrorMessage>{error}</FormErrorMessage>
    </FormControl>
  );
}
