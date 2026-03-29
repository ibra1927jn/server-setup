import { useApi, relTime } from '../hooks';

export default function JobsCard() {
  const { data, loading } = useApi('/api/jobs?limit=10', 60000);
  const jobs = data?.jobs || [];
  const sources = ['Seek', 'Indeed', 'TradeMe'];

  return (
    <div className="card" id="card-jobs">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon" style={{ background: 'var(--accent-blue-dim)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2" /><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
            </svg>
          </div>
          <span className="card-title">Job Scanner</span>
        </div>
        <div className="card-header-right">
          <span className="card-meta">{jobs.length} active</span>
        </div>
      </div>
      <div className="card-body">
        <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
          {sources.map(s => (
            <span key={s} className="status-pill ok" style={{ fontSize: '0.68rem' }}>{s} ✓</span>
          ))}
        </div>
        {loading ? (
          <div className="skeleton" style={{ width: '100%', height: 100 }} />
        ) : jobs.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>
            <div>No active listings — next scrape pending</div>
          </div>
        ) : (
          jobs.map((j, i) => (
            <div className="list-item" key={i}>
              <div className="list-dot" style={{ background: 'var(--accent-blue)' }} />
              <div className="list-content">
                <div className="list-title">{j.title || 'Untitled'}</div>
                <div className="list-sub">{j.company || ''} · {j.location || ''} {j.salary ? `· ${j.salary}` : ''}</div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
