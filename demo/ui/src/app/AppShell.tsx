"use client";

import { usePathname } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";
import WelcomeModal from "@/components/WelcomeModal";
import { isAuthEnabled } from "@/lib/auth";

const PUBLIC_PATHS = ["/login", "/signup"];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { ready, authenticated } = useAuth();
  const authEnabled = isAuthEnabled();

  // Auth pages (login/signup) render without shell
  if (PUBLIC_PATHS.includes(pathname)) {
    return <>{children}</>;
  }

  // Wait for auth to initialise
  if (!ready) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0d0d12]">
        {/* Skeleton loading spinner */}
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-700 border-t-teal-500" />
          <span className="text-sm text-zinc-500">Loading...</span>
        </div>
      </div>
    );
  }

  // If auth is enabled and user is not authenticated, redirect to login
  if (authEnabled && !authenticated) {
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    return null;
  }

  return (
    <div className="flex h-screen flex-col">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto bg-[#0d0d12]">{children}</main>
      </div>
      <WelcomeModal />
    </div>
  );
}
