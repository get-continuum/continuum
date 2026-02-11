"use client";

import { useState } from "react";

type Props = {
  scopes: string[];
  onChange: (scopes: string[]) => void;
};

export default function ScopePills({ scopes, onChange }: Props) {
  const [adding, setAdding] = useState(false);
  const [newScope, setNewScope] = useState("");

  const remove = (s: string) => {
    onChange(scopes.filter((x) => x !== s));
  };

  const add = () => {
    const trimmed = newScope.trim();
    if (trimmed && !scopes.includes(trimmed)) {
      onChange([...scopes, trimmed]);
    }
    setNewScope("");
    setAdding(false);
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      {scopes.map((s) => (
        <span
          key={s}
          className="flex items-center gap-1 rounded-full border border-zinc-200 bg-zinc-100 px-2.5 py-1 text-xs font-medium dark:border-zinc-700 dark:bg-zinc-800"
        >
          <code>{s}</code>
          <button
            onClick={() => remove(s)}
            className="ml-0.5 text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-50"
          >
            &times;
          </button>
        </span>
      ))}
      {adding ? (
        <input
          autoFocus
          value={newScope}
          onChange={(e) => setNewScope(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") add();
            if (e.key === "Escape") setAdding(false);
          }}
          onBlur={add}
          placeholder="scope:value"
          className="rounded-full border border-zinc-300 px-2.5 py-1 text-xs outline-none focus:ring-2 focus:ring-teal-500/30 dark:border-zinc-700 dark:bg-zinc-900"
        />
      ) : (
        <button
          onClick={() => setAdding(true)}
          className="rounded-full border border-dashed border-zinc-300 px-2.5 py-1 text-xs text-zinc-500 hover:border-zinc-400 hover:text-zinc-700 dark:border-zinc-700 dark:hover:border-zinc-600"
        >
          + Add scope
        </button>
      )}
    </div>
  );
}
