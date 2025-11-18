from pathlib import Path
import fitz


def extract_text_from_pdf(file_path: Path) -> str:
    try:
        doc = fitz.open(file_path)
        all_pages_text = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            words = page.get_text("words")
            
            if not words:
                continue
            
            page_rect = page.rect
            page_width = page_rect.width
            center_line = page_width / 2
            
            left_column = []
            right_column = []
            
            for word in words:
                x0, y0, x1, y1, text, *_ = word
                
                if x0 < center_line:
                    left_column.append((y0, text))
                else:
                    right_column.append((y0, text))
            
            left_column.sort(key=lambda item: item[0])
            right_column.sort(key=lambda item: item[0])
            
            page_text_parts = []
            
            if left_column:
                left_text = " ".join([word for _, word in left_column])
                page_text_parts.append(left_text)
            
            if right_column:
                right_text = " ".join([word for _, word in right_column])
                page_text_parts.append(right_text)
            
            all_pages_text.append("\n\n".join(page_text_parts))
        
        doc.close()
        
        text = "\n\n".join(all_pages_text)
        
        if not text or text.strip() == "":
            raise ValueError("PDF text extraction failed or file is image-only.")
        
        return text
        
    except Exception as e:
        raise ValueError(f"PDF extraction error: {str(e)}")
