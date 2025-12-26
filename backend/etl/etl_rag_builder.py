import pandas as pd
import json
import uuid
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ETL_RAG_Builder")

# Configuration
CSV_PATH = "/data/input.csv" if os.path.exists("/data/input.csv") else "c:/Users/Filipo/Documents/code/icfes_pruebas/preguntas_sociales_final_enriquecido.csv"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5433/icfes_rag_db")

# Mock embedding function (replace with real OpenAI call)
def get_embedding(text):
    # Return a random vector of size 1536 for testing
    import numpy as np
    return np.random.rand(1536).tolist()

def process_csv(csv_path=None, source_filename=None):
    if csv_path is None:
        csv_path = CSV_PATH

    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found at {csv_path}")
        return {"status": "error", "message": "File not found"}

    df = pd.read_csv(csv_path)
    filename = source_filename if source_filename else os.path.basename(csv_path)
    logger.info(f"Loaded CSV with {len(df)} rows from {filename}.")

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Process Skill Cards
        skills_count = process_skills(df, session, filename)
        
        # 2. Process Distractor Patterns
        patterns_count = process_distractors(df, session, filename)
        
        # 3. Process Similarity Items (Blocking Copying)
        process_similarity_items(df, session)
        
        session.commit()
        logger.info("ETL process completed successfully.")
        return {
            "status": "success", 
            "details": {
                "rows_processed": len(df),
                "skills_created": skills_count, 
                "patterns_created": patterns_count
            }
        }
    except Exception as e:
        session.rollback()
        logger.error(f"ETL failed: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        session.close()

def process_skills(df, session, source_file):
    skills = df.groupby('skill')
    count = 0
    
    for skill_name, group in skills:
        if pd.isna(skill_name): continue
        
        # Aggregate metadata
        topics = group['topic'].unique().tolist()
        difficulties = group['difficulty'].unique().tolist()
        steps = group['required_steps'].dropna().unique().tolist()
        misconceptions = group['common_misconception'].dropna().unique().tolist()
        
        content = f"Skill: {skill_name}\n\nTopics: {', '.join(map(str, topics))}\n\n"
        content += "Common Misconceptions:\n" + "\n".join([f"- {m}" for m in misconceptions]) + "\n\n"
        content += "Required Steps:\n" + "\n".join([f"- {s}" for s in steps])

        metadata = {
            "topics": topics,
            "difficulties": difficulties,
            "sample_item_ids": group['item_id'].tolist()[:5] # Store ref to source items
        }

        # Check if already exists (naive check)
        # For MVP we just insert. In prod, update or skip.
        
        stmt = text("""
            INSERT INTO rag_documents (doc_type, skill, content, metadata, source_file, embedding)
            VALUES (:doc_type, :skill, :content, :metadata, :source_file, :embedding)
        """)
        
        session.execute(stmt, {
            "doc_type": "skill_card",
            "skill": skill_name,
            "content": content,
            "metadata": json.dumps(metadata),
            "source_file": source_file,
            "embedding": get_embedding(content)
        })
        count += 1
    
    logger.info(f"Processed {count} skill cards.")
    return count

def process_distractors(df, session, source_file):
    # Collect all distractor patterns and their rationales
    patterns = {} # name -> list of rationales
    
    for i, row in df.iterrows():
        for char in ['a', 'b', 'c', 'd']:
            pat_col = f'distractor_pattern_{char}'
            rat_col = f'distractor_rationale_{char}'
            
            pat = row.get(pat_col)
            rat = row.get(rat_col)
            
            if pd.notna(pat) and pd.notna(rat):
                if pat not in patterns:
                    patterns[pat] = []
                patterns[pat].append(rat)
    
    count = 0
    for pat_name, examples in patterns.items():
        # Deduplicate examples and limit
        unique_examples = list(set(examples))[:10]
        
        content = f"Distractor Pattern: {pat_name}\n\nExamples of Logic:\n" + "\n".join([f"- {ex}" for ex in unique_examples])
        
        stmt = text("""
            INSERT INTO rag_documents (doc_type, content, source_file, embedding)
            VALUES (:doc_type, :content, :source_file, :embedding)
        """)
        
        session.execute(stmt, {
            "doc_type": "distractor_pattern",
            "content": content,
            "source_file": source_file,
            "embedding": get_embedding(content)
        })
        count += 1
        
    logger.info(f"Processed {count} distractor patterns.")
    return count

def process_similarity_items(df, session):
    for i, row in df.iterrows():
        # Construct full content for similarity check
        full_text = f"{row.get('stimulus', '')} {row.get('question_stem', '')} {row.get('option_a', '')} {row.get('option_b', '')} {row.get('option_c', '')} {row.get('option_d', '')}"
        
        stmt = text("""
            INSERT INTO similarity_items (content_snippet, source, embedding)
            VALUES (:content_snippet, :source, :embedding)
        """)
        
        session.execute(stmt, {
            "content_snippet": full_text[:500], # Store first 500 chars for reference
            "source": "historical_restricted",
            "embedding": get_embedding(full_text)
        })
        
    logger.info(f"Processed {len(df)} similarity items.")

if __name__ == "__main__":
    process_csv()
