"use client";

import Image from "next/image";
import { useAuth } from "./AuthProvider";
import { isAuthEnabled } from "@/lib/auth";

export default function Header() {
  const { workspace, logout } = useAuth();
  const authEnabled = isAuthEnabled();
  const mode = authEnabled ? "Hosted" : "Local";

  const copyApiKey = async () => {
    try {
      const { fetchApiKeys } = await import("@/lib/api");
      const data = await fetchApiKeys();
      if (data.keys.length > 0) {
        await navigator.clipboard.writeText(data.keys[0].id);
        alert("API key ID copied to clipboard");
      } else {
        alert("No API keys found. Create one in Settings.");
      }
    } catch {
      alert("Could not copy API key");
    }
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-zinc-200 bg-white px-4 dark:border-zinc-800 dark:bg-zinc-950">
      {/* Left: Logo + Title */}
      <div className="flex items-center gap-2.5">
        <Image
          src="/continuum-logo.png"
          alt="Continuum"
          width={28}
          height={28}
          className="rounded"
        />
        <span className="text-sm font-semibold tracking-tight">
          Continuum Console
        </span>
      </div>

      {/* Center: Workspace + Mode */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 rounded-md border border-zinc-200 px-2.5 py-1 text-xs dark:border-zinc-800">
          <span className="text-zinc-500 dark:text-zinc-400">Workspace</span>
          <span className="font-medium">{workspace?.name ?? "default"}</span>
        </div>
        <div className="flex items-center gap-1.5 rounded-md border border-zinc-200 px-2.5 py-1 text-xs dark:border-zinc-800">
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              mode === "Hosted" ? "bg-emerald-500" : "bg-zinc-400"
            }`}
          />
          <span className="font-medium">{mode}</span>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {authEnabled && (
          <button
            onClick={copyApiKey}
            className="rounded-md border border-zinc-200 px-2.5 py-1 text-xs font-medium hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
          >
            Copy API Key
          </button>
        )}
        <a
          href="https://docs.getcontinuum.ai"
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-md border border-zinc-200 px-2.5 py-1 text-xs font-medium hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
        >
          Docs
        </a>
        {authEnabled && (
          <button
            onClick={logout}
            className="rounded-md border border-zinc-200 px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50 dark:border-zinc-800 dark:text-red-400 dark:hover:bg-red-950"
          >
            Logout
          </button>
        )}
      </div>
    </header>
  );
}
