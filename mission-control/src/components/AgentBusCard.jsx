import { useApi, relTime } from '../hooks';

export default function AgentBusCard() {
  const { data, loading } = useApi('/api/agent-bus/status', 30000);

  const pAnti = data?.pending_for_antigravity || [];
  const pCode = data?.pending_for_claude_code || [];
  const total = pAnti.length + pCode.length;
  const completed = (data?.recent_completed || []).slice(0, 5);

  const allPending = [
    ...pAnti.map(t => ({ ...t, agent: 'antigravity' })),
    ...pCode.map(t => ({ ...t, agent: 'claude-code' })),
  ];

  return (
    <div className="card" id="card-bus">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon" style={{ background: 'var(--accent-purple-dim)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-purple)" strokeWidth="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <span className="card-title">Agent Bus</span>
        </div>
        <div className="card-header-right">
          <span className="card-meta">{pAnti.length} antigravity · {pCode.length} code</span>
          <span className={`status-pill ${total === 0 ? 'ok' : total < 3 ? 'warn' : 'danger'}`}>
            <span className="dot" />
            <span>{total}</span>
          </span>
        </div>
      </div>
      <div className="card-body">
        {loading ? (
          <div className="skeleton" style={{ width: '100%', height: 80 }} />
        ) : allPending.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg>
            <div>All clear — no pending tasks</div>
          </div>
        ) : (
          allPending.map((t, i) => (
            <div className="bus-task" key={i}>
              <span className={`bus-agent ${t.agent}`}>
                {t.agent === 'antigravity' ? 'AG' : 'CC'}
              </span>
              <span className="bus-summary">{t.summary || t.action || 'task'}</span>
              <span className="bus-time">{relTime(t.created_at)}</span>
            </div>
          ))
        )}

        {completed.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div className="section-label">RECENT COMPLETED</div>
            {completed.map((t, i) => {
              const agentClass = (t.from || '').includes('code') ? 'claude-code' :
                (t.from || '').includes('chat') ? 'claude-chat' : 'antigravity';
              return (
                <div className="bus-task" key={i} style={{ opacity: 0.6 }}>
                  <span className={`bus-agent ${agentClass}`}>{t.from || '?'}</span>
                  <span className="bus-summary">{t.summary || ''}</span>
                  <span className="bus-time">{relTime(t.completed_at)}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
