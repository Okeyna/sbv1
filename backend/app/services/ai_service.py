"""AI Service for generating summaries, quizzes, and answers"""
import os
import json
from typing import Optional, Dict, Any

# Mock data for when OpenAI is not configured
MOCK_SUMMARY = """• Key concept 1: Main idea from the material
• Key concept 2: Important detail to remember  
• Key concept 3: Critical takeaway
• Key concept 4: Supporting evidence
• Key concept 5: Practical application"""

MOCK_QUIZ = {
    "questions": [
        {
            "question": "What is the main topic discussed in this material?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "explanation": "This is the correct answer based on the main theme."
        },
        {
            "question": "Which concept is emphasized as most important?",
            "options": ["Concept X", "Concept Y", "Concept Z", "Concept W"],
            "correct_answer": 1,
            "explanation": "The material highlights this as a key point."
        },
        {
            "question": "What is the primary application of this knowledge?",
            "options": ["Application 1", "Application 2", "Application 3", "Application 4"],
            "correct_answer": 2,
            "explanation": "This is the main practical use case mentioned."
        },
        {
            "question": "Which term best describes the core principle?",
            "options": ["Term A", "Term B", "Term C", "Term D"],
            "correct_answer": 3,
            "explanation": "This term captures the essence of the principle."
        },
        {
            "question": "What conclusion can be drawn from the material?",
            "options": ["Conclusion 1", "Conclusion 2", "Conclusion 3", "Conclusion 4"],
            "correct_answer": 0,
            "explanation": "This follows logically from the presented information."
        }
    ]
}

def get_openai_client():
    """Get OpenAI client if configured"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except ImportError:
        return None

def truncate_text(text: str, max_tokens: int = 4000) -> str:
    """Truncate text to fit within token limit"""
    # Rough estimate: 1 token ≈ 4 characters
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."

def generate_summary(text: str) -> str:
    """Generate a summary of the text"""
    client = get_openai_client()
    
    if not client:
        return MOCK_SUMMARY
    
    try:
        truncated = truncate_text(text)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "Summarize this study material into 5 concise bullet points for learning."},
                {"role": "user", "content": truncated}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return MOCK_SUMMARY

def generate_quiz(text: str) -> Dict[str, Any]:
    """Generate a quiz from the text"""
    client = get_openai_client()
    
    if not client:
        return MOCK_QUIZ
    
    try:
        truncated = truncate_text(text)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "Generate exactly 5 multiple-choice questions based on this material. Return valid JSON with format: {\"questions\": [{\"question\": \"...\", \"options\": [\"A\", \"B\", \"C\", \"D\"], \"correct_answer\": 0-3, \"explanation\": \"...\"}]}"},
                {"role": "user", "content": truncated}
            ],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("questions", MOCK_QUIZ["questions"])
    except Exception:
        return MOCK_QUIZ

def answer_question(context: str, question: str) -> str:
    """Answer a question based on the context"""
    client = get_openai_client()
    
    if not client:
        return f"Based on the study material, here's what I found about your question: This is a mock response since no OpenAI API key is configured. In production, I would analyze the uploaded content and provide a specific answer to: '{question}'"
    
    try:
        truncated = truncate_text(context)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a helpful AI tutor. Answer questions based only on the provided study material. If the answer is not in the material, say so clearly."},
                {"role": "user", "content": f"Context: {truncated}\n\nQuestion: {question}"}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return f"I encountered an error processing your question. Please try again."
