import { useEffect, useRef, useState, useMemo} from "react";
import type { SubmitEvent } from "react";
import TraceStep from "../components/TraceStep";

type ThoughtStep = {
  step_number: number;
  thought?: string | null;
  tool?: string | null;
  tool_input?: string | null;
  observation?: string | null;
};

type AgentResponse = {
  final_answer: string;
  trace?: ThoughtStep[];
  iteration_count?: number;
  latency_ms?: number;
  stop_reason?: string;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "thinking" | "complete" | "error";
  trace?: ThoughtStep[];
  iterationCount?: number;
  latencyMs?: number;
  stopReason?: string;
};

const API_URL = "http://localhost:8000/agent/query";

const exampleQuestions = [
    "How long can customers export data after cancelling?",
    "What is the population of France?",
    "What is the area of Germany?",
    "What is 125 multiplied by 48?",
];

function createId() {
  return crypto.randomUUID();
}

function ChatPage() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isTraceOpen, setIsTraceOpen] = useState(false);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sessionId = useMemo(() => crypto.randomUUID(), []);

  const selectedMessage = messages.find(
    (message) => message.id === selectedMessageId
  );

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages]);

  const toggleTrace = (message: ChatMessage) => {
  if (!message.trace?.length) {
    return;
  }

  const isSelectedMessage = selectedMessageId === message.id;

  if (isTraceOpen && isSelectedMessage) {
    setIsTraceOpen(false);
    return;
  }

  setSelectedMessageId(message.id);
  setIsTraceOpen(true);
};

  const handleSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    const question = query.trim();

    if (!question || isLoading) {
      return;
    }

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content: question,
      status: "complete",
    };

    const assistantMessageId = createId();
    const thinkingMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "Thinking…",
      status: "thinking",
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
      thinkingMessage,
    ]);
    setQuery("");
    setIsLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: question,
          session_id: sessionId,
          return_trace: true,
        }),
      });

      if (!response.ok) {
        let detail = "The assistant could not complete that request.";

        try {
          const errorBody = await response.json();
          detail = errorBody.detail ?? errorBody.message ?? detail;
        } catch {
          // The fallback message is used when the API does not return JSON.
        }

        throw new Error(detail);
      }

      const data: AgentResponse = await response.json();

      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                content: data.final_answer || "The assistant returned an empty answer.",
                status: "complete",
                trace: data.trace ?? [],
                iterationCount: data.iteration_count,
                latencyMs: data.latency_ms,
                stopReason: data.stop_reason,
              }
            : message
        )
      );
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Something went wrong while contacting the assistant.";

      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                content: errorMessage,
                status: "error",
              }
            : message
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  const handleClearChat = () => {
    setMessages([]);
    setQuery("");
    setIsTraceOpen(false);
    setSelectedMessageId(null);
  };

  const handleKeyDown = (
  event: React.KeyboardEvent<HTMLTextAreaElement>
) => {
  if (event.key !== "Enter" || event.shiftKey) {
    return;
  }

  event.preventDefault();

  if (!isLoading && query.trim()) {
    event.currentTarget.form?.requestSubmit();
  }
};

  return (
    <main className="chat-page">
      <div
        className={`chat-layout ${
          isTraceOpen ? "chat-layout-trace-open" : ""
        }`}
      >
        <section className="chat-panel" aria-label="Assistant chat">
          <header className="chat-header">
            <div>
              <p className="eyebrow">Research assistant</p>
              <h1>Ask the ReAct Agent</h1>
              <p className="chat-subtitle">
                Ask a question and review the answer. Your earlier questions and
                answers remain in this conversation until you clear it.
              </p>
            </div>
          </header>

          <div className="chat-messages" aria-live="polite">
            {messages.length === 0 && (
              <div className="chat-message assistant-message">
                <p className="message-label">Assistant</p>
                <p>
                  Hi. Ask me a question about the research material, a world fact,
                  or a calculation.
                </p>
              </div>
            )}

            {messages.map((message) => (
              <article
                className={[
                  "chat-message",
                  message.role === "user" ? "user-message" : "assistant-message",
                  message.status === "thinking" ? "loading-message" : "",
                  message.status === "error" ? "error-message" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                key={message.id}
              >
                <p className="message-label">
                  {message.role === "user" ? "You" : "Assistant"}
                </p>
                <p>{message.content}</p>

                {message.role === "assistant" &&
                  message.status === "complete" &&
                  Boolean(message.trace?.length) && (
                    <button
                      className="message-trace-button"
                      type="button"
                      onClick={() => toggleTrace(message)}
                    >
                      {isTraceOpen && selectedMessageId === message.id ? "Hide reasoning trace" : "View reasoning trace"}
                    </button>
                  )}
              </article>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form className="chat-form" onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor="chat-question">
              Ask a question
            </label>
            <textarea
              id="chat-question"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question…"
              disabled={isLoading}
              rows={3}
            />

            <div className="chat-form-actions">
              <div className="example-buttons" aria-label="Example questions">
                {exampleQuestions.map((example) => (
                  <button
                    className="example-button"
                    type="button"
                    key={example}
                    onClick={() => handleExampleClick(example)}
                    disabled={isLoading}
                  >
                    {example}
                  </button>
                ))}
              </div>

              <div className="chat-action-buttons">
                <button
                  className="clear-button"
                  type="button"
                  onClick={handleClearChat}
                  disabled={isLoading || messages.length === 0}
                >
                  Clear chat
                </button>
                <button type="submit" disabled={isLoading || !query.trim()}>
                  {isLoading ? "Thinking…" : "Send"}
                </button>
              </div>
            </div>
          </form>
        </section>

        {isTraceOpen && (
          <aside className="trace-sidebar" aria-label="Reasoning trace">
            <div className="trace-sidebar-header">
              <div>
                <p className="eyebrow">Selected response</p>
                <h2>Reasoning trace</h2>
              </div>
              <button
                className="trace-close-button"
                type="button"
                onClick={() => setIsTraceOpen(false)}
                aria-label="Close reasoning trace"
              >
                ×
              </button>
            </div>

            {!selectedMessage?.trace?.length ? (
              <p className="trace-empty">
                Select “View reasoning trace” on an assistant response to review
                its steps.
              </p>
            ) : (
              <>
                <div className="metadata">
                  {selectedMessage.iterationCount !== undefined && (
                    <span>{selectedMessage.iterationCount} iterations</span>
                  )}
                  {selectedMessage.latencyMs !== undefined && (
                    <span>{selectedMessage.latencyMs} ms</span>
                  )}
                  {selectedMessage.stopReason && (
                    <span>{selectedMessage.stopReason}</span>
                  )}
                </div>

                <div className="trace-list">
                  {selectedMessage.trace.map((step) => (
                    <TraceStep key={step.step_number} step={step} />
                  ))}
                </div>
              </>
            )}
          </aside>
        )}
      </div>
    </main>
  );
}

export default ChatPage;