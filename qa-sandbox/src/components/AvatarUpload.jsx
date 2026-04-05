import './AvatarUpload.css';
import { useState } from 'react';

function AvatarUpload() {
  const [avatarUrl, setAvatarUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUpload = () => {
    setUploading(true);
    // Simulate upload delay
    setTimeout(() => {
      setAvatarUrl(previewUrl);
      setUploading(false);
      setPreviewUrl(null);
    }, 1500);
  };

  return (
    <div className="avatar-upload">
      <div className="avatar-preview">
        {avatarUrl ? (
          <img src={avatarUrl} alt="User Avatar" className="avatar-image" />
        ) : (
          <div className="avatar-placeholder">
            <svg width="80" height="80" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
              <circle cx="40" cy="40" r="35" fill="#e2e8f0" />
              <path d="M40 25a15 15 0 1 0 0 30 15 15 0 0 0 0-30z" fill="#64748b" />
              <path d="M30 45h20v10h-20z" fill="#64748b" />
            </svg>
          </div>
        )}
        {!avatarUrl && !uploading && (
          <div className="avatar-upload-prompt">
            <p>Click to upload or drag & drop</p>
            <p className="upload-hint">Supported formats: JPG, PNG, GIF (max 5MB)</p>
          </div>
        )}
        {uploading && (
          <div className="avatar-uploading">
            <div className="spinner"></div>
            <p>Uploading...</p>
          </div>
        )}
      </div>
      <input
        type="file"
        accept="image/*"
        id="avatar-input"
        onChange={handleImageChange}
        className="avatar-input"
        style={{ display: 'none' }}
      />
      <label htmlFor="avatar-input" className="avatar-label">
        Upload New Avatar
      </label>
      {previewUrl && !uploading && (
        <button onClick={handleUpload} className="confirm-upload-btn">
          Use This Avatar
        </button>
      )}
    </div>
  );
}

export default AvatarUpload;