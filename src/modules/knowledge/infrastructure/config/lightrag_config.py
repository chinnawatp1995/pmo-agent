"""
LightRAG Configuration

Configuration settings for LightRAG with PostgreSQL and FalkorDB backends.
"""
import os
from typing import Optional
from pydantic import BaseModel as PydanticBaseModel, Field


class PostgreSQLConfig(PydanticBaseModel):
    """PostgreSQL connection configuration."""
    
    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    user: str = Field(default="lightrag", description="PostgreSQL user")
    password: str = Field(default="", description="PostgreSQL password")
    database: str = Field(default="lightrag_db", description="PostgreSQL database name")
    
    @property
    def connection_string(self) -> str:
        """Get the PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_connection_string(self) -> str:
        """Get the async PostgreSQL connection string."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @classmethod
    def from_env(cls) -> "PostgreSQLConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "lightrag"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            database=os.getenv("POSTGRES_DB", "lightrag_db"),
        )


class FalkorDBConfig(PydanticBaseModel):
    """FalkorDB (Redis Graph) configuration."""
    
    host: str = Field(default="localhost", description="FalkorDB host")
    port: int = Field(default=6379, description="FalkorDB port")
    password: Optional[str] = Field(default=None, description="FalkorDB password")
    database: int = Field(default=0, description="FalkorDB database number")
    
    @property
    def connection_string(self) -> str:
        """Get the FalkorDB connection string."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"redis://{self.host}:{self.port}/{self.database}"
    
    @classmethod
    def from_env(cls) -> "FalkorDBConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("FALKORDB_HOST", "localhost"),
            port=int(os.getenv("FALKORDB_PORT", "6379")),
            password=os.getenv("FALKORDB_PASSWORD"),
            database=int(os.getenv("FALKORDB_DB", "0")),
        )


class LLMConfig(PydanticBaseModel):
    """LLM provider configuration."""
    
    provider: str = Field(default="openai", description="LLM provider (openai, fireworks)")
    model: str = Field(default="gpt-4o-mini", description="LLM model name")
    api_key: str = Field(default="", description="API key for the LLM provider")
    base_url: Optional[str] = Field(default=None, description="Base URL for API")
    max_tokens: int = Field(default=4000, description="Maximum tokens for response")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create configuration from environment variables."""
        # Support both OpenAI and Fireworks AI
        fireworks_key = os.getenv("FIREWORKS_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        
        if fireworks_key:
            return cls(
                provider="fireworks",
                model=os.getenv("LLM_MODEL", "accounts/fireworks/models/llama-v3p1-70b-instruct"),
                api_key=fireworks_key,
                base_url=os.getenv("LLM_BASE_URL", "https://api.fireworks.ai/inference/v1"),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            )
        else:
            return cls(
                provider="openai",
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                api_key=openai_key,
                base_url=os.getenv("LLM_BASE_URL"),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            )


class EmbeddingConfig(PydanticBaseModel):
    """Embedding model configuration."""
    
    provider: str = Field(default="openai", description="Embedding provider")
    model: str = Field(default="text-embedding-3-small", description="Embedding model name")
    api_key: str = Field(default="", description="API key for embedding provider")
    base_url: Optional[str] = Field(default=None, description="Base URL for API")
    dimension: int = Field(default=1536, description="Embedding dimension")
    batch_size: int = Field(default=100, description="Batch size for embedding")
    
    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Create configuration from environment variables."""
        fireworks_key = os.getenv("FIREWORKS_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        
        if fireworks_key:
            return cls(
                provider="fireworks",
                model=os.getenv("EMBEDDING_MODEL", "nomic-ai/nomic-embed-text-v1.5"),
                api_key=fireworks_key,
                base_url=os.getenv("EMBEDDING_BASE_URL", "https://api.fireworks.ai/inference/v1"),
                dimension=int(os.getenv("EMBEDDING_DIMENSION", "768")),
                batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "100")),
            )
        else:
            return cls(
                provider="openai",
                model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                api_key=openai_key,
                base_url=os.getenv("EMBEDDING_BASE_URL"),
                dimension=int(os.getenv("EMBEDDING_DIMENSION", "1536")),
                batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "100")),
            )


class LightRAGConfig(PydanticBaseModel):
    """
    Complete LightRAG configuration.
    
    Combines all configuration components needed to initialize
    the LightRAG service with PostgreSQL and FalkorDB backends.
    """
    
    # Working directory for LightRAG
    working_dir: str = Field(
        default="./rag_storage",
        description="Working directory for LightRAG"
    )
    
    # Workspace for logical data isolation
    workspace: str = Field(
        default="default",
        description="Workspace name for data isolation"
    )
    
    # Storage backends
    kv_storage: str = Field(
        default="PGKVStorage",
        description="KV storage backend"
    )
    vector_storage: str = Field(
        default="PGVectorStorage",
        description="Vector storage backend"
    )
    graph_storage: str = Field(
        default="PGGraphStorage",
        description="Graph storage backend (PGGraphStorage or FalkorDBStorage)"
    )
    doc_status_storage: str = Field(
        default="PGDocStatusStorage",
        description="Document status storage backend"
    )
    
    # Sub-configurations
    postgres: PostgreSQLConfig = Field(
        default_factory=PostgreSQLConfig,
        description="PostgreSQL configuration"
    )
    falkordb: FalkorDBConfig = Field(
        default_factory=FalkorDBConfig,
        description="FalkorDB configuration"
    )
    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="LLM configuration"
    )
    embedding: EmbeddingConfig = Field(
        default_factory=EmbeddingConfig,
        description="Embedding configuration"
    )
    
    # Query defaults
    default_query_mode: str = Field(
        default="hybrid",
        description="Default query mode"
    )
    default_top_k: int = Field(
        default=60,
        description="Default number of results"
    )
    
    @classmethod
    def from_env(cls) -> "LightRAGConfig":
        """Create complete configuration from environment variables."""
        return cls(
            working_dir=os.getenv("LIGHTRAG_WORKING_DIR", "./rag_storage"),
            workspace=os.getenv("LIGHTRAG_WORKSPACE", "default"),
            kv_storage=os.getenv("LIGHTRAG_KV_STORAGE", "PGKVStorage"),
            vector_storage=os.getenv("LIGHTRAG_VECTOR_STORAGE", "PGVectorStorage"),
            graph_storage=os.getenv("LIGHTRAG_GRAPH_STORAGE", "PGGraphStorage"),
            doc_status_storage=os.getenv("LIGHTRAG_DOC_STATUS_STORAGE", "PGDocStatusStorage"),
            postgres=PostgreSQLConfig.from_env(),
            falkordb=FalkorDBConfig.from_env(),
            llm=LLMConfig.from_env(),
            embedding=EmbeddingConfig.from_env(),
            default_query_mode=os.getenv("LIGHTRAG_DEFAULT_QUERY_MODE", "hybrid"),
            default_top_k=int(os.getenv("LIGHTRAG_DEFAULT_TOP_K", "60")),
        )
    
    def setup_env(self) -> None:
        """Set up environment variables for LightRAG."""
        # PostgreSQL
        os.environ["POSTGRES_HOST"] = self.postgres.host
        os.environ["POSTGRES_PORT"] = str(self.postgres.port)
        os.environ["POSTGRES_USER"] = self.postgres.user
        os.environ["POSTGRES_PASSWORD"] = self.postgres.password
        os.environ["POSTGRES_DB"] = self.postgres.database
        
        # FalkorDB (if using)
        os.environ["FALKORDB_HOST"] = self.falkordb.host
        os.environ["FALKORDB_PORT"] = str(self.falkordb.port)
        if self.falkordb.password:
            os.environ["FALKORDB_PASSWORD"] = self.falkordb.password
        
        # LLM
        os.environ["LLM_BINDING"] = self.llm.provider
        os.environ["LLM_MODEL"] = self.llm.model
        os.environ["LLM_BINDING_API_KEY"] = self.llm.api_key
        if self.llm.base_url:
            os.environ["LLM_BINDING_HOST"] = self.llm.base_url
        
        # Embedding
        os.environ["EMBEDDING_BINDING"] = self.embedding.provider
        os.environ["EMBEDDING_MODEL"] = self.embedding.model
        os.environ["EMBEDDING_DIM"] = str(self.embedding.dimension)
        if self.embedding.base_url:
            os.environ["EMBEDDING_BINDING_HOST"] = self.embedding.base_url