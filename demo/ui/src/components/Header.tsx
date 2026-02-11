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
    <header className="flex h-14 items-center justify-between border-b border-white/[0.06] bg-[#0a0a0f] px-4">
      {/* Left: Logo + Title */}
      <div className="flex items-center gap-2.5">
        <Image
          src="/continuum-logo.png"
          alt="Continuum"
          width={28}
          height={28}
          className="rounded"
        />
        <span className="text-sm font-semibold tracking-tight text-white">
          Continuum Console
        </span>
      </div>

      {/* Center: Workspace + Mode */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2.5 py-1 text-xs">
          <span className="text-zinc-500">Workspace</span>
          <span className="font-medium text-zinc-200">{workspace?.name ?? "default"}</span>
        </div>
        <div className="flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2.5 py-1 text-xs">
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              mode === "Hosted" ? "bg-emerald-500" : "bg-zinc-500"
            }`}
          />
          <span className="font-medium text-zinc-200">{mode}</span>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {authEnabled && (
          <button
            onClick={copyApiKey}
            className="rounded-md border border-white/10 px-2.5 py-1 text-xs font-medium text-zinc-300 transition-colors hover:bg-white/5"
          >
            Copy API Key
          </button>
        )}
        <a
          href="https://continuum-4f565acd.mintlify.app/"
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-md border border-white/10 px-2.5 py-1 text-xs font-medium text-zinc-300 transition-colors hover:bg-white/5"
        >
          Docs
        </a>
        {authEnabled && (
          <button
            onClick={logout}
            className="rounded-md border border-white/10 px-2.5 py-1 text-xs font-medium text-red-400 transition-colors hover:bg-red-500/10"
          >
            Logout
          </button>
        )}
      </div>
    </header>
  );
}
