
"use client";

import { useEffect, useRef, useState } from "react";
import { AgentInfo, OrgGraph } from "@/lib/types";
import { motion } from "framer-motion";
import clsx from "clsx";

interface Point {
    x: number;
    y: number;
    vx: number;
    vy: number;
}

interface OrgGraphProps {
    agents: AgentInfo[];
    graph: OrgGraph;
    selectedAgent: string | null;
    onSelectAgent: (name: string) => void;
    className?: string;
}

export function OrgGraphView({ agents, graph, selectedAgent, onSelectAgent, className }: OrgGraphProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [positions, setPositions] = useState<Record<string, Point>>({});

    // Initialize random positions
    useEffect(() => {
        // Check if we need to initialize positions for new agents
        if (agents.length === 0) return;

        // We only want to set initial positions if they don't exist yet
        // or if the agent count significantly changed (reset)
        // But doing it in useEffect with setPositions is fine as long as we don't do it on every render

        setPositions(prev => {
            const width = containerRef.current?.clientWidth || 800;
            const height = containerRef.current?.clientHeight || 600;

            const next = { ...prev };
            let changed = false;

            agents.forEach(a => {
                if (!next[a.name]) {
                    next[a.name] = {
                        x: Math.random() * width * 0.6 + width * 0.2,
                        y: Math.random() * height * 0.6 + height * 0.2,
                        vx: 0,
                        vy: 0
                    };
                    changed = true;
                }
            });

            return changed ? next : prev;
        });
    }, [agents]);

    // Simulation Loop
    useEffect(() => {
        if (Object.keys(positions).length === 0) return;

        let animationFrameId: number;
        const items = agents.map(a => a.name);

        // Edges
        const edges: [string, string][] = [];
        Object.entries(graph).forEach(([target, node]) => {
            node.can_read.forEach(source => {
                edges.push([source, target]);
            });
        });

        const runSimulation = () => {
            setPositions(prev => {
                const next = { ...prev };
                const width = containerRef.current?.clientWidth || 800;
                const height = containerRef.current?.clientHeight || 600;
                const center = { x: width / 2, y: height / 2 };

                // Constants
                const k = 0.05; // Spring constant
                const repulsion = 5000;
                const damping = 0.85;

                // Reset forces logic or apply directly to velocities
                // We do a simple integration step

                items.forEach(nodeId => {
                    const p = next[nodeId];
                    if (!p) return;

                    let fx = 0;
                    let fy = 0;

                    // 1. Repulsion from other nodes
                    items.forEach(otherId => {
                        if (nodeId === otherId) return;
                        const p2 = prev[otherId];
                        if (!p2) return;

                        const dx = p.x - p2.x;
                        const dy = p.y - p2.y;
                        const distSq = dx * dx + dy * dy;
                        const dist = Math.sqrt(distSq) || 0.1;

                        const f = repulsion / distSq;
                        fx += (dx / dist) * f;
                        fy += (dy / dist) * f;
                    });

                    // 2. Attraction along edges
                    // If we are source, pull to target
                    edges.forEach(([source, target]) => {
                        if (source === nodeId) {
                            const p2 = prev[target];
                            if (p2) {
                                const dx = p2.x - p.x;
                                const dy = p2.y - p.y;
                                fx += k * dx;
                                fy += k * dy;
                            }
                        } else if (target === nodeId) {
                            const p2 = prev[source];
                            if (p2) {
                                const dx = p2.x - p.x;
                                const dy = p2.y - p.y;
                                fx += k * dx;
                                fy += k * dy;
                            }
                        }
                    });

                    // 3. Center Gravity (keep them in view)
                    const dx = center.x - p.x;
                    const dy = center.y - p.y;
                    fx += dx * 0.01;
                    fy += dy * 0.01;

                    // Update Velocity
                    p.vx = (p.vx + fx) * damping;
                    p.vy = (p.vy + fy) * damping;

                    // Update Position
                    p.x += p.vx;
                    p.y += p.vy;

                    // Boundaries (Soft)
                    // if (p.x < 0) p.x = 0;
                    // if (p.y < 0) p.y = 0;
                    // ...

                    next[nodeId] = p;
                });

                return next;
            });

            animationFrameId = requestAnimationFrame(runSimulation);
        };

        runSimulation();
        return () => cancelAnimationFrame(animationFrameId);
    }, [agents, graph]); // Re-bind if graph changes

    return (
        <div ref={containerRef} className={clsx("relative w-full h-full overflow-hidden bg-neo-bg/50 rounded-xl border border-neo-border", className)}>

            {/* SVG for Edges */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
                <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="25" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#4b5563" />
                    </marker>
                    <marker id="arrow-active" viewBox="0 0 10 10" refX="25" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#06b6d4" />
                    </marker>
                </defs>
                {Object.entries(graph).map(([target, node]) =>
                    node.can_read.map(source => {
                        const s = positions[source];
                        const t = positions[target];
                        if (!s || !t) return null;

                        const isRelated = selectedAgent && (source === selectedAgent || target === selectedAgent);

                        return (
                            <line
                                key={`${source}-${target}`}
                                x1={s.x} y1={s.y}
                                x2={t.x} y2={t.y}
                                stroke={isRelated ? "#06b6d4" : "#27272a"}
                                strokeWidth={isRelated ? 2 : 1}
                                strokeOpacity={isRelated ? 0.8 : 0.4}
                                markerEnd={isRelated ? "url(#arrow-active)" : "url(#arrow)"}
                            />
                        );
                    })
                )}
            </svg>

            {/* Nodes */}
            {agents.map(agent => {
                const pos = positions[agent.name] || { x: 0, y: 0 };
                const isSel = selectedAgent === agent.name;

                return (
                    <div
                        key={agent.name}
                        onClick={() => onSelectAgent(agent.name)}
                        className={clsx(
                            "absolute transform -translate-x-1/2 -translate-y-1/2 w-16 h-16 rounded-full flex items-center justify-center cursor-pointer transition-colors border",
                            isSel
                                ? "bg-brand-cyan/20 border-brand-cyan text-brand-cyan shadow-[0_0_15px_rgba(6,182,212,0.4)]"
                                : "bg-neo-surface border-neo-border text-gray-400 hover:border-gray-500"
                        )}
                        style={{
                            left: pos.x,
                            top: pos.y,
                            zIndex: isSel ? 10 : 1
                        }}
                    >
                        <div className="text-[10px] text-center font-mono leading-tight px-1 overflow-hidden">
                            {agent.name.length > 10 ? agent.name.substring(0, 8) + ".." : agent.name}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
