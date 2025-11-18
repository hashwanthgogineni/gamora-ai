// src/components/ProtectedRoute.tsx
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth"; // adjust import if your hook path differs

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * Wrap a page/component and require authentication.
 * If not logged in, user is redirected to /signin with their original location saved.
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  // While auth state is loading, show a spinner/placeholder
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <p className="text-gray-400 text-sm">Checking authentication…</p>
      </div>
    );
  }

  // If not authenticated → redirect to /signin, passing current path in state
  if (!user) {
    return (
      <Navigate
        to="/signin"
        state={{ from: location }} // full location object to preserve pathname + search
        replace
      />
    );
  }

  // If authenticated → render children
  return <>{children}</>;
};

export default ProtectedRoute;
