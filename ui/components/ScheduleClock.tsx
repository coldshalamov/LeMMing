// Interactive Clock Component for Agent Scheduling
"use client";

import { useState } from "react";
import clsx from "clsx";

interface ScheduleClockProps {
    frequency: number; // e.g., 1, 0.5 (1/2), 0.333 (1/3), 0.25 (1/4)
    offset: number; // 0-11 (clock positions)
    onChange: (offset: number) => void;
}

export function ScheduleClock({ frequency, offset, onChange }: ScheduleClockProps) {
    const [hoveredPosition, setHoveredPosition] = useState<number | null>(null);

    // Calculate activation points based on frequency
    const getActivationPoints = (): number[] => {
        const points: number[] = [];
        const interval = frequency * 12; // Convert to clock positions

        let currentPos = offset;
        points.push(currentPos);

        // Add subsequent activation points
        while (points.length < 12) {
            currentPos = (currentPos + interval) % 12;
            if (Math.abs(currentPos - points[0]) < 0.1) break; // Full cycle
            points.push(Math.round(currentPos));
        }

        return [...new Set(points)]; // Remove duplicates
    };

    const activationPoints = getActivationPoints();

    // Generate 12 clock positions
    const positions = Array.from({ length: 12 }, (_, i) => {
        const angle = (i * 30 - 90) * (Math.PI / 180); // Start at 12 o'clock
        const radius = 80;
        return {
            x: 100 + radius * Math.cos(angle),
            y: 100 + radius * Math.sin(angle),
            index: i,
        };
    });

    return (
        <div className="flex flex-col items-center gap-4">
            <div
                role="radiogroup"
                aria-label="Select start phase offset"
                className="relative"
            >
                <svg width="200" height="200" viewBox="0 0 200 200">
                    {/* Clock circle */}
                    <circle
                        cx="100"
                        cy="100"
                        r="90"
                        fill="none"
                        stroke="rgba(255,255,255,0.1)"
                        strokeWidth="2"
                    />

                    {/* Hour markers */}
                    {positions.map((pos) => {
                        const isActivation = activationPoints.includes(pos.index);
                        const isFirst = pos.index === offset;
                        const isHovered = hoveredPosition === pos.index;

                        return (
                            <g
                                key={pos.index}
                                role="button"
                                tabIndex={0}
                                aria-label={`Set start offset to position ${pos.index === 0 ? 12 : pos.index}`}
                                aria-pressed={isFirst}
                                onClick={() => onChange(pos.index)}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter" || e.key === " ") {
                                        e.preventDefault();
                                        onChange(pos.index);
                                    }
                                }}
                                onMouseEnter={() => setHoveredPosition(pos.index)}
                                className="cursor-pointer focus:outline-none group"
                            >
                                {/* Clickable area */}
                                <circle
                                    cx={pos.x}
                                    cy={pos.y}
                                    r="15"
                                    fill="transparent"
                                />

                                {/* Visual marker */}
                                <circle
                                    cx={pos.x}
                                    cy={pos.y}
                                    r={isFirst ? 8 : isActivation ? 6 : 3}
                                    fill={
                                        isFirst
                                            ? "#ef4444" // Red for first activation
                                            : isActivation
                                                ? "#9ca3af" // Grey for subsequent
                                                : "rgba(255,255,255,0.2)" // Dim for inactive
                                    }
                                    className={clsx(
                                        "transition-all",
                                        isHovered && "opacity-80 scale-110"
                                    )}
                                    style={{
                                        filter: isFirst ? "drop-shadow(0 0 8px #ef4444)" : "none",
                                    }}
                                />

                                {/* Focus Ring Indicator (Visible only on keyboard focus) */}
                                <circle
                                    cx={pos.x}
                                    cy={pos.y}
                                    r="18"
                                    fill="none"
                                    stroke="#22d3ee"
                                    strokeWidth="2"
                                    className="opacity-0 transition-opacity group-focus:opacity-100"
                                />

                                {/* Position label */}
                                <text
                                    x={pos.x}
                                    y={pos.y + 25}
                                    textAnchor="middle"
                                    className="text-[10px] font-mono fill-white/30 pointer-events-none"
                                >
                                    {pos.index === 0 ? "12" : pos.index}
                                </text>
                            </g>
                        );
                    })}

                    {/* Center dot */}
                    <circle cx="100" cy="100" r="3" fill="rgba(255,255,255,0.3)" />
                </svg>
            </div>

            <div className="text-xs font-mono text-gray-400 text-center">
                <div>
                    <span className="text-red-400">●</span> First activation at position {offset === 0 ? 12 : offset}
                </div>
                {activationPoints.length > 1 && (
                    <div className="mt-1">
                        <span className="text-gray-400">●</span> {activationPoints.length - 1} more activation{activationPoints.length > 2 ? "s" : ""} per cycle
                    </div>
                )}
            </div>
        </div>
    );
}
