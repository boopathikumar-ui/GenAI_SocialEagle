import { Button, ButtonGroup } from '@chakra-ui/react';
import type { Intensity } from '../../types';

interface IntensityPickerProps {
  value: Intensity;
  onChange: (value: Intensity) => void;
  isDisabled?: boolean;
}

const OPTIONS: Array<{ value: Intensity; label: string; scheme: string }> = [
  { value: 'mild', label: 'Mild', scheme: 'green' },
  { value: 'medium', label: 'Medium', scheme: 'orange' },
  { value: 'spicy', label: 'Spicy', scheme: 'red' },
];

export function IntensityPicker({ value, onChange, isDisabled }: IntensityPickerProps) {
  return (
    <ButtonGroup isAttached role="radiogroup" aria-label="Roast intensity" isDisabled={isDisabled}>
      {OPTIONS.map((o) => (
        <Button
          key={o.value}
          role="radio"
          aria-checked={value === o.value}
          colorScheme={o.scheme}
          variant={value === o.value ? 'solid' : 'outline'}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </Button>
      ))}
    </ButtonGroup>
  );
}
