# System Assumptions, Scope Boundaries, and Engineering Limitations

**Project**: Agentic Commerce Reliability & Recovery Lab  
**Domain**: Simulated Retail Operations Sandbox  

---

## 1. Explicit Assumptions & Scope Boundaries

1. **Synthetic Commerce Sandbox**: All customers, products, inventory records, orders, and payment transactions are 100% synthetic fixtures generated deterministically. The platform does not connect to real Amazon internal systems, live AWS production accounts, real credit card processors, or live customer PII.
2. **Deterministic Default Model Provider**: In standard benchmarking mode, the platform utilizes a rule-informed local deterministic provider to allow zero-cost, reproducible, and completely offline verification. Optional adapters for Gemini, OpenAI, and Ollama are supported but not required for local validation.
3. **No Financial Claims**: We measure technical metrics (task success rate, unauthorized action rate, latency, recovery rate, cryptographic audit completeness). We make no claims of revenue improvement or internal Amazon operational metrics.

---

## 2. Technical Limitations & Production Considerations

1. **Single-Node Hash Chaining vs. Distributed Blockchains**:
   - The current evidence ledger uses SHA-256 sequential hash-chaining stored in relational tables (SQLite/PostgreSQL).
   - In massive multi-region distributed deployments, high concurrency would require Merkle trees or decentralized append-only ledgers (e.g. Amazon QLDB or verifiable log trees) to avoid serialization bottlenecks on single sequential chains.
2. **Simplified Payment State Machine**:
   - The sandbox implements the primary order lifecycle (`pending` $\to$ `confirmed` $\to$ `processing` $\to$ `shipped` $\to$ `delivered` / `cancelled`).
   - Complex edge cases such as split-shipments, partial fulfillment from multiple regional fulfillment centers, and customs holds are simulated via abstract fault injection rules rather than full physical modeling.
3. **Local Event Streaming Fallback**:
   - While Docker Compose provides Redpanda (Kafka-compatible) for distributed event streaming, the local Python runner defaults to a transactional outbox table with an async event dispatcher to guarantee out-of-the-box developer execution without requiring heavy Docker containers.
