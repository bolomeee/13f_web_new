import { Activity } from '../data/mockData';
import { TrendingUp, TrendingDown, ShoppingCart, Trash2 } from 'lucide-react';

interface ActivityFeedProps {
  activities: Activity[];
}

export function ActivityFeed({ activities }: ActivityFeedProps) {
  const getActionBadge = (action: Activity['action']) => {
    const isBuy = action === 'buy' || action === 'increase';
    const Icon = isBuy ? (action === 'buy' ? ShoppingCart : TrendingUp) : (action === 'sell' ? Trash2 : TrendingDown);
    const bgColor = isBuy ? 'bg-[var(--accent-buy)]/10' : 'bg-[var(--accent-sell)]/10';
    const textColor = isBuy ? 'text-[var(--accent-buy)]' : 'text-[var(--accent-sell)]';

    return (
      <div className={`flex items-center gap-1.5 px-2 py-1 rounded ${bgColor} ${textColor}`}>
        <Icon size={14} />
        <span className="text-xs font-semibold uppercase">{action}</span>
      </div>
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg overflow-hidden">
      <div className="p-4 border-b border-[var(--border-color)]">
        <h2 className="text-lg font-semibold">Recent Activity Feed</h2>
      </div>

      <div className="overflow-x-auto max-h-[320px] overflow-y-auto">
        <table className="w-full">
          <thead className="bg-[var(--bg-tertiary)] text-[var(--text-secondary)] text-xs uppercase">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Institution</th>
              <th className="px-4 py-3 text-left font-medium">Action</th>
              <th className="px-4 py-3 text-left font-medium">Ticker</th>
              <th className="px-4 py-3 text-right font-medium">% Change</th>
              <th className="px-4 py-3 text-right font-medium">Date</th>
            </tr>
          </thead>
          <tbody>
            {activities.map((activity, index) => (
              <tr
                key={activity.id}
                className={`border-b border-[var(--border-color)] hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer ${
                  index === activities.length - 1 ? 'border-b-0' : ''
                }`}
              >
                <td className="px-4 py-3 text-sm">{activity.guruName}</td>
                <td className="px-4 py-3">{getActionBadge(activity.action)}</td>
                <td className="px-4 py-3">
                  <span className="mono font-semibold">{activity.ticker}</span>
                </td>
                <td className={`px-4 py-3 text-right mono font-semibold ${
                  activity.changePercent >= 0 ? 'text-[var(--accent-buy)]' : 'text-[var(--accent-sell)]'
                }`}>
                  {activity.changePercent >= 0 ? '+' : ''}{activity.changePercent}%
                </td>
                <td className="px-4 py-3 text-right text-sm text-[var(--text-secondary)]">
                  {formatDate(activity.date)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}