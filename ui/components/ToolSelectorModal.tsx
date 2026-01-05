// Tool Selector Modal - User-Friendly Tool Selection
"use client";

import { useState } from "react";
import { X, FileText, Code, Terminal, Database, Settings, Plus } from "lucide-react";
import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";

interface Tool {
    id: string;
    name: string;
    description: string;
    icon: React.ComponentType<{ size?: number; className?: string }>;
    category: "files" | "code" | "data" | "org";
    hasAdvanced?: boolean;
}

const TOOL_CATALOG: Tool[] = [
    {
        id: "file_read",
        name: "File Access",
        description: "Read files from the agent workspace or shared folder",
        icon: FileText,
        category: "files",
        hasAdvanced: true,
    },
    {
        id: "file_write",
        name: "Write Files",
        description: "Create and modify files in the agent workspace or shared folder",
        icon: FileText,
        category: "files",
        hasAdvanced: true,
    },
    {
        id: "file_list",
        name: "List Files",
        description: "List directory contents in the agent workspace or shared folder",
        icon: FileText,
        category: "files",
    },
    {
        id: "shell",
        name: "Execute Code",
        description: "Run allowed commands in a secure terminal",
        icon: Terminal,
        category: "code",
        hasAdvanced: true,
    },
    {
        id: "memory_read",
        name: "Memory Read",
        description: "Read a key from the agent memory store",
        icon: Database,
        category: "data",
    },
    {
        id: "memory_write",
        name: "Memory Write",
        description: "Write a key/value into the agent memory store",
        icon: Database,
        category: "data",
    },
    {
        id: "list_agents",
        name: "List Agents",
        description: "List all agents and basic information",
        icon: Settings,
        category: "org",
    },
    {
        id: "create_agent",
        name: "Create Agent",
        description: "Create a new agent folder from the template",
        icon: Plus,
        category: "org",
    },
];

interface ToolSelectorModalProps {
    selectedTools: string[];
    onClose: () => void;
    onSave: (tools: string[]) => void;
}

export function ToolSelectorModal({ selectedTools, onClose, onSave }: ToolSelectorModalProps) {
    const [selected, setSelected] = useState<Set<string>>(new Set(selectedTools));
    const [activeCategory, setActiveCategory] = useState<string | null>(null);

    const toggleTool = (toolId: string) => {
        const newSelected = new Set(selected);
        if (newSelected.has(toolId)) {
            newSelected.delete(toolId);
        } else {
            newSelected.add(toolId);
        }
        setSelected(newSelected);
    };

    const handleSave = () => {
        onSave(Array.from(selected));
        onClose();
    };

    const categories = [
        { id: "files", label: "Files", icon: FileText },
        { id: "code", label: "Code", icon: Code },
        { id: "data", label: "Data", icon: Database },
        { id: "org", label: "Org", icon: Settings },
    ];

    const filteredTools = activeCategory
        ? TOOL_CATALOG.filter(t => t.category === activeCategory)
        : TOOL_CATALOG;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                onClick={onClose}
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    onClick={(e) => e.stopPropagation()}
                    className="bg-neo-panel border border-neo-border rounded-xl max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col"
                >
                    {/* Header */}
                    <div className="p-6 border-b border-white/5 flex items-center justify-between">
                        <div>
                            <h2 className="text-2xl font-bold text-white">Select Capabilities</h2>
                            <p className="text-sm text-gray-400 mt-1">Choose what your agent can do</p>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-white/5 rounded-lg transition-colors"
                            aria-label="Close"
                        >
                            <X size={24} className="text-gray-400" />
                        </button>
                    </div>

                    {/* Category Filter */}
                    <div className="p-4 border-b border-white/5 flex gap-2">
                        <button
                            type="button"
                            onClick={() => setActiveCategory(null)}
                            aria-pressed={activeCategory === null}
                            className={clsx(
                                "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                                activeCategory === null
                                    ? "bg-brand-cyan text-white"
                                    : "bg-white/5 text-gray-400 hover:bg-white/10"
                            )}
                        >
                            All
                        </button>
                        {categories.map(cat => (
                            <button
                                key={cat.id}
                                type="button"
                                onClick={() => setActiveCategory(cat.id)}
                                aria-pressed={activeCategory === cat.id}
                                className={clsx(
                                    "px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2",
                                    activeCategory === cat.id
                                        ? "bg-brand-cyan text-white"
                                        : "bg-white/5 text-gray-400 hover:bg-white/10"
                                )}
                            >
                                <cat.icon size={14} />
                                {cat.label}
                            </button>
                        ))}
                    </div>

                    {/* Tool Grid */}
                    <div className="flex-1 overflow-y-auto p-6">
                        <div className="grid grid-cols-2 gap-4">
                            {filteredTools.map(tool => {
                                const isSelected = selected.has(tool.id);
                                const Icon = tool.icon;

                                return (
                                    <button
                                        key={tool.id}
                                        type="button"
                                        onClick={() => toggleTool(tool.id)}
                                        aria-pressed={isSelected}
                                        className={clsx(
                                            "p-4 rounded-xl border-2 transition-all text-left",
                                            isSelected
                                                ? "border-brand-cyan bg-brand-cyan/10"
                                                : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10"
                                        )}
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className={clsx(
                                                "p-2 rounded-lg",
                                                isSelected ? "bg-brand-cyan/20" : "bg-white/10"
                                            )}>
                                                <Icon size={20} className={isSelected ? "text-brand-cyan" : "text-gray-400"} />
                                            </div>
                                            <div className="flex-1">
                                                <div className="font-medium text-white mb-1">{tool.name}</div>
                                                <div className="text-xs text-gray-400 leading-relaxed">{tool.description}</div>
                                                {tool.hasAdvanced && (
                                                    <div className="mt-2 flex items-center gap-1 text-[10px] text-gray-500">
                                                        <Settings size={10} />
                                                        <span>Advanced options available</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="p-6 border-t border-white/5 flex items-center justify-between">
                        <div className="text-sm text-gray-400">
                            {selected.size} {selected.size === 1 ? "capability" : "capabilities"} selected
                        </div>
                        <div className="flex gap-3">
                            <button
                                type="button"
                                onClick={onClose}
                                className="px-4 py-2 rounded-lg border border-white/10 text-gray-300 hover:bg-white/5 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                onClick={handleSave}
                                className="px-6 py-2 rounded-lg bg-brand-cyan text-white hover:bg-brand-cyan/90 transition-colors font-medium"
                            >
                                Save Selection
                            </button>
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
