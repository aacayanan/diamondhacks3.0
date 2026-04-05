import './Profile.css';
import { useState } from 'react';
import AvatarUpload from '../components/AvatarUpload';
import SecuritySettings from '../components/SecuritySettings';
import AccountInfo from '../components/AccountInfo';

function Profile() {
  const [activeTab, setActiveTab] = useState('account');

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  return (
    <div className="profile-page">
      <div className="profile-header">
        <h1>Profile</h1>
        <p className="profile-subtitle">Manage your account information and preferences</p>
      </div>

      <div className="profile-tabs">
        <button
          onClick={() => handleTabChange('account')}
          className={activeTab === 'account' ? 'tab-active' : 'tab-inactive'}
        >
          Account Info
        </button>
        <button
          onClick={() => handleTabChange('avatar')}
          className={activeTab === 'avatar' ? 'tab-active' : 'tab-inactive'}
        >
          Avatar
        </button>
        <button
          onClick={() => handleTabChange('security')}
          className={activeTab === 'security' ? 'tab-active' : 'tab-inactive'}
        >
          Security
        </button>
      </div>

      <div className="profile-content">
        {activeTab === 'account' && <AccountInfo />}
        {activeTab === 'avatar' && <AvatarUpload />}
        {activeTab === 'security' && <SecuritySettings />}
      </div>
    </div>
  );
}

export default Profile;