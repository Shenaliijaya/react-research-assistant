import { Link, Route, Routes } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import ChatPage from "./pages/ChatPage";
import AboutPage from "./pages/AboutPage";
import "./App.css";

function App() {
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