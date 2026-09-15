import { useState } from "react";
import type { SubmitEvent } from "react";
import "./App.css";

type ThoughtStep = {
  step_number: number;
  thought: string;
  tool: string | null;
  tool_input: string | null;
  observation: string | null;
};

type AgentResponse = {
  final_answer: string;
  trace: ThoughtStep[];
  iterations: number;
  latency_ms: number;
  stop_reason: string;
};

const API_URL = "http://127.0.0.1:8000/agent/query";

function App() {
  const [query, setQuery] = useState(
    "How long does a customer have to export their data after cancelling?",
  );
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    const cleanedQuery = query.trim();

    if (!cleanedQuery) {
      setError("Please enter a question.");
      return;
    }

    setIsLoading(true);
    setError("");
    setResponse(null);

    try {
      const apiResponse = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: cleanedQuery,
          session_id: null,
          max_iterations: 10,
          return_trace: true,
        }),
      });

      const data = await apiResponse.json();

      if (!apiResponse.ok) {
        throw new Error(data.detail || "The API request failed.");
      }

      setResponse(data as AgentResponse);
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : "Unable to reach the agent.";

      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="agent-card">
        <p className="eyebrow">React + TypeScript + FastAPI</p>

        <h1>ReAct Research Assistant</h1>

        <p className="intro">
          Ask a question. The agent can retrieve document evidence, search
          supplied facts, or use a calculator.
        </p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="query">Question</label>

          <textarea
            id="query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ask a question..."
            rows={5}
            disabled={isLoading}
          />

          <button type="submit" disabled={isLoading}>
            {isLoading ? "Thinking..." : "Ask Agent"}
          </button>
        </form>

        {error && (
          <section className="message error-message">
            <h2>Request error</h2>
            <p>{error}</p>
          </section>
        )}

        {response && (
          <>
            <section className="message answer-message">
              <h2>Answer</h2>
              <p>{response.final_answer}</p>

              <div className="metadata">
                <span>Iterations: {response.iterations}</span>
                <span>Latency: {response.latency_ms.toFixed(0)} ms</span>
                <span>Stop reason: {response.stop_reason}</span>
              </div>
            </section>

            <section className="trace-section">
              <h2>Agent trace</h2>

              {response.trace.length === 0 ? (
                <p>No tool calls were needed for this request.</p>
              ) : (
                response.trace.map((step) => (
                  <article className="trace-step" key={step.step_number}>
                    <h3>Step {step.step_number}</h3>
                    <p>
                      <strong>Tool:</strong> {step.tool ?? "No tool"}
                    </p>
                    <p>
                      <strong>Tool input:</strong>{" "}
                      {step.tool_input ?? "No input"}
                    </p>
                    <p>
                      <strong>Observation:</strong>{" "}
                      {step.observation ?? "No observation"}
                    </p>
                  </article>
                ))
              )}
            </section>
          </>
        )}
      </section>
    </main>
  );
}

export default App;
