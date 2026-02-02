import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from 'recharts';
import { buffettHoldings } from '../data/mockData';

interface DetailPanelProps {
  selectedGuru: string | null;
}

export function DetailPanel({ selectedGuru }: DetailPanelProps) {
  const chartData = buffettHoldings.slice(0, 5).map((holding) => ({
    name: holding.ticker,
    value: holding.portfolioPercent,
  }));

  const COLORS = ['#00C853', '#00E676', '#69F0AE', '#B9F6CA', '#E0F2F1'];

  return (
    <div className="w-96 bg-[var(--bg-secondary)] border-l border-[var(--border-color)] h-screen overflow-y-auto">
      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-1">Focus View</h2>
          <p className="text-sm text-[var(--text-secondary)]">
            {selectedGuru || 'Berkshire Hathaway'} Portfolio
          </p>
        </div>

        {/* Holdings Table */}
        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold mb-3 text-[var(--text-secondary)] uppercase">
            Top Holdings
          </h3>
          <div className="space-y-3">
            {buffettHoldings.map((holding) => (
              <div key={holding.ticker} className="border-b border-[var(--border-color)] pb-3 last:border-b-0 last:pb-0">
                <div className="flex items-start justify-between mb-1">
                  <div>
                    <div className="font-semibold mono">{holding.ticker}</div>
                    <div className="text-xs text-[var(--text-secondary)] truncate">
                      {holding.company}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold mono text-sm">{holding.value}</div>
                    <div className="text-xs text-[var(--text-secondary)]">
                      {holding.portfolioPercent}%
                    </div>
                  </div>
                </div>
                <div className="text-xs text-[var(--text-tertiary)] mono">
                  {holding.shares.toLocaleString()} shares
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Portfolio Chart */}
        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4">
          <h3 className="text-sm font-semibold mb-3 text-[var(--text-secondary)] uppercase">
            Portfolio Distribution
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value) => (
                  <span className="text-xs text-[var(--text-secondary)] mono">{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-3 mt-6">
          <div className="bg-[var(--bg-tertiary)] rounded-lg p-3">
            <div className="text-xs text-[var(--text-secondary)] mb-1">Total AUM</div>
            <div className="text-lg font-bold mono">$360B</div>
          </div>
          <div className="bg-[var(--bg-tertiary)] rounded-lg p-3">
            <div className="text-xs text-[var(--text-secondary)] mb-1">Holdings</div>
            <div className="text-lg font-bold mono">42</div>
          </div>
          <div className="bg-[var(--bg-tertiary)] rounded-lg p-3">
            <div className="text-xs text-[var(--text-secondary)] mb-1">Q/Q Change</div>
            <div className="text-lg font-bold mono text-[var(--accent-buy)]">+2.8%</div>
          </div>
          <div className="bg-[var(--bg-tertiary)] rounded-lg p-3">
            <div className="text-xs text-[var(--text-secondary)] mb-1">Win Rate</div>
            <div className="text-lg font-bold mono text-[var(--accent-buy)]">67%</div>
          </div>
        </div>
      </div>
    </div>
  );
}