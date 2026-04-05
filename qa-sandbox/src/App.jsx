import './App.css';
import { Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import Billing from './pages/Billing';
import Profile from './pages/Profile';
import FeedbackForm from './pages/FeedbackForm';
import About from './pages/About';

function App() {
  return (
    <Routes>
      <Route path="/" element={
        <div className="app">
          <div className="page-content">
            <Dashboard />
          </div>
        </div>
      } />
      <Route path="/form" element={<FeedbackForm />} />
      <Route path="/about" element={<About />} />
      <Route path="/billing" element={<div className="app"><div className="page-content"><Billing /></div></div>} />
      <Route path="/settings" element={<div className="app"><div className="page-content"><Settings /></div></div>} />
      <Route path="/profile" element={<div className="app"><div className="page-content"><Profile /></div></div>} />
    </Routes>
  );
}

export default App;