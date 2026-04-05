function About() {
  return (
    <div className="app">
      <div className="container">
        <div className="card">
          <h1>About</h1>
          <p style={{ marginBottom: '1.5rem', color: '#64748b', lineHeight: '1.6' }}>
            Diamond Hacks 3.0 is a QA testing demo showcasing automated browser
            testing with BrowserUse SDK. This application contains intentional bugs
            for testing purposes.
          </p>
          <button className="submit-btn" onClick={(e) => e.preventDefault()}>
            Contact Us
          </button>
        </div>
      </div>
    </div>
  );
}

export default About;
