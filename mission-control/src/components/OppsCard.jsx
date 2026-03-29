import { useApi } from '../hooks';

export default function OppsCard() {
  const { data, loading } = useApi('/api/opportunities', 60000);
  const opps = data?.opportunities || [];
  const stages = ['detected', 'applied', 'followup', 'closed'];

  const grouped = {};
  stages.forEach(s => grouped[s] = []);
  opps.forEach(o => {
    const stage = (o.stage || 'detected').toLowerCase().replace('-', '');
    if (grouped[stage]) grouped[stage].push(o);
    else grouped.detected.push(o);
  });

  return (
    <div className="card" id="card-opps">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon" style={{ background: 'var(--accent-blue-dim)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
            </svg>
          </div>
          <span className="card-title">Opportunities</span>
        </div>
        <div className="card-header-right">
          <span className="card-meta">{opps.length} pipeline</span>
        </div>
      </div>
      <div className="card-body">
        {loading ? (
          <div className="skeleton" style={{ width: '100%', height: 100 }} />
        ) : opps.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>
            <div>No opportunities detected</div>
          </div>
        ) : (
          <div className="kanban">
            {stages.map(stage => (
              <div key={stage}>
                <div className="kanban-col-header">{stage}</div>
                {grouped[stage].map((o, i) => (
                  <div className="kanban-card" key={i} style={{
                    borderColor: o.deadline_soon ? 'var(--accent-amber)' : 'var(--accent-teal)'
                  }}>
                    {o.name || o.title || '?'}
                    <br />
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{o.type || ''}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
