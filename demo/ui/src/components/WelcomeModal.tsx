"use client";

import { useEffect, useState } from "react";
import { COLAB_NOTEBOOK_URL } from "@/lib/constants";

const WELCOMED_KEY = "continuum_welcomed";

export default function WelcomeModal() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const dismissed = localStorage.getItem(WELCOMED_KEY);
    if (!dismissed) {
      setVisible(true);
    }
  }, []);

  function dismiss() {
    localStorage.setItem(WELCOMED_KEY, "true");
    setVisible(false);
  }

  function openColab() {
    window.open(COLAB_NOTEBOOK_URL, "_blank", "noopener,noreferrer");
    dismiss();
  }

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={dismiss}
      />

      {/* Modal */}
      <div className="relative mx-4 w-full max-w-md rounded-2xl border border-zinc-200 bg-white p-6 shadow-xl dark:border-zinc-800 dark:bg-zinc-950">
        {/* Icon */}
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-teal-100 dark:bg-teal-900/30">
          <svg
            className="h-6 w-6 text-teal-600 dark:text-teal-400"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z"
            />
          </svg>
        </div>

        <h2 className="mt-4 text-lg font-semibold tracking-tight">
          Welcome to Continuum!
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
          Want to see Continuum in action? Run through a hands-on demo in Google
          Colab — no setup needed. You&apos;ll commit decisions, enforce actions,
          and see the ambiguity gate in under 5 minutes.
        </p>

        <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
          <button
            onClick={dismiss}
            className="rounded-lg border border-zinc-200 px-4 py-2.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
          >
            Skip for now
          </button>
          <button
            onClick={openColab}
            className="rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-teal-700"
          >
            Open Demo in Colab
          </button>
        </div>
      </div>
    </div>
  );
}
