import PyPDF2
from io import BytesIO


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        file_bytes: The PDF file as bytes
        
    Returns:
        Extracted text content
    """
    try:
        pdf_file = BytesIO(file_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        
        text_content = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
        
        return "\n\n".join(text_content)
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def truncate_text(text: str, max_length: int = 4000) -> str:
    """
    Truncate text to a maximum length while trying to preserve context.
    
    Args:
        text: The text to truncate
        max_length: Maximum number of characters
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Try to cut at a sentence boundary
    truncated = text[:max_length]
    last_period = truncated.rfind('.')
    
    if last_period > max_length * 0.8:  # If there's a period in the last 20%
        return truncated[:last_period + 1]
    
    return truncated + "..."
