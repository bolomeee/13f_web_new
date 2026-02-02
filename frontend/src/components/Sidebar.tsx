import { Link, useLocation } from 'react-router';
import { LayoutDashboard, Settings } from 'lucide-react';
import { trackedGurus } from '../data/mockData';

export function Sidebar() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="w-64 bg-[var(--bg-secondary)] border-r border-[var(--border-color)] h-screen flex flex-col overflow-y-auto">
      {/* Header */}
      <div className="p-6 border-b border-[var(--border-color)]">
        <h1 className="text-xl font-bold">13F Insider Tracker</h1>
      </div>

      {/* Navigation */}
      <nav className="p-4 border-b border-[var(--border-color)]">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg mb-2 transition-colors ${
                isActive
                  ? 'bg-[var(--bg-tertiary)] text-[var(--text-primary)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'
              }`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Tracked Gurus */}
      <div className="p-4 flex-1">
        <h2 className="text-sm text-[var(--text-secondary)] mb-3 uppercase tracking-wide">
          Tracked Institutions
        </h2>
        <div className="space-y-2">
          {trackedGurus.map((guru) => (
            <Link
              key={guru.id}
              to={`/institution/${guru.id}`}
              className="flex items-center gap-3 p-2 rounded-lg hover:bg-[var(--bg-tertiary)] cursor-pointer transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center text-sm font-semibold">
                {guru.avatar}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{guru.name}</div>
                <div className="text-xs text-[var(--text-tertiary)] mono">{guru.aum}</div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}