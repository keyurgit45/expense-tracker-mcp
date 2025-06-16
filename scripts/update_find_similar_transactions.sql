-- Fix the date type mismatch in find_similar_transactions function
-- This updates the return type from DATE to TIMESTAMPTZ to match the transactions table

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