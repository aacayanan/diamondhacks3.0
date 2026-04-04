import './App.css';

function App() {
  return (
    <div className="app">
      <div className="container">
        <div className="card">
          <h1>Feedback Form - HMR Working!</h1>
          <form className="feedback-form">
            <div className="form-group">
              <label htmlFor="name">Name</label>
              <input
                type="text"
                id="name"
                placeholder="Your name"
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                placeholder="your@email.com"
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label htmlFor="message">Message</label>
              <textarea
                id="message"
                placeholder="Your message..."
                rows="5"
                className="form-input"
              />
            </div>
            <button
              type="submit"
              id="submit-btn"
              className="submit-btn"
              disabled={true}
            >
              Submit
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;