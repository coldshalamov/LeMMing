"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { AgentInfo, OrgGraph } from "@/lib/types";
import { OrgTimer } from "./OrgTimer";
import { AgentCard } from "./AgentCard";
import {
  Users,
  Zap,
  Brain,
  Sparkles,
  Terminal,
  FileText,
  Database,
  Globe,
} from "lucide-react";
import clsx from "clsx";

interface OrgGraphViewProps {
  agents: AgentInfo[];
  graph: OrgGraph;
  selectedAgent: string | null;
  onSelectAgent: (name: string | null) => void;
  currentTick: number;
  className?: string;
}

export function OrgGraphView({
  agents,
  graph,
  selectedAgent,
  onSelectAgent,
  currentTick,
  className,
}: OrgGraphViewProps) {
  // Simple grid layout for now as placeholder
  return (
    <div className={clsx("p-8 overflow-auto", className)}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto pt-24">
        {agents.map((agent) => (
          <div key={agent.name} className="relative">
            <AgentCard
              agent={agent}
              currentTick={currentTick}
              isSelected={selectedAgent === agent.name}
              onSelect={() => onSelectAgent(agent.name === selectedAgent ? null : agent.name)}
              variant="compact"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
