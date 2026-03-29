import { useApi } from '../hooks';

export default function DocsCard() {
  const { data, loading } = useApi('/api/documents', 60000);
  const docs = (data?.documents || []).sort((a, b) => (a.days_remaining || 999) - (b.days_remaining || 999));

  const typeColors = {
    passport: 'var(--accent-coral)',
    visa: 'var(--accent-blue)',
    insurance: 'var(--accent-teal)',
    wof: 'var(--accent-amber)',
  };

  return (
    <div className="card" id="card-docs">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon" style={{ background: 'var(--accent-amber-dim)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-amber)" strokeWidth="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><path d="M14 2v6h6" />
            </svg>
          </div>
          <span className="card-title">Documents</span>
        </div>
        <div className="card-header-right">
          <span className="card-meta">{docs.length} tracked</span>
        </div>
      </div>
      <div className="card-body">
        {loading ? (
          <div className="skeleton" style={{ width: '100%', height: 100 }} />
        ) : docs.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>
            <div>No documents tracked</div>
          </div>
        ) : (
          docs.map((d, i) => {
            const days = d.days_remaining != null ? d.days_remaining : '?';
            const color = days !== '?' && days < 30 ? 'var(--accent-coral)' : days < 90 ? 'var(--accent-amber)' : 'var(--accent-teal)';
            const bg = typeColors[(d.type || '').toLowerCase()] || 'var(--text-muted)';
            return (
              <div className="doc-item" key={i}>
                <div className="doc-icon" style={{ background: `${bg}22`, color: bg }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><path d="M14 2v6h6" />
                  </svg>
                </div>
                <div className="doc-info">
                  <div className="doc-name">{d.name || 'Document'}</div>
                  <div className="doc-type">{d.type || ''}</div>
                </div>
                <div className="doc-countdown">
                  <div className="doc-days" style={{ color }}>{days}</div>
                  <div className="doc-days-label">days left</div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
