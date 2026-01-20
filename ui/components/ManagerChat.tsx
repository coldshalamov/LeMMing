import { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { OutboxEntry } from "../lib/types";
import { sendMessage } from "../lib/api";
import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";

interface ManagerChatProps {
    messages: OutboxEntry[];
    compact?: boolean; // If we want to collapse it
}

export function ManagerChat({ messages, compact = false }: ManagerChatProps) {
    const [inputValue, setInputValue] = useState("");
    const [isSending, setIsSending] = useState(false);
    const [isCollapsed, setIsCollapsed] = useState(compact);
    const scrollRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Filter messages relevant to the Manager interaction
    // We want: 
    // 1. Messages FROM 'human' (User)
    // 2. Messages FROM 'manager' (Replies)
    const chatHistory = messages
        .filter(m => m.agent === "human" || m.agent === "manager")
        .sort((a, b) => {
            // Sort by tick, then creation time
            if (a.tick !== b.tick) return a.tick - b.tick;
            return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        });

    // Auto-scroll to bottom
    useEffect(() => {
        if (!isCollapsed && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [chatHistory.length, isCollapsed]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
        }
    }, [inputValue]);

    const handleSend = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!inputValue.trim() || isSending) return;

        const text = inputValue.trim();
        setInputValue("");
        setIsSending(true);

        try {
            await sendMessage("manager", text);
        } catch (err) {
            console.error("Failed to send message", err);
            // Ideally show toast
        } finally {
            setIsSending(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInputValue(e.target.value);
    };

    return (
        <motion.div
            initial={false}
            animate={{ height: isCollapsed ? "auto" : "100%" }}
            transition={{ type: "spring", bounce: 0, duration: 0.4 }}
            className="flex flex-col bg-black/40 backdrop-blur-md rounded-xl border border-white/10 overflow-hidden shadow-2xl relative z-40 w-[400px] pointer-events-auto"
        >
            {/* Header */}
            <div
                className="p-4 border-b border-white/5 bg-black/20 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors group"
                onClick={() => setIsCollapsed(!isCollapsed)}
                role="button"
                aria-expanded={!isCollapsed}
                aria-label={isCollapsed ? "Expand manager chat" : "Collapse manager chat"}
                tabIndex={0}
                onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setIsCollapsed(!isCollapsed);
                    }
                }}
            >
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-brand-purple/20 border border-brand-purple flex items-center justify-center text-brand-purple">
                        <Bot size={20} />
                    </div>
                    <div>
                        <h3 className="text-sm font-bold text-white">Manager</h3>
                        <div className="flex items-center gap-1.5 mt-0.5" role="status">
                             <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                             <p className="text-[10px] text-gray-400 font-mono">ONLINE // READY TO DELEGATE</p>
                        </div>
                    </div>
                </div>
                <div className="text-gray-400 group-hover:text-white transition-colors p-1">
                    {isCollapsed ? <ChevronDown size={20} /> : <ChevronUp size={20} />}
                </div>
            </div>

            {/* Content */}
            <AnimatePresence>
                {!isCollapsed && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex flex-col flex-1 min-h-0"
                    >
                        {/* Messages Area */}
                        <div
                            ref={scrollRef}
                            className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent"
                            role="log"
                            aria-live="polite"
                            aria-label="Chat history"
                        >
                            {chatHistory.length === 0 && (
                                <div className="text-center text-gray-500 text-xs italic mt-10">
                                    Start a conversation with the Manager to begin orchestrating your organization.
                                </div>
                            )}

                            {chatHistory.map((msg) => {
                                const isUser = msg.agent === "human";
                                return (
                                    <motion.div
                                        key={msg.id}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className={clsx(
                                            "flex gap-3 max-w-[90%]",
                                            isUser ? "ml-auto flex-row-reverse" : "mr-auto"
                                        )}
                                    >
                                        {/* Avatar */}
                                        <div className={clsx(
                                            "w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-1",
                                            isUser ? "bg-brand-cyan/20 text-brand-cyan" : "bg-brand-purple/20 text-brand-purple"
                                        )}>
                                            {isUser ? <User size={12} /> : <Bot size={12} />}
                                        </div>

                                        {/* Bubble */}
                                        <div className={clsx(
                                            "p-3 rounded-xl text-sm leading-relaxed whitespace-pre-wrap font-mono",
                                            isUser
                                                ? "bg-brand-cyan/10 border border-brand-cyan/20 text-cyan-50 rounded-tr-none"
                                                : "bg-white/5 border border-white/10 text-gray-200 rounded-tl-none"
                                        )}>
                                            {msg.kind !== "message" && (
                                                <div className="text-[9px] uppercase tracking-wider opacity-50 mb-1">{msg.kind}</div>
                                            )}
                                            {msg.payload.text || JSON.stringify(msg.payload)}
                                        </div>
                                    </motion.div>
                                );
                            })}
                        </div>

                        {/* Input Area */}
                        <form onSubmit={handleSend} className="p-3 bg-black/40 border-t border-white/5 flex gap-2 items-end">
                            <textarea
                                ref={textareaRef}
                                value={inputValue}
                                onChange={handleChange}
                                onKeyDown={handleKeyDown}
                                rows={1}
                                placeholder="Type your instructions..."
                                aria-label="Message to Manager"
                                className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-brand-purple/50 focus:bg-white/10 transition-all font-mono resize-none min-h-[38px] max-h-[120px]"
                            />
                            <button
                                type="submit"
                                disabled={!inputValue.trim() || isSending}
                                aria-label={isSending ? "Sending message..." : "Send message"}
                                className="p-2 bg-brand-purple text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors h-[38px] flex items-center justify-center"
                            >
                                {isSending ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                            </button>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}
