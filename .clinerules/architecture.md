# PMO-Agentic-Platform: Architectural Rules

## 1. Clean Architecture Boundaries
- **Domain Layer (`src/modules/*/domain`)**: Contains Pydantic Models (Entities) and Interfaces. ABSOLUTELY NO dependencies on Agno, SQL, or external APIs here.
- **Application Layer (`src/modules/*/application`)**: Contains Use Cases and Agent Workflows. This is where the "Orchestrator" lives.
- **Infrastructure Layer (`src/modules/*/infrastructure`)**: Implementation of Tools. Agno Agent definitions, SQL queries, FalkorDB Cypher, and Gemini CLI calls live here.

## 2. Agentic SOLID Principles
- **Single Responsibility**: One Agent = One Domain. (e.g., The SQL Agent never writes Python code; it only provides data).
- **Interface Segregation**: Agents must return Pydantic objects, never raw strings, to ensure the next agent in the chain can parse the data reliably.
- **Dependency Inversion**: The Orchestrator depends on `AgentProtocols`, not specific Agno implementations.