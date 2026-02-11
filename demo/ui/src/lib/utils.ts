/**
 * Shared utility functions for the Continuum Console UI.
 */

/**
 * Return a human-readable relative-time string such as "about 2 hours ago".
 */
export function timeAgo(dateStr: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(dateStr).getTime()) / 1000
  );
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60)
    return `about ${minutes} minute${minutes > 1 ? "s" : ""} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24)
    return `about ${hours} hour${hours > 1 ? "s" : ""} ago`;
  const days = Math.floor(hours / 24);
  if (days < 30)
    return `about ${days} day${days > 1 ? "s" : ""} ago`;
  const months = Math.floor(days / 30);
  return `about ${months} month${months > 1 ? "s" : ""} ago`;
}

/**
 * A single level parsed from a chained scope string.
 *
 * Example: `repo:acme/backend/folder:src/api` yields:
 *   [{ type: "repo", value: "acme/backend", level: 1, specificity: 2 },
 *    { type: "folder", value: "src/api",     level: 2, specificity: 4 }]
 */
export type ScopeLevel = {
  type: string;
  value: string;
  level: number;
  specificity: number;
};

/**
 * Parse a Continuum scope string into typed hierarchy levels.
 *
 * Known prefixes: repo, folder, user, workflow, team.
 * Falls back to a single "scope" level if no known prefix is found.
 */
const KNOWN_PREFIXES = ["repo:", "folder:", "user:", "workflow:", "team:"];

export function parseScope(scope: string): ScopeLevel[] {
  if (!scope) return [];

  // Find positions of known prefixes
  const positions: { prefix: string; idx: number }[] = [];
  for (const prefix of KNOWN_PREFIXES) {
    let searchFrom = 0;
    while (true) {
      const idx = scope.indexOf(prefix, searchFrom);
      if (idx === -1) break;
      // Only count if at start or preceded by /
      if (idx === 0 || scope[idx - 1] === "/") {
        positions.push({ prefix, idx });
      }
      searchFrom = idx + prefix.length;
    }
  }

  if (positions.length === 0) {
    // No known prefix — treat whole string as a single scope
    const segments = scope.split("/").filter(Boolean);
    return [
      {
        type: "scope",
        value: scope,
        level: 1,
        specificity: segments.length,
      },
    ];
  }

  // Sort by position
  positions.sort((a, b) => a.idx - b.idx);

  const levels: ScopeLevel[] = [];
  let cumulativeSegments = 0;

  for (let i = 0; i < positions.length; i++) {
    const start = positions[i].idx + positions[i].prefix.length;
    const end =
      i + 1 < positions.length
        ? positions[i + 1].idx - 1 // -1 to skip the / separator
        : scope.length;

    const value = scope.slice(start, end);
    const type = positions[i].prefix.replace(":", "");
    const valueSegments = value.split("/").filter(Boolean);
    // +1 for the prefix segment itself
    cumulativeSegments += 1 + valueSegments.length;

    levels.push({
      type,
      value,
      level: i + 1,
      specificity: cumulativeSegments,
    });
  }

  return levels;
}

/**
 * Simple className merge — filters out falsy values and joins.
 */
export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}
