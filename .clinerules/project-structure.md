# Project Structure

root/
├── apps/
│   ├── api/                # FastAPI application entry point
│   ├── worker/             # Background task processor (Argo/Celery)
│   └── web/                # Frontend (React/Next.js)
├── src/
│   ├── shared/             # Common utilities, base classes, exceptions
│   └── modules/            # Bounded Contexts (The Core)
│       ├── identity/       # User Management & Auth
│       ├── communication/  # Chat, Messaging, Session History
│       ├── intelligence/   # Agentic Orchestration (The "Brain")
│       ├── knowledge/      # RAG, Vector/Graph Processing (The "Memory")
│       └── integrations/   # 3rd Party Adapters (GitHub, GDrive, etc.)
├── docker/                 # Dockerfiles and Compose configs
├── pyproject.toml          # Dependency management (Poetry/PDM)
└── README.md

# Project Subsstructure (Inside each module)

module_name/
├── domain/                 # Pure Business Logic
│   ├── entities/           # e.g., Agent, ChatMessage, DataSource
│   ├── value_objects/      # e.g., Email, QueryVector
│   ├── repository_interfaces.py # Ports
│   └── service_interfaces.py    # Ports for external logic
├── application/            # Use Cases (Orchestration)
│   ├── commands/           # Logic that changes state (e.g., CreateAgent)
│   └── usecases/           # Businesse Logic 
├── infrastructure/         # External Tech (Adapters)
│   ├── persistence/        # Postgres/Qdrant/FalkorDB implementations
│   ├── external_apis/      # GitHub/Langfuse/AI Provider clients
│   └── mappers/            # Converts DB models to Domain Entities
└── interfaces/             # Entry Points
    └── api/                # Module-specific FastAPI routes