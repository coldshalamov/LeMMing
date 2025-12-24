
"use client";

import { AgentInfo } from "@/lib/types";
import { OrgTimer } from "./OrgTimer";
import { Brain, Sparkles, Terminal, FileText, Database, Globe } from "lucide-react";
import clsx from "clsx";
import { motion } from "framer-motion";
import { memo } from "react";

interface AgentCardProps {
    agent: AgentInfo;
    currentTick: number;
    isSelected?: boolean;
    onSelect?: () => void;
    variant?: "compact" | "full";
}

// Helper to map model/temp to stats
function getAgentStats(model: string, temperature: number = 0.7) {
    let intelligence = 65; // Base
    if (model.includes("gpt-4")) intelligence = 92;
    if (model.includes("gpt-4-turbo")) intelligence = 95;
    if (model.includes("opus")) intelligence = 98;
    if (model.includes("sonnet")) intelligence = 88;
    if (model.includes("haiku")) intelligence = 75;

    // Fake temperature for now as it's not in the simple AgentInfo (would be in full config)
    const creativity = 70;

    return { intelligence, creativity };
}

function ToolIcon({ tool }: { tool: string }) {
    if (tool.includes("read")) return <FileText size={12} />;
    if (tool.includes("write")) return <FileText size={12} className="text-yellow-400" />;
    if (tool.includes("web") || tool.includes("browser")) return <Globe size={12} />;
    if (tool.includes("sql") || tool.includes("data")) return <Database size={12} />;
    return <Terminal size={12} />;
}

// Memoized content that doesn't depend on currentTick
const AgentCardContent = memo(function AgentCardContent({ agent, isSelected, variant }: { agent: AgentInfo, isSelected?: boolean, variant: string }) {
    const { intelligence, creativity } = getAgentStats(agent.model);

    return (
        <>
            {/* Stats Bars */}
            <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-gray-500 font-mono">
                    <Brain size={12} />
                    <span className="w-16">INT</span>
                    <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${intelligence}%` }}
                            className="h-full bg-brand-purple"
                        />
                    </div>
                    <span className="w-6 text-right text-gray-400">{intelligence}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500 font-mono">
                    <Sparkles size={12} />
                    <span className="w-16">CRE</span>
                    <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${creativity}%` }}
                            className="h-full bg-brand-cyan"
                        />
                    </div>
                    <span className="w-6 text-right text-gray-400">{creativity}</span>
                </div>
            </div>

            {/* Description (Only if full or selected) */}
            {(isSelected || variant === "full") && (
                <div className="text-xs text-gray-400 leading-relaxed border-t border-white/5 pt-3">
                    {agent.description}
                </div>
            )}

            {/* Toolbelt Chip Row */}
            <div className="flex flex-wrap gap-1 pt-1">
                {agent.tools.map((tool) => (
                    <div key={tool} className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/5 border border-white/5 text-[10px] text-gray-400">
                        <ToolIcon tool={tool} />
                        {tool}
                    </div>
                ))}
            </div>

            {/* Credits */}
            {agent.credits && (
                <div className="mt-2 text-[10px] font-mono text-gray-500 flex justify-between">
                    <span>CREDITS</span>
                    <span className={clsx(agent.credits.credits_left && agent.credits.credits_left < 100 ? "text-red-500" : "text-brand-lime")}>
                        {agent.credits.credits_left?.toFixed(1)} / {agent.credits.max_credits}
                    </span>
                </div>
            )}
        </>
    );
});

export function AgentCard({ agent, currentTick, isSelected, onSelect, variant = "compact" }: AgentCardProps) {
    const isFiring = (currentTick % agent.schedule.run_every_n_ticks) === (agent.schedule.phase_offset % agent.schedule.run_every_n_ticks);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (onSelect && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            onSelect();
        }
    };

    return (
        <motion.div
            layoutId={`agent-card-${agent.name}`}
            onClick={onSelect}
            onKeyDown={handleKeyDown}
            role="button"
            tabIndex={0}
            aria-pressed={isSelected}
            aria-label={`Select agent ${agent.name}`}
            className={clsx(
                "relative rounded-xl border transition-all duration-300 overflow-hidden cursor-pointer group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-cyan",
                isSelected
                    ? "border-brand-cyan shadow-[0_0_25px_rgba(6,182,212,0.15)] bg-neo-panel z-10 scale-105"
                    : "border-neo-border bg-neo-surface hover:border-white/20 hover:bg-neo-surface-highlight"
            )}
            style={{
                backdropFilter: "blur(20px)",
            }}
        >
            {/* Active Status Stripe */}
            {isFiring && (
                <div className="absolute top-0 left-0 w-full h-1 bg-brand-lime shadow-[0_0_15px_#84cc16]" />
            )}

            <div className="p-4 flex flex-col gap-4">
                {/* Header */}
                <div className="flex justify-between items-start">
                    <div className="flex-1 flex flex-col gap-4">
                         <div className="flex justify-between items-start">
                            <div>
                                <h3 className={clsx("font-bold font-mono tracking-tight", isSelected ? "text-white text-lg" : "text-gray-200")}>
                                    {agent.name}
                                </h3>
                                <div className="text-xs text-brand-cyan font-mono uppercase tracking-widest opacity-80 mt-1">
                                    {agent.title}
                                </div>
                            </div>

                             <OrgTimer
                                n={agent.schedule.run_every_n_ticks}
                                offset={agent.schedule.phase_offset}
                                currentTick={currentTick}
                                size={isSelected ? 48 : 32}
                                className={clsx("transition-transform", isFiring ? "scale-110" : "scale-100")}
                            />
                        </div>

                         {/* We can memoize the rest of the content below the header */}
                         <AgentCardContent agent={agent} isSelected={isSelected} variant={variant} />
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
