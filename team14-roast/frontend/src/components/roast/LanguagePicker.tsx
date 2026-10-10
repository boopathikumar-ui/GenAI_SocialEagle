import { Button, ButtonGroup } from '@chakra-ui/react';
import type { RoastLanguage } from '../../types';

interface LanguagePickerProps {
  value: RoastLanguage;
  onChange: (value: RoastLanguage) => void;
  isDisabled?: boolean;
}

const OPTIONS: Array<{ value: RoastLanguage; label: string }> = [
  { value: 'english', label: 'English' },
  { value: 'thanglish', label: 'Thanglish' },
];

export function LanguagePicker({ value, onChange, isDisabled }: LanguagePickerProps) {
  return (
    <ButtonGroup isAttached role="radiogroup" aria-label="Roast language" isDisabled={isDisabled}>
      {OPTIONS.map((o) => (
        <Button
          key={o.value}
          role="radio"
          aria-checked={value === o.value}
          colorScheme="purple"
          variant={value === o.value ? 'solid' : 'outline'}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </Button>
      ))}
    </ButtonGroup>
  );
}
