import { Table, Tbody, Td, Th, Thead, Tr, VisuallyHidden } from '@chakra-ui/react';
import type { LanguageCount } from '../../types/dashboard';
import { AXIS_COLOR, SERIES_COLOR } from './palette';
import { ChartCard } from './ChartCard';

interface Props {
  data: LanguageCount[];
}

const ROW_H = 26;

export function summarizeLanguages(data: LanguageCount[]): string {
  const total = data.reduce((s, l) => s + l.count, 0);
  if (data.length === 0 || total === 0) return 'No language data yet.';
  return `Top language: ${data[0].language} (${data[0].count}). ${data.length} languages shown.`;
}

export function LanguagesChart({ data }: Props) {
  const max = Math.max(1, ...data.map((l) => l.count));
  const h = Math.max(ROW_H, data.length * ROW_H);

  return (
    <ChartCard title="Top languages" summary={summarizeLanguages(data)}>
      <svg viewBox={`0 0 600 ${h}`} width="100%" role="img" aria-label="Bar chart of top languages">
        {data.map((l, i) => {
          const w = (l.count / max) * 380;
          const y = i * ROW_H;
          return (
            <g key={l.language}>
              <text x={0} y={y + 17} fontSize="13" fill={AXIS_COLOR}>
                {l.language}
              </text>
              <rect x={140} y={y + 4} width={w} height={ROW_H - 10} fill={SERIES_COLOR}>
                <title>{`${l.language}: ${l.count}`}</title>
              </rect>
              <text x={146 + w} y={y + 17} fontSize="12" fill={AXIS_COLOR}>
                {l.count}
              </text>
            </g>
          );
        })}
      </svg>
      <VisuallyHidden>
        <Table>
          <caption>Top languages</caption>
          <Thead>
            <Tr>
              <Th>Language</Th>
              <Th>Roasts</Th>
            </Tr>
          </Thead>
          <Tbody>
            {data.map((l) => (
              <Tr key={l.language}>
                <Td>{l.language}</Td>
                <Td>{l.count}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </VisuallyHidden>
    </ChartCard>
  );
}
