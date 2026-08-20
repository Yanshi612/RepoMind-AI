import { Link, useLocation } from 'react-router-dom';

const NAV_ITEMS = [
  {
    label: 'Home',
    to: '/',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9.75L12 3l9 6.75V21a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.75z"/>
        <path d="M9 22V12h6v10"/>
      </svg>
    ),
  },
  {
    label: 'Dashboard',
    to: '/dashboard',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1"/>
        <rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="3" y="14" width="7" height="7" rx="1"/>
        <rect x="14" y="14" width="7" height="7" rx="1"/>
      </svg>
    ),
  },
  {
    label: 'Repository',
    to: '/repository',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M7 8l-4 4 4 4"/>
        <path d="M17 8l4 4-4 4"/>
        <path d="M14 4l-4 16"/>
      </svg>
    ),
  },
  {
    label: 'Analysis',
    to: '/analysis',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="7"/>
        <path d="M21 21l-4.35-4.35"/>
        <path d="M11 8v6M8 11h6"/>
      </svg>
    ),
  },
  {
    label: 'Recent Scans',
    to: '/recent-scans',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9"/>
        <path d="M12 7v5l3 3"/>
      </svg>
    ),
  },
];

export default function Sidebar() {
  const { pathname } = useLocation();

  const isActive = (to) => {
    if (to === '/') return pathname === '/';
    return pathname.startsWith(to);
  };

  return (
    <aside
      className="flex flex-col w-60 min-h-screen flex-shrink-0"
      style={{ background: '#0d0f1a', borderRight: '1px solid rgba(255,255,255,0.07)' }}
    >
      {/* Logo */}
      <div className="px-5 pt-6 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center"
               style={{ background: 'linear-gradient(135deg,#3b82f6,#8b5cf6)' }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span className="text-white font-bold text-sm tracking-wide">RepoMind AI</span>
        </div>
        <div className="ml-11 mt-1">
          <span className="text-xs px-1.5 py-0.5 rounded font-medium"
                style={{ color: 'rgba(156,163,175,0.6)', background: 'rgba(255,255,255,0.05)' }}>
            v1.0
          </span>
        </div>
      </div>

      {/* Divider */}
      <div style={{ height: '1px', background: 'rgba(255,255,255,0.05)', margin: '0 20px 10px' }} />

      {/* Nav */}
      <nav className="flex flex-col gap-0.5 px-3 flex-1">
        {NAV_ITEMS.map(({ label, to, icon }) => {
          const active = isActive(to);
          return (
            <Link
              key={to}
              to={to}
              className={[
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 border-l-2',
                active
                  ? 'bg-blue-600/10 text-blue-400 border-blue-500'
                  : 'text-gray-400 border-transparent hover:bg-white/5 hover:text-white',
              ].join(' ')}
            >
              <span className="flex-shrink-0">{icon}</span>
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-5">
        <p className="text-xs text-center" style={{ color: '#334155' }}>
          Powered by py · 2026
        </p>
      </div>
    </aside>
  );
}