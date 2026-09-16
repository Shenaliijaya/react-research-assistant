function AboutPage() {
  return (
    <main className="about-page">
      <section className="about-card">
        <p className="eyebrow">How it works</p>

        <h1>About This Project</h1>

        <p className="about-intro">
          This is a learning project that combines a React TypeScript frontend
          with a FastAPI backend and a ReAct research agent.
        </p>

        <div className="architecture-flow">
          <article>
            <span>1</span>
            <h2>User question</h2>
            <p>The user enters a question in the React frontend.</p>
          </article>

          <article>
            <span>2</span>
            <h2>FastAPI validation</h2>
            <p>Pydantic validates the request before the agent runs.</p>
          </article>

          <article>
            <span>3</span>
            <h2>ReAct agent</h2>
            <p>LangChain helps the agent choose search, retrieve, or calculate.</p>
          </article>

          <article>
            <span>4</span>
            <h2>Evidence and response</h2>
            <p>The API returns an answer, tool trace, latency, and stop reason.</p>
          </article>
        </div>

        <section className="technology-section">
          <h2>Technology used</h2>

          <div className="technology-grid">
            <article>
              <h3>React + TypeScript</h3>
              <p>Builds the interactive frontend and validates UI data shapes.</p>
            </article>

            <article>
              <h3>FastAPI + Pydantic</h3>
              <p>Provides the backend endpoints and validates API data.</p>
            </article>

            <article>
              <h3>LangChain</h3>
              <p>Runs the ReAct agent loop and connects the available tools.</p>
            </article>

            <article>
              <h3>ChromaDB</h3>
              <p>Stores document chunks and retrieves relevant evidence.</p>
            </article>
          </div>
        </section>
      </section>
    </main>
  );
}

export default AboutPage;