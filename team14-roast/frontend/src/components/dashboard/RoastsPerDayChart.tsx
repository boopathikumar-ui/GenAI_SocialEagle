import { Table, Tbody, Td, Th, Thead, Tr, VisuallyHidden } from '@chakra-ui/react';
import type { RoastsPerDayPoint } from '../../types/dashboard';
import { AXIS_COLOR, GRID_COLOR, SERIES_COLOR } from './palette';
import { ChartCard } from './ChartCard';

interface Props {
  data: RoastsPerDayPoint[];
}

const W = 600;
const H = 180;
const PAD = 24;

export function summarizePerDay(data: RoastsPerDayPoint[]): string {
  const total = data.reduce((sum, p) => sum + p.count, 0);
  if (data.length === 0 || total === 0) return 'No roasts in this period.';
  const peak = data.reduce((best, p) => (p.count > best.count ? p : best), data[0]);
  return `${total} roasts over ${data.length} days. Busiest day: ${peak.date} with ${peak.count}.`;
}

export function RoastsPerDayChart({ data }: Props) {
  const max = Math.max(1, ...data.map((p) => p.count));
  const slot = data.length > 0 ? (W - PAD) / data.length : 0;
  const barW = Math.max(1, slot * 0.7);
  const innerH = H - PAD;

  return (
    <ChartCard title="Roasts per day" summary={summarizePerDay(data)}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Bar chart of roasts per day">
        <line x1={PAD} y1={innerH} x2={W} y2={innerH} stroke={AXIS_COLOR} />
        <line x1={PAD} y1={4} x2={PAD} y2={innerH} stroke={GRID_COLOR} />
        <text x={0} y={12} fontSize="11" fill={AXIS_COLOR}>
          {max}
        </text>
        <text x={8} y={innerH} fontSize="11" fill={AXIS_COLOR}>
          0
        </text>
        {data.map((p, i) => {
          const h = (p.count / max) * (innerH - 8);
          return (
            <rect
              key={p.date}
              x={PAD + i * slot + (slot - barW) / 2}
              y={innerH - h}
              width={barW}
              height={h}
              fill={SERIES_COLOR}
            >
              <title>{`${p.date}: ${p.count}`}</title>
            </rect>
          );
        })}
        {data.length > 0 && (
          <>
            <text x={PAD} y={H - 6} fontSize="11" fill={AXIS_COLOR}>
              {data[0].date}
            </text>
            <text x={W} y={H - 6} fontSize="11" fill={AXIS_COLOR} textAnchor="end">
              {data[data.length - 1].date}
            </text>
          </>
        )}
      </svg>
      <VisuallyHidden>
        <Table>
          <caption>Roasts per day</caption>
          <Thead>
            <Tr>
              <Th>Date</Th>
              <Th>Roasts</Th>
            </Tr>
          </Thead>
          <Tbody>
            {data.map((p) => (
              <Tr key={p.date}>
                <Td>{p.date}</Td>
                <Td>{p.count}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </VisuallyHidden>
    </ChartCard>
  );
}
