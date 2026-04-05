import './Dashboard.css';
import { useState } from 'react';
import StatsCard from '../components/StatsCard';
import RecentActivity from '../components/RecentActivity';

function Dashboard() {
  const [stats, setStats] = useState([
    { id: 1, label: 'Users Today', value: '1,234', change: '+12%' },
    { id: 2, label: 'Revenue', value: '$45,678', change: '+8.5%' },
    { id: 3, label: 'Conversion Rate', value: '3.2%', change: '-0.5%' },
    { id: 4, label: 'Active Sessions', value: '567', change: '+23%' }
  ]);

  const [activityTab, setActivityTab] = useState('all');

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard Overview</h1>
        <div className="date-filter">
          <button onClick={() => setActivityTab('all')} className={activityTab === 'all' ? 'active' : ''}>
            All Time
          </button>
          <button onClick={() => setActivityTab('week')} className={activityTab === 'week' ? 'active' : ''}>
            This Week
          </button>
          <button onClick={() => {}} className={activityTab === 'today' ? 'active' : ''}>
            Today
          </button>
        </div>
      </div>

      <div className="stats-grid">
        {stats.map(stat => (
          <StatsCard key={stat.id} {...stat} />
        ))}
      </div>

      <div className="activity-section">
        <h2>Recent Activity</h2>
        <RecentActivity tab={activityTab} />
      </div>
    </div>
  );
}

export default Dashboard;