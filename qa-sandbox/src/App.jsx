import './App.css';
import { useState } from 'react';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import Billing from './pages/Billing';
import Profile from './pages/Profile';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  return (
    <div className="app">
      <Navigation
        currentPage={currentPage}
        onPageChange={setCurrentPage}
      />
      <div className="page-content">
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'settings' && <Settings />}
        {currentPage === 'billing' && <Billing />}
        {currentPage === 'profile' && <Profile />}
      </div>
    </div>
  );
}

export default App;