import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home.jsx";
import Seatings from "./pages/Seatings.jsx";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/seatings" element={<Seatings />} />
    </Routes>
  );
}

export default App;
