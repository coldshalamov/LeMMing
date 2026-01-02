"use client";

import { motion } from "framer-motion";
import clsx from "clsx";

interface OrgTimerProps {
  n: number; // run every N ticks
  offset: number; // phase offset
  currentTick: number; // global tick
  size?: number;
  className?: string;
}

export function OrgTimer({
  n,
  offset,
  currentTick,
  size = 64,
  className,
}: OrgTimerProps) {
  // Normalize N
  const cycle = n > 0 ? n : 1;
  const normalizedOffset = offset % cycle;

  // Current position in the cycle (0 to cycle-1)
  const tickInCycle = currentTick % cycle;

  // Angle for the agent's firing point
  // The wheel represents 0 to N-1.
  // We'll put 0 at the top (-90deg).
  // Angle = (offset / cycle) * 360
  const targetAngle = (normalizedOffset / cycle) * 360;

  // Angle for the current global time (discrete steps)
  // We can animate this smoothly if we want, but discrete is more "accurate" to the logic.
  // Let's smoothe it slightly with framer-motion layout
  const currentAngle = (tickInCycle / cycle) * 360;

  const radius = size / 2 - 4; // padding
  const circumference = 2 * Math.PI * radius;

  // Accessibility label
  const a11yLabel = `Schedule timer: Runs every ${cycle} ticks, offset ${normalizedOffset}. Current cycle position: ${tickInCycle} of ${cycle}.`;

  return (
    <div
      className={clsx("relative flex items-center justify-center", className)}
      style={{ width: size, height: size }}
      role="img"
      aria-label={a11yLabel}
    >
      {/* Background Track */}
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
        aria-hidden="true"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth="2"
          fill="transparent"
          className="text-white/10"
        />

        {/* The Current Time Arc (Red/Accented) */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth="2"
          fill="transparent"
          className="text-brand-cyan"
          strokeDasharray={circumference}
          strokeDashoffset={
            circumference - (currentAngle / 360) * circumference
          }
          initial={{ strokeDashoffset: circumference }}
          animate={{
            strokeDashoffset:
              circumference - (currentAngle / 360) * circumference,
          }}
          transition={{ type: "spring", stiffness: 50, damping: 15 }}
          style={{ strokeLinecap: "round" }}
        />
      </svg>

      {/* The Firing Dot (Target) */}
      <div
        className="absolute w-2 h-2 bg-white rounded-full shadow-[0_0_8px_rgba(255,255,255,0.8)] z-10"
        style={{
          top: size / 2 - 4, // center - half height
          left: size / 2 - 4, // center - half width
          transform: `rotate(${targetAngle - 90}deg) translate(${radius}px) rotate(${90 - targetAngle}deg)`, // Move to rim (start at top)
        }}
        aria-hidden="true"
      />

      <div
        className={clsx(
          "absolute w-2.5 h-2.5 rounded-full border border-black z-20 transition-all duration-300",
          Math.abs(currentAngle - targetAngle) < 1
            ? "bg-brand-lime shadow-[0_0_10px_#84cc16] scale-125"
            : "bg-white/50",
        )}
        style={{
          left: size / 2 + radius * Math.sin((targetAngle * Math.PI) / 180) - 5,
          top: size / 2 - radius * Math.cos((targetAngle * Math.PI) / 180) - 5,
        }}
        aria-hidden="true"
      />

      {/* Tick Number Center Text */}
      <div
        className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
        aria-hidden="true"
      >
        <span className="text-[10px] text-white/40 font-mono tracking-tighter">
          T-{cycle}
        </span>
      </div>
    </div>
  );
}
