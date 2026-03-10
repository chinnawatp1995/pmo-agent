-- Knowledge Module Database Schema
-- PostgreSQL Migration Script

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================
-- Data Sources Table
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL,
    description TEXT,
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID DEFAULT '00000000-0000-0000-0000-000000000000',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID DEFAULT '00000000-0000-0000-0000-000000000000',
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID
);

CREATE INDEX idx_data_sources_name ON knowledge_data_sources(name);
CREATE INDEX idx_data_sources_active ON knowledge_data_sources(is_active);

-- ============================================
-- Documents Table
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    data_source_id UUID REFERENCES knowledge_data_sources(id),
    document_type VARCHAR(20) NOT NULL DEFAULT 'txt',
    title VARCHAR(500),
    content_hash VARCHAR(64) NOT NULL,
    file_path TEXT,
    file_size BIGINT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    error_message TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID DEFAULT '00000000-0000-0000-0000-000000000000',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID DEFAULT '00000000-0000-0000-0000-000000000000',
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID
);

CREATE INDEX idx_documents_data_source ON knowledge_documents(data_source_id);
CREATE INDEX idx_documents_status ON knowledge_documents(status);
CREATE INDEX idx_documents_content_hash ON knowledge_documents(content_hash);
CREATE INDEX idx_documents_created_at ON knowledge_documents(created_at);

-- ============================================
-- Chunks Table
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES knowledge_documents(id),
    chunk_index INTEGER NOT NULL,
    locator JSONB DEFAULT '{}',
    content TEXT NOT NULL,
    length INTEGER NOT NULL,
    valid_til TIMESTAMP WITH TIME ZONE,
    embedding_status VARCHAR(20) DEFAULT 'pending',
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID DEFAULT '00000000-0000-0000-0000-000000000000',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID DEFAULT '00000000-0000-0000-0000-000000000000',
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID
);

CREATE INDEX idx_chunks_document ON knowledge_chunks(document_id);
CREATE INDEX idx_chunks_index ON knowledge_chunks(chunk_index);
CREATE INDEX idx_chunks_valid_til ON knowledge_chunks(valid_til);

-- ============================================
-- Vectors Table (pgvector)
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID NOT NULL REFERENCES knowledge_chunks(id),
    embedding vector(1536),
    embedding_model VARCHAR(100),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID DEFAULT '00000000-0000-0000-0000-000000000000',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID DEFAULT '00000000-0000-0000-0000-000000000000',
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID
);

CREATE INDEX idx_vectors_chunk ON knowledge_vectors(chunk_id);
CREATE INDEX idx_vectors_embedding ON knowledge_vectors USING ivfflat (embedding vector_cosine_ops);

-- ============================================
-- Graph Entities Table
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_graph_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    entity_type VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    reference TEXT,
    confidence FLOAT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID DEFAULT '00000000-0000-0000-0000-000000000000',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID DEFAULT '00000000-0000-0000-0000-000000000000',
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID
);

CREATE INDEX idx_graph_entities_name ON knowledge_graph_entities(name);
CREATE INDEX idx_graph_entities_type ON knowledge_graph_entities(entity_type);

-- ============================================
-- Graph Relationships Table
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_graph_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    source_entity_id UUID REFERENCES knowledge_graph_entities(id),
    target_entity_id UUID REFERENCES knowledge_graph_entities(id),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    reference TEXT,
    weight FLOAT DEFAULT 1.0,
    confidence FLOAT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID DEFAULT '00000000-0000-0000-0000-000000000000',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID DEFAULT '00000000-0000-0000-0000-000000000000',
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID
);

CREATE INDEX idx_graph_relationships_source ON knowledge_graph_relationships(source_entity_id);
CREATE INDEX idx_graph_relationships_target ON knowledge_graph_relationships(target_entity_id);
CREATE INDEX idx_graph_relationships_name ON knowledge_graph_relationships(name);

-- ============================================
-- Update Trigger Function
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all tables
CREATE TRIGGER update_data_sources_updated_at
    BEFORE UPDATE ON knowledge_data_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON knowledge_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chunks_updated_at
    BEFORE UPDATE ON knowledge_chunks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vectors_updated_at
    BEFORE UPDATE ON knowledge_vectors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_graph_entities_updated_at
    BEFORE UPDATE ON knowledge_graph_entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_graph_relationships_updated_at
    BEFORE UPDATE ON knowledge_graph_relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Vector Similarity Search Functions
-- ============================================
CREATE OR REPLACE FUNCTION vector_similarity_search(
    query_vector vector,
    limit_count INTEGER DEFAULT 10,
    threshold FLOAT DEFAULT 0.0
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cv.chunk_id,
        kc.document_id,
        kc.content,
        1 - (cv.embedding <=> query_vector) AS similarity
    FROM knowledge_vectors cv
    JOIN knowledge_chunks kc ON cv.chunk_id = kc.id
    WHERE kc.deleted_at IS NULL
      AND cv.deleted_at IS NULL
      AND (1 - (cv.embedding <=> query_vector)) >= threshold
    ORDER BY cv.embedding <=> query_vector
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;