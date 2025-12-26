
"use client";

import { useMemo, useState } from "react";
import { AgentCard } from "@/components/AgentCard";
import { AgentInfo } from "@/lib/types";
import { createAgent, useModels } from "@/lib/api";
import { ArrowRight, ArrowLeft, Check, Terminal, Cpu, Clock, Shield, Save, X, Brain, Plus } from "lucide-react";
import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { ScheduleClock } from "@/components/ScheduleClock";
import { ToolSelectorModal } from "@/components/ToolSelectorModal";

const STEPS = [
    { id: "identity", label: "Identity", icon: Terminal },
    { id: "brain", label: "Brain", icon: Cpu },
    { id: "schedule", label: "Schedule", icon: Clock },
    { id: "permissions", label: "Permissions", icon: Shield },
    { id: "review", label: "Review", icon: Save },
];

const FALLBACK_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
    "claude-3-opus",
    "claude-3-sonnet",
    "claude-3-haiku",
];

const DEFAULT_INSTRUCTIONS =
    "You are a LeMMing agent operating in a multi-agent organization.\n\n" +
    "Read your virtual inbox (permitted outboxes), do your role, and write results to your outbox.\n\n" +
    "Be concise. Cite file paths when relevant. Use tools only when needed.";

type WizardState = {
    name: string;
    title: string;
    short_description: string;
    workflow_description: string;
    model: { key: string; temperature: number; max_tokens: number };
    schedule: { run_every_n_ticks: number; phase_offset: number };
    permissions: { read_outboxes: string[]; tools: string[] };
    credits: { max_credits: number; soft_cap: number };
    instructions: string;
};

