import './StatsCard.css';

function StatsCard({ label, value, change }) {
  const isPositive = change.startsWith('+');

  return (
    <div className="stats-card">
      <div className="stats-card-content">
        <h3 className="stats-card-label">{label}</h3>
        <div className="stats-card-value">{value}</div>
        <div className={`stats-card-change ${isPositive ? 'positive' : 'negative'}`}>
          {change}
        </div>
      </div>
      {/* BUG 22: Invisible overlay blocking clicks on card */}
      <div className="stats-card-overlay" />
    </div>
  );
}

export default StatsCard;