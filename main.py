import fitz  # PyMuPDF
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.colors import HexColor
import google.generativeai as genai
import os

# ================== CONFIGURE GEMINI API ==================
genai.configure(api_key="AIzaSyAnnB65Tw32lOcYPA5_A_HNljjl6Gvr88s")
model = genai.GenerativeModel(model_name="gemini-2.0-flash-001")

# ================== ENHANCED STYLE CONFIGURATION ==================
styles = getSampleStyleSheet()

# Heading Styles
styles.add(ParagraphStyle(
    name='TitleStyle',
    fontName='Helvetica-Bold',
    fontSize=20,
    leading=24,
    spaceAfter=18,
    textColor=HexColor('#2c3e50'),
    alignment=TA_LEFT
))

styles.add(ParagraphStyle(
    name='HeadingStyle',
    fontName='Helvetica-Bold',
    fontSize=16,
    leading=20,
    spaceAfter=12,
    textColor=HexColor('#2980b9'),
    alignment=TA_LEFT
))

styles.add(ParagraphStyle(
    name='SubheadingStyle',
    fontName='Helvetica-Bold',
    fontSize=14,
    leading=18,
    spaceAfter=10,
    textColor=HexColor('#34495e'),
    alignment=TA_LEFT
))

# Content Styles
styles.add(ParagraphStyle(
    name='BodyStyle',
    fontSize=12,
    leading=16,
    leftIndent=10,
    spaceAfter=8,
    fontName='Helvetica'
))

styles.add(ParagraphStyle(
    name='BulletStyle',
    leftIndent=25,
    bulletIndent=15,
    fontSize=12,
    leading=16,
    spaceAfter=6,
    fontName='Helvetica'
))

styles.add(ParagraphStyle(
    name='ExampleStyle',
    backColor=HexColor('#f8f9fa'),
    borderPadding=10,
    fontSize=12,
    leading=16,
    spaceBefore=8,
    spaceAfter=12,
    leftIndent=15
))

# ================== IMPROVED CONTENT PROCESSING ==================
def extract_text_from_pdf(pdf_path):
    """Extract structured text from PDF with layout awareness."""
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        blocks = page.get_text("blocks")
        clean_blocks = [b[4] for b in blocks if b[6] == 0]
        pages.append("\n".join(clean_blocks))
    return pages

def elaborate_content_with_gemini(text):
    """
    Get structured content with enhanced formatting instructions using Gemini API.
    In case of an error, log it and return the original text.
    """
    system_prompt = """Structure your response EXACTLY like this:

## MAIN TITLE
## [Main Heading Here]

### [Subheading 1]
• Bullet points for key ideas
• Use * for bullets
• Keep explanations concise

<example>
[Relevant example here]
</example>

### [Subheading 2]
..."""
    
    prompt = f"{system_prompt}\n\nContent to elaborate:\n{text}"
    try:
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        else:
            print("Gemini API returned an empty response; using original text.")
            return text
    except Exception as e:
        print(f"Gemini Error: {e}")
        print("Falling back to original content.")
        return text

def process_content_blocks(content):
    """
    Parse the elaborated content to create a hierarchical structure based on markers.
    """
    hierarchy = []
    current_level = 0
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('## '):
            hierarchy.append(('title', line[3:].strip()))
            current_level = 1
        elif line.startswith('### '):
            hierarchy.append(('subheading', line[4:].strip()))
            current_level = 2
        elif line.startswith('* '):
            hierarchy.append(('bullet', line[2:].strip()))
        elif '<example>' in line:
            example = line.replace('<example>', '').replace('</example>', '').strip()
            hierarchy.append(('example', example))
        else:
            if current_level == 1:
                hierarchy.append(('heading', line.strip()))
            else:
                hierarchy.append(('body', line.strip()))
                
    return hierarchy

def draw_structured_content(c, content, margin, page_height):
    """Render the structured content using ReportLab and custom styles."""
    y_position = page_height - margin
    parsed_content = process_content_blocks(content)
    
    for element_type, text in parsed_content:
        if element_type == 'title':
            style = styles['TitleStyle']
        elif element_type == 'heading':
            style = styles['HeadingStyle']
        elif element_type == 'subheading':
            style = styles['SubheadingStyle']
        elif element_type == 'bullet':
            style = styles['BulletStyle']
            text = f"• {text}"
        elif element_type == 'example':
            style = styles['ExampleStyle']
        else:
            style = styles['BodyStyle']
        
        para = Paragraph(text, style)
        available_width = c._pagesize[0] - 2 * margin
        w, h = para.wrap(available_width, c._pagesize[1])
        
        if y_position - h < margin:
            c.showPage()
            y_position = page_height - margin
        
        para.drawOn(c, margin, y_position - h)
        y_position -= h + style.spaceAfter
        
        if element_type == 'title':
            y_position -= 15

def create_enhanced_pdf(output_path, elaborated_contents):
    """Generate a structured PDF document in landscape mode."""
    page_size = landscape(letter)
    c = canvas.Canvas(output_path, pagesize=page_size)
    margin = 45
    
    for content in elaborated_contents:
        draw_structured_content(c, content, margin, page_size[1])
        c.showPage()
    
    c.save()

def process_pdf(input_path, output_path):
    """
    Full processing pipeline:
    - Extract text from input PDF.
    - Generate enhanced elaboration with Gemini.
    - Export structured landscape-mode PDF.
    """
    original_contents = extract_text_from_pdf(input_path)
    elaborated_contents = []
    
    for page_text in original_contents:
        print("Generating enriched content with Gemini...")
        enhanced_content = elaborate_content_with_gemini(page_text)
        elaborated_contents.append(enhanced_content)
    
    create_enhanced_pdf(output_path, elaborated_contents)
    return output_path

# ================== ENTRY POINT ==================
if __name__ == "__main__":
    input_pdf = "ch4 - Thread.pdf"
    output_pdf = "g3enhanced_document.pdf"
    result_path = process_pdf(input_pdf, output_pdf)
    print(f"Styled PDF saved: {result_path}")

# ================== LIST AVAILABLE MODELS (Optional) ==================
for m in genai.list_models():
    print(f"{m.name} -> {m.supported_generation_methods}")
