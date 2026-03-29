import { useApi } from '../hooks';

export default function BioCard() {
  const { data, loading } = useApi('/api/bio', 60000);
  const m = data?.metrics || {};
  const insights = data?.insights || [];

  const metrics = [
    { l: 'Sleep', v: m.sleep_avg || '--', u: 'h/night' },
    { l: 'Weight', v: m.weight || '--', u: 'kg' },
    { l: 'Exercise', v: m.exercise || '--', u: 'days/wk' },
    { l: 'Mood', v: m.mood || '--', u: '/10' },
  ];

  return (
    <div className="card" id="card-bio">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon" style={{ background: 'var(--accent-coral-dim)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-coral)" strokeWidth="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <span className="card-title">Bio / Health</span>
        </div>
        <div className="card-header-right">
          <span className="card-meta">Weekly</span>
        </div>
      </div>
      <div className="card-body">
        {loading ? (
          <div className="skeleton" style={{ width: '100%', height: 80 }} />
        ) : (
          <>
            <div className="metric-row">
              {metrics.map((x, i) => (
                <div className="metric-card" key={i}>
                  <div className="metric-label">{x.l}</div>
                  <div className="metric-value">{x.v}</div>
                  <div className="metric-trend neutral">{x.u}</div>
                </div>
              ))}
            </div>
            {insights.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <div className="section-label">INSIGHTS</div>
                {insights.map((text, i) => (
                  <div className="list-item" key={i}>
                    <div className="list-dot" style={{ background: 'var(--accent-teal)' }} />
                    <div className="list-content">
                      <div className="list-title">{text}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
