import { LineChart, Line } from 'recharts';
import { TrendingUp, Users } from 'lucide-react';
import type { TopPick } from '../data/mockData';

interface TopPickCardProps {
  pick: TopPick;
}

export function TopPickCard({ pick }: TopPickCardProps) {
  const chartData = pick.sparklineData.map((value, index) => ({ index, value }));

  return (
    <div
      className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg p-4 hover:border-[var(--text-tertiary)] transition-colors"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="text-2xl font-bold mono">{pick.ticker}</div>
          <div className="text-xs text-[var(--text-secondary)] mt-1">{pick.company}</div>
        </div>
        <div className="text-right">
          <div className={`text-lg font-semibold mono ${pick.changePercent >= 0 ? 'text-[var(--accent-buy)]' : 'text-[var(--accent-sell)]'}`}>
            {pick.changePercent >= 0 ? '+' : ''}{pick.changePercent}%
          </div>
          <TrendingUp size={16} className={pick.changePercent >= 0 ? 'text-[var(--accent-buy)]' : 'text-[var(--accent-sell)]'} />
        </div>
      </div>

      <div className="h-12 mb-3">
        <LineChart width={240} height={48} data={chartData}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={pick.changePercent >= 0 ? 'var(--accent-buy)' : 'var(--accent-sell)'}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </div>

      <div className="flex items-center gap-2 text-[var(--text-secondary)]">
        <Users size={14} />
        <span className="text-sm mono">{pick.guruCount} institutions holding</span>
      </div>
    </div>
  );
}