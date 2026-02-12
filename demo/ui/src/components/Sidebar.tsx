"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/* SVG icon components */
function PlayIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4.5 3L12 8L4.5 13V3Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function DecisionsIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5 6H11M5 8.5H9M5 11H7" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" />
    </svg>
  );
}

function InspectorIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function GraphIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="4" cy="4" r="2" stroke="currentColor" strokeWidth="1.25" />
      <circle cx="12" cy="4" r="2" stroke="currentColor" strokeWidth="1.25" />
      <circle cx="8" cy="12" r="2" stroke="currentColor" strokeWidth="1.25" />
      <path d="M5.5 5.5L7 10.5M10.5 5.5L9 10.5" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" />
    </svg>
  );
}

function IntegrationsIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6.5 2L8 4.5L6.5 7H3.5L2 4.5L3.5 2H6.5Z" stroke="currentColor" strokeWidth="1.25" strokeLinejoin="round" />
      <path d="M12.5 9L14 11.5L12.5 14H9.5L8 11.5L9.5 9H12.5Z" stroke="currentColor" strokeWidth="1.25" strokeLinejoin="round" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="8" cy="8" r="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M8 1.5V3.5M8 12.5V14.5M1.5 8H3.5M12.5 8H14.5M3.05 3.05L4.46 4.46M11.54 11.54L12.95 12.95M3.05 12.95L4.46 11.54M11.54 4.46L12.95 3.05" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" />
    </svg>
  );
}

const NAV_ITEMS = [
  { href: "/playground", label: "Playground", Icon: PlayIcon },
  { href: "/decisions", label: "Decisions", Icon: DecisionsIcon },
  { href: "/inspector", label: "Inspector", Icon: InspectorIcon },
  { href: "/graph", label: "Graph", Icon: GraphIcon },
  { href: "/integrations", label: "Integrations", Icon: IntegrationsIcon },
  { href: "/settings", label: "Settings", Icon: SettingsIcon },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-52 shrink-0 flex-col border-r border-white/[0.06] bg-[#0a0a0f]">
      <nav className="flex flex-col gap-0.5 p-2 pt-3">
        {NAV_ITEMS.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={[
                "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-all",
                active
                  ? "bg-teal-500/10 text-teal-400 shadow-[inset_0_0_0_1px_rgba(20,184,166,0.15)]"
                  : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200",
              ].join(" ")}
            >
              <span className="leading-none">
                <item.Icon />
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
