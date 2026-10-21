"use client";

import { useState, useEffect } from "react";
import {
  useAgents,
  useOrgGraph,
  useStatus,
  useMessages,
  useWebSocketStream,
  triggerTick,
} from "@/lib/api";
import { AgentCard } from "@/components/AgentCard";
import { OrgGraphView } from "@/components/OrgGraph";
import { ManagerChat } from "@/components/ManagerChat";
import { GlobalSettingsModal } from "@/components/GlobalSettingsModal";
import {
  Activity,
  Clock,
  Server,
  Terminal,
  Plus,
  Wifi,
  WifiOff,
  Play,
  Settings,
  Loader2,
} from "lucide-react";
import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

export default function Dashboard() {
  const { agents, isLoading: agentsLoading } = useAgents();
  const { graph } = useOrgGraph();
  const { status } = useStatus();
  const { messages } = useMessages();
  const { isConnected } = useWebSocketStream();

  const [selectedAgentName, setSelectedAgentName] = useState<string | null>(null);
  const [visualTick, setVisualTick] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [isTicking, setIsTicking] = useState(false);

  // Sync visual tick with backend status
  useEffect(() => {
    if (status?.tick && visualTick !== status.tick) {
      setVisualTick(status.tick);
    }
  }, [status?.tick, visualTick]);

  const selectedAgent = agents?.find((a) => a.name === selectedAgentName);

  const handleRunTick = async () => {
    if (isTicking) return;
    setIsTicking(true);
    try {
      await triggerTick();
      // Tick results will come in via WebSocket/SWR status updates
    } catch (err) {
      console.error("Failed to trigger tick:", err);
    } finally {
      setIsTicking(false);
    }
  };

  if (agentsLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-neo-bg text-brand-cyan font-mono animate-pulse">
        INITIALIZING NEURAL LINK...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-neo-bg text-foreground font-sans overflow-hidden relative">
      {/* 1) Graph Background */}
      <div className="absolute inset-0 z-0">
        {agents && graph && (
          <OrgGraphView
            agents={agents}
            graph={graph}
            selectedAgent={selectedAgentName}
            onSelectAgent={setSelectedAgentName}
            currentTick={visualTick}
          />
        )}
      </div>

      {/* 2) Top Header Bar (layer 1) */}
      <div className="absolute top-0 inset-x-0 z-10 pointer-events-none flex flex-col justify-between h-full">
        <header className="px-6 py-4 flex items-center justify-between pointer-events-none">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-white tracking-widest pointer-events-auto">
              LeMMing <span className="text-white/30">OVERMIND</span>
            </h1>
          </div>

          <div className="flex items-center gap-6">
            {/* Global Stats */}
            <div className="flex items-center gap-6 bg-black/40 px-4 py-2 rounded-lg border border-white/5 pointer-events-auto backdrop-blur-md">
              <div className="flex items-center gap-2" title="Current global tick" aria-label="Current global tick">
                <Clock size={14} className="text-brand-cyan" aria-hidden="true" />
                <span className="text-xs text-brand-cyan font-mono">TICK: {visualTick}</span>
              </div>
              <div className="w-px h-4 bg-white/10" />
              <div className="flex items-center gap-2" title="Active agents" aria-label="Active agents">
                <Server size={14} className="text-brand-purple" aria-hidden="true" />
                <span className="text-xs text-brand-purple font-mono">AGENTS: {agents?.length || 0}</span>
              </div>
              <div className="w-px h-4 bg-white/10" />
              <div className="flex items-center gap-2" title="Total credits used" aria-label="Total credits used">
                <Activity size={14} className="text-brand-lime" aria-hidden="true" />
                <span className="text-xs text-brand-lime font-mono">CREDITS: 0</span>
              </div>
              <div className="w-px h-4 bg-white/10" />
              <div className="flex items-center gap-2" title={isConnected ? "WebSocket connected" : "WebSocket disconnected"} aria-label={isConnected ? "WebSocket connected" : "WebSocket disconnected"}>
                {isConnected ? (
                  <Wifi size={14} className="text-brand-lime" aria-hidden="true" />
                ) : (
                  <WifiOff size={14} className="text-red-500 animate-pulse" aria-hidden="true" />
                )}
                <span className={clsx("text-xs font-mono", isConnected ? "text-brand-lime" : "text-red-500")}>
                  {isConnected ? "ONLINE" : "OFFLINE"}
                </span>
              </div>
            </div>

            {/* Buttons */}
            <div className="pointer-events-auto flex items-center gap-3">
              <button
                onClick={() => setShowSettings(true)}
                className="p-2 bg-black/40 hover:bg-white/5 text-gray-400 hover:text-white rounded-lg border border-white/5 transition-all"
                title="Global Settings"
                aria-label="Global Settings"
              >
                <Settings size={20} />
              </button>

              <Link
                href="/wizard"
                className="flex items-center gap-2 px-4 py-2 bg-brand-cyan text-black font-bold rounded shadow-[0_0_15px_rgba(6,182,212,0.3)] hover:bg-cyan-300 transition-colors"
              >
                <Plus size={16} aria-hidden="true" /> NEW UNIT
              </Link>
            </div>
          </div>
        </header>

        {/* Bottom: (reserved space, actual control bar is layer 4 below) */}
        <div className="h-20" />
      </div>

      {/* 3) Left / Right Panels (layer 2) */}
      <div className="absolute inset-0 z-20 pointer-events-none flex p-6 pt-24 pb-24 h-full">
        {/* Left Side: Agent Detail */}
        <div className="w-96 flex flex-col h-full gap-4">
          <AnimatePresence mode="popLayout">
            {selectedAgent ? (
              <motion.div
                key="agent-detail"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="bg-black/60 backdrop-blur-xl border border-white/10 rounded-xl flex flex-col pointer-events-auto shadow-2xl flex-1 min-h-0"
              >
                <div className="p-4 border-b border-white/5 flex items-center justify-between shrink-0">
                  <div className="flex items-center gap-3">
                    <Terminal className="text-brand-cyan" size={20} />
                    <div>
                      <h2 className="text-lg font-bold text-white tracking-wide">
                        {selectedAgent.name}
                      </h2>
                      <p className="text-xs text-brand-cyan font-mono uppercase">
                        {selectedAgent.title}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedAgentName(null)}
                    className="text-white/20 hover:text-white transition-colors"
                    title="Close"
                    aria-label="Close agent details"
                  >
                    <Plus size={20} className="rotate-45" />
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  <AgentCard
                    agent={selectedAgent}
                    currentTick={visualTick}
                    isSelected={true}
                    variant="full"
                  />

                  {/* Mini Logs */}
                  <div className="rounded border border-white/5 bg-black/20 p-3">
                    <h4 className="text-[10px] font-mono text-white/40 uppercase mb-2">
                      Recent Activity
                    </h4>
                    <div className="space-y-2">
                      {messages
                        ?.filter(
                          (m) =>
                            m.sender === selectedAgent.name ||
                            m.recipient === selectedAgent.name
                        )
                        .slice(0, 5)
                        .map((m, i) => (
                          <div key={i} className="text-xs font-mono flex gap-2">
                            <span className="text-white/30 shrink-0">T{m.tick}</span>
                            <span className="text-white/50 truncate">
                              {m.sender === selectedAgent.name ? "→" : "←"} {m.recipient === selectedAgent.name ? m.sender : m.recipient}
                            </span>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>

        {/* Right Side: Global Log / Manager Chat */}
        <div className="flex-1 flex justify-end">
          <div className="w-[450px] pointer-events-auto h-full min-h-0 pb-6">
            <ManagerChat />
          </div>
        </div>
      </div>

      {/* 4) Bottom Control Bar (layer 3) */}
      <div className="absolute bottom-6 inset-x-0 z-30 pointer-events-none flex justify-center">
        <div className="bg-black/80 backdrop-blur-xl border border-white/10 rounded-full py-2 px-6 flex items-center gap-6 pointer-events-auto shadow-2xl">
          <div className="flex flex-col items-center">
            <span className="text-[10px] font-mono text-white/40 uppercase tracking-widest">
              System Status
            </span>
            <span className="text-sm font-bold text-white">
              {isTicking ? "EXECUTING_TICK..." : "READY_TO_EXECUTE"}
            </span>
          </div>

          <div className="h-8 w-px bg-white/10 mx-2" />

          <button
            onClick={(e) => {
              if (isTicking) {
                e.preventDefault();
                return;
              }
              handleRunTick();
            }}
            aria-disabled={isTicking}
            className={clsx(
              "w-12 h-12 rounded-full flex items-center justify-center transition-transform shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-lime",
              isTicking
                ? "bg-gray-600 text-gray-400 cursor-wait opacity-50"
                : "bg-brand-lime text-black shadow-[0_0_20px_rgba(132,204,22,0.4)] hover:scale-105 active:scale-95",
            )}
            title={isTicking ? "Executing tick, please wait..." : "Run one tick"}
            aria-label="Run one tick"
          >
            {isTicking ? (
              <Loader2 size={24} className="animate-spin" />
            ) : (
              <Play fill="currentColor" className="ml-1" size={24} />
            )}
          </button>
        </div>
      </div>

      {/* Modals */}
      {showSettings && (
        <GlobalSettingsModal onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}