export default function WizardPage() {
    const [currentStep, setCurrentStep] = useState(0);

    const { models } = useModels();
    const modelOptions = models?.length ? models : FALLBACK_MODELS;

    const [formData, setFormData] = useState<WizardState>({
        name: "",
        title: "",
        short_description: "",
        workflow_description: "",
        model: { key: modelOptions[0] ?? "gpt-4o-mini", temperature: 0.2, max_tokens: 2048 },
        schedule: { run_every_n_ticks: 1, phase_offset: 0 },
        permissions: { read_outboxes: [], tools: [] },
        credits: { max_credits: 1000, soft_cap: 500 },
        instructions: DEFAULT_INSTRUCTIONS,
    });

    const [isDeploying, setIsDeploying] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showToolModal, setShowToolModal] = useState(false);

    const stepIdx = currentStep;
    const StepIcon = STEPS[stepIdx].icon;

    const handleNext = () => setCurrentStep(prev => Math.min(prev + 1, STEPS.length - 1));

    // Improved Back handler: Goes to dashboard if on Step 0
    const handleBack = () => {
        if (currentStep === 0) {
            window.location.href = "/";
        } else {
            setCurrentStep(prev => Math.max(prev - 1, 0));
        }
    };

    const handleDeploy = async () => {
        setIsDeploying(true);
        setError(null);
        try {
            const resume = {
                name: formData.name,
                title: formData.title,
                short_description: formData.short_description,
                workflow_description: formData.workflow_description,
                model: formData.model,
                permissions: formData.permissions,
                schedule: formData.schedule,
                instructions: formData.instructions,
                credits: formData.credits,
            };

            await createAgent({ name: formData.name, resume });

            // Success! Redirect to dashboard
            window.location.href = "/";

        } catch (e: any) {
            setError(e.message);
            setIsDeploying(false);
        }
    };

    const previewAgent: AgentInfo = useMemo(() => ({
        name: formData.name || "new_agent",
        title: formData.title || "New Agent",
        description: formData.short_description || "No description provided",
        model: formData.model.key,
        schedule: formData.schedule,
        read_outboxes: formData.permissions.read_outboxes,
        tools: formData.permissions.tools,
        credits: {
            credits_left: formData.credits.max_credits,
            max_credits: formData.credits.max_credits,
            soft_cap: formData.credits.soft_cap,
        },
    }), [formData]);

    return (
        <div className="min-h-screen bg-neo-bg text-foreground font-sans flex flex-col">
            {/* Header */}
            <header className="h-16 border-b border-neo-border bg-neo-panel flex items-center justify-between px-4 shrink-0">
                <div className="flex items-center gap-2">
                    <Link href="/" className="hover:text-brand-cyan transition-colors">
                        <h1 className="font-bold text-lg tracking-tight">LeMMing <span className="text-white/30 font-light text-sm">WIZARD</span></h1>
                    </Link>
                </div>

                <div className="flex items-center gap-3">
                    <div className="flex gap-1.5">
                        {STEPS.map((step, idx) => (
                            <div key={step.id} className={clsx("flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-mono transition-colors",
                                idx === stepIdx ? "bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/50" :
                                    idx < stepIdx ? "text-brand-lime" : "text-white/20"
                            )}>
                                <step.icon size={10} />
                                {idx < stepIdx ? <Check size={10} /> : <span className="hidden sm:inline">{step.label}</span>}
                            </div>
                        ))}
                    </div>

                    <Link href="/" className="text-white/40 hover:text-white transition-colors p-1.5 hover:bg-white/5 rounded-full" title="Close Wizard">
                        <X size={18} />
                    </Link>
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
                                                <span className={clsx("text-[10px] font-mono", formData.short_description.length > 200 ? "text-orange-400" : "text-gray-600")}>
                                                    {formData.short_description.length} chars
                                                </span>
                                            </div>
                                            <textarea
                                                id="agent-desc"
                                                required
                                                value={formData.short_description}
                                                onChange={e => setFormData({ ...formData, short_description: e.target.value })}
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
                                                value={formData.model.key}
                                                onChange={e => setFormData({ ...formData, model: { ...formData.model, key: e.target.value } })}
                                                className="w-full bg-neo-surface border border-neo-border p-3 rounded text-white focus:border-brand-cyan focus:outline-none"
                                            >
                                                {modelOptions.map(m => <option key={m} value={m}>{m}</option>)}
                                            </select>
                                        </div>
                                        <div className="p-4 rounded border border-neo-border bg-neo-surface/50">
                                            <h4 id="instructions-label" className="text-sm font-bold text-white mb-2">System Instructions Preamble</h4>
                                            <p id="instructions-desc" className="text-xs text-gray-400">
                                                &quot;You are a LeMMing agent operating in a multi-agent organization...&quot;
                                            </p>
                                            <textarea
                                                aria-labelledby="instructions-label"
                                                aria-describedby="instructions-desc"
                                                className="w-full mt-2 bg-black/20 border border-white/10 p-2 text-xs font-mono text-gray-300 h-40 focus:outline-none focus:border-brand-cyan"
                                                placeholder="Add custom instructions here (e.g. coding style, specific rules)..."
                                                value={formData.instructions}
                                                onChange={e => setFormData({ ...formData, instructions: e.target.value })}
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* STEP 3: SCHEDULE */}
                                {stepIdx === 2 && (
                                    <div className="space-y-6">
                                        <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded text-blue-300 text-sm">
                                            <p className="mb-2">Set when your agent runs during each tick cycle.</p>
                                            <p className="text-xs text-gray-400">The organization runs on a regular timer (default: 10 seconds per tick, configurable).</p>
                                        </div>

                                        {/* Frequency Selector */}
                                        <div>
                                            <label htmlFor="agent-frequency" className="block text-sm font-medium text-gray-300 mb-2">
                                                How often should this agent run?
                                            </label>
                                            <select
                                                id="agent-frequency"
                                                value={formData.schedule.run_every_n_ticks}
                                                onChange={e => setFormData({ ...formData, schedule: { ...formData.schedule, run_every_n_ticks: parseInt(e.target.value) } })}
                                                className="w-full bg-neo-surface border border-neo-border p-3 rounded text-white focus:border-brand-cyan focus:outline-none"
                                            >
                                                <option value={1}>Every Tick (100% active)</option>
                                                <option value={2}>Every 2 Ticks (50% active)</option>
                                                <option value={3}>Every 3 Ticks (33% active)</option>
                                                <option value={4}>Every 4 Ticks (25% active)</option>
                                                <option value={6}>Every 6 Ticks (17% active)</option>
                                                <option value={12}>Every 12 Ticks (8% active)</option>
                                            </select>
                                            <p className="mt-2 text-xs text-gray-500">
                                                More frequent = more responsive, but uses more credits
                                            </p>
                                        </div>

                                        {/* Interactive Clock for Offset */}
                                        <div>
                                            <label className="block text-sm font-medium text-gray-300 mb-3">
                                                When should it start? (Click the clock)
                                            </label>
                                            <ScheduleClock
                                                frequency={1 / formData.schedule.run_every_n_ticks}
                                                offset={formData.schedule.phase_offset}
                                                onChange={(newOffset) => setFormData({ ...formData, schedule: { ...formData.schedule, phase_offset: newOffset } })}
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* STEP 4: PERMISSIONS */}
                                {stepIdx === 3 && (
                                    <div className="space-y-6">
                                        {/* Tool Selection */}
                                        <div>
                                            <label className="block text-sm font-medium text-gray-300 mb-3">
                                                What can this agent do?
                                            </label>

                                            <button
                                                type="button"
                                                onClick={() => setShowToolModal(true)}
                                                className="w-full p-6 border-2 border-dashed border-white/20 rounded-xl hover:border-brand-cyan/50 hover:bg-white/5 transition-all group"
                                            >
                                                <div className="flex items-center justify-center gap-3 text-gray-400 group-hover:text-brand-cyan transition-colors">
                                                    <Plus size={24} />
                                                    <span className="text-lg font-medium">
                                                        {formData.permissions.tools.length > 0
                                                            ? `${formData.permissions.tools.length} Capabilities Selected - Click to Edit`
                                                            : "Select Capabilities"}
                                                    </span>
                                                </div>
                                            </button>

                                            {/* Selected Tools Display */}
                                            {formData.permissions.tools.length > 0 && (
                                                <div className="mt-4 flex flex-wrap gap-2">
                                                    {formData.permissions.tools.map(tool => (
                                                        <div key={tool} className="px-3 py-1.5 bg-brand-cyan/10 border border-brand-cyan/30 rounded-full text-xs text-brand-cyan flex items-center gap-2">
                                                            <Check size={12} />
                                                            {tool}
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>

                                        {/* Read Access */}
                                        <div>
                                            <label htmlFor="agent-read-access" className="block text-sm font-medium text-gray-300 mb-2">
                                                Which agents can this one read from?
                                            </label>
                                            <p className="text-xs text-gray-500 mb-3">
                                                Your agent can see messages from these other agents
                                            </p>
                                            <input
                                                id="agent-read-access"
                                                type="text"
                                                placeholder="Enter agent names separated by commas (e.g., manager, researcher)"
                                                className="w-full bg-neo-surface border border-neo-border p-3 rounded text-white focus:border-brand-cyan focus:outline-none text-sm"
                                                value={formData.permissions.read_outboxes.join(", ")}
                                                onChange={e => setFormData({ ...formData, permissions: { ...formData.permissions, read_outboxes: e.target.value.split(",").map(s => s.trim()).filter(Boolean) } })}
                                            />
                                        </div>
                                    </div>
                                )}

                                {/* STEP 5: REVIEW */}
                                {stepIdx === 4 && (
                                    <div className="space-y-6">
                                        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded text-green-400 text-sm flex items-center gap-2">
                                            <Check size={16} />
                                            <span>Ready to deploy your agent!</span>
                                        </div>

                                        {/* Visual Summary Card */}
                                        <div className="bg-gradient-to-br from-neo-panel to-neo-surface border border-neo-border rounded-xl overflow-hidden">
                                            {/* Header */}
                                            <div className="p-6 border-b border-white/5 bg-black/20">
                                                <h3 className="text-2xl font-bold text-white mb-1">{formData.name || "Unnamed Agent"}</h3>
                                                <p className="text-brand-cyan text-sm font-mono uppercase">{formData.title || "No Title"}</p>
                                            </div>

                                            {/* Details Grid */}
                                            <div className="p-6 space-y-4">
                                                {/* Description */}
                                                <div>
                                                    <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Purpose</div>
                                                    <p className="text-gray-300 text-sm">{formData.short_description || "No description provided"}</p>
                                                </div>

                                                {/* Model */}
                                                <div className="grid grid-cols-2 gap-4">
                                                    <div>
                                                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">AI Model</div>
                                                        <div className="flex items-center gap-2">
                                                            <Brain size={16} className="text-brand-purple" />
                                                            <span className="text-white font-mono text-sm">{formData.model.key}</span>
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Schedule</div>
                                                        <div className="flex items-center gap-2">
                                                            <Clock size={16} className="text-brand-cyan" />
                                                            <span className="text-white text-sm">Every {formData.schedule.run_every_n_ticks} tick{formData.schedule.run_every_n_ticks > 1 ? 's' : ''}</span>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Tools */}
                                                {formData.permissions.tools.length > 0 && (
                                                    <div>
                                                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Capabilities</div>
                                                        <div className="flex flex-wrap gap-2">
                                                            {formData.permissions.tools.map(tool => (
                                                                <div key={tool} className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-full text-xs text-gray-300">
                                                                    {tool}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Read Access */}
                                                {formData.permissions.read_outboxes.length > 0 && (
                                                    <div>
                                                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Can Read From</div>
                                                        <div className="flex flex-wrap gap-2">
                                                            {formData.permissions.read_outboxes.map(agent => (
                                                                <div key={agent} className="px-3 py-1.5 bg-brand-cyan/10 border border-brand-cyan/30 rounded-full text-xs text-brand-cyan">
                                                                    {agent}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Credits */}
                                                <div className="pt-4 border-t border-white/5">
                                                    <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Resource Budget</div>
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-sm text-gray-300">Maximum Credits</span>
                                                        <span className="text-brand-lime font-mono font-bold">{formData.credits.max_credits}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {error && (
                                            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded text-red-400 text-sm">
                                                <strong>Error:</strong> {error}
                                            </div>
                                        )}
                                    </div>
                                )}


                                {/* Footer Controls */}
                                <div className="flex justify-between pt-8 border-t border-white/5">
                                    <button
                                        onClick={handleBack}
                                        className="px-6 py-2 rounded border border-neo-border text-gray-400 hover:text-white flex items-center gap-2"
                                    >
                                        <ArrowLeft size={16} />
                                        {stepIdx === 0 ? "Cancel" : "Back"}
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
                                            onClick={handleDeploy}
                                            disabled={isDeploying}
                                            className={clsx("px-6 py-2 rounded font-bold flex items-center gap-2 shadow-[0_0_20px_rgba(132,204,22,0.4)]",
                                                isDeploying ? "bg-gray-500 cursor-wait" : "bg-brand-lime text-black hover:bg-lime-400"
                                            )}
                                        >
                                            <Save size={16} />
                                            {isDeploying ? "DEPLOYING..." : "DEPLOY AGENT"}
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
                                agent={previewAgent}
                                currentTick={1}
                                isSelected={true}
                                variant="compact"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Tool Selector Modal */}
            {showToolModal && (
                <ToolSelectorModal
                    selectedTools={formData.permissions.tools}
                    onClose={() => setShowToolModal(false)}
                    onSave={(tools) => setFormData({ ...formData, permissions: { ...formData.permissions, tools } })}
                />
            )}
        </div>
    );
}
