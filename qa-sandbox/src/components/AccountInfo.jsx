import './AccountInfo.css';
import { useState } from 'react';

function AccountInfo() {
  const [profile, setProfile] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    bio: '',
    website: '',
    location: ''
  });
  const [editing, setEditing] = useState(false);

  const handleInputChange = (field, value) => {
    setProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = () => {
    setEditing(false);
    // In a real app, this would save to backend
    alert('Profile saved successfully!');
  };

  return (
    <div className="account-info">
      <h2>Account Information</h2>

      {!editing ? (
        <div className="profile-display">
          <div className="profile-field">
            <span className="field-label">Name:</span>
            <span className="field-value">
              {profile.firstName} {profile.lastName}
            </span>
          </div>
          <div className="profile-field">
            <span className="field-label">Email:</span>
            <span className="field-value">{profile.email}</span>
          </div>
          <div className="profile-field">
            <span className="field-label">Phone:</span>
            <span className="field-value">{profile.phone}</span>
          </div>
          <div className="profile-field">
            <span className="field-label">Location:</span>
            <span className="field-value">{profile.location}</span>
          </div>
          <div className="profile-field">
            <span className="field-label">Website:</span>
            <span className="field-value">{profile.website}</span>
          </div>
          <div className="profile-field">
            <span className="field-label">Bio:</span>
            <span className="field-value">{profile.bio}</span>
          </div>
          <button onClick={() => setEditing(true)} className="edit-btn">
            Edit Profile
          </button>
        </div>
      ) : (
        <form className="edit-profile-form">
          <div className="form-group">
            <label htmlFor="first-name">First Name</label>
            <input
              type="text"
              id="first-name"
              value={profile.firstName}
              onChange={(e) => handleInputChange('firstName', e.target.value)}
              placeholder="Enter your first name"
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label htmlFor="last-name">Last Name</label>
            <input
              type="text"
              id="last-name"
              value={profile.lastName}
              onChange={(e) => handleInputChange('lastName', e.target.value)}
              placeholder="Enter your last name"
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={profile.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="Enter your email"
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label htmlFor="phone">Phone Number</label>
            <input
              type="tel"
              id="phone"
              value={profile.phone}
              onChange={(e) => handleInputChange('phone', e.target.value)}
              placeholder="Enter your phone number"
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label htmlFor="location">Location</label>
            <input
              type="text"
              id="location"
              value={profile.location}
              onChange={(e) => handleInputChange('location', e.target.value)}
              placeholder="Enter your location"
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label htmlFor="website">Website</label>
            <input
              type="url"
              id="website"
              value={profile.website}
              onChange={(e) => handleInputChange('website', e.target.value)}
              placeholder="Enter your website URL"
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label htmlFor="bio">Bio</label>
            <textarea
              id="bio"
              value={profile.bio}
              onChange={(e) => handleInputChange('bio', e.target.value)}
              placeholder="Tell us about yourself"
              className="form-input"
              rows="4"
            />
          </div>
          <div className="form-actions">
            <button onClick={() => setEditing(false)} className="cancel-btn">
              Cancel
            </button>
            <button onClick={handleSave} className="save-btn">
              Save Changes
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

export default AccountInfo;