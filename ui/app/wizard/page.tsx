
"use client";

import { useState } from "react";
import { AgentCard } from "@/components/AgentCard";
import { AgentInfo } from "@/lib/types";
import { ArrowRight, ArrowLeft, Check, Terminal, Cpu, Clock, Shield, Save } from "lucide-react";
import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

const STEPS = [
    { id: "identity", label: "Identity", icon: Terminal },
    { id: "brain", label: "Brain", icon: Cpu },
    { id: "schedule", label: "Schedule", icon: Clock },
    { id: "permissions", label: "Permissions", icon: Shield },
    { id: "review", label: "Review", icon: Save },
];

const MODELS = ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"];
const TOOLS = ["read_file", "write_file", "browser_test", "run_shell", "scraper", "api_call"];

export default function WizardPage() {
    const [currentStep, setCurrentStep] = useState(0);

    const [formData, setFormData] = useState<AgentInfo>({
        name: "",
        title: "",
        description: "",
        model: "gpt-4-turbo",
        schedule: { run_every_n_ticks: 1, phase_offset: 0 },
        read_outboxes: [],
        tools: [],
        credits: { max_credits: 1000, cost_per_action: 0.1, credits_left: 1000 }
    });

    const stepIdx = currentStep;
    const StepIcon = STEPS[stepIdx].icon;

    const handleNext = () => setCurrentStep(prev => Math.min(prev + 1, STEPS.length - 1));
    const handleBack = () => setCurrentStep(prev => Math.max(prev - 1, 0));

    return (
        <div className="min-h-screen bg-neo-bg text-foreground font-sans flex flex-col">
            {/* Header */}
            <header className="h-16 border-b border-neo-border bg-neo-panel flex items-center justify-between px-8 shrink-0">
                <div className="flex items-center gap-3">
                    <Link href="/" className="hover:text-brand-cyan transition-colors">
                        <h1 className="font-bold text-xl tracking-tight">LeMMing <span className="text-white/30 font-light">WIZARD</span></h1>
                    </Link>
                </div>
                <div className="flex gap-2">
                    {STEPS.map((step, idx) => (
                        <div key={step.id} className={clsx("flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono transition-colors",
                            idx === stepIdx ? "bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/50" :
                                idx < stepIdx ? "text-brand-lime" : "text-white/20"
                        )}>
                            <step.icon size={12} />
                            {idx < stepIdx ? <Check size={12} /> : <span>{step.label}</span>}
                        </div>
                    ))}
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
                {/* Form Area */}
                <div className="flex-1 p-12 overflow-y-auto">
                    <div className="max-w-2xl mx-auto">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={currentStep}
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="space-y-8"
                            >
                                <div className="flex items-center gap-4 mb-8">
                                    <div className="w-12 h-12 rounded-xl bg-neo-surface border border-neo-border flex items-center justify-center text-brand-cyan">
                                        <StepIcon size={24} />
                                    </div>
                                    <div>
                                        <h2 className="text-2xl font-bold">{STEPS[stepIdx].label}</h2>
                                        <p className="text-white/50">Configure your agent&apos;s {STEPS[stepIdx].label.toLowerCase()}</p>
                                    </div>
                                </div>

                                {/* STEP 1: IDENTITY */}
                                {stepIdx === 0 && (
                                    <div className="space-y-4">
                                        <div>
                                            <label htmlFor="agent-slug" className="block text-xs font-mono text-gray-400 mb-1">AGENT_SLUG (Folder Name)</label>
                                            <input
                                                id="agent-slug"
                                                type="text"
                                                required
                                                value={formData.name}
                                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                                className="w-full bg-neo-surface border border-neo-border p-3 rounded text-white focus:border-brand-cyan focus:outline-none font-mono"
                                                placeholder="e.g. backend_dev"
                                            />
                                        </div>
                                        <div>
                                            <label htmlFor="agent-title" className="block text-xs font-mono text-gray-400 mb-1">TITLE</label>
                                            <input
                                                id="agent-title"
                                                type="text"
                                                required
                                                value={formData.title}
                                                onChange={e => setFormData({ ...formData, title: e.target.value })}
                                                className="w-full bg-neo-surface border border-neo-border p-3 rounded text-white focus:border-brand-cyan focus:outline-none"
                                                placeholder="Backend Engineer"
                                            />
                                        </div>
                                        <div>
                                            <div className="flex justify-between items-baseline mb-1">
                                                <label htmlFor="agent-desc" className="block text-xs font-mono text-gray-400">DESCRIPTION</label>
                                                <span className={clsx("text-[10px] font-mono", formData.description.length > 200 ? "text-orange-400" : "text-gray-600")}>
                                                    {formData.description.length} chars
                                                </span>
                                            </div>
                                            <textarea
                                                id="agent-desc"
                                                required
                                                value={formData.description}
                                                onChange={e => setFormData({ ...formData, description: e.target.value })}
                                                className="w-full bg-neo-surface border border-neo-border p-3 rounded text-white focus:border-brand-cyan focus:outline-none h-32"
                                                placeholder="What is this agent&apos;s purpose?"
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* STEP 2: BRAIN */}
                                {stepIdx === 1 && (
                                    <div className="space-y-4">
                                        <div>
                                            <label htmlFor="agent-model" className="block text-xs font-mono text-gray-400 mb-1">MODEL</label>
                                            <select
                                                id="agent-model"
                                                value={formData.model}
                                                onChange={e => setFormData({ ...formData, model: e.target.value })}
                                                className="w-full bg-neo-surface border border-neo-border p-3 rounded text-white focus:border-brand-cyan focus:outline-none"
                                            >
                                                {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
                                            </select>
                                        </div>
                                        <div className="p-4 rounded border border-neo-border bg-neo-surface/50">
                                            <h4 className="text-sm font-bold text-white mb-2">System Instructions Preamble</h4>
                                            <p className="text-xs text-gray-400">
                                                &quot;You are a LeMMing agent operating in a multi-agent organization...&quot;
                                            </p>
                                            <textarea
                                                className="w-full mt-2 bg-black/20 border border-white/10 p-2 text-xs font-mono text-gray-300 h-40"
                                                placeholder="Add custom instructions here (e.g. coding style, specific rules)..."
                                            // In real app this would update instructions field
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* STEP 3: SCHEDULE */}
                                {stepIdx === 2 && (
                                    <div className="space-y-6">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label htmlFor="agent-schedule" className="block text-xs font-mono text-gray-400 mb-1">RUN EVERY N TICKS</label>
                                                <input
                                                    id="agent-schedule"
                                                    type="number"
                                                    min={1}
                                                    value={formData.schedule.run_every_n_ticks}
                                                    onChange={e => setFormData({ ...formData, schedule: { ...formData.schedule, run_every_n_ticks: parseInt(e.target.value) } })}
                                                    className="w-full bg-neo-surface border border-neo-border p-3 rounded text-white focus:border-brand-cyan focus:outline-none"
                                                />
                                            </div>
                                            <div>
                                                <label htmlFor="agent-offset" className="block text-xs font-mono text-gray-400 mb-1">PHASE OFFSET</label>
                                                <input
                                                    id="agent-offset"
                                                    type="number"
                                                    min={0}
                                                    value={formData.schedule.phase_offset}
                                                    onChange={e => setFormData({ ...formData, schedule: { ...formData.schedule, phase_offset: parseInt(e.target.value) } })}
                                                    className="w-full bg-neo-surface border border-neo-border p-3 rounded text-white focus:border-brand-cyan focus:outline-none"
                                                />
                                            </div>
                                        </div>
                                        <div className="p-4 bg-neo-surface/30 rounded border border-neo-border flex items-center gap-4">
                                            <div className="flex-1 text-sm text-gray-300">
                                                This agent will run when <code className="text-brand-cyan">tick % {formData.schedule.run_every_n_ticks} == {formData.schedule.phase_offset % formData.schedule.run_every_n_ticks}</code>.
                                                <br />
                                                It has a {((1 / formData.schedule.run_every_n_ticks) * 100).toFixed(0)}% duty cycle.
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* STEP 4: PERMISSIONS */}
                                {stepIdx === 3 && (
                                    <div className="space-y-6">
                                        <div role="group" aria-labelledby="tools-label">
                                            <label id="tools-label" className="block text-xs font-mono text-gray-400 mb-2">TOOLS</label>
                                            <div className="flex flex-wrap gap-2">
                                                {TOOLS.map(tool => (
                                                    <button
                                                        type="button"
                                                        key={tool}
                                                        aria-pressed={formData.tools.includes(tool)}
                                                        onClick={() => {
                                                            const tools = formData.tools.includes(tool)
                                                                ? formData.tools.filter(t => t !== tool)
                                                                : [...formData.tools, tool];
                                                            setFormData({ ...formData, tools });
                                                        }}
                                                        className={clsx("flex items-center gap-1.5 px-3 py-1.5 rounded border text-xs font-mono transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-cyan",
                                                            formData.tools.includes(tool)
                                                                ? "bg-brand-cyan/20 border-brand-cyan text-brand-cyan"
                                                                : "bg-neo-surface border-neo-border text-gray-500 hover:border-gray-400"
                                                        )}
                                                    >
                                                        {formData.tools.includes(tool) && <Check size={12} />}
                                                        {tool}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                        <div>
                                            <label htmlFor="agent-read-access" className="block text-xs font-mono text-gray-400 mb-2">READ ACCESS (Outboxes)</label>
                                            <div className="p-4 border border-neo-border bg-neo-surface rounded flex items-center justify-center text-gray-500 text-sm italic">
                                                [Graph Selector Would Go Here]
                                            </div>
                                            <input
                                                id="agent-read-access"
                                                type="text"
                                                placeholder="Comma separated agent names (e.g. overmind, backend)"
                                                className="w-full mt-2 bg-neo-surface border border-neo-border p-3 rounded text-white focus:border-brand-cyan focus:outline-none font-mono text-xs"
                                                value={formData.read_outboxes.join(", ")}
                                                onChange={e => setFormData({ ...formData, read_outboxes: e.target.value.split(",").map(s => s.trim()) })}
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* STEP 5: REVIEW */}
                                {stepIdx === 4 && (
                                    <div className="space-y-6">
                                        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded text-green-400 text-sm">
                                            Ready to deploy agent to filesystem.
                                        </div>
                                        <div className="bg-black/40 p-4 rounded border border-white/5 font-mono text-xs text-gray-400 whitespace-pre-wrap">
                                            {JSON.stringify(formData, null, 2)}
                                        </div>
                                    </div>
                                )}


                                {/* Footer Controls */}
                                <div className="flex justify-between pt-8 border-t border-white/5">
                                    <button
                                        onClick={handleBack}
                                        disabled={stepIdx === 0}
                                        className="px-6 py-2 rounded border border-neo-border text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                    >
                                        <ArrowLeft size={16} /> Back
                                    </button>

                                    {stepIdx < STEPS.length - 1 ? (
                                        <button
                                            onClick={handleNext}
                                            className="px-6 py-2 rounded bg-brand-cyan text-black font-bold hover:bg-cyan-300 flex items-center gap-2"
                                        >
                                            Next <ArrowRight size={16} />
                                        </button>
                                    ) : (
                                        <button
                                            className="px-6 py-2 rounded bg-brand-lime text-black font-bold hover:bg-lime-400 flex items-center gap-2 shadow-[0_0_20px_rgba(132,204,22,0.4)]"
                                        >
                                            <Save size={16} /> DEPLOY AGENT
                                        </button>
                                    )}
                                </div>

                            </motion.div>
                        </AnimatePresence>
                    </div>
                </div>

                {/* Right Preview */}
                <div className="w-1/3 border-l border-neo-border bg-neo-surface flex flex-col items-center justify-center p-8 bg-[url('/grid.svg')]">
                    <div className="mb-8 text-center">
                        <h3 className="text-white/40 font-mono text-xs tracking-widest uppercase mb-4">Live Preview</h3>
                        <div className="transform scale-125">
                            <AgentCard
                                agent={formData}
                                currentTick={1}
                                isSelected={true}
                                variant="compact"
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
