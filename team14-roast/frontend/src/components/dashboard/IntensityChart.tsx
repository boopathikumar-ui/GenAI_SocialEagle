import { Flex, Table, Tbody, Td, Text, Th, Thead, Tr, VisuallyHidden } from '@chakra-ui/react';
import type { Intensity } from '../../types';
import type { IntensitySplit } from '../../types/dashboard';
import { INTENSITY_COLORS } from './palette';
import { ChartCard } from './ChartCard';

interface Props {
  data: IntensitySplit;
}

const ORDER: Intensity[] = ['mild', 'medium', 'spicy'];
const LABELS: Record<Intensity, string> = { mild: 'Mild', medium: 'Medium', spicy: 'Spicy' };

function pct(n: number, total: number): number {
  return total === 0 ? 0 : Math.round((n / total) * 100);
}

export function summarizeIntensity(data: IntensitySplit): string {
  const total = ORDER.reduce((s, k) => s + data[k], 0);
  if (total === 0) return 'No roasts in this period.';
  return ORDER.map((k) => `${LABELS[k]} ${data[k]} (${pct(data[k], total)}%)`).join(', ');
}

export function IntensityChart({ data }: Props) {
  const total = ORDER.reduce((s, k) => s + data[k], 0);
  let offset = 0;

  return (
    <ChartCard title="Intensity split" summary={summarizeIntensity(data)}>
      <svg viewBox="0 0 600 40" width="100%" role="img" aria-label="Stacked bar of roast intensity">
        <rect x={0} y={0} width={600} height={40} fill="#EDF2F7" />
        {total > 0 &&
          ORDER.map((k) => {
            const w = (data[k] / total) * 600;
            const x = offset;
            offset += w;
            return w > 0 ? (
              <rect key={k} x={x} y={0} width={w} height={40} fill={INTENSITY_COLORS[k]}>
                <title>{`${LABELS[k]}: ${data[k]}`}</title>
              </rect>
            ) : null;
          })}
      </svg>
      <Flex gap={4} mt={3} wrap="wrap">
        {ORDER.map((k) => (
          <Flex key={k} align="center" gap={2}>
            <svg width="12" height="12" aria-hidden="true">
              <rect width="12" height="12" fill={INTENSITY_COLORS[k]} />
            </svg>
            <Text fontSize="sm">
              {LABELS[k]}: {data[k]}
            </Text>
          </Flex>
        ))}
      </Flex>
      <VisuallyHidden>
        <Table>
          <caption>Intensity split</caption>
          <Thead>
            <Tr>
              <Th>Intensity</Th>
              <Th>Roasts</Th>
            </Tr>
          </Thead>
          <Tbody>
            {ORDER.map((k) => (
              <Tr key={k}>
                <Td>{LABELS[k]}</Td>
                <Td>{data[k]}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </VisuallyHidden>
    </ChartCard>
  );
}
