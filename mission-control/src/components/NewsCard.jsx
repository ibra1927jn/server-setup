import { useApi, relTime } from '../hooks';

export default function NewsCard() {
  const { data, loading } = useApi('/api/feeds/articles?limit=8', 60000);
  const articles = data?.articles || [];

  return (
    <div className="card" id="card-news">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon" style={{ background: 'var(--accent-teal-dim)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-teal)" strokeWidth="2">
              <path d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2" />
            </svg>
          </div>
          <span className="card-title">Intel Feed</span>
        </div>
        <div className="card-header-right">
          <span className="card-meta">{articles.length} articles</span>
        </div>
      </div>
      <div className="card-body">
        {loading ? (
          <div className="empty-state"><div className="skeleton" style={{width:'100%',height:120}} /></div>
        ) : articles.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>
            <div>No articles yet</div>
          </div>
        ) : (
          articles.map((a, i) => (
            <div className="list-item" key={i}>
              <div className="list-dot" style={{
                background: a.score > 7 ? 'var(--accent-teal)' : a.score > 4 ? 'var(--accent-amber)' : 'var(--text-muted)'
              }} />
              <div className="list-content">
                <div className="list-title" dangerouslySetInnerHTML={{
                  __html: (a.title || '').replace(/\b(AI|NZ|tech|crypto|startup)\b/gi, '<span class="kw">$1</span>')
                }} />
                <div className="list-sub">{a.source || '?'} · {relTime(a.published_at || a.created_at)}</div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
