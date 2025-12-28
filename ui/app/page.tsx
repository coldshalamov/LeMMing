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
            className="w-full h-full border-none rounded-none bg-neo-bg"
          />
        )}
      </div>

      {/* 2) Overlay HUD */}
      <div className="absolute inset-0 pointer-events-none z-10 flex flex-col justify-between">
        {/* Header Bar */}
        <header className="flex items-center justify-between px-6 pt-4">
          <div className="flex items-center gap-3 pointer-events-auto bg-black/40 backdrop-blur-md p-2 rounded-lg border border-white/5">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-brand-cyan to-brand-purple flex items-center justify-center shadow-lg shadow-brand-cyan/20">
              <Terminal className="text-white w-5 h-5" />
            </div>
            <h1 className="font-bold text-xl tracking-tight text-white">
              LeMMing <span className="text-white/30 font-light">OVERMIND</span>
            </h1>
          </div>

          <div className="flex items-center gap-3">
            {/* Stats Widget */}
            <div className="pointer-events-auto bg-black/40 backdrop-blur-md px-4 py-2 rounded-lg border border-white/5 flex items-center gap-6 text-xs font-mono text-gray-400">
              <div className="flex items-center gap-2">
                <Clock size={14} className="text-brand-cyan" />
                <span className="text-white">TICK: {visualTick}</span>
              </div>
              <div className="flex items-center gap-2">
                <Server size={14} className="text-brand-purple" />
                <span>AGENTS: {status?.total_agents || 0}</span>
              </div>
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-brand-lime" />
                <span>
                  CREDITS:{" "}
                  {status?.total_credits !== undefined
                    ? status.total_credits.toFixed(0)
                    : 0}
                </span>
              </div>
              <div className="w-px h-4 bg-white/10" />
              <div
                className={clsx(
                  "flex items-center gap-2",
                  isConnected ? "text-brand-cyan" : "text-red-400",
                )}
                title={
                  isConnected
                    ? "Connected to backend"
                    : "Disconnected from backend"
                }
              >
                {isConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
                {isConnected ? "ONLINE" : "OFFLINE"}
              </div>
            </div>

            {/* Buttons */}
            <div className="pointer-events-auto flex items-center gap-3">
              <button
                onClick={() => setShowSettings(true)}
                className="p-2 bg-black/40 hover:bg-white/5 text-gray-400 hover:text-white rounded-lg border border-white/5 transition-all"
                title="Global Settings"
              >
                <Settings size={20} />
              </button>

              <Link href="/wizard">
                <button className="flex items-center gap-2 px-4 py-2 bg-brand-cyan text-black font-bold rounded shadow-[0_0_15px_rgba(6,182,212,0.3)] hover:bg-cyan-300 transition-colors">
                  <Plus size={16} /> NEW UNIT
                </button>
              </Link>
            </div>
          </div>
        </header>

        {/* Bottom: (reserved space, actual control bar is layer 4 below) */}
        <div className="h-20" />
      </div>

      {/* 3) Manager Sidebar (Left) */}
      <div className="absolute top-24 left-6 bottom-24 w-[400px] z-20 pointer-events-auto">
        {messages && <ManagerChat messages={messages} />}
      </div>

      {/* 4) Agent Overlay (Top Right) */}
      <div className="absolute top-20 right-6 bottom-24 w-[450px] pointer-events-none z-20 flex flex-col justify-start">
        <AnimatePresence>
          {selectedAgent ? (
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 50 }}
              className="pointer-events-auto bg-neo-panel/90 backdrop-blur-xl border border-neo-border rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-full"
            >
              {/* Compact Header */}
              <div className="p-4 border-b border-white/5 flex justify-between items-start bg-black/20">
                <div>
                  <h2 className="text-lg font-bold text-white">
                    {selectedAgent.name}
                  </h2>
                  <p className="text-xs text-brand-cyan font-mono uppercase">
                    {selectedAgent.title}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedAgentName(null)}
                  className="text-white/20 hover:text-white transition-colors"
                  title="Close"
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
                  <div className="text-xs font-mono text-gray-400 space-y-1">
                    {messages
                      ?.filter((m) => m.agent === selectedAgent.name)
                      .slice(0, 3)
                      .map((m, i) => (
                        <div
                          key={i}
                          className="opacity-70 truncate border-l-2 border-white/10 pl-2"
                        >
                          {m.payload.text || JSON.stringify(m.payload)}
                        </div>
                      )) || <div className="italic opacity-30">No recent activity</div>}
                  </div>
                </div>
              </div>
            </motion.div>
          ) : (
            <div className="flex-1 flex items-center justify-center flex-col text-white/20">
              {!agents || agents.length === 0 ? (
                <>
                  <Terminal size={64} className="mb-4 opacity-20" />
                  <p className="font-mono text-sm mb-4">
                    SYSTEM_OFFLINE: NO AGENTS DETECTED
                  </p>
                  <Link href="/wizard">
                    <button className="flex items-center gap-2 px-6 py-3 bg-brand-cyan text-black font-bold rounded hover:bg-cyan-300 transition-colors">
                      <Plus size={18} /> INITIALIZE_FIRST_AGENT
                    </button>
                  </Link>
                </>
              ) : (
                <>
                  <Activity size={64} className="mb-4 opacity-20" />
                  <p className="font-mono text-sm">
                    SELECT AN AGENT NODE TO INSPECT
                  </p>
                  <p className="font-mono text-xs mt-2 text-white/10">
                    Use{" "}
                    <span className="px-1.5 py-0.5 bg-white/10 rounded">TAB</span>{" "}
                    to navigate graph
                  </p>
                </>
              )}
            </div>
          )}
        </AnimatePresence>
      </div>

      {/* 5) Bottom Control Bar */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-30 pointer-events-auto">
        <div className="flex items-center gap-4 p-2 pl-6 pr-2 bg-black/60 backdrop-blur-xl border border-white/10 rounded-full shadow-2xl">
          <div className="flex flex-col">
            <span className="text-[10px] font-mono text-brand-lime uppercase tracking-widest">
              System Status
            </span>
            <span className="text-sm font-bold text-white">
              {isTicking ? "EXECUTING_TICK..." : "READY_TO_EXECUTE"}
            </span>
          </div>

          <div className="h-8 w-px bg-white/10 mx-2" />

          <button
            onClick={handleRunTick}
            disabled={isTicking}
            className={clsx(
              "w-12 h-12 rounded-full flex items-center justify-center hover:scale-105 active:scale-95 transition-transform shadow-lg disabled:opacity-50",
              isTicking
                ? "bg-gray-600 text-gray-400"
                : "bg-brand-lime text-black shadow-[0_0_20px_rgba(132,204,22,0.4)]",
            )}
            title="Run one tick"
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
