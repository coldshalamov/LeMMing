"use client";

import { useState, useEffect } from "react";
import { X, Key, Shield, Check, AlertTriangle, Eye, EyeOff } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { getEngineConfig, updateEngineConfig } from "@/lib/api";

interface GlobalSettingsModalProps {
    onClose: () => void;
}

export function GlobalSettingsModal({ onClose }: GlobalSettingsModalProps) {
    const [config, setConfig] = useState({ openai_api_key: "", anthropic_api_key: "" });
    const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
    const [isExisting, setIsExisting] = useState({ openai: false, anthropic: false });
    const [showPassword, setShowPassword] = useState({ openai: false, anthropic: false });

    useEffect(() => {
        getEngineConfig().then(data => {
            setIsExisting({
                openai: !!data.openai_api_key,
                anthropic: !!data.anthropic_api_key
            });
        }).catch(err => console.error(err));
    }, []);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape") {
                onClose();
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [onClose]);

    const handleSave = async () => {
        setStatus("loading");
        try {
            await updateEngineConfig(config);
            setStatus("success");
            setTimeout(onClose, 1500);
        } catch {
            setStatus("error");
        }
    };

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                onClick={onClose}
                role="dialog"
                aria-modal="true"
                aria-labelledby="modal-title"
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    onClick={(e) => e.stopPropagation()}
                    className="bg-neo-panel border border-neo-border rounded-xl max-w-lg w-full overflow-hidden flex flex-col shadow-2xl"
                >
                    {/* Header */}
                    <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-brand-cyan/20 rounded-lg">
                                <Shield className="text-brand-cyan" size={20} />
                            </div>
                            <div>
                                <h2 id="modal-title" className="text-xl font-bold text-white">System Config</h2>
                                <p className="text-xs text-gray-400">Manage LLM providers and secrets</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-white/5 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-cyan"
                            aria-label="Close settings"
                        >
                            <X size={20} className="text-gray-400" />
                        </button>
                    </div>

                    <div className="p-6 space-y-6">
                        <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex gap-3 text-yellow-500 text-xs leading-relaxed">
                            <AlertTriangle size={16} className="shrink-0" />
                            <p>API keys are stored locally in <code className="bg-black/40 px-1 rounded">secrets.json</code> and loaded into the engine environment. Never share this file.</p>
                        </div>

                        {/* OpenAI Key */}
                        <div className="space-y-2">
                            <label htmlFor="openai-key" className="flex items-center justify-between">
                                <span className="flex items-center gap-2 text-sm font-medium text-gray-300">
                                    <Key size={14} className="text-brand-cyan" />
                                    OpenAI API Key
                                </span>
                                {isExisting.openai && (
                                    <span className="text-[10px] bg-green-500/10 text-green-400 px-2 py-0.5 rounded border border-green-500/20">ALREADY SET</span>
                                )}
                            </label>
                            <div className="relative">
                                <input
                                    id="openai-key"
                                    autoFocus
                                    type={showPassword.openai ? "text" : "password"}
                                    placeholder={isExisting.openai ? "••••••••••••••••" : "sk-..."}
                                    value={config.openai_api_key}
                                    onChange={e => setConfig({ ...config, openai_api_key: e.target.value })}
                                    className="w-full bg-neo-surface border border-neo-border p-3 pr-10 rounded text-white focus:border-brand-cyan focus:outline-none focus:ring-1 focus:ring-brand-cyan font-mono text-sm"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(prev => ({ ...prev, openai: !prev.openai }))}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"
                                    aria-label={showPassword.openai ? "Hide OpenAI API Key" : "Show OpenAI API Key"}
                                >
                                    {showPassword.openai ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                        </div>

                        {/* Claude Key */}
                        <div className="space-y-2">
                            <label htmlFor="anthropic-key" className="flex items-center justify-between">
                                <span className="flex items-center gap-2 text-sm font-medium text-gray-300">
                                    <Key size={14} className="text-brand-purple" />
                                    Anthropic API Key
                                </span>
                                {isExisting.anthropic && (
                                    <span className="text-[10px] bg-green-500/10 text-green-400 px-2 py-0.5 rounded border border-green-500/20">ALREADY SET</span>
                                )}
                            </label>
                            <div className="relative">
                                <input
                                    id="anthropic-key"
                                    type={showPassword.anthropic ? "text" : "password"}
                                    placeholder={isExisting.anthropic ? "••••••••••••••••" : "sk-ant-..."}
                                    value={config.anthropic_api_key}
                                    onChange={e => setConfig({ ...config, anthropic_api_key: e.target.value })}
                                    className="w-full bg-neo-surface border border-neo-border p-3 pr-10 rounded text-white focus:border-brand-purple focus:outline-none focus:ring-1 focus:ring-brand-purple font-mono text-sm"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(prev => ({ ...prev, anthropic: !prev.anthropic }))}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"
                                    aria-label={showPassword.anthropic ? "Hide Anthropic API Key" : "Show Anthropic API Key"}
                                >
                                    {showPassword.anthropic ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="p-6 border-t border-white/5 flex items-center justify-end gap-3 bg-black/10">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={status === "loading" || (!config.openai_api_key && !config.anthropic_api_key)}
                            className="px-6 py-2 bg-brand-cyan text-black font-bold rounded flex items-center gap-2 hover:bg-cyan-300 transition-colors disabled:opacity-50"
                        >
                            {status === "loading" ? "SAVING..." : status === "success" ? (
                                <>
                                    <Check size={16} /> SAVED
                                </>
                            ) : "SAVE CONFIG"}
                        </button>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
