import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Retrospective from "./pages/Retrospective";
import Responses from "./pages/Responses";
import Influencers from "./pages/Influencers";

function RequireAuth({ children }: { children: JSX.Element }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

// Mirror of RequireAuth for the login route itself -- without this, going
// straight to /login always rendered the form regardless of auth state,
// since RequireAuth only ever guarded the routes nested under it.
function RedirectIfAuthed({ children }: { children: JSX.Element }) {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) return <Navigate to="/retrospective" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <RedirectIfAuthed>
            <Login />
          </RedirectIfAuthed>
        }
      />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/retrospective" replace />} />
        <Route path="retrospective" element={<Retrospective />} />
        <Route path="responses" element={<Responses />} />
        <Route path="influencers" element={<Influencers />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
