import './RecentActivity.css';

function RecentActivity({ tab }) {
  const activities = [
    { id: 1, action: 'User signed up', time: '2 min ago', type: 'success' },
    { id: 2, action: 'Payment processed', time: '5 min ago', type: 'success' },
    { id: 3, action: 'Failed login attempt', time: '12 min ago', type: 'error' },
    { id: 4, action: 'Settings updated', time: '20 min ago', type: 'info' },
    { id: 5, action: 'New subscription', time: '35 min ago', type: 'success' },
    { id: 6, action: 'API key generated', time: '1 hour ago', type: 'info' }
  ];

  const filteredActivities = activities.filter(activity => {
    if (tab === 'week') return true; // Simplified
    if (tab === 'today') return activity.id <= 3; // Simplified
    return true;
  });

  return (
    <div className="recent-activity">
      <div className="activity-list">
        {filteredActivities.map(activity => (
          <div key={activity.id} className={`activity-item ${activity.type}`}>
            <div className="activity-icon">
              {activity.type === 'success' && '✓'}
              {activity.type === 'error' && '✗'}
              {activity.type === 'info' && 'ℹ️'}
            </div>
            <div className="activity-content">
              <p className="activity-description">{activity.action}</p>
              <p className="activity-time">{activity.time}</p>
            </div>
          </div>
        ))}
      </div>
      {/* BUG 31: Misaligned flex container causing uneven spacing */}
      <div className="activity-footer">
        <button className="load-more">Load More</button>
        <span className="activity-count">{filteredActivities.length} activities</span>
      </div>
    </div>
  );
}

export default RecentActivity;