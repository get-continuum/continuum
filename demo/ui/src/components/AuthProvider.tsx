"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { ReactNode } from "react";
import {
  clearSession,
  getStoredToken,
  getStoredUser,
  getStoredWorkspace,
  isAuthEnabled,
  verifySession,
} from "@/lib/auth";
import type { User, Workspace } from "@/lib/auth";

type AuthCtx = {
  ready: boolean;
  authenticated: boolean;
  user: User | null;
  workspace: Workspace | null;
  token: string | null;
  logout: () => void;
};

const AuthContext = createContext<AuthCtx>({
  ready: false,
  authenticated: false,
  user: null,
  workspace: null,
  token: null,
  logout: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    // If auth is not enabled (local mode), skip everything
    if (!isAuthEnabled()) {
      setReady(true);
      setAuthenticated(true);
      setWorkspace({ id: "ws_default", name: "default" });
      return;
    }

    // Hosted mode: verify stored session
    const storedToken = getStoredToken();
    if (!storedToken) {
      setReady(true);
      return;
    }

    verifySession().then((valid) => {
      if (valid) {
        setAuthenticated(true);
        setUser(getStoredUser());
        setWorkspace(getStoredWorkspace());
        setToken(storedToken);
      }
      setReady(true);
    });
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setAuthenticated(false);
    setUser(null);
    setWorkspace(null);
    setToken(null);
    window.location.href = "/login";
  }, []);

  return (
    <AuthContext.Provider
      value={{ ready, authenticated, user, workspace, token, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}
