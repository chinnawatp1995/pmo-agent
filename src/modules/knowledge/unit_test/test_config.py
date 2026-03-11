"""
Unit Tests for Infrastructure Configuration

Tests for LightRAGConfig, PostgreSQLConfig, FalkorDBConfig, LLMConfig, and EmbeddingConfig.
"""
import os
import pytest
from unittest.mock import patch

from ..infrastructure.config.lightrag_config import (
    PostgreSQLConfig,
    FalkorDBConfig,
    LLMConfig,
    EmbeddingConfig,
    LightRAGConfig,
)


class TestPostgreSQLConfig:
    """Tests for the PostgreSQLConfig class."""
    
    def test_postgresql_config_creation(self):
        """Test creating a PostgreSQLConfig with default values."""
        config = PostgreSQLConfig()
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.user == "lightrag"
        assert config.database == "lightrag_db"
    
    def test_postgresql_config_custom_values(self):
        """Test creating a PostgreSQLConfig with custom values."""
        config = PostgreSQLConfig(
            host="custom-host",
            port=5433,
            user="custom_user",
            password="custom_password",
            database="custom_db",
        )
        
        assert config.host == "custom-host"
        assert config.port == 5433
        assert config.user == "custom_user"
        assert config.password == "custom_password"
        assert config.database == "custom_db"
    
    def test_postgresql_connection_string(self):
        """Test the connection_string property."""
        config = PostgreSQLConfig(
            user="testuser",
            password="testpass",
            host="testhost",
            port=5432,
            database="testdb",
        )
        
        conn_str = config.connection_string
        
        assert "testuser" in conn_str
        assert "testpass" in conn_str
        assert "testhost" in conn_str
        assert "5432" in conn_str
        assert "testdb" in conn_str
        assert conn_str.startswith("postgresql://")
    
    def test_postgresql_async_connection_string(self):
        """Test the async_connection_string property."""
        config = PostgreSQLConfig(
            user="testuser",
            password="testpass",
            host="testhost",
            port=5432,
            database="testdb",
        )
        
        conn_str = config.async_connection_string
        
        assert conn_str.startswith("postgresql+asyncpg://")
        assert "testuser" in conn_str
        assert "testdb" in conn_str
    
    def test_postgresql_config_from_env(self):
        """Test creating PostgreSQLConfig from environment variables."""
        with patch.dict(os.environ, {
            "POSTGRES_HOST": "env-host",
            "POSTGRES_PORT": "5434",
            "POSTGRES_USER": "env_user",
            "POSTGRES_PASSWORD": "env_password",
            "POSTGRES_DB": "env_db",
        }):
            config = PostgreSQLConfig.from_env()
            
            assert config.host == "env-host"
            assert config.port == 5434
            assert config.user == "env_user"
            assert config.password == "env_password"
            assert config.database == "env_db"


class TestFalkorDBConfig:
    """Tests for the FalkorDBConfig class."""
    
    def test_falkordb_config_creation(self):
        """Test creating a FalkorDBConfig with default values."""
        config = FalkorDBConfig()
        
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.password is None
        assert config.database == 0
    
    def test_falkordb_config_custom_values(self):
        """Test creating a FalkorDBConfig with custom values."""
        config = FalkorDBConfig(
            host="redis-host",
            port=6380,
            password="redis_password",
            database=1,
        )
        
        assert config.host == "redis-host"
        assert config.port == 6380
        assert config.password == "redis_password"
        assert config.database == 1
    
    def test_falkordb_connection_string_no_password(self):
        """Test connection string without password."""
        config = FalkorDBConfig(
            host="localhost",
            port=6379,
            database=0,
        )
        
        conn_str = config.connection_string
        
        assert conn_str == "redis://localhost:6379/0"
    
    def test_falkordb_connection_string_with_password(self):
        """Test connection string with password."""
        config = FalkorDBConfig(
            host="localhost",
            port=6379,
            password="secret",
            database=0,
        )
        
        conn_str = config.connection_string
        
        assert "secret" in conn_str
        assert conn_str.startswith("redis://:")
    
    def test_falkordb_config_from_env(self):
        """Test creating FalkorDBConfig from environment variables."""
        with patch.dict(os.environ, {
            "FALKORDB_HOST": "env-redis",
            "FALKORDB_PORT": "6380",
            "FALKORDB_PASSWORD": "env_redis_pass",
            "FALKORDB_DB": "2",
        }):
            config = FalkorDBConfig.from_env()
            
            assert config.host == "env-redis"
            assert config.port == 6380
            assert config.password == "env_redis_pass"
            assert config.database == 2


