import './PaymentMethod.css';
import { useState } from 'react';

function PaymentMethod() {
  const [paymentMethods, setPaymentMethods] = useState([
    { id: 1, type: 'visa', lastFour: '4242', expiry: '12/25', isDefault: true },
    { id: 2, type: 'paypal', lastFour: 'paypal', expiry: '', isDefault: false }
  ]);
  const [addingPayment, setAddingPayment] = useState(false);
  const [newCard, setNewCard] = useState({
    number: '',
    expiry: '',
    cvc: '',
    name: ''
  });

  const handleInputChange = (field, value) => {
    setNewCard(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAddPayment = () => {
    // Simple validation
    if (newCard.number.length >= 13 && newCard.expiry && newCard.cvc.length === 3 && newCard.name) {
      const newMethod = {
        id: paymentMethods.length + 1,
        type: 'card',
        lastFour: newCard.number.slice(-4),
        expiry: newCard.expiry,
        isDefault: false
      };
      setPaymentMethods([...paymentMethods, newMethod]);
      setAddingPayment(false);
      // Reset form
      setNewCard({ number: '', expiry: '', cvc: '', name: '' });
    }
  };

  const handleSetDefault = (id) => {
    setPaymentMethods(paymentMethods.map(method => ({
      ...method,
      isDefault: method.id === id
    })));
  };

  const handleRemovePayment = (id) => {
    setPaymentMethods(paymentMethods.filter(method => method.id !== id));
  };

  return (
    <div className="payment-methods">
      {paymentMethods.length > 0 ? (
        <div className="payment-list">
          {paymentMethods.map(method => (
            <div key={method.id} className={`payment-card ${method.isDefault ? 'default' : ''}`}>
              <div className="payment-info">
                {method.type === 'visa' && <div className="payment-icon">💳 Visa</div>}
                {method.type === 'paypal' && <div className="payment-icon">💰 PayPal</div>}
                {method.type === 'card' && <div className="payment-icon">💳 Card</div>}
                <div className="payment-details">
                  <p className="card-number">•••• •••• •••• {method.lastFour}</p>
                  {method.expiry && <p className="card-expiry">Expires {method.expiry}</p>}
                  {method.isDefault && <span className="default-badge">Default</span>}
                </div>
              </div>
              <div className="payment-actions">
                {!method.isDefault && (
                  <button onClick={() => handleSetDefault(method.id)} className="set-default-btn">
                    Set as Default
                  </button>
                )}
                <button onClick={() => handleRemovePayment(method.id)} className="remove-payment-btn">
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="no-payment-methods">No payment methods added yet.</p>
      )}

      {!addingPayment && (
        <button onClick={() => setAddingPayment(true)} className="add-payment-method-btn">
          Add Payment Method
        </button>
      )}

      {addingPayment && (
        <div className="add-payment-form">
          <h4>Add New Payment Method</h4>
          <div className="form-group">
            <label htmlFor="card-number">Card Number</label>
            <input
              type="text"
              id="card-number"
              value={newCard.number}
              onChange={(e) => handleInputChange('number', e.target.value.replace(/\s/g, '').replace(/(.{4})/g, '$1 ').trim())}
              placeholder="1234 5678 9012 3456"
              className="form-input"
            />
          </div>
          <div className="form-group">
            <label htmlFor="card-expiry">Expiry Date</label>
            <input
              type="text"
              id="card-expiry"
              value={newCard.expiry}
              onChange={(e) => handleInputChange('expiry', e.target.value)}
              placeholder="MM/YY"
              className="form-input"
              maxLength="5"
            />
          </div>
          <div className="form-group">
            <label htmlFor="card-cvc">CVC</label>
            <input
              type="text"
              id="card-cvc"
              value={newCard.cvc}
              onChange={(e) => handleInputChange('cvc', e.target.value)}
              placeholder="123"
              className="form-input"
              maxLength="3"
            />
          </div>
          <div className="form-group">
            <label htmlFor="card-name">Name on Card</label>
            <input
              type="text"
              id="card-name"
              value={newCard.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="John Doe"
              className="form-input"
            />
          </div>
          <div className="form-actions">
            <button onClick={() => setAddingPayment(false)} className="cancel-btn">
              Cancel
            </button>
            <button onClick={handleAddPayment} className="save-btn">
              Add Card
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default PaymentMethod;