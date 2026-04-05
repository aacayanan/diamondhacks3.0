import { useState } from 'react';

function FeedbackForm() {
  const [name, setName] = useState('');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    fetch('/api/dead-end', { method: 'POST', body: JSON.stringify({ name, message }) });
    setSubmitted(true);
  };

  return (
    <div className="app">
      <div className="container">
        <div className="card">
          <h1>Feedback</h1>
          {submitted ? (
            <p style={{ textAlign: 'center', color: '#16a34a' }}>
              Thank you for your feedback!
            </p>
          ) : (
            <form className="feedback-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="name">Name</label>
                <input
                  id="name"
                  className="form-input"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                />
              </div>
              <div className="form-group">
                <label htmlFor="message">Message</label>
                <textarea
                  id="message"
                  className="form-input"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Your feedback"
                  rows={4}
                />
              </div>
              <button type="submit" className="submit-btn">
                Submit
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default FeedbackForm;
