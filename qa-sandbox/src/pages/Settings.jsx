import './Settings.css';
import { useState } from 'react';

function Settings() {
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    sms: true
  });

  const [profile, setProfile] = useState({
    name: '',
    email: '',
    company: ''
  });

  const handleToggle = (type) => {
    setNotifications(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  const handleInputChange = (field, value) => {
    setProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>Settings</h1>
        <p className="settings-subtitle">Manage your account and preferences</p>
      </div>

      <div className="settings-grid">
        <div className="settings-section">
          <h2>Notifications</h2>
          <div className="toggle-group">
            <div className="toggle-item">
              <label htmlFor="email-toggle">Email Notifications</label>
              <div className="toggle-switch">
                <input
                  type="checkbox"
                  id="email-toggle"
                  checked={notifications.email}
                  onChange={() => handleToggle('email')}
                />
                <span className="toggle-slider" aria-label="Email notifications toggle"></span>
              </div>
            </div>

            <div className="toggle-item">
              <label htmlFor="push-toggle">Push Notifications</label>
              <div className="toggle-switch">
                <input
                  type="checkbox"
                  id="push-toggle"
                  checked={notifications.push}
                  onChange={() => handleToggle('push')}
                />
                <span className="toggle-slider" aria-label="Push notifications toggle"></span>
              </div>
            </div>

            <div className="toggle-item">
              <label htmlFor="sms-toggle">SMS Notifications</label>
              <div className="toggle-switch">
                <input
                  type="checkbox"
                  id="sms-toggle"
                  checked={notifications.sms}
                  onChange={() => handleToggle('sms')}
                />
                <span className="toggle-slider" aria-label="SMS notifications toggle"></span>
              </div>
            </div>
          </div>
        </div>

        <div className="settings-section">
          <h2>Profile Information</h2>
          <form className="profile-form">
            <div className="form-group">
              <label htmlFor="profile-name">Full Name</label>
              <input
                type="text"
                id="profile-name"
                value={profile.name}
                onChange={(e) => {}}
                placeholder="Enter your full name"
                className="form-input"
                /* BUG 48: Missing aria-label for screen readers */
                /* BUG 49: No autocomplete attribute */
              />
              <div className="form-hint">This will be displayed on your public profile</div>
            </div>

            <div className="form-group">
              <label htmlFor="profile-email">Email Address</label>
              <input
                type="email"
                id="profile-email"
                value={profile.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                placeholder="your@email.com"
                className="form-input"
                /* BUG 50: Input too wide causing overflow */
              />
            </div>

            <div className="form-group">
              <label htmlFor="profile-company">Company Name</label>
              <input
                type="text"
                id="profile-company"
                value={profile.company}
                onChange={(e) => handleInputChange('company', e.target.value)}
                placeholder="Your company name"
                className="form-input"
              />
            </div>
          </form>
        </div>
      </div>

      <div className="settings-actions">
        <button className="cancel-btn">Cancel</button>
        <button className="save-btn">Save Changes</button>
        {/* BUG 51: Buttons too close together causing misclicks */}
        {/* BUG 52: Save button not visually distinct enough */}
      </div>
    </div>
  );
}

export default Settings;