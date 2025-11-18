from pathlib import Path
from docx import Document


def extract_text_from_docx(file_path: Path) -> str:
    try:
        document = Document(str(file_path))
        text_parts = []
        
        for paragraph in document.paragraphs:
            if not paragraph.text.strip():
                continue
            
            style_name = paragraph.style.name.lower()
            
            if "heading" in style_name:
                text_parts.append(f"\n## {paragraph.text.strip()} ##\n")
            else:
                text_parts.append(paragraph.text.strip())
        
        text = "\n".join(text_parts)
        
        if not text or text.strip() == "":
            raise ValueError("DOCX text extraction failed.")
        
        return text
        
    except Exception as e:
        raise ValueError(f"DOCX extraction error: {str(e)}")
