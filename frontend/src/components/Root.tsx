import { Outlet } from 'react-router';

export function Root() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Outlet />
    </div>
  );
}
