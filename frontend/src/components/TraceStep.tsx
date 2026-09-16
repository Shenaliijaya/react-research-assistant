import { useState } from "react";

type ThoughtStep = {
  step_number: number;
  thought?: string | null;
  tool?: string | null;
  tool_input?: string | null;
  observation?: string | null;
};

type TraceStepProps = {
  step: ThoughtStep;
};

function TraceStep({ step }: TraceStepProps) {
  const [showObservation, setShowObservation] = useState(false);

  return (
    <article className="trace-step">
      <h3>Step {step.step_number}</h3>

      {step.thought && (
        <p>
          <strong>Thought:</strong> {step.thought}
        </p>
      )}

      <p>
        <strong>Tool:</strong> {step.tool ?? "No tool"}
      </p>

      <p>
        <strong>Tool input:</strong> {step.tool_input ?? "No input"}
      </p>

      {step.observation && (
        <>
          <button
            className="observation-button"
            type="button"
            onClick={() => setShowObservation((visible) => !visible)}
          >
            {showObservation ? "Hide observation" : "Show observation"}
          </button>

          {showObservation && (
            <p className="observation-text">
              <strong>Observation:</strong> {step.observation}
            </p>
          )}
        </>
      )}
    </article>
  );
}

export default TraceStep;