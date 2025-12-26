
"use client";

import { useEffect, useRef, useState } from "react";
import { AgentInfo, OrgGraph } from "@/lib/types";
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
    const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
    const [isDraggingCanvas, setIsDraggingCanvas] = useState(false);
    const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null);
    const [pinnedNodes, setPinnedNodes] = useState<Set<string>>(new Set());
    const wasDragged = useRef(false);
    const lastMousePos = useRef({ x: 0, y: 0 });

    // Initialize positions if needed
    useEffect(() => {
        if (agents.length === 0) return;
        const width = containerRef.current?.clientWidth || 800;
        const height = containerRef.current?.clientHeight || 600;

        if (Object.keys(positions).length === agents.length) return;

        const initial: Record<string, Point> = {};
        agents.forEach(a => {
            initial[a.name] = {
                x: Math.random() * width * 0.6 + width * 0.2,
                y: Math.random() * height * 0.6 + height * 0.2,
                vx: 0,
                vy: 0
            };
        });
        setPositions(initial);
    }, [agents.length]);

    // Filter out human from valid nodes
    const validAgents = useMemo(() => agents.filter(a => a.name !== "human"), [agents]);
    const items = useMemo(() => validAgents.map(a => a.name), [validAgents]);

    // Simulation Loop
    useEffect(() => {
        if (Object.keys(positions).length === 0) return;

        let animationFrameId: number;

        const edges: [string, string][] = [];
        Object.entries(graph).forEach(([target, node]) => {
            // Only include edges if both source and target are in our validAgents list
            if (!items.includes(target)) return;

            node.can_read.forEach(source => {
                if (items.includes(source)) {
                    edges.push([source, target]);
                }
            });
        });

        const runSimulation = () => {
            setPositions(prev => {
                const next = { ...prev };
                const width = containerRef.current?.clientWidth || 800;
                const height = containerRef.current?.clientHeight || 600;
                const center = { x: width / 2, y: height / 2 };

                const k = 0.02; // Lower spring constant
                const repulsion = 3000; // Lower repulsion
                const damping = 0.8; // More aggressive damping
                const maxForce = 10; // Cap force
                const maxVelocity = 5; // Cap velocity
                const minDistance = 20; // Minimum distance for repulsion logic

                items.forEach(nodeId => {
                    // Skip simulation for the node currently being dragged by user or pinned
                    if (nodeId === draggedNodeId || pinnedNodes.has(nodeId)) {
                        // Keep velocity at zero while pinned/dragged
                        if (next[nodeId]) {
                            next[nodeId].vx = 0;
                            next[nodeId].vy = 0;
                        }
                        return;
                    }

                    const p = next[nodeId];
                    if (!p) return;

                    let fx = 0;
                    let fy = 0;

                    // Repulsion
                    items.forEach(otherId => {
                        if (nodeId === otherId) return;
                        const p2 = prev[otherId];
                        if (!p2) return;
                        const dx = p.x - p2.x;
                        const dy = p.y - p2.y;
                        const distSq = Math.max(minDistance * minDistance, dx * dx + dy * dy);
                        const dist = Math.sqrt(distSq);

                        const f = repulsion / distSq;
                        fx += (dx / dist) * f;
                        fy += (dy / dist) * f;
                    });

                    // Attraction
                    edges.forEach(([source, target]) => {
                        if (source === nodeId) {
                            const p2 = prev[target];
                            if (p2) { fx += k * (p2.x - p.x); fy += k * (p2.y - p.y); }
                        } else if (target === nodeId) {
                            const p2 = prev[source];
                            if (p2) { fx += k * (p2.x - p.x); fy += k * (p2.y - p.y); }
                        }
                    });

                    // Center Gravity
                    fx += (center.x - p.x) * 0.01;
                    fy += (center.y - p.y) * 0.01;

                    // Cap total force to keep things calm
                    const totalForce = Math.sqrt(fx * fx + fy * fy);
                    if (totalForce > maxForce) {
                        fx = (fx / totalForce) * maxForce;
                        fy = (fy / totalForce) * maxForce;
                    }

                    // Update Velocity
                    p.vx = (p.vx + fx) * damping;
                    p.vy = (p.vy + fy) * damping;

                    // Cap Velocity
                    const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
                    if (speed > maxVelocity) {
                        p.vx = (p.vx / speed) * maxVelocity;
                        p.vy = (p.vy / speed) * maxVelocity;
                    }

                    // Update Position
                    p.x += p.vx;
                    p.y += p.vy;

                    next[nodeId] = p;
                });

                return next;
            });

            animationFrameId = requestAnimationFrame(runSimulation);
        };

        runSimulation();
        return () => cancelAnimationFrame(animationFrameId);
    }, [agents, graph, positions.length, draggedNodeId]);

    const handleWheel = (e: React.WheelEvent) => {
        setTransform(prev => {
            const zoomSensitivity = 0.001;
            const newScale = Math.min(Math.max(0.1, prev.scale - e.deltaY * zoomSensitivity), 5);
            return { ...prev, scale: newScale };
        });
    };

    const handleMouseDown = (e: React.MouseEvent) => {
        // If clicking on the background (not a node or button), start canvas panning
        const target = e.target as HTMLElement;
        const isNode = target.closest('[data-node-id]');
        const isButton = target.closest('button');

        if (!isNode && !isButton) {
            setIsDraggingCanvas(true);
            lastMousePos.current = { x: e.clientX, y: e.clientY };
        }
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        if (isDraggingCanvas) {
            const dx = e.clientX - lastMousePos.current.x;
            const dy = e.clientY - lastMousePos.current.y;
            lastMousePos.current = { x: e.clientX, y: e.clientY };
            setTransform(prev => ({ ...prev, x: prev.x + dx, y: prev.y + dy }));
        } else if (draggedNodeId) {
            // Reposition node relative to transform
            const dx = (e.clientX - lastMousePos.current.x) / transform.scale;
            const dy = (e.clientY - lastMousePos.current.y) / transform.scale;

            if (Math.abs(dx) > 1 || Math.abs(dy) > 1) {
                wasDragged.current = true;
                if (!pinnedNodes.has(draggedNodeId)) {
                    setPinnedNodes(prev => new Set(prev).add(draggedNodeId));
                }
            }

            lastMousePos.current = { x: e.clientX, y: e.clientY };

            setPositions(prev => {
                const p = prev[draggedNodeId];
                if (!p) return prev;
                return {
                    ...prev,
                    [draggedNodeId]: { ...p, x: p.x + dx, y: p.y + dy, vx: 0, vy: 0 }
                };
            });
        }
    };

    const handleMouseUp = () => {
        setIsDraggingCanvas(false);
        setDraggedNodeId(null);
        // Reset wasDragged after a timeout so onClick can read it if it fires immediately
        setTimeout(() => { wasDragged.current = false; }, 50);
    };

    return (
        <div
            ref={containerRef}
            className={clsx("relative w-full h-full overflow-hidden bg-neo-bg cursor-grab active:cursor-grabbing", className)}
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
        >

            <div
                className="absolute inset-0 origin-center transition-transform duration-75 will-change-transform"
                style={{ transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})` }}
            >
                {/* SVG for Edges */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none overflow-visible">
                    <defs>
                        <marker id="arrow" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#4b5563" />
                        </marker>
                        <marker id="arrow-active" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
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
                                    strokeWidth={isRelated ? 2 / transform.scale : 1 / transform.scale}
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
                            data-node-id={agent.name}
                            onMouseDown={(e) => {
                                e.stopPropagation();
                                setDraggedNodeId(agent.name);
                                wasDragged.current = false;
                                lastMousePos.current = { x: e.clientX, y: e.clientY };
                            }}
                            onClick={(e) => {
                                e.stopPropagation();
                                if (!wasDragged.current) {
                                    onSelectAgent(agent.name);
                                }
                            }}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" || e.key === " ") {
                                    e.preventDefault();
                                    onSelectAgent(agent.name);
                                }
                            }}
                            role="button"
                            tabIndex={0}
                            aria-pressed={isSel}
                            aria-label={`Select agent ${agent.name}`}
                            title={agent.name}
                            className={clsx(
                                "absolute transform -translate-x-1/2 -translate-y-1/2 w-16 h-16 rounded-full flex items-center justify-center cursor-pointer transition-colors border-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-cyan shadow-lg",
                                isSel
                                    ? "bg-brand-cyan/20 border-brand-cyan text-brand-cyan shadow-[0_0_15px_rgba(6,182,212,0.4)]"
                                    : pinnedNodes.has(agent.name)
                                        ? "bg-neo-surface border-brand-cyan/40 text-gray-300 shadow-[0_0_10px_rgba(6,182,212,0.1)]"
                                        : "bg-neo-surface border-neo-border text-gray-400 hover:border-gray-500 hover:bg-neo-panel"
                            )}
                            style={{
                                left: pos.x,
                                top: pos.y,
                                zIndex: isSel ? 10 : 1,
                            }}
                        >
                            <div className="text-[10px] text-center font-mono leading-tight px-1 overflow-hidden pointer-events-none select-none">
                                {agent.name.length > 10 ? agent.name.substring(0, 10) + ".." : agent.name}
                            </div>
                            {pinnedNodes.has(agent.name) && !isSel && (
                                <div className="absolute -top-1 -right-1 w-3 h-3 bg-brand-cyan rounded-full border border-black" title="Pinned" />
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Zoom Controls Overlay */}
            <div className="absolute bottom-4 left-4 flex gap-2">
                <button
                    onClick={() => setTransform(p => ({ ...p, scale: p.scale / 1.2 }))}
                    className="p-2 bg-black/50 border border-white/10 rounded text-white/50 hover:text-white"
                    title="Zoom Out"
                >
                    -
                </button>
                <button
                    onClick={() => setTransform(p => ({ ...p, scale: p.scale * 1.2 }))}
                    className="p-2 bg-black/50 border border-white/10 rounded text-white/50 hover:text-white"
                    title="Zoom In"
                >
                    +
                </button>
                <button
                    onClick={() => setTransform({ x: 0, y: 0, scale: 1 })}
                    className="p-2 bg-black/50 border border-white/10 rounded text-white/50 hover:text-white text-xs font-mono"
                    title="Reset View"
                >
                    RESET
                </button>
            </div>
        </div>
    );
}
