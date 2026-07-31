"use client";

import React, { useState } from "react";
import {
  ChevronRight,
  ChevronDown,
  Terminal,
  MessageSquare,
  Brain,
  Wrench,
  Copy,
  Check,
} from "lucide-react";
import clsx from "clsx";

interface LogMessageProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  payload: Record<string, any>;
  kind: string;
}

export function LogMessage({ payload, kind }: LogMessageProps) {
  const [expanded, setExpanded] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  // Try to find a primary message
  const text =
    typeof payload === "string"
      ? payload
      : payload.text || payload.message || payload.content;
  const thought = payload.thought;
  const tool = payload.tool;
  const toolArgs = payload.args;

  // Determine icon and color
  let icon = <Terminal size={12} />;
  let color = "text-gray-400";

  if (kind === "report") {
    icon = <MessageSquare size={12} />;
    color = "text-yellow-500";
  } else if (kind === "status") {
    icon = <Terminal size={12} />;
    color = "text-gray-500";
  } else if (tool) {
    icon = <Wrench size={12} />;
    color = "text-brand-cyan";
  } else if (thought) {
    icon = <Brain size={12} />;
    color = "text-brand-purple";
  }

  // If we have a clear text/thought/tool, show that as primary
  let primaryContent = null;
  if (tool) {
    primaryContent = (
      <span>
        <span className="font-bold">Tool: {tool}</span>{" "}
        <span className="opacity-70">{JSON.stringify(toolArgs)}</span>
      </span>
    );
  } else if (thought) {
    primaryContent = <span className="italic">&quot;{thought}&quot;</span>;
  } else if (text) {
    primaryContent = <span>{text}</span>;
  } else {
    // Fallback: just JSON
    primaryContent = (
      <span className="font-mono">{JSON.stringify(payload)}</span>
    );
  }

  // If the primary content is just the JSON, we don't need expand toggle unless it's huge
  // But actually, we might want to see the raw payload anyway.
  // Let's always allow expand if payload is object.
  const canExpand = typeof payload === "object" && payload !== null;

  const contentClass = clsx(
    "flex-1 min-w-0 text-xs font-mono break-words",
    color,
    !expanded && "truncate",
  );

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div className="flex flex-col gap-1 w-full min-w-0">
      <div
        className="flex items-start gap-2 cursor-pointer group"
        onClick={() => canExpand && setExpanded(!expanded)}
        role="button"
        aria-expanded={expanded}
        tabIndex={0}
        onKeyDown={(e) => {
          if (canExpand && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            setExpanded(!expanded);
          }
        }}
      >
        <div
          className={clsx(
            "mt-0.5 transition-opacity",
            canExpand ? "opacity-50 group-hover:opacity-100" : "opacity-0",
          )}
        >
          {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        </div>
        <div className="mt-0.5 opacity-70 shrink-0">{icon}</div>
        <div className={contentClass}>{primaryContent}</div>
      </div>

      {expanded && (
        <div className="relative pl-6 pr-2 pb-2 text-[10px] font-mono text-gray-500 overflow-x-auto group/code">
          <button
            onClick={handleCopy}
            className={clsx(
              "absolute top-4 right-4 p-1.5 rounded border border-white/10 transition-all z-10",
              isCopied
                ? "bg-green-500/10 text-green-400 border-green-500/20"
                : "bg-black/40 text-gray-400 hover:text-white hover:bg-white/10 opacity-0 group-hover/code:opacity-100 focus:opacity-100"
            )}
            aria-label={isCopied ? "Copied" : "Copy JSON payload"}
            title="Copy JSON"
          >
            {isCopied ? <Check size={12} /> : <Copy size={12} />}
          </button>
          <pre className="bg-black/20 p-2 rounded border border-white/5 whitespace-pre-wrap break-all min-h-[40px]">
            {JSON.stringify(payload, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
