
import { AgentInfo, OutboxEntry, OrgGraph, StatusResponse as OrgStatus } from "./types";

export const MOCK_AGENTS: AgentInfo[] = [
    {
        name: "overmind",
        title: "System Architect",
        description: "Maintains high-level system coherence and strategic planning.",
        model: "gpt-4-turbo",
        schedule: { run_every_n_ticks: 10, phase_offset: 0 },
        read_outboxes: ["frontend_dev", "backend_dev", "qa_bot"],
        tools: ["read_file", "write_file", "search_web"],
        credits: { credits_left: 950.5, cost_per_action: 0.1, max_credits: 1000 },
    },
    {
        name: "frontend_dev",
        title: "Frontend Engineer",
        description: "Implements UI components and manages React state.",
        model: "claude-3-opus",
        schedule: { run_every_n_ticks: 2, phase_offset: 1 },
        read_outboxes: ["overmind", "backend_dev"],
        tools: ["read_file", "write_file", "browser_test"],
        credits: { credits_left: 120.0, cost_per_action: 0.05, max_credits: 500 },
    },
    {
        name: "backend_dev",
        title: "Backend Engineer",
        description: "Implements API endpoints and database logic.",
        model: "gpt-4",
        schedule: { run_every_n_ticks: 2, phase_offset: 0 },
        read_outboxes: ["overmind"],
        tools: ["read_file", "write_file", "run_shell"],
        credits: { credits_left: 45.2, cost_per_action: 0.05, max_credits: 500 },
    },
    {
        name: "qa_bot",
        title: "Quality Assurance",
        description: "Verifies code quality and runs tests.",
        model: "gpt-3.5-turbo",
        schedule: { run_every_n_ticks: 5, phase_offset: 3 },
        read_outboxes: ["frontend_dev", "backend_dev"],
        tools: ["run_test", "github_issue"],
        credits: { credits_left: 800.0, cost_per_action: 0.01, max_credits: 1000 },
    },
    {
        name: "data_scraper",
        title: "Data Harvester",
        description: "Scrapes the web for latest trends.",
        model: "gpt-3.5-turbo",
        schedule: { run_every_n_ticks: 20, phase_offset: 10 },
        read_outboxes: ["overmind"],
        tools: ["scraper", "save_json"],
        credits: { credits_left: 20.0, cost_per_action: 0.02, max_credits: 100 },
    },
];

export const MOCK_GRAPH: OrgGraph = {
    overmind: { can_read: ["frontend_dev", "backend_dev", "qa_bot"], tools: ["read_file"] },
    frontend_dev: { can_read: ["overmind", "backend_dev"], tools: ["read_file"] },
    backend_dev: { can_read: ["overmind"], tools: ["read_file"] },
    qa_bot: { can_read: ["frontend_dev", "backend_dev"], tools: ["run_test"] },
    data_scraper: { can_read: ["overmind"], tools: ["scraper"] },
};

export const MOCK_MESSAGES: OutboxEntry[] = [
    {
        id: "msg_1",
        tick: 102,
        created_at: new Date(Date.now() - 10000).toISOString(),
        agent: "overmind",
        kind: "directive",
        payload: { text: "We need to refactor the navigation component." },
        tags: ["feature", "priority-high"],
    },
    {
        id: "msg_2",
        tick: 103,
        created_at: new Date(Date.now() - 8000).toISOString(),
        agent: "frontend_dev",
        kind: "status",
        payload: { text: "Starting refactor. Checking out branch." },
        tags: ["dev"],
    },
    {
        id: "msg_3",
        tick: 104,
        created_at: new Date(Date.now() - 5000).toISOString(),
        agent: "backend_dev",
        kind: "response",
        payload: { text: "API endpoint for navigation is ready at /api/nav/structure." },
        tags: ["api"],
    },
    {
        id: "msg_4",
        tick: 105,
        created_at: new Date(Date.now() - 1000).toISOString(),
        agent: "qa_bot",
        kind: "report",
        payload: { text: "Found a regression in login flow when navigation changes." },
        tags: ["bug"],
    },
];

export const MOCK_STATUS: OrgStatus = {
    tick: 105,
    total_agents: 5,
    total_messages: 1420,
    total_credits: 1935.7,
    timestamp: new Date().toISOString(),
};
