/**
 * Auth helpers for signup, login, and session management.
 */

import { getJson, postJson } from "./api";

const TOKEN_KEY = "continuum_token";
const USER_KEY = "continuum_user";
const WORKSPACE_KEY = "continuum_workspace";

export type User = { id: string; email: string };
export type Workspace = { id: string; name: string };
export type AuthSession = {
  token: string;
  user: User;
  workspace: Workspace;
};

export function isAuthEnabled(): boolean {
  return process.env.NEXT_PUBLIC_CONTINUUM_AUTH === "true";
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function getStoredWorkspace(): Workspace | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(WORKSPACE_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function storeSession(session: AuthSession): void {
  localStorage.setItem(TOKEN_KEY, session.token);
  localStorage.setItem(USER_KEY, JSON.stringify(session.user));
  localStorage.setItem(WORKSPACE_KEY, JSON.stringify(session.workspace));
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(WORKSPACE_KEY);
}

export async function signup(
  email: string,
  password: string,
  workspaceName: string
): Promise<AuthSession> {
  const data = await postJson<AuthSession>("/auth/signup", {
    email,
    password,
    workspace_name: workspaceName,
  });
  storeSession(data);
  return data;
}

export async function login(
  email: string,
  password: string
): Promise<AuthSession> {
  const data = await postJson<AuthSession>("/auth/login", {
    email,
    password,
  });
  storeSession(data);
  return data;
}

export async function verifySession(): Promise<boolean> {
  const token = getStoredToken();
  if (!token) return false;
  try {
    await getJson("/auth/me");
    return true;
  } catch {
    clearSession();
    return false;
  }
}
