import './SecuritySettings.css';
import { useState } from 'react';

function SecuritySettings() {
  const [twoFaEnabled, setTwoFaEnabled] = useState(false);
  const [loginAlerts, setLoginAlerts] = useState(true);
  const [sessionTimeout, setSessionTimeout] = useState(30);
  const [showRecoveryCodes, setShowRecoveryCodes] = useState(false);
  const [recoveryCodes, setRecoveryCodes] = useState([]);

  const generateRecoveryCodes = () => {
    const codes = [];
    for (let i = 0; i < 8; i++) {
      const code = Math.random().toString(36).substring(2, 8).toUpperCase();
      codes.push(code);
    }
    setRecoveryCodes(codes);
    setShowRecoveryCodes(true);
  };

  return (
    <div className="security-settings">
      <div className="security-section">
        <h2>Two-Factor Authentication</h2>
        <div className="toggle-group">
          <label htmlFor="2fa-toggle">Enable Two-Factor Authentication</label>
          <div className="toggle-switch">
            <input
              type="checkbox"
              id="2fa-toggle"
              checked={twoFaEnabled}
              onChange={(e) => setTwoFaEnabled(e.target.checked)}
            />
            <span className="toggle-slider" aria-label="Two-factor authentication toggle"></span>
          </div>
          {twoFaEnabled && (
            <div className="twofa-info">
              <p>Two-factor authentication is enabled for your account.</p>
              <button onClick={generateRecoveryCodes} className="recovery-codes-btn">
                Show Recovery Codes
              </button>
            </div>
          )}
          {!twoFaEnabled && (
            <p className="twofa-disabled-info">
              Enable two-factor authentication to add an extra layer of security to your account.
            </p>
          )}
        </div>
      </div>

      <div className="security-section">
        <h2>Login Alerts</h2>
        <div className="toggle-group">
          <label htmlFor="login-alerts-toggle">Receive login alerts</label>
          <div className="toggle-switch">
            <input
              type="checkbox"
              id="login-alerts-toggle"
              checked={loginAlerts}
              onChange={(e) => setLoginAlerts(e.target.checked)}
            />
            <span className="toggle-slider" aria-label="Login alerts toggle"></span>
          </div>
          <p className="toggle-description">
            Get notified by email when there's a new login to your account.
          </p>
        </div>
      </div>

      <div className="security-section">
        <h2>Session Management</h2>
        <div className="form-group">
          <label htmlFor="session-timeout">Session timeout</label>
          <select
            id="session-timeout"
            value={sessionTimeout}
            onChange={(e) => setSessionTimeout(parseInt(e.target.value))}
          >
            <option value={15}>15 minutes</option>
            <option value={30}>30 minutes</option>
            <option value={60}>1 hour</option>
            <option value={240}>4 hours</option>
            <option value={1440}>24 hours</option>
          </select>
          <p className="form-hint">
            Automatically log out after {sessionTimeout} minutes of inactivity.
          </p>
        </div>
        <div className="active-sessions">
          <h3>Active Sessions</h3>
          <div className="session-item">
            <div className="session-info">
              <div className="session-device">Chrome on Windows</div>
              <div className="session-location">New York, US</div>
              <div className="session-time">Active now</div>
            </div>
            <button className="terminate-session-btn">Terminate</button>
          </div>
          <div className="session-item">
            <div className="session-info">
              <div className="session-device">Safari on iPhone</div>
              <div className="session-location">Los Angeles, US</div>
              <div className="session-time">Active 2 hours ago</div>
            </div>
            <button className="terminate-session-btn">Terminate</button>
          </div>
        </div>
      </div>

      {showRecoveryCodes && (
        <div className="recovery-codes-modal">
          <div className="recovery-codes-header">
            <h3>Your Recovery Codes</h3>
            <button onClick={() => setShowRecoveryCodes(false)} className="close-modal">
              ×
            </button>
          </div>
          <div className="recovery-codes-body">
            <p className="recovery-warning">
              Save these codes in a safe place. Each code can be used only once to recover your account.
            </p>
            <div className="codes-grid">
              {recoveryCodes.map((code, index) => (
                <div key={index} className="recovery-code">{code}</div>
              ))}
            </div>
            <button onClick={generateRecoveryCodes} className="refresh-codes-btn">
              Generate New Codes
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default SecuritySettings;