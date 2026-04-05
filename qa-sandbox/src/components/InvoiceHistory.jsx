import './InvoiceHistory.css';
import { useState } from 'react';

function InvoiceHistory() {
  const [invoices, setInvoices] = useState([
    { id: 1, number: 'INV-001', date: '2024-01-15', amount: '$49.00', status: 'paid' },
    { id: 2, number: 'INV-002', date: '2024-02-15', amount: '$49.00', status: 'paid' },
    { id: 3, number: 'INV-003', date: '2024-03-15', amount: '$49.00', status: 'paid' },
    { id: 4, number: 'INV-004', date: '2024-04-10', amount: '$49.00', status: 'pending' }
  ]);
  const [showDetails, setShowDetails] = useState(null);

  const toggleDetails = (id) => {
    setShowDetails(showDetails === id ? null : id);
  };

  return (
    <div className="invoice-history">
      <div className="invoice-table">
        <div className="invoice-header">
          <div className="invoice-col invoice-number">Invoice #</div>
          <div className="invoice-col invoice-date">Date</div>
          <div className="invoice-col invoice-amount">Amount</div>
          <div className="invoice-col invoice-status">Status</div>
          <div className="invoice-col invoice-actions">Actions</div>
        </div>
        {invoices.map(invoice => (
          <div key={invoice.id} className="invoice-row">
            <div className="invoice-col invoice-number">{invoice.number}</div>
            <div className="invoice-col invoice-date">{invoice.date}</div>
            <div className="invoice-col invoice-amount">{invoice.amount}</div>
            <div className="invoice-col invoice-status status-{invoice.status}">
              {invoice.status === 'paid' && 'Paid'}
              {invoice.status === 'pending' && 'Pending'}
              {invoice.status === 'overdue' && 'Overdue'}
            </div>
            <div className="invoice-col invoice-actions">
              <button onClick={() => toggleDetails(invoice.id)} className="details-btn">
                {showDetails === invoice.id ? 'Hide' : 'Details'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {showDetails !== null && (
        <div className="invoice-details">
          <div className="invoice-details-header">
            <h3>Invoice Details</h3>
            <button onClick={() => setShowDetails(null)} className="close-details">
              ×
            </button>
          </div>
          <div className="invoice-details-body">
            <div className="detail-row">
              <span className="detail-label">Invoice Number:</span>
              <span className="detail-value">INV-00{showDetails}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Date:</span>
              <span className="detail-value">2024-0{showDetails}-15</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Amount:</span>
              <span className="detail-value">$49.00</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Status:</span>
              <span className="detail-value">Paid</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Description:</span>
              <span className="detail-value">Pro Plan Subscription - Monthly</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Payment Method:</span>
              <span className="detail-value">Visa ending in 4242</span>
            </div>
          </div>
          <div className="invoice-details-footer">
            <button className="pay-now-btn">Pay Now</button>
            <button className="download-btn">Download PDF</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default InvoiceHistory;