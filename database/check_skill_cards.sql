-- Select all documents of type 'skill_card'
SELECT id, skill, topic, difficulty_band, substring(content from 1 for 100) as content_preview
FROM rag_documents
WHERE doc_type = 'skill_card';
