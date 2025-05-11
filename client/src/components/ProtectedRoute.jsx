import { Navigate } from "react-router-dom";

// Protected route component that checks for API key
export default function ProtectedRoute({ children }) {
  const apiKey = localStorage.getItem("api-key");

  if (!apiKey) {
    return <Navigate to="/signup" replace />;
  }

  return children;
}
