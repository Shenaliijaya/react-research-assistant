import { Link } from "react-router-dom";

function LandingPage() {
  return (
    <main className="landing-page">
      <section className="landing-card">
        <p className="eyebrow">React + TypeScript + FastAPI</p>

        <h1>ReAct Research Assistant</h1>

        <p className="landing-intro">
          Ask questions and receive evidence-based answers from an AI agent
          that can search facts, retrieve document context, and perform safe
          calculations.
        </p>

        <div className="feature-list">
          <article className="feature-card">
            <h2>Search</h2>
            <p>Find answers from the supplied general fact table.</p>
          </article>

          <article className="feature-card">
            <h2>Retrieve</h2>
            <p>Find relevant information from ingested documents.</p>
          </article>

          <article className="feature-card">
            <h2>Calculate</h2>
            <p>Use controlled arithmetic instead of model guessing.</p>
          </article>
        </div>

        <Link className="primary-link" to="/chat">
          Try the Assistant
        </Link>
      </section>
    </main>
  );
}

export default LandingPage;