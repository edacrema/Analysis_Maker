import os
from datetime import datetime
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from nodes import AgentState
import markdown

def sanitize_filename(filename):
    """
    Convert a string into a valid filename by removing or replacing invalid characters.
    """
    # Remove or replace invalid filename characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple spaces and underscores
    filename = re.sub(r'[\s_]+', '_', filename)
    # Limit length and trim
    return filename.strip('_')[:100]

def markdown_to_reportlab(text, style):
    """Convert markdown text to reportlab paragraphs"""
    if not text:
        return []
    
    paragraphs = []
    lines = text.split('\n')
    current_paragraph = []
    
    for line in lines:
        if line.strip():
            # Handle headers
            if line.startswith('# '):
                if current_paragraph:
                    paragraphs.append(Paragraph(''.join(current_paragraph), style['Normal']))
                    current_paragraph = []
                paragraphs.append(Paragraph(line[2:], style['Heading1']))
            elif line.startswith('## '):
                if current_paragraph:
                    paragraphs.append(Paragraph(''.join(current_paragraph), style['Normal']))
                    current_paragraph = []
                paragraphs.append(Paragraph(line[3:], style['Heading2']))
            elif line.startswith('### '):
                if current_paragraph:
                    paragraphs.append(Paragraph(''.join(current_paragraph), style['Normal']))
                    current_paragraph = []
                paragraphs.append(Paragraph(line[4:], style['Heading3']))
            # Handle bullet points
            elif line.strip().startswith('- '):
                if current_paragraph:
                    paragraphs.append(Paragraph(''.join(current_paragraph), style['Normal']))
                    current_paragraph = []
                paragraphs.append(Paragraph('• ' + line[2:], style['Bullet']))
            else:
                current_paragraph.append(line + ' ')
        else:
            if current_paragraph:
                paragraphs.append(Paragraph(''.join(current_paragraph), style['Normal']))
                current_paragraph = []
                paragraphs.append(Spacer(1, 12))
    
    if current_paragraph:
        paragraphs.append(Paragraph(''.join(current_paragraph), style['Normal']))
    
    return paragraphs

def generate_analysis_pdf(state: "AgentState", output_dir="Reports"):
    """Generate a PDF containing all analyses from the state."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert AgentState to dict if needed
    state_dict = state if isinstance(state, dict) else state.model_dump()
    
    # Generate filename
    date_str = datetime.strptime(state_dict['today'], "%Y-%m-%d").strftime("%Y%m%d")
    topic_safe = sanitize_filename(state_dict['topic'])
    filename = f"{date_str}_{topic_safe}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    # If file exists, add a counter
    counter = 1
    base_path = output_path[:-4]  # Remove .pdf
    while os.path.exists(output_path):
        output_path = f"{base_path}_{counter}.pdf"
        counter += 1

    # Create the PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Get styles
    styles = getSampleStyleSheet()
    
    # Only add the Bullet style if it doesn't exist
    if 'Bullet' not in styles:
        styles.add(ParagraphStyle(
            name='Bullet',
            parent=styles['Normal'],
            leftIndent=20,
            spaceAfter=5
        ))

    # Build the content
    content = []
    
    # Title
    content.append(Paragraph("Comprehensive Analysis Report", styles['Title']))
    content.append(Spacer(1, 12))
    content.append(Paragraph(f"Generated on: {state_dict['today']}", styles['Normal']))
    content.append(Spacer(1, 24))
    
    # Topic
    content.append(Paragraph("Topic of Analysis", styles['Heading1']))
    content.append(Paragraph(state_dict['topic'], styles['Normal']))
    content.append(Spacer(1, 24))

    # 1. Executive Summary
    content.append(Paragraph("1. Executive Summary", styles['Heading1']))
    content.extend(markdown_to_reportlab(state_dict.get('final_analysis', ''), styles))
    content.append(Spacer(1, 24))

    # 2. Impact Analysis
    content.append(Paragraph("2. Impact Analysis", styles['Heading1']))
    content.append(Paragraph("2.1 Humanitarian Impact Analysis", styles['Heading2']))
    content.extend(markdown_to_reportlab(state_dict.get('humanitarian_impact_analysis', ''), styles))
    content.append(Spacer(1, 24))

    # 3. Background Information
    content.append(Paragraph("3. Background Information", styles['Heading1']))
    if isinstance(state_dict.get('background'), list):
        background_text = "\n\n".join(state_dict['background'])
    else:
        background_text = str(state_dict.get('background', ''))
    content.extend(markdown_to_reportlab(background_text, styles))
    content.append(Spacer(1, 24))

    # 4. Systems and Strategic Analyses
    content.append(Paragraph("4. Systems and Strategic Analyses", styles['Heading1']))
    
    content.append(Paragraph("4.1 Complex Systems Analysis", styles['Heading2']))
    content.extend(markdown_to_reportlab(state_dict.get('complex_system_analysis', ''), styles))
    content.append(Spacer(1, 12))
    
    content.append(Paragraph("4.2 Entropy Analysis", styles['Heading2']))
    content.extend(markdown_to_reportlab(state_dict.get('entropy_analysis', ''), styles))
    content.append(Spacer(1, 12))
    
    content.append(Paragraph("4.3 Actor Mapping Analysis", styles['Heading2']))
    content.extend(markdown_to_reportlab(state_dict.get('actor_mapping_analysis', ''), styles))
    content.append(Spacer(1, 12))
    
    content.append(Paragraph("4.4 Game Theory Analysis", styles['Heading2']))
    content.extend(markdown_to_reportlab(state_dict.get('game_theory_analysis', ''), styles))
    content.append(Spacer(1, 24))

    # Annex
    content.append(Paragraph("Annex: News and Current Events", styles['Heading1']))
    content.append(Paragraph("This section contains relevant news articles and current events related to the analysis.", styles['Normal']))
    content.append(Spacer(1, 12))
    if isinstance(state_dict.get('news'), list):
        news_text = "\n\n".join(state_dict['news'])
    else:
        news_text = str(state_dict.get('news', ''))
    content.extend(markdown_to_reportlab(news_text, styles))

    # Build the PDF
    doc.build(content)
    
    return output_path
