import { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopPicksColumns } from './TopPicksColumns';
import { ActivityFeed } from './ActivityFeed';
import { recentActivities } from '../data/mockData';

export function Dashboard() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 overflow-y-auto">
        <div className="p-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
            <p className="text-[var(--text-secondary)]">
              Track institutional 13F filings and fund investments
            </p>
          </div>

          {/* Top Picks - 3 Columns */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">Top Picks</h2>
            <TopPicksColumns />
          </div>

          {/* Recent Activity Feed */}
          <ActivityFeed activities={recentActivities} />
        </div>
      </div>
    </div>
  );
}