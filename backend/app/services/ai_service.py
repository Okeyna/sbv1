"""AI service for generating summaries, quizzes, and answering questions"""
import json
import os
from app.config import Config

# Try to import OpenAI, but don't fail if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def _get_client():
    """Get OpenAI client if configured"""
    if Config.OPENAI_API_KEY and OPENAI_AVAILABLE:
        return OpenAI(api_key=Config.OPENAI_API_KEY)
    return None


def generate_summary(text_content: str) -> str:
    """
    Generate a summary of the text content.
    
    Args:
        text_content: The text to summarize
        
    Returns:
        Summary as string with 5 bullet points
    """
    client = _get_client()
    
    if client and Config.OPENAI_API_KEY:
        try:
            # Truncate text if too long (OpenAI has token limits)
            truncated_text = text_content[:8000] if len(text_content) > 8000 else text_content
            
            response = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful study assistant. Summarize the provided text into exactly 5 concise bullet points for studying."
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this study material into 5 bullet points:\n\n{truncated_text}"
                    }
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fall through to mock response
    
    # Mock response when no API key is configured
    return _generate_mock_summary(text_content)


def _generate_mock_summary(text_content: str) -> str:
    """Generate a deterministic mock summary"""
    # Extract first few sentences as a simple summary
    sentences = text_content.replace('\n', ' ').split('.')[:5]
    summary_parts = []
    
    for i, sentence in enumerate(sentences, 1):
        sentence = sentence.strip()
        if sentence:
            summary_parts.append(f"{i}. {sentence}.")
    
    if not summary_parts:
        summary_parts = [
            "1. Document contains study material.",
            "2. Key concepts are presented throughout.",
            "3. Important details should be reviewed.",
            "4. Practice exercises may be included.",
            "5. Review all sections for complete understanding."
        ]
    
    return '\n'.join(summary_parts)


def generate_quiz(text_content: str) -> list:
    """
    Generate quiz questions from text content.
    
    Args:
        text_content: The text to generate questions from
        
    Returns:
        List of question dictionaries with keys:
        - question: str
        - options: list[str] (4 options)
        - correct_answer: int (index 0-3)
        - explanation: str
    """
    client = _get_client()
    
    if client and Config.OPENAI_API_KEY:
        try:
            truncated_text = text_content[:8000] if len(text_content) > 8000 else text_content
            
            response = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful study assistant. Generate exactly 5 multiple-choice questions based on the provided text. Return ONLY valid JSON in this format: [{\"question\": \"...\", \"options\": [\"A\", \"B\", \"C\", \"D\"], \"correct_answer\": 0, \"explanation\": \"...\"}]"
                    },
                    {
                        "role": "user",
                        "content": f"Generate 5 multiple-choice questions from this text:\n\n{truncated_text}"
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1500
            )
            
            result = response.choices[0].message.content
            questions_data = json.loads(result)
            
            # Handle both array and object with questions key
            if isinstance(questions_data, dict) and 'questions' in questions_data:
                questions_data = questions_data['questions']
            
            if isinstance(questions_data, list) and len(questions_data) > 0:
                return questions_data[:5]
                
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fall through to mock response
    
    # Mock quiz generation
    return _generate_mock_quiz(text_content)


def _generate_mock_quiz(text_content: str) -> list:
    """Generate deterministic mock quiz questions"""
    # Extract some words from the text to make questions relevant
    words = text_content.replace('\n', ' ').split()[:50]
    key_terms = [w for w in words if len(w) > 5 and w.isalpha()]
    
    if len(key_terms) < 3:
        key_terms = ["concept", "principle", "method", "theory", "approach"]
    
    questions = []
    for i in range(5):
        term = key_terms[i % len(key_terms)]
        questions.append({
            "question": f"What is the significance of {term} in this context?",
            "options": [
                f"It is a fundamental {term} that underpins the theory.",
                f"It represents an alternative {term} approach.",
                f"It is unrelated to the main {term} discussed.",
                f"It contradicts the established {term} framework."
            ],
            "correct_answer": 0,
            "explanation": f"The term '{term}' is central to understanding the material. It refers to a key concept that forms the foundation of the topic being studied."
        })
    
    return questions


def answer_question(question: str, context: str) -> str:
    """
    Answer a question using the provided context.
    
    Args:
        question: The user's question
        context: The text content to use as context
        
    Returns:
        AI-generated answer
    """
    client = _get_client()
    
    if client and Config.OPENAI_API_KEY:
        try:
            truncated_context = context[:8000] if len(context) > 8000 else context
            
            response = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI tutor. Answer questions based ONLY on the provided study material. If the answer cannot be found in the material, clearly state that you don't have enough information."
                    },
                    {
                        "role": "user",
                        "content": f"Study material:\n\n{truncated_context}\n\nQuestion: {question}"
                    }
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fall through to mock response
    
    # Mock response
    return _generate_mock_answer(question, context)


def _generate_mock_answer(question: str, context: str) -> str:
    """Generate a deterministic mock answer"""
    # Simple keyword matching
    question_lower = question.lower()
    context_lower = context.lower()
    
    # Check if question keywords appear in context
    question_words = set(question_lower.split())
    context_words = set(context_lower.split())
    
    matching_words = question_words & context_words
    
    if len(matching_words) > 2:
        return f"Based on the study material, your question about '{question[:50]}...' relates to concepts found in the text. The material discusses relevant topics that address your query. Please review the sections containing these terms for more details."
    else:
        return "This question may relate to concepts in your study material. I recommend reviewing the uploaded document sections that discuss similar topics. For specific answers, please ensure your question directly references content from the material."