class TestLLMConfig:
    """Tests for the LLMConfig class."""
    
    def test_llm_config_creation(self):
        """Test creating an LLMConfig with default values."""
        config = LLMConfig()
        
        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 4000
        assert config.temperature == 0.7
    
    def test_llm_config_custom_values(self):
        """Test creating an LLMConfig with custom values."""
        config = LLMConfig(
            provider="fireworks",
            model="custom-model",
            api_key="test_key",
            base_url="https://api.custom.com",
            max_tokens=8000,
            temperature=0.5,
        )
        
        assert config.provider == "fireworks"
        assert config.model == "custom-model"
        assert config.api_key == "test_key"
        assert config.base_url == "https://api.custom.com"
        assert config.max_tokens == 8000
        assert config.temperature == 0.5
    
    def test_llm_config_from_env_fireworks(self):
        """Test creating LLMConfig from env with Fireworks AI."""
        with patch.dict(os.environ, {
            "FIREWORKS_API_KEY": "fw_test_key",
            "LLM_MODEL": "accounts/fireworks/models/test-model",
            "LLM_BASE_URL": "https://api.fireworks.ai/inference/v1",
            "LLM_MAX_TOKENS": "2000",
            "LLM_TEMPERATURE": "0.3",
        }):
            config = LLMConfig.from_env()
            
            assert config.provider == "fireworks"
            assert config.api_key == "fw_test_key"
            assert "fireworks" in config.model
            assert config.max_tokens == 2000
            assert config.temperature == 0.3
    
    def test_llm_config_from_env_openai(self):
        """Test creating LLMConfig from env with OpenAI."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk_test_key",
            "FIREWORKS_API_KEY": "",  # Empty to use OpenAI
            "LLM_MODEL": "gpt-4",
            "LLM_MAX_TOKENS": "4000",
        }, clear=False):
            # Need to remove FIREWORKS_API_KEY if it exists
            if "FIREWORKS_API_KEY" in os.environ:
                del os.environ["FIREWORKS_API_KEY"]
            
            config = LLMConfig.from_env()
            
            assert config.provider == "openai"
            assert config.api_key == "sk_test_key"


class TestEmbeddingConfig:
    """Tests for the EmbeddingConfig class."""
    
    def test_embedding_config_creation(self):
        """Test creating an EmbeddingConfig with default values."""
        config = EmbeddingConfig()
        
        assert config.provider == "openai"
        assert config.model == "text-embedding-3-small"
        assert config.dimension == 1536
        assert config.batch_size == 100
    
    def test_embedding_config_custom_values(self):
        """Test creating an EmbeddingConfig with custom values."""
        config = EmbeddingConfig(
            provider="fireworks",
            model="custom-embedding-model",
            api_key="test_key",
            dimension=768,
            batch_size=50,
        )
        
        assert config.provider == "fireworks"
        assert config.model == "custom-embedding-model"
        assert config.dimension == 768
        assert config.batch_size == 50
    
    def test_embedding_config_from_env(self):
        """Test creating EmbeddingConfig from environment variables."""
        with patch.dict(os.environ, {
            "FIREWORKS_API_KEY": "fw_key",
            "EMBEDDING_MODEL": "nomic-embed",
            "EMBEDDING_DIMENSION": "768",
            "EMBEDDING_BATCH_SIZE": "32",
        }):
            config = EmbeddingConfig.from_env()
            
            assert config.provider == "fireworks"
            assert config.model == "nomic-embed"
            assert config.dimension == 768
            assert config.batch_size == 32


class TestLightRAGConfig:
    """Tests for the LightRAGConfig class."""
    
    def test_lightrag_config_creation(self):
        """Test creating a LightRAGConfig with default values."""
        config = LightRAGConfig()
        
        assert config.working_dir == "./rag_storage"
        assert config.workspace == "default"
        assert config.kv_storage == "PGKVStorage"
        assert config.vector_storage == "PGVectorStorage"
        assert config.graph_storage == "PGGraphStorage"
        assert config.doc_status_storage == "PGDocStatusStorage"
        assert config.default_query_mode == "hybrid"
        assert config.default_top_k == 60
    
    def test_lightrag_config_custom_values(self):
        """Test creating a LightRAGConfig with custom values."""
        config = LightRAGConfig(
            working_dir="/custom/rag/dir",
            workspace="custom_workspace",
            kv_storage="CustomKVStorage",
            vector_storage="CustomVectorStorage",
            graph_storage="FalkorDBStorage",
            doc_status_storage="CustomDocStatusStorage",
            default_query_mode="local",
            default_top_k=30,
        )
        
        assert config.working_dir == "/custom/rag/dir"
        assert config.workspace == "custom_workspace"
        assert config.kv_storage == "CustomKVStorage"
        assert config.vector_storage == "CustomVectorStorage"
        assert config.graph_storage == "FalkorDBStorage"
        assert config.default_query_mode == "local"
        assert config.default_top_k == 30
    
    def test_lightrag_config_nested_configs(self):
        """Test that nested configs are created properly."""
        config = LightRAGConfig()
        
        assert isinstance(config.postgres, PostgreSQLConfig)
        assert isinstance(config.falkordb, FalkorDBConfig)
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.embedding, EmbeddingConfig)
    
    def test_lightrag_config_from_env(self):
        """Test creating LightRAGConfig from environment variables."""
        with patch.dict(os.environ, {
            "LIGHTRAG_WORKING_DIR": "/env/rag/dir",
            "LIGHTRAG_WORKSPACE": "env_workspace",
            "LIGHTRAG_KV_STORAGE": "EnvKVStorage",
            "LIGHTRAG_VECTOR_STORAGE": "EnvVectorStorage",
            "LIGHTRAG_GRAPH_STORAGE": "EnvGraphStorage",
            "LIGHTRAG_DOC_STATUS_STORAGE": "EnvDocStatusStorage",
            "LIGHTRAG_DEFAULT_QUERY_MODE": "global",
            "LIGHTRAG_DEFAULT_TOP_K": "50",
        }):
            config = LightRAGConfig.from_env()
            
            assert config.working_dir == "/env/rag/dir"
            assert config.workspace == "env_workspace"
            assert config.kv_storage == "EnvKVStorage"
            assert config.vector_storage == "EnvVectorStorage"
            assert config.graph_storage == "EnvGraphStorage"
            assert config.doc_status_storage == "EnvDocStatusStorage"
            assert config.default_query_mode == "global"
            assert config.default_top_k == 50
    
    def test_lightrag_config_setup_env(self):
        """Test the setup_env method sets environment variables."""
        config = LightRAGConfig(
            postgres=PostgreSQLConfig(
                host="test-host",
                port=5433,
                user="test_user",
                password="test_pass",
                database="test_db",
            ),
            falkordb=FalkorDBConfig(
                host="test-redis",
                port=6380,
            ),
            llm=LLMConfig(
                provider="test_provider",
                model="test-model",
                api_key="test-api-key",
            ),
        )
        
        config.setup_env()
        
        assert os.environ.get("POSTGRES_HOST") == "test-host"
        assert os.environ.get("POSTGRES_PORT") == "5433"
        assert os.environ.get("POSTGRES_USER") == "test_user"
        assert os.environ.get("POSTGRES_PASSWORD") == "test_pass"
        assert os.environ.get("POSTGRES_DB") == "test_db"
        assert os.environ.get("FALKORDB_HOST") == "test-redis"
        assert os.environ.get("FALKORDB_PORT") == "6380"
        assert os.environ.get("LLM_BINDING") == "test_provider"
        assert os.environ.get("LLM_MODEL") == "test-model"
        assert os.environ.get("LLM_BINDING_API_KEY") == "test-api-key"
    
    def test_lightrag_config_validation(self):
        """Test that Pydantic validation works."""
        # Valid config
        config = LightRAGConfig(default_top_k=50)
        assert config.default_top_k == 50
        
        # Test with invalid type (Pydantic should coerce or raise)
        config = LightRAGConfig(default_top_k="30")
        assert config.default_top_k == 30  # Pydantic coerces string to int


class TestConfigIntegration:
    """Integration tests for configuration classes."""
    
    def test_full_config_from_env(self):
        """Test creating a full configuration from environment."""
        env_vars = {
            # PostgreSQL
            "POSTGRES_HOST": "prod-db",
            "POSTGRES_PORT": "5432",
            "POSTGRES_USER": "prod_user",
            "POSTGRES_PASSWORD": "prod_pass",
            "POSTGRES_DB": "prod_db",
            # FalkorDB
            "FALKORDB_HOST": "prod-redis",
            "FALKORDB_PORT": "6379",
            "FALKORDB_PASSWORD": "redis_pass",
            "FALKORDB_DB": "1",
            # LLM
            "FIREWORKS_API_KEY": "fw_prod_key",
            "LLM_MODEL": "accounts/fireworks/models/prod-model",
            "LLM_MAX_TOKENS": "8000",
            "LLM_TEMPERATURE": "0.5",
            # Embedding
            "EMBEDDING_MODEL": "prod-embedding",
            "EMBEDDING_DIMENSION": "1024",
            "EMBEDDING_BATCH_SIZE": "64",
            # LightRAG
            "LIGHTRAG_WORKING_DIR": "/prod/rag",
            "LIGHTRAG_WORKSPACE": "production",
            "LIGHTRAG_DEFAULT_QUERY_MODE": "hybrid",
            "LIGHTRAG_DEFAULT_TOP_K": "100",
        }
        
        with patch.dict(os.environ, env_vars):
            config = LightRAGConfig.from_env()
            
            # Verify all nested configs
            assert config.postgres.host == "prod-db"
            assert config.falkordb.host == "prod-redis"
            assert config.llm.provider == "fireworks"
            assert config.embedding.model == "prod-embedding"
            assert config.working_dir == "/prod/rag"
            assert config.workspace == "production"
    
    def test_config_serialization(self):
        """Test that configs can be serialized to dict."""
        config = LightRAGConfig()
        
        # Pydantic models have model_dump() method
        config_dict = config.model_dump()
        
        assert isinstance(config_dict, dict)
        assert "working_dir" in config_dict
        assert "postgres" in config_dict
        assert "llm" in config_dict