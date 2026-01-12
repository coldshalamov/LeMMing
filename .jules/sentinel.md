## 2024-05-23 - Rate Limiting Pattern for API Endpoints

**Vulnerability:** The API lacked rate limiting on sensitive endpoints (`/api/messages` and `/api/agents`), making it vulnerable to Denial of Service (DoS) attacks and resource exhaustion (spawning infinite agents or LLM calls).

**Learning:**
- In-memory rate limiting using a simple dependency factory (`rate_limiter`) is an effective, low-overhead solution for single-instance deployments like this.
- FastAPI's dependency injection system (`Depends`) allows applying rate limits declaratively to specific endpoints without cluttering the business logic.
- Using `request.client.host` is a reasonable identifier for local/simple setups, but behind a proxy (like Docker or Nginx), it might need adjustment (e.g., `X-Forwarded-For`). For this local tool, it suffices.

**Prevention:**
- Always apply rate limits to endpoints that trigger expensive operations (LLM calls, filesystem writes).
- Use the `rate_limiter` dependency factory for any new sensitive endpoints.
