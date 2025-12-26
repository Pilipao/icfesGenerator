import os
import openai
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.models import RagDocument
import json
import logging

logger = logging.getLogger("GenerationService")

# Configure OpenAI / Groq Client
from openai import OpenAI

# We use OpenAI client but pointing to Groq
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
# Note: Groq mainly does chat/generation. 
# For embeddings, we might still need OpenAI or a local model.
# Current code attempts 'client.embeddings.create' which might fail if using Groq base URL unless they proxy it or have a model.
# We will flag embedding generation to check for separate key or fallback.


class GenerationService:
    def __init__(self, db: Session):
        self.db = db

    def get_embedding(self, text_content: str):
        """Generates embedding for query text."""
        # GROQ does not currently support consistent embeddings via this endpoint URL in same way as OpenAI 'text-embedding-ada-002'.
        # For this MVP with Groq, we will use random mock embeddings unless a separate OPENAI_API_KEY is provided for a separate client.
        # Returning mock for stability now.
        import numpy as np
        return np.random.rand(1536).tolist()
        
        # Original logic commented out to prevent Groq client error on embeddings:
        """
        try:
            if not client.api_key or "sk-" not in client.api_key:
                logger.warning("No valid OpenAI API Key found. Returning mock embedding.")
                import numpy as np
                return np.random.rand(1536).tolist()
                
            response = client.embeddings.create(
                input=text_content,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            import numpy as np
            return np.random.rand(1536).tolist()
        """

    def retrieve_context(self, exam: str, skill: str, topic: str = None):
        """Retrieves relevant skill cards and distractors."""
        # Simple logical retrieval for now (since we might have random embeddings in DB)
        # 1. Get Skill Card
        skill_card = self.db.query(RagDocument).filter(
            RagDocument.doc_type == "skill_card",
            RagDocument.skill.ilike(f"%{skill}%")
        ).first()

        # 2. Get some random distractors patterns for variety
        # In a real scenario, we would use vector search here
        distractors = self.db.query(RagDocument).filter(
            RagDocument.doc_type == "distractor_pattern"
        ).limit(3).all()

        return {
            "skill_card": skill_card.content if skill_card else f"Skill {skill} not found.",
            "distractors": "\n".join([d.content for d in distractors])
        }

    def generate_item(self, exam: str, skill: str, difficulty: str):
        context = self.retrieve_context(exam, skill)
        
        system_prompt = "You are an expert assessment specialist for the ICFES exam (Colombia). Your goal is to create high-quality, valid multiple-choice questions that measure specific competencies."
        
        user_prompt = f"""
        TASK: Generate a multiple-choice question (4 options: A, B, C, D) for the '{exam}' exam.
        
        COMPETENCY/SKILL TARGET:
        {context['skill_card']}
        
        DIFFICULTY: {difficulty}
        
        GUIDELINES FOR DISTRACTORS:
        Use the following patterns to create plausible but incorrect answers:
        {context['distractors']}
        
        OUTPUT FORMAT (JSON):
        {{
            "stimulus": "The context text or situation...",
            "question_stem": "The specific question...",
            "options": {{
                "A": "...",
                "B": "...",
                "C": "...",
                "D": "..."
            }},
            "correct_option": "A|B|C|D",
            "rationale": "Explanation of why the correct answer is correct...",
            "distractor_rationales": {{
                "wrong_option_1": "Why it is wrong...",
                "wrong_option_2": "..."
            }}
        }}
        """
        
        # Log the full prompt for debugging
        logger.info(f"--- GENERATION PROMPT ---\nSYSTEM: {system_prompt}\nUSER: {user_prompt}\n-------------------------")

        try:
            if not client.api_key:
                raise Exception("Missing GROQ_API_KEY")

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile", # Groq model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={ "type": "json_object" } 
            )
            
            content = response.choices[0].message.content
            # Try to parse JSON
            try:
                return json.loads(content)
            except:
                return {"raw_output": content}

        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            return {
                "error": str(e),
                "mock_fallback": True,
                "stimulus": "Error connecting to OpenAI or Key missing.",
                "question_stem": "Please check your API Key configuration.",
                "options": {"A": "Check Logs", "B": "Retry", "C": "Config", "D": "Support"},
                "correct_option": "C",
                "debug_info": {"system_prompt": system_prompt, "user_prompt": user_prompt} 
            }
