# Open Questions

## For User Decision

### Q1: Priority after Phase 1 completion?
**Context:** The ROADMAP outlines Phases 2-5 in order, but `plan.md` marks some as MUST vs NICE-to-have.
**Options:**
1. Follow strict phase order (Phase 2: Tests/Validation → Phase 3: Human CLI → etc.)
2. Jump to human-in-the-loop CLI (Phase 3) for immediate usability
3. Focus on real-time dashboard (Phase 4) for observability

### Q2: LLM Provider Priorities?
**Context:** ROADMAP lists multiple providers. Currently OpenAI, Anthropic, Ollama are supported.
**Question:** Which additional providers (Azure OpenAI, Google Gemini) should be prioritized?

### Q3: Database Integration?
**Context:** ROADMAP Phase 5 mentions optional SQLite integration.
**Question:** Is this desired, or should the project remain strictly filesystem-only?

### Q4: Target Deployment Environment?
**Question:** Local development only, cloud (which platform?), or both?

## Tool System Redesign (2025-12-25)

**Context**: Current tool names are too technical ("read_file", "run_shell"). Need user-friendly redesign for cloud SaaS product.

**Requirements**:
- Simple names: "File Access", "Write Code", "Execute Code", "Web Browser"
- Modal popup selector (not inline buttons)
- Tool categories with descriptions
- Advanced settings per tool (e.g., terminal type, browser engine)
- Designed for VM-based execution (cloud service)

**Questions**:
1. Should we map user-friendly names to backend tool IDs, or rename backend tools too?
2. What default tools should every agent have access to?
3. Should "File Access" be split into "Read Files" and "Write Files"?
4. For "Execute Code", what languages/runtimes should be supported by default?

---
*Add questions here when clarification is needed. Mark answered with [ANSWERED].*
