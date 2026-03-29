import { useApi, budgetColor } from '../hooks';

export default function FinancesCard() {
  const { data: fin, loading: loadFin } = useApi('/api/finances', 60000);
  const { data: bud } = useApi('/api/budgets', 60000);

  const balance = fin?.balance != null ? '$' + Number(fin.balance).toLocaleString() : '--';
  const budgets = bud?.budgets || [];
  const expenses = fin?.recent_expenses || [];

  return (
    <div className="card" id="card-finances">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon" style={{ background: 'var(--accent-teal-dim)' }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-teal)" strokeWidth="2">
              <line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
            </svg>
          </div>
          <span className="card-title">Finances</span>
        </div>
        <div className="card-header-right">
          <span className="card-meta" style={{ fontFamily: 'var(--font-data)', fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-teal)' }}>
            {balance} <span style={{ fontSize: '0.7rem', fontWeight: 400, color: 'var(--text-muted)' }}>NZD</span>
          </span>
        </div>
      </div>
      <div className="card-body">
        <div className="metric-row">
          <div className="metric-card">
            <div className="metric-label">Balance</div>
            <div className="metric-value">{balance}</div>
            <div className="metric-trend neutral">NZD</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">This Month</div>
            <div className="metric-value">${fin?.month_spent != null ? Number(fin.month_spent).toLocaleString() : '--'}</div>
            <div className="metric-trend down">spent</div>
          </div>
        </div>

        {budgets.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div className="section-label">BUDGET</div>
            {budgets.map((b, i) => {
              const pct = Math.min(100, Math.round((b.spent / b.limit) * 100));
              return (
                <div className="progress-item" key={i}>
                  <div className="progress-label-row">
                    <span className="progress-name">{b.category}</span>
                    <span className="progress-pct">{pct}%</span>
                  </div>
                  <div className="progress-track">
                    <div className="progress-fill" style={{ width: `${pct}%`, background: budgetColor(pct) }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {expenses.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div className="section-label">RECENT</div>
            {expenses.slice(0, 5).map((e, i) => (
              <div className="list-item" key={i}>
                <div className="list-dot" style={{ background: 'var(--accent-coral)' }} />
                <div className="list-content">
                  <div className="list-title">{e.description || 'Expense'}</div>
                  <div className="list-sub">${e.amount}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
