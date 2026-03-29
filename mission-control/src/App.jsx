import { useState, useEffect } from 'react';
import { getNZTime } from './hooks';
import NewsCard from './components/NewsCard';
import JobsCard from './components/JobsCard';
import FinancesCard from './components/FinancesCard';
import DocsCard from './components/DocsCard';
import LogisticsCard from './components/LogisticsCard';
import OppsCard from './components/OppsCard';
import BioCard from './components/BioCard';
import AgentBusCard from './components/AgentBusCard';

const NAV_ITEMS = [
  { id: 'news', icon: <path d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2" /> },
  { id: 'finances', icon: <><line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" /></> },
  { id: 'logistics', icon: <><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></> },
  { id: 'jobs', icon: <><rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" /></> },
  { id: 'docs', icon: <><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><path d="M14 2v6h6" /></> },
  { id: 'opps', icon: <><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /></> },
  { id: 'bio', icon: <path d="M22 12h-4l-3 9L9 3l-3 9H2" /> },
  { id: 'bus', icon: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" /></> },
];

export default function App() {
  const [nzTime, setNzTime] = useState(getNZTime());
  const [activeNav, setActiveNav] = useState('news');

  useEffect(() => {
    const id = setInterval(() => setNzTime(getNZTime()), 10000);
    return () => clearInterval(id);
  }, []);

  return (
    <>
      {/* ═══ HEADER ═══ */}
      <header className="header">
        <div className="header-left">
          <div className="logo-text">ULTRA SYSTEM</div>
          <span className="status-pill ok"><span className="dot" /><span>ONLINE</span></span>
        </div>
        <div className="header-right">
          <span className="status-pill ok" style={{ fontFamily: 'var(--font-data)' }}>
            {nzTime} NZST
          </span>
          <span className="status-pill ok"><span className="dot" /><span>VPS</span></span>
        </div>
      </header>

      {/* ═══ APP LAYOUT ═══ */}
      <div className="app-layout">
        {/* ─── Sidebar Nav ─── */}
        <nav className="sidebar">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              className={`nav-btn ${activeNav === item.id ? 'active' : ''}`}
              onClick={() => setActiveNav(item.id)}
              title={item.id}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                {item.icon}
              </svg>
            </button>
          ))}
        </nav>

        {/* ─── Main Content ─── */}
        <main className="main-grid">
          <NewsCard />
          <FinancesCard />
          <JobsCard />
          <DocsCard />
          <LogisticsCard />
          <OppsCard />
          <BioCard />
          <AgentBusCard />
        </main>
      </div>
    </>
  );
}
