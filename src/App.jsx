import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home        from "./pages/Home";
import Dashboard   from "./pages/Dashboard";
import Analysis    from "./pages/Analysis";
import Repository  from "./pages/Repository";
import RecentScans from "./pages/RecentScans";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"             element={<Home />}        />
        <Route path="/dashboard"    element={<Dashboard />}   />
        <Route path="/analysis"     element={<Analysis />}    />
        <Route path="/repository"   element={<Repository />}  />
        <Route path="/recent-scans" element={<RecentScans />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;