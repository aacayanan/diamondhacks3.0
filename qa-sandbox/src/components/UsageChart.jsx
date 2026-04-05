import './UsageChart.css';
import { useState, useEffect } from 'react';

function UsageChart() {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate API call
    const fetchData = async () => {
      try {
        // Mock data for usage chart
        const mockData = [
          { month: 'Jan', apiCalls: 1200, bandwidth: 2.4 },
          { month: 'Feb', apiCalls: 1900, bandwidth: 3.1 },
          { month: 'Mar', apiCalls: 1500, bandwidth: 2.8 },
          { month: 'Apr', apiCalls: 2300, bandwidth: 3.9 },
          { month: 'May', apiCalls: 1800, bandwidth: 3.2 },
          { month: 'Jun', apiCalls: 2100, bandwidth: 3.7 }
        ];
        setChartData(mockData);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch chart data:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="chart-placeholder">Loading chart data...</div>;
  }

  return (
    <div className="usage-chart">
      <div className="chart-header">
        <h3>API Usage (Last 6 Months)</h3>
        <p className="chart-subtitle">Track your API consumption over time</p>
      </div>
      <div className="chart-container">
        {/* Simple bar chart representation */}
        <div className="bars">
          {chartData.map((data, index) => (
            <div key={index} className="bar-group">
              <div className="bar-label">{data.month}</div>
              <div className="bar-container">
                <div
                  className="bar api-bar"
                  style={{ height: `${(data.apiCalls / 2300) * 100}%` }}
                ></div>
                <div className="bar-label-value">{data.apiCalls}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="chart-legend">
          <div className="legend-item">
            <div className="legend-color api"></div>
            <span>API Calls</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UsageChart;