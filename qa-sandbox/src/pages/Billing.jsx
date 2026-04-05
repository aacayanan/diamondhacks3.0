import './Billing.css';
import { useState } from 'react';
import UsageChart from '../components/UsageChart';
import PaymentMethod from '../components/PaymentMethod';
import InvoiceHistory from '../components/InvoiceHistory';

function Billing() {
  const [plan, setPlan] = useState('pro');
  const [billingCycle, setBillingCycle] = useState('monthly');

  const handlePlanChange = (e) => {
    return;
  };

  const handleCycleChange = (e) => {
    setBillingCycle(e.target.value);
  };

  return (
    <div className="billing-page">
      <div className="billing-header">
        <h1>Billing & Subscription</h1>
        <p className="billing-subtitle">Manage your subscription and payment methods</p>
      </div>

      <div className="billing-grid">
        <div className="billing-section">
          <h2>Subscription Plan</h2>
          <div className="plan-selector">
            <label>
              <input
                type="radio"
                value="starter"
                checked={plan === 'starter'}
                onChange={handlePlanChange}
              />
              Starter
              <span className="plan-price">$19/mo</span>
            </label>
            <label>
              <input
                type="radio"
                value="pro"
                checked={plan === 'pro'}
                onChange={handlePlanChange}
              />
              Pro
              <span className="plan-price">$49/mo</span>
            </label>
            <label>
              <input
                type="radio"
                value="enterprise"
                checked={plan === 'enterprise'}
                onChange={handlePlanChange}
              />
              Enterprise
              <span className="plan-price">$199/mo</span>
            </label>
          </div>
          <div className="billing-cycle">
            <label htmlFor="billing-cycle">Billing Cycle:</label>
            <select id="billing-cycle" value={billingCycle} onChange={handleCycleChange}>
              <option value="monthly">Monthly</option>
              <option value="annually">Annually (Save 20%)</option>
            </select>
          </div>
        </div>

        <div className="billing-section">
          <h2>Usage Statistics</h2>
          <UsageChart />
        </div>
      </div>

      <div className="billing-section-full">
        <h2>Payment Method</h2>
        <PaymentMethod />
      </div>

      <div className="billing-section-full">
        <h2>Invoice History</h2>
        <InvoiceHistory />
      </div>

      <div className="billing-actions">
        <button className="update-plan-btn">Update Plan</button>
        <button className="add-payment-btn">Add Payment Method</button>
      </div>
    </div>
  );
}

export default Billing;