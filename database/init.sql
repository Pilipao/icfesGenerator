-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Table for RAG documents (Skill Cards, Distractor Patterns, Rules)
CREATE TABLE IF NOT EXISTS rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_type TEXT NOT NULL, -- 'skill_card', 'distractor_pattern', 'blueprint_rule', 'seed_text'
    exam TEXT,
    skill TEXT,
    topic TEXT,
    difficulty_band TEXT,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    source_file TEXT,
    embedding VECTOR(1536) -- Adjust dimension based on embedding model (e.g., OpenAI text-embedding-ada-002 is 1536)
);

-- Index for faster vector similarity search
CREATE INDEX IF NOT EXISTS rag_documents_embedding_idx ON rag_documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Table for storing generated items
CREATE TABLE IF NOT EXISTS items_bank (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam TEXT,
    skill TEXT,
    difficulty TEXT,
    question_content JSONB NOT NULL, -- Stores the full JSON of the question
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'draft' -- 'draft', 'approved', 'rejected'
);

-- Table for similarity checks (storing embeddings of generated or restricted items)
CREATE TABLE IF NOT EXISTS similarity_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_hash TEXT, -- To avoid storing full text if needed, or store full text below
    content_snippet TEXT,
    embedding VECTOR(1536),
    source TEXT -- 'generated', 'historical_restricted'
);

CREATE INDEX IF NOT EXISTS similarity_items_embedding_idx ON similarity_items USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Table to log generation runs
CREATE TABLE IF NOT EXISTS generation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_used TEXT,
    parameters JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
