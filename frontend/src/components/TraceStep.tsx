import { useState } from "react";

type ThoughtStep = {
  step_number: number;
  thought: string;
  tool: string | null;
  tool_input: string | null;
  observation: string | null;
};

type TraceStepProps = {
  step: ThoughtStep;
};

function getToolClassName(tool: string | null) {
  if (tool === "search") {
    return "tool-badge tool-badge-search";
  }

  if (tool === "retrieve") {
    return "tool-badge tool-badge-retrieve";
  }

  if (tool === "calculate") {
    return "tool-badge tool-badge-calculate";
  }

  return "tool-badge tool-badge-none";
} 

function TraceStep({ step }: TraceStepProps) {
  const [showObservation, setShowObservation] = useState(false);

  return (
    <article className="trace-step">
      <h3>Step {step.step_number}</h3>
      
      <div className="tool-row">
        <strong>Tool:</strong>
        
        <span className={getToolClassName(step.tool)}>
            {step.tool ?? "No tool"}
        </span>
      </div>

      <p>
        <strong>Tool input:</strong> {step.tool_input ?? "No input"}
      </p>

      {step.observation && (
        <>
          <button
            className="observation-button"
            type="button"
            onClick={() => setShowObservation(!showObservation)}
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