"use client";

import type { DecisionRecord } from "@/lib/api";
import HierarchyExplorer from "@/components/HierarchyExplorer";

type Props = {
  decision: DecisionRecord;
  onClose?: () => void;
  onSupersede?: () => void;
  onArchive?: () => void;
};

/**
 * DecisionArtifact — wraps HierarchyExplorer with the same external API.
 *
 * Used by Playground and Inspector pages. The Decisions page calls
 * HierarchyExplorer directly.
 */
export default function DecisionArtifact({
  decision,
  onClose,
  onSupersede,
  onArchive,
}: Props) {
  return (
    <HierarchyExplorer
      decision={decision}
      onClose={onClose}
      onSupersede={onSupersede}
      onArchive={onArchive}
    />
  );
}
