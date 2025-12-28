"use client";

import useSWR, { useSWRConfig } from "swr";
import { useEffect, useMemo, useState } from "react";
import { AgentInfo, OrgGraph, OutboxEntry, OrgStatus } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const STATUS_KEY = `${API_BASE}/api/status`;
const AGENTS_KEY = `${API_BASE}/api/agents`;
const GRAPH_KEY = `${API_BASE}/api/org-graph`;
const MESSAGES_KEY = `${API_BASE}/api/messages`;
const TICK_KEY = `${API_BASE}/api/engine/tick`;
const CONFIG_KEY = `${API_BASE}/api/engine/config`;
const TOOLS_KEY = `${API_BASE}/api/tools`;
const MODELS_KEY = `${API_BASE}/api/models`;

export interface ToolInfo {
  id: string;
  description: string;
}

export interface CreateAgentRequest {
  name: string;
  resume: Record<string, unknown>;
  path_prefix?: string | null;
}

export async function sendMessage(target: string, text: string, importance: "normal" | "high" = "normal") {
  const res = await fetch(MESSAGES_KEY, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target, text, importance })
  });
  if (!res.ok) throw new Error("Failed to send message: " + res.statusText);
  return res.json();
}

async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch ${url}: ${res.status}`);
  }
  return res.json();
}

function toWebSocketUrl(baseHttpUrl: string): string {
  if (baseHttpUrl.startsWith("https://"))
    return `wss://${baseHttpUrl.slice(8)}`;
  if (baseHttpUrl.startsWith("http://")) return `ws://${baseHttpUrl.slice(7)}`;
  return baseHttpUrl;
}

export function useAgents() {
  const { data, error, isLoading, mutate } = useSWR<AgentInfo[]>(
    AGENTS_KEY,
    fetcher,
    {
      refreshInterval: 30_000,
    },
  );

  return {
    agents: data,
    error,
    isLoading,
    refresh: mutate,
  };
}

export function useOrgGraph() {
  const { data, error, isLoading, mutate } = useSWR<OrgGraph>(
    GRAPH_KEY,
    fetcher,
    {
      refreshInterval: 60_000,
    },
  );

  return {
    graph: data,
    error,
    isLoading,
    refresh: mutate,
  };
}

export function useStatus() {
  const { data, error, isLoading, mutate } = useSWR<OrgStatus>(
    STATUS_KEY,
    fetcher,
    {
      refreshInterval: 10_000,
    },
  );

  return {
    status: data,
    error,
    isLoading,
    refresh: mutate,
  };
}

export function useMessages(limit: number = 50) {
  const key = useMemo(() => `${MESSAGES_KEY}?limit=${limit}`, [limit]);
  const { data, error, isLoading, mutate } = useSWR<OutboxEntry[]>(
    key,
    fetcher,
    {
      refreshInterval: 15_000,
    },
  );

  return {
    messages: data,
    error,
    isLoading,
    refresh: mutate,
  };
}

export function useTools() {
  const { data, error, isLoading, mutate } = useSWR<ToolInfo[]>(TOOLS_KEY, fetcher, {
    refreshInterval: 60_000,
  });

  return {
    tools: data,
    error,
    isLoading,
    refresh: mutate,
  };
}

export function useModels() {
  const { data, error, isLoading, mutate } = useSWR<string[]>(MODELS_KEY, fetcher, {
    refreshInterval: 60_000,
  });

  return {
    models: data,
    error,
    isLoading,
    refresh: mutate,
  };
}

export function useWebSocketStream() {
  const { mutate } = useSWRConfig();
  const [isConnected, setIsConnected] = useState(false);
  const wsUrl = `${toWebSocketUrl(API_BASE)}/ws`;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let active = true;

    const connect = () => {
      if (!active) return;
      socket = new WebSocket(wsUrl);

      socket.onopen = () => setIsConnected(true);
      socket.onclose = () => {
        setIsConnected(false);
        if (active) setTimeout(connect, 2000);
      };
      socket.onerror = () => setIsConnected(false);
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.status) {
            mutate(STATUS_KEY, payload.status, false);
          }
          if (payload.messages) {
            mutate(MESSAGES_KEY, payload.messages, false);
          }
        } catch (err) {
          console.error("Failed to handle websocket payload", err);
        }
      };
    };

    connect();
    return () => {
      active = false;
      socket?.close();
    };
  }, [mutate, wsUrl]);

  return { isConnected };
}

export async function triggerTick() {
  const res = await fetch(TICK_KEY, { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger tick");
  return res.json();
}

export async function getEngineConfig() {
  const res = await fetch(CONFIG_KEY);
  if (!res.ok) throw new Error("Failed to get config");
  return res.json();
}

export async function updateEngineConfig(config: { openai_api_key?: string; anthropic_api_key?: string }) {
  const res = await fetch(CONFIG_KEY, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error("Failed to update config");
  return res.json();
}

export async function createAgent(request: CreateAgentRequest) {
  const res = await fetch(AGENTS_KEY, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  const payload = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = (payload && (payload.detail ?? payload)) || res.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload;
}
