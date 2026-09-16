import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import ChatPage from "./pages/ChatPage";
import AboutPage from "./pages/AboutPage";
import "./App.css";

const HEALTH_URL = "http://localhost:8000/health";
const HEALTH_CHECK_INTERVAL_MS = 30_000;

function App() {
  const [isApiOnline, setIsApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;

    const checkHealth = async () => {
      try {
        const response = await fetch(HEALTH_URL);

        if (!response.ok) {
          throw new Error("Health check failed.");
        }

        const data: { status?: string; collection_size?: number } =
          await response.json();

        if (!isMounted) {
          return;
        }

        setIsApiOnline(data.status === "ok");
      } catch {
        if (!isMounted) {
          return;
        }

        setIsApiOnline(false);
      }
    };

    void checkHealth();

    const intervalId = window.setInterval(
      () => void checkHealth(),
      HEALTH_CHECK_INTERVAL_MS
    );

    return () => {
      isMounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  const healthLabel =
    isApiOnline === null
      ? "Checking API…"
      : isApiOnline
        ? "API online"
        : "API offline";

  return (
    <>
      <header className="site-header">
        <Link className="brand" to="/">
          ReAct Assistant
        </Link>

        <nav className="site-nav" aria-label="Main navigation">
          <Link to="/">Home</Link>
          <Link to="/chat">Chat</Link>
          <Link to="/about">About</Link>
        </nav>

        <div
        className={[
          "api-status",
          isApiOnline === null
            ? "api-status-checking"
            : isApiOnline
              ? "api-status-online"
              : "api-status-offline",
        ].join(" ")}
        role="status"
        aria-live="polite"
      >
        <span className="api-status-dot" aria-hidden="true" />
        <span>{isApiOnline ? "Online" : "Offline"}</span>
      </div>
      </header>

      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/about" element={<AboutPage />} />
      </Routes>
    </>
  );
}

export default App;