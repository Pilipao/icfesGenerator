-- Select all records from rag_documents
-- Limiting content output for readability
SELECT id, doc_type, substring(content from 1 for 50) as content_preview, created_at
FROM rag_documents
ORDER BY doc_type, id;
