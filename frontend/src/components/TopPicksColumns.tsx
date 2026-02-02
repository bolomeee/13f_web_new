import { TrendingUp, TrendingDown, Building2 } from 'lucide-react';
import { topIncreasesByPercent, topDecreasesByPercent, topIncreasesByInstitutions, topDecreasesByInstitutions } from '../data/mockData';
import type { TopIncreaseByPercent, TopDecreaseByPercent, TopByInstitutionCount } from '../data/mockData';

export function TopPicksColumns() {
  return (
    <div className="grid grid-cols-4 gap-6">
      {/* Left Column: Top Increases by Percent */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg overflow-hidden">
        <div className="p-3 border-b border-[var(--border-color)] bg-[var(--accent-buy)]/10">
          <div className="flex items-center gap-2">
            <TrendingUp size={16} className="text-[var(--accent-buy)]" />
            <h3 className="font-semibold text-sm">Highest Increase %</h3>
          </div>
        </div>
        <div className="h-[340px] overflow-y-auto">
          {topIncreasesByPercent.map((item, index) => (
            <div
              key={`${item.ticker}-${item.institution}-${index}`}
              className="p-3 border-b border-[var(--border-color)] last:border-b-0 hover:bg-[var(--bg-tertiary)] transition-colors h-[68px] flex flex-col justify-center"
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-baseline gap-2 min-w-0">
                  <div className="font-semibold mono text-sm flex-shrink-0">{item.ticker}</div>
                  <div className="text-[10px] text-[var(--text-secondary)] truncate">{item.company}</div>
                </div>
                <div className="text-sm font-bold mono text-[var(--accent-buy)] flex-shrink-0 ml-2">
                  +{item.increasePercent}%
                </div>
              </div>
              <div className="flex items-center gap-1 text-[10px] text-[var(--text-secondary)]">
                <Building2 size={10} className="flex-shrink-0" />
                <span className="truncate">{item.institution}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Second Column: Top Decreases by Percent */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg overflow-hidden">
        <div className="p-3 border-b border-[var(--border-color)] bg-[var(--accent-sell)]/10">
          <div className="flex items-center gap-2">
            <TrendingDown size={16} className="text-[var(--accent-sell)]" />
            <h3 className="font-semibold text-sm">Highest Decrease %</h3>
          </div>
        </div>
        <div className="max-h-[340px] overflow-y-auto">
          {topDecreasesByPercent.map((item, index) => (
            <div
              key={`${item.ticker}-${item.institution}-${index}`}
              className="p-3 border-b border-[var(--border-color)] last:border-b-0 hover:bg-[var(--bg-tertiary)] transition-colors h-[68px] flex flex-col justify-center"
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-baseline gap-2 min-w-0">
                  <div className="font-semibold mono text-sm flex-shrink-0">{item.ticker}</div>
                  <div className="text-[10px] text-[var(--text-secondary)] truncate">{item.company}</div>
                </div>
                <div className="text-sm font-bold mono text-[var(--accent-sell)] flex-shrink-0 ml-2">
                  {item.decreasePercent}%
                </div>
              </div>
              <div className="flex items-center gap-1 text-[10px] text-[var(--text-secondary)]">
                <Building2 size={10} className="flex-shrink-0" />
                <span className="truncate">{item.institution}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Middle Column: Top Increases by Institution Count */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg overflow-hidden">
        <div className="p-3 border-b border-[var(--border-color)] bg-[var(--accent-buy)]/10">
          <div className="flex items-center gap-2">
            <TrendingUp size={16} className="text-[var(--accent-buy)]" />
            <h3 className="font-semibold text-sm">Most Increased (by Institutions)</h3>
          </div>
        </div>
        <div className="max-h-[340px] overflow-y-auto">
          {topIncreasesByInstitutions.map((item, index) => (
            <div
              key={item.ticker}
              className="p-3 border-b border-[var(--border-color)] last:border-b-0 hover:bg-[var(--bg-tertiary)] transition-colors h-[68px] flex flex-col justify-center"
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-baseline gap-2 min-w-0">
                  <div className="font-semibold mono text-sm flex-shrink-0">{item.ticker}</div>
                  <div className="text-[10px] text-[var(--text-secondary)] truncate">{item.company}</div>
                </div>
                <div className="text-sm font-bold mono text-[var(--accent-buy)] flex-shrink-0 ml-2">
                  +{item.changePercent}%
                </div>
              </div>
              <div className="text-[10px] text-[var(--text-secondary)]">
                {item.institutionCount} institutions
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right Column: Top Decreases by Institution Count */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg overflow-hidden">
        <div className="p-3 border-b border-[var(--border-color)] bg-[var(--accent-sell)]/10">
          <div className="flex items-center gap-2">
            <TrendingDown size={16} className="text-[var(--accent-sell)]" />
            <h3 className="font-semibold text-sm">Most Decreased (by Institutions)</h3>
          </div>
        </div>
        <div className="h-[340px] overflow-y-auto">
          {topDecreasesByInstitutions.map((item, index) => (
            <div
              key={item.ticker}
              className="p-3 border-b border-[var(--border-color)] last:border-b-0 hover:bg-[var(--bg-tertiary)] transition-colors h-[68px] flex flex-col justify-center"
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-baseline gap-2 min-w-0">
                  <div className="font-semibold mono text-sm flex-shrink-0">{item.ticker}</div>
                  <div className="text-[10px] text-[var(--text-secondary)] truncate">{item.company}</div>
                </div>
                <div className="text-sm font-bold mono text-[var(--accent-sell)] flex-shrink-0 ml-2">
                  {item.changePercent}%
                </div>
              </div>
              <div className="text-[10px] text-[var(--text-secondary)]">
                {item.institutionCount} institutions
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}