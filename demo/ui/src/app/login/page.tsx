"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { login } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/playground");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glow-bg flex min-h-screen flex-col items-center justify-center px-4">
      {/* Logo + tagline */}
      <div className="animate-fadeIn mb-10 flex flex-col items-center">
        <Image
          src="/continuum-logo.png"
          alt="Continuum"
          width={56}
          height={56}
          className="rounded-xl"
        />
        <h1 className="mt-6 text-center text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Intelligence without continuity
          <br />
          isn&apos;t reliable.
        </h1>
      </div>

      {/* Glass login card */}
      <div className="animate-slideUp glass-card w-full max-w-sm p-6">
        <h2 className="text-center text-sm font-medium text-zinc-400">
          Sign in to your workspace
        </h2>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {error && (
            <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-zinc-400">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white placeholder-zinc-500 outline-none transition-colors focus:border-blue-500/40 focus:ring-2 focus:ring-blue-500/20"
              placeholder="you@company.com"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-400">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white placeholder-zinc-500 outline-none transition-colors focus:border-blue-500/40 focus:ring-2 focus:ring-blue-500/20"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-teal-600 py-2.5 text-sm font-medium text-white transition-all hover:bg-teal-500 hover:shadow-lg hover:shadow-teal-600/20 disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Log In"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-zinc-500">
          Don&apos;t have an account?{" "}
          <Link
            href="/signup"
            className="font-medium text-teal-400 transition-colors hover:text-teal-300"
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
