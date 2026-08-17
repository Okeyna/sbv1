import json
import os
from typing import Optional, List, Dict, Any
from .config import settings

# Mock data for when OpenAI is not configured
MOCK_SUMMARY = """• This document covers key concepts and fundamental principles.
• Important definitions and terminology are explained in detail.
• Practical examples illustrate the theoretical concepts.
• Common applications and use cases are discussed.
• Summary points help reinforce the main takeaways."""

MOCK_QUIZ = [
    {
        "question": "What is the main topic of this document?",
        "options": [
            "Advanced theoretical concepts",
            "Key concepts and fundamental principles",
            "Historical background only",
            "Future predictions"
        ],
        "correct_answer": 1,
        "explanation": "The document primarily focuses on key concepts and fundamental principles as outlined in the summary."
    },
    {
        "question": "How are the concepts illustrated in the document?",
        "options": [
            "Through abstract theories only",
            "Using practical examples",
            "With complex mathematical formulas",
            "Via historical anecdotes"
        ],
        "correct_answer": 1,
        "explanation": "The document uses practical examples to illustrate theoretical concepts."
    },
    {
        "question": "What type of content is included in the document?",
        "options": [
            "Only definitions",
            "Only applications",
            "Definitions, examples, and applications",
            "Only summary points"
        ],
        "correct_answer": 2,
        "explanation": "The document includes definitions, practical examples, applications, and summary points."
    },
    {
        "question": "What is the purpose of the summary points?",
        "options": [
            "To introduce new topics",
            "To confuse the reader",
            "To reinforce main takeaways",
            "To provide additional references"
        ],
        "correct_answer": 2,
        "explanation": "Summary points help reinforce the main takeaways from the document."
    },
    {
        "question": "What does the document discuss regarding the concepts?",
        "options": [
            "Only theoretical aspects",
            "Common applications and use cases",
            "Only historical context",
            "Future research directions"
        ],
        "correct_answer": 1,
        "explanation": "The document discusses common applications and use cases of the concepts."
    }
]


def _get_openai_client():
    """Get OpenAI client if API key is configured."""
    if not settings.openai_api_key:
        return None
    
    try:
        from openai import OpenAI
        return OpenAI(api_key=settings.openai_api_key)
    except ImportError:
        return None


def generate_summary(text: str) -> str:
    """
    Generate a summary of the given text.
    
    Args:
        text: The text to summarize
        
    Returns:
        A 5-bullet summary
    """
    client = _get_openai_client()
    
    if client and settings.openai_api_key:
        try:
            # Truncate text if too long
            from .pdf_service import truncate_text
            truncated_text = truncate_text(text, max_length=4000)
            
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a study assistant. Summarize the given text into exactly 5 concise bullet points for studying. Start each bullet with '•'."
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this text into 5 bullet points:\n\n{truncated_text}"
                    }
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI summary failed: {e}, using mock summary")
    
    # Return mock summary
    return MOCK_SUMMARY


def generate_quiz(text: str, difficulty: str = "medium", num_questions: int = 5) -> List[Dict[str, Any]]:
    """
    Generate a multiple-choice quiz from the given text.
    
    Args:
        text: The text to generate questions from
        difficulty: Question difficulty (easy, medium, hard)
        num_questions: Number of questions to generate
        
    Returns:
        List of question dictionaries with question, options, correct_answer, explanation
    """
    client = _get_openai_client()
    
    if client and settings.openai_api_key:
        try:
            from .pdf_service import truncate_text
            truncated_text = truncate_text(text, max_length=4000)
            
            prompt = f"""Generate exactly {num_questions} multiple-choice questions based on this text. 
Difficulty: {difficulty}

Text:
{truncated_text}

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question": "question text",
    "options": ["option A", "option B", "option C", "option D"],
    "correct_answer": 0,
    "explanation": "why this answer is correct"
  }}
]

Rules:
- correct_answer must be an integer 0-3 indicating the index of the correct option
- Each question must have exactly 4 options
- Include an explanation for each question
- Make sure the JSON is valid and parseable"""

            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a quiz generator. Create multiple-choice questions from study material. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            questions = json.loads(content)
            
            # Validate structure
            if isinstance(questions, list) and len(questions) > 0:
                return questions[:num_questions]
                
        except Exception as e:
            print(f"OpenAI quiz generation failed: {e}, using mock quiz")
    
    # Return mock quiz
    return MOCK_QUIZ[:num_questions]


def answer_question(question: str, context: str) -> str:
    """
    Answer a question based on the provided context.
    
    Args:
        question: The user's question
        context: The context text to use for answering
        
    Returns:
        AI-generated answer
    """
    client = _get_openai_client()
    
    if client and settings.openai_api_key:
        try:
            from .pdf_service import truncate_text
            truncated_context = truncate_text(context, max_length=4000)
            
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI tutor. Answer questions based on the provided study material. If the answer is not in the material, say so clearly."
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{truncated_context}\n\nQuestion: {question}"
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI chat failed: {e}, using mock response")
    
    # Mock response
    return f"Based on the study material, I can help you understand this topic. Your question '{question}' relates to the content you've uploaded. For detailed answers, consider adding an OpenAI API key to enable full AI capabilities."
