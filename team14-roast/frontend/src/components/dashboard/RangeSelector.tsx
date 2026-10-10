import { Button, ButtonGroup } from '@chakra-ui/react';
import type { DashboardRange } from '../../types/dashboard';

interface Props {
  value: DashboardRange;
  onChange: (days: DashboardRange) => void;
}

const OPTIONS: DashboardRange[] = [7, 30, 90];

export function RangeSelector({ value, onChange }: Props) {
  return (
    <ButtonGroup isAttached role="group" aria-label="Date range">
      {OPTIONS.map((d) => (
        <Button
          key={d}
          aria-pressed={value === d}
          colorScheme={value === d ? 'purple' : 'gray'}
          variant={value === d ? 'solid' : 'outline'}
          onClick={() => onChange(d)}
        >
          {d} days
        </Button>
      ))}
    </ButtonGroup>
  );
}
