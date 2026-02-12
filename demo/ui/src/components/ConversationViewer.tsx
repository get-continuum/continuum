"use client";

import { useState } from "react";

type Props = {
  onExtract: (conversations: string[]) => void;
  loading: boolean;
};

const PLACEHOLDER = `Paste a conversation here...

Example:
User: I'm planning a trip to Japan next month. Budget is $3000 max.
Assistant: Great! What are your preferences?
User: I'm vegetarian and prefer trains over flights. No flying please.
User: Always book hotels with free cancellation.`;

export default function ConversationViewer({ onExtract, loading }: Props) {
  const [text, setText] = useState("");

  const handleExtract = () => {
    if (!text.trim()) return;
    onExtract([text.trim()]);
  };

  return (
    <div className="rounded-xl border border-white/[0.08] bg-[#111115] p-5 shadow-sm">
      <h2 className="text-sm font-semibold text-zinc-200">
        Mine Decisions from Conversation
      </h2>
      <p className="mt-1 text-xs text-zinc-500">
        Paste a conversation to extract facts and decision candidates.
      </p>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={8}
        placeholder={PLACEHOLDER}
        className="mt-3 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-zinc-600 outline-none transition-colors focus:border-teal-500/40 focus:ring-2 focus:ring-teal-500/20 resize-none font-mono"
      />
      <button
        onClick={handleExtract}
        disabled={loading || !text.trim()}
        className="mt-3 rounded-lg bg-purple-600 px-5 py-2 text-sm font-medium text-white transition-all hover:bg-purple-500 hover:shadow-lg hover:shadow-purple-600/20 disabled:opacity-50"
      >
        {loading ? "Extracting..." : "Extract Facts & Candidates"}
      </button>
    </div>
  );
}
