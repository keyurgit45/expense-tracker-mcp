-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create transaction embeddings table
CREATE TABLE IF NOT EXISTS transaction_embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    
    -- Text representation of the transaction (for reference and debugging)
    transaction_text TEXT NOT NULL,
    
    -- The embedding vector (384 dimensions for all-MiniLM-L6-v2)
    embedding vector(384) NOT NULL,
    
    -- Confirmed category after user verification
    confirmed_category_id UUID REFERENCES categories(category_id),
    confirmed_category_name TEXT NOT NULL,
    
    -- Confidence score and metadata
    confidence_score FLOAT,
    embedding_model TEXT DEFAULT 'all-MiniLM-L6-v2',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate embeddings for same transaction
    CONSTRAINT unique_transaction_embedding UNIQUE (transaction_id)
);

-- Create index for vector similarity search
CREATE INDEX idx_transaction_embeddings_vector ON transaction_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for transaction lookups
CREATE INDEX idx_transaction_embeddings_transaction_id ON transaction_embeddings(transaction_id);

-- Update trigger for updated_at
CREATE TRIGGER update_transaction_embeddings_updated_at 
BEFORE UPDATE ON transaction_embeddings 
FOR EACH ROW 
EXECUTE FUNCTION update_updated_at_column();

-- Function to find similar transactions
CREATE OR REPLACE FUNCTION find_similar_transactions(
    query_embedding vector(384),
    limit_count INTEGER DEFAULT 5,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    transaction_id UUID,
    transaction_text TEXT,
    confirmed_category_id UUID,
    confirmed_category_name TEXT,
    similarity_score FLOAT,
    merchant TEXT,
    amount DECIMAL,
    date TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        te.transaction_id,
        te.transaction_text,
        te.confirmed_category_id,
        te.confirmed_category_name,
        1 - (te.embedding <=> query_embedding) AS similarity_score,
        t.merchant,
        t.amount,
        t.date
    FROM transaction_embeddings te
    JOIN transactions t ON te.transaction_id = t.transaction_id
    WHERE 1 - (te.embedding <=> query_embedding) >= similarity_threshold
    ORDER BY te.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to upsert transaction embedding
CREATE OR REPLACE FUNCTION upsert_transaction_embedding(
    p_transaction_id UUID,
    p_transaction_text TEXT,
    p_embedding vector(384),
    p_category_id UUID,
    p_category_name TEXT,
    p_confidence_score FLOAT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_embedding_id UUID;
BEGIN
    INSERT INTO transaction_embeddings (
        transaction_id,
        transaction_text,
        embedding,
        confirmed_category_id,
        confirmed_category_name,
        confidence_score
    ) VALUES (
        p_transaction_id,
        p_transaction_text,
        p_embedding,
        p_category_id,
        p_category_name,
        p_confidence_score
    )
    ON CONFLICT (transaction_id) 
    DO UPDATE SET
        transaction_text = EXCLUDED.transaction_text,
        embedding = EXCLUDED.embedding,
        confirmed_category_id = EXCLUDED.confirmed_category_id,
        confirmed_category_name = EXCLUDED.confirmed_category_name,
        confidence_score = EXCLUDED.confidence_score,
        updated_at = NOW()
    RETURNING embedding_id INTO v_embedding_id;
    
    RETURN v_embedding_id;
END;
$$ LANGUAGE plpgsql;