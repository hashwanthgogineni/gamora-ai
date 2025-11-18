// src/hooks/useAuth.tsx
import { useEffect, useState, createContext, useContext, useCallback } from "react";
import { supabase } from "../lib/supabase";
import type { User } from "@supabase/supabase-js";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  refreshUser: () => Promise<void>; // 👈 optional helper
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  refreshUser: async () => {},
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // helper to force refresh user
  const refreshUser = useCallback(async () => {
    const { data, error } = await supabase.auth.getSession();
    if (!error) {
      setUser(data.session?.user ?? null);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    // Load session on mount
    refreshUser();

    // Subscribe to auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      setLoading(false); // stop loading once we know state
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [refreshUser]);

  return (
    <AuthContext.Provider value={{ user, loading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook to access auth anywhere
export const useAuth = () => useContext(AuthContext);
