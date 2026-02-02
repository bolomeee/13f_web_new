import { useParams, Link } from 'react-router';
import { Sidebar } from './Sidebar';
import { ArrowLeft, TrendingUp, TrendingDown, PhoneCall, Shield } from 'lucide-react';
import { institutionDetails } from '../data/mockData';
import type { Holding, OptionPosition } from '../data/mockData';

export function InstitutionDetail() {
  const { id } = useParams<{ id: string }>();
  const institution = id ? institutionDetails[id] : null;

  if (!institution) {
    return (
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-semibold mb-2">Institution Not Found</h2>
            <Link to="/" className="text-[var(--accent-buy)] hover:underline">
              Return to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const renderHoldingsTable = (holdings: Holding[], type: 'increase' | 'decrease') => {
    if (holdings.length === 0) {
      return (
        <div className="text-center py-8 text-[var(--text-secondary)]">
          No {type === 'increase' ? 'increased' : 'decreased'} positions this quarter
        </div>
      );
    }

    return (
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-xs uppercase">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Ticker</th>
              <th className="px-4 py-3 text-left font-medium">Company</th>
              <th className="px-4 py-3 text-right font-medium">Shares</th>
              <th className="px-4 py-3 text-right font-medium">Value</th>
              <th className="px-4 py-3 text-right font-medium">% of Portfolio</th>
              <th className="px-4 py-3 text-right font-medium">Change</th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((holding, index) => (
              <tr
                key={holding.ticker}
                className={`border-b border-[var(--border-color)] hover:bg-[var(--bg-tertiary)] transition-colors ${
                  index === holdings.length - 1 ? 'border-b-0' : ''
                }`}
              >
                <td className="px-4 py-3">
                  <span className="mono font-semibold">{holding.ticker}</span>
                </td>
                <td className="px-4 py-3 text-sm">{holding.company}</td>
                <td className="px-4 py-3 text-right mono text-sm">
                  {holding.shares.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right mono font-semibold">{holding.value}</td>
                <td className="px-4 py-3 text-right mono text-sm text-[var(--text-secondary)]">
                  {holding.portfolioPercent}%
                </td>
                <td
                  className={`px-4 py-3 text-right mono font-semibold ${
                    type === 'increase' ? 'text-[var(--accent-buy)]' : 'text-[var(--accent-sell)]'
                  }`}
                >
                  {type === 'increase' ? '+' : ''}{holding.change}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderOptionsTable = (options: OptionPosition[], type: 'call' | 'put') => {
    if (options.length === 0) {
      return (
        <div className="text-center py-8 text-[var(--text-secondary)]">
          No {type} options positions
        </div>
      );
    }

    return (
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-xs uppercase">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Ticker</th>
              <th className="px-4 py-3 text-left font-medium">Company</th>
              <th className="px-4 py-3 text-right font-medium">Contracts</th>
              <th className="px-4 py-3 text-right font-medium">Total Value</th>
              <th className="px-4 py-3 text-right font-medium">Strike Price</th>
              <th className="px-4 py-3 text-right font-medium">Expiry Date</th>
            </tr>
          </thead>
          <tbody>
            {options.map((option, index) => (
              <tr
                key={option.ticker + option.expiryDate}
                className={`border-b border-[var(--border-color)] hover:bg-[var(--bg-tertiary)] transition-colors ${
                  index === options.length - 1 ? 'border-b-0' : ''
                }`}
              >
                <td className="px-4 py-3">
                  <span className="mono font-semibold">{option.ticker}</span>
                </td>
                <td className="px-4 py-3 text-sm">{option.company}</td>
                <td className="px-4 py-3 text-right mono text-sm">
                  {option.contracts.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right mono font-semibold">{option.totalValue}</td>
                <td className="px-4 py-3 text-right mono text-sm">
                  ${option.strikePrice.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-right text-sm text-[var(--text-secondary)]">
                  {option.expiryDate}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <div className="flex-1 overflow-y-auto">
        <div className="p-8">
          {/* Back Button */}
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] mb-6 transition-colors"
          >
            <ArrowLeft size={20} />
            <span>Back to Dashboard</span>
          </Link>

          {/* Header */}
          <div className="flex items-center gap-4 mb-8">
            <div className="w-16 h-16 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center text-xl font-bold">
              {institution.avatar}
            </div>
            <div>
              <h1 className="text-3xl font-bold mb-1">{institution.name}</h1>
              <p className="text-[var(--text-secondary)] mono">AUM: {institution.aum}</p>
            </div>
          </div>

          {/* Holdings Grid */}
          <div className="grid grid-cols-2 gap-6 mb-6">
            {/* Increased Positions */}
            <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg overflow-hidden">
              <div className="p-4 border-b border-[var(--border-color)] bg-[var(--accent-buy)]/10">
                <div className="flex items-center gap-2">
                  <TrendingUp size={20} className="text-[var(--accent-buy)]" />
                  <h2 className="text-lg font-semibold">
                    Increased Positions ({institution.increasedPositions.length})
                  </h2>
                </div>
              </div>
              {renderHoldingsTable(institution.increasedPositions, 'increase')}
            </div>

            {/* Decreased Positions */}
            <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg overflow-hidden">
              <div className="p-4 border-b border-[var(--border-color)] bg-[var(--accent-sell)]/10">
                <div className="flex items-center gap-2">
                  <TrendingDown size={20} className="text-[var(--accent-sell)]" />
                  <h2 className="text-lg font-semibold">
                    Decreased Positions ({institution.decreasedPositions.length})
                  </h2>
                </div>
              </div>
              {renderHoldingsTable(institution.decreasedPositions, 'decrease')}
            </div>
          </div>

          {/* Options Grid */}
          <div className="grid grid-cols-2 gap-6">
            {/* Call Options */}
            <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg overflow-hidden">
              <div className="p-4 border-b border-[var(--border-color)] bg-[var(--accent-buy)]/10">
                <div className="flex items-center gap-2">
                  <PhoneCall size={20} className="text-[var(--accent-buy)]" />
                  <h2 className="text-lg font-semibold">
                    Call Options ({institution.callOptions.length})
                  </h2>
                </div>
                {institution.callOptions.length > 0 && (
                  <div className="mt-2 text-sm text-[var(--text-secondary)]">
                    Total Value:{' '}
                    <span className="mono font-semibold text-[var(--text-primary)]">
                      {institution.callOptions.reduce((sum, opt) => {
                        const value = parseFloat(opt.totalValue.replace(/[^0-9.]/g, ''));
                        return sum + value;
                      }, 0).toFixed(1)}M
                    </span>
                  </div>
                )}
              </div>
              {renderOptionsTable(institution.callOptions, 'call')}
            </div>

            {/* Put Options */}
            <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg overflow-hidden">
              <div className="p-4 border-b border-[var(--border-color)] bg-[var(--accent-sell)]/10">
                <div className="flex items-center gap-2">
                  <Shield size={20} className="text-[var(--accent-sell)]" />
                  <h2 className="text-lg font-semibold">
                    Put Options ({institution.putOptions.length})
                  </h2>
                </div>
                {institution.putOptions.length > 0 && (
                  <div className="mt-2 text-sm text-[var(--text-secondary)]">
                    Total Value:{' '}
                    <span className="mono font-semibold text-[var(--text-primary)]">
                      {institution.putOptions.reduce((sum, opt) => {
                        const value = parseFloat(opt.totalValue.replace(/[^0-9.]/g, ''));
                        return sum + value;
                      }, 0).toFixed(1)}M
                    </span>
                  </div>
                )}
              </div>
              {renderOptionsTable(institution.putOptions, 'put')}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
