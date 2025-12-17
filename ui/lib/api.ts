"use client";

import useSWR, { useSWRConfig } from "swr";
import { useEffect, useMemo, useState } from "react";
import { AgentInfo, OrgGraph, OutboxEntry, StatusResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const STATUS_KEY = `${API_BASE}/api/status`;
const AGENTS_KEY = `${API_BASE}/api/agents`;
const GRAPH_KEY = `${API_BASE}/api/org-graph`;
const MESSAGES_KEY = `${API_BASE}/api/messages`;

async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch ${url}: ${res.status}`);
  }
  return res.json();
}

function toWebSocketUrl(baseHttpUrl: string): string {
  if (baseHttpUrl.startsWith("https://")) return `wss://${baseHttpUrl.slice(8)}`;
  if (baseHttpUrl.startsWith("http://")) return `ws://${baseHttpUrl.slice(7)}`;
  return baseHttpUrl;
}

export function useAgents() {
  const { data, error, isLoading, mutate } = useSWR<AgentInfo[]>(AGENTS_KEY, fetcher, {
    refreshInterval: 30_000,
  });

  return {
    agents: data,
    error,
    isLoading,
    refresh: mutate,
  };
}

export function useOrgGraph() {
  const { data, error, isLoading, mutate } = useSWR<OrgGraph>(GRAPH_KEY, fetcher, {
    refreshInterval: 60_000,
  });

  return {
    graph: data,
    error,
    isLoading,
    refresh: mutate,
  };
}

export function useStatus() {
  const { data, error, isLoading, mutate } = useSWR<StatusResponse>(STATUS_KEY, fetcher, {
    refreshInterval: 10_000,
  });

  return {
    status: data,
    error,
    isLoading,
    refresh: mutate,
  };
}

export function useMessages(limit: number = 50) {
  const key = useMemo(() => `${MESSAGES_KEY}?limit=${limit}`, [limit]);
  const { data, error, isLoading, mutate } = useSWR<OutboxEntry[]>(key, fetcher, {
    refreshInterval: 15_000,
  });

  return {
    messages: data,
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
