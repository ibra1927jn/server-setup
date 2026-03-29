import { useApi } from '../hooks';

export default function LogisticsCard() {
  const { data, loading } = useApi('/api/logistics', 60000);
  const items = data?.items || [];

  return (
    <div className="card" id="card-logistics">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon" style={{ background: 'var(--accent-amber-dim)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-amber)" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" />
            </svg>
          </div>
          <span className="card-title">Logistics — 48h Window</span>
        </div>
        <div className="card-header-right">
          <span className="card-meta">{items.length} items</span>
        </div>
      </div>
      <div className="card-body">
        {loading ? (
          <div className="skeleton" style={{ width: '100%', height: 80 }} />
        ) : items.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>
            <div>No items in next 48h</div>
          </div>
        ) : (
          items.map((it, i) => (
            <div className="timeline-item" key={i}>
              <div className={`timeline-dot ${it.overdue ? 'urgent' : it.priority === 'high' ? 'warn' : ''}`} />
              <div className="timeline-time">{it.time || ''}</div>
              <div className="timeline-title">{it.description || it.title || ''}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
