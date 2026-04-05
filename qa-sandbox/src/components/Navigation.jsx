import './Navigation.css';

function Navigation({ currentPage, onPageChange }) {
  const pages = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'settings', label: 'Settings' },
    { id: 'billing', label: 'Billing' },
    { id: 'profile', label: 'Profile' }
  ];

  return (
    <nav className="navbar">
      <div className="nav-container">
        <div className="nav-brand">
          <h2>AdminPanel</h2>
        </div>
        <div className="nav-links">
          {pages.map(page => (
            <button
              key={page.id}
              className={`nav-link ${currentPage === page.id ? 'active' : ''}`}
              onClick={() => onPageChange(page.id)}
            >
              {page.label}
            </button>
          ))}
        </div>
        <div className="nav-user">
          <span>Welcome, Admin</span>
        </div>
      </div>
    </nav>
  );
}

export default Navigation;