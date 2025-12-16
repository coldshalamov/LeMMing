
"use client";

import { useState, useEffect } from "react";
import { useAgents, useOrgGraph, useStatus, useMessages, useWebSocketStream } from "@/lib/api";
import { AgentCard } from "@/components/AgentCard";
import { OrgGraphView } from "@/components/OrgGraph";
import { Activity, Clock, Server, Terminal, Plus, Wifi, WifiOff } from "lucide-react";
import clsx from "clsx";
import { motion } from "framer-motion";
import Link from "next/link";

export default function Dashboard() {
  const { agents, isLoading: agentsLoading } = useAgents();
  const { graph } = useOrgGraph();
  const { status } = useStatus();
  const { messages } = useMessages();
  const { isConnected } = useWebSocketStream();

  const [selectedAgentName, setSelectedAgentName] = useState<string | null>(null);

  const selectedAgent = agents?.find(a => a.name === selectedAgentName);

  if (agentsLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-neo-bg text-brand-cyan font-mono animate-pulse">
        INITIALIZING NEURAL LINK...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-neo-bg text-foreground font-sans overflow-hidden">
      {/* Top Bar / Header */}
      <header className="h-14 border-b border-neo-border bg-neo-panel flex items-center justify-between px-4 shrink-0 z-20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-brand-cyan to-brand-purple flex items-center justify-center shadow-lg shadow-brand-cyan/20">
            <Terminal className="text-white w-5 h-5" />
          </div>
          <h1 className="font-bold text-xl tracking-tight text-white">LeMMing <span className="text-white/30 font-light">OVERMIND</span></h1>
        </div>

        {/* Global Stats */}
        <div className="flex items-center gap-6 text-xs font-mono text-gray-400">
          <div className="flex items-center gap-2">
            <Clock size={14} className="text-brand-cyan" />
            <span className="text-white">TICK: {status?.tick || 1}</span>
          </div>
          <div className="flex items-center gap-2">
            <Server size={14} className="text-brand-purple" />
            <span>AGENTS: {status?.total_agents || 0}</span>
          </div>
          <div className="flex items-center gap-2">
            <Activity size={14} className="text-brand-lime" />
            <span>CREDITS: {status?.total_credits !== undefined ? status.total_credits.toFixed(0) : 0}</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <div
            className={clsx(
              "flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono border",
              isConnected
                ? "border-brand-cyan text-brand-cyan bg-brand-cyan/10"
                : "border-red-500 text-red-400 bg-red-500/10"
            )}
            title={isConnected ? "Connected to backend" : "Disconnected from backend"}
          >
            {isConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
            {isConnected ? "LIVE" : "DISCONNECTED"}
          </div>
          <Link href="/wizard">
            <button className="flex items-center gap-2 px-3 py-1.5 bg-brand-cyan/10 border border-brand-cyan/50 text-brand-cyan rounded text-xs font-mono hover:bg-brand-cyan/20 transition-colors mr-2">
              <Plus size={14} /> DEPLOY_UNIT
            </button>
          </Link>
        </div>
      </header>

      {/* Main Layout */}
      <main className="flex-1 flex overflow-hidden">

        {/* LEFT COLUMN: Graph & List */}
        <div className="w-1/3 min-w-[400px] border-r border-neo-border flex flex-col bg-neo-bg/50 backdrop-blur-sm z-10">

          {/* Graph View */}
          <div className="flex-1 relative border-b border-neo-border">
            <div className="absolute top-2 left-2 z-10 text-xs font-mono text-white/50 bg-black/50 px-2 py-1 rounded">ORG TOPOLOGY</div>
            {agents && graph && (
              <OrgGraphView
                agents={agents}
                graph={graph}
                selectedAgent={selectedAgentName}
                onSelectAgent={setSelectedAgentName}
              />
            )}
          </div>

          {/* Agent List / Mini Grid */}
          <div className="h-1/3 overflow-y-auto p-4 bg-neo-panel">
            <div className="text-xs font-mono text-white/50 mb-3 sticky top-0 bg-neo-panel py-1 z-10 w-full flex justify-between">
              <span>AGENTS_REGISTRY</span>
              <span>{agents?.length || 0} UNITS</span>
            </div>
            <div className="grid grid-cols-1 gap-2">
              {agents?.map(agent => (
                <div key={agent.name} onClick={() => setSelectedAgentName(agent.name)}>
                  <AgentCard
                    agent={agent}
                    currentTick={status?.tick || 1}
                    isSelected={agent.name === selectedAgentName}
                    variant="compact"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Active Focus or Feed */}
        <div className="flex-1 bg-neo-surface relative flex flex-col">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-brand-purple/5 via-transparent to-transparent pointer-events-none" />

          {selectedAgent ? (
            <div className="flex-1 p-8 overflow-y-auto">
              <div className="max-w-4xl mx-auto space-y-6">
                {/* BIG CARD */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  key={selectedAgent.name}
                >
                  <AgentCard
                    agent={selectedAgent}
                    currentTick={status?.tick || 1}
                    isSelected={true}
                    variant="full"
                  />
                </motion.div>

                {/* Context / Logs */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-xl border border-neo-border bg-neo-panel/50 p-4 h-64 overflow-hidden flex flex-col">
                    <h3 className="text-xs font-mono text-brand-cyan mb-2">INCOMING_SIGNALS</h3>
                    <div className="flex-1 overflow-y-auto text-xs font-mono text-gray-400 space-y-2">
                      {/* Fake incoming messages based on graph */}
                      {messages?.filter(m => m.kind !== "status").slice(0, 5).map((m, i) => (
                        <div key={i} className="p-2 bg-white/5 rounded border border-white/5">
                          <span className="text-brand-purple">@{m.agent}</span>: {m.payload.text?.substring(0, 50)}...
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-xl border border-neo-border bg-neo-panel/50 p-4 h-64 overflow-hidden flex flex-col">
                    <h3 className="text-xs font-mono text-brand-lime mb-2">MEMORY_DUMP</h3>
                    <div className="flex-1 overflow-y-auto text-xs font-mono text-gray-500">
                      <pre>{JSON.stringify({ last_run: "success", memory_slots: 4, context_window: "128k" }, null, 2)}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center flex-col text-white/20">
              <Activity size={64} className="mb-4 opacity-20" />
              <p className="font-mono text-sm">SELECT AN AGENT NODE TO INSPECT</p>
            </div>
          )}

          {/* Bottom Feed (Global Log) */}
          <div className="h-48 border-t border-neo-border bg-neo-panel p-4 flex flex-col shrink-0">
            <h3 className="text-[10px] font-mono text-white/30 mb-2 uppercase tracking-wider">System_Log</h3>
            <div className="flex-1 overflow-y-auto font-mono text-xs space-y-1">
              {messages?.map((msg) => (
                <div key={msg.id} className="flex gap-2 opacity-70 hover:opacity-100 transition-opacity">
                  <span className="text-white/30 w-16">T-{msg.tick}</span>
                  <span className={clsx("w-24 text-right", getColorForAgent(msg.agent))}>{msg.agent}</span>
                  <span className="text-white/20">::</span>
                  <span className={clsx(msg.kind === "report" ? "text-yellow-500" : msg.kind === "status" ? "text-gray-500" : "text-white")}>
                    {JSON.stringify(msg.payload)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}

function getColorForAgent(name: string) {
  if (name === "overmind") return "text-red-400";
  if (name.includes("frontend")) return "text-brand-cyan";
  if (name.includes("backend")) return "text-brand-purple";
  return "text-brand-lime";
}
