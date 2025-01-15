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
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

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

def markdown_to_html(text):
    """Enhanced markdown to HTML conversion for better formatting"""
    if not text:
        return ""
    
    # Normalize line endings
    text = text.replace('\r\n', '\n')
    
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    processed_paragraphs = []
    
    for para in paragraphs:
        # Skip empty paragraphs
        if not para.strip():
            continue
            
        # Check if this paragraph is a list
        lines = para.split('\n')
        is_list = all(line.strip().startswith('- ') for line in lines if line.strip())
        
        if is_list:
            # Handle bullet list
            list_items = []
            for line in lines:
                if line.strip():
                    # Remove the bullet point and create a proper list item
                    content = line.strip()[2:]  # Remove '- ' from start
                    # Convert any inline formatting
                    content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
                    content = re.sub(r'\*(.*?)\*', r'<i>\1</i>', content)
                    list_items.append(f'<li>{content}</li>')
            
            # Join list items with proper list formatting
            processed_para = '<ul>' + ''.join(list_items) + '</ul>'
        else:
            # Handle regular paragraph
            # Convert headers
            if para.strip().startswith('# '):
                processed_para = f"<h1>{para.strip()[2:]}</h1>"
            elif para.strip().startswith('## '):
                processed_para = f"<h2>{para.strip()[3:]}</h2>"
            elif para.strip().startswith('### '):
                processed_para = f"<h3>{para.strip()[4:]}</h3>"
            else:
                # Convert bold and italic
                para = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', para)
                para = re.sub(r'\*(.*?)\*', r'<i>\1</i>', para)
                # Preserve line breaks within paragraphs
                para = re.sub(r'([^\n])\n([^\n])', r'\1<br/>\2', para)
                processed_para = f"<p>{para}</p>"
        
        if processed_para:  # Only append if we have content
            processed_paragraphs.append(processed_para)
    
    # Join all processed paragraphs
    return '\n'.join(processed_paragraphs)

def generate_analysis_pdf(state: "AgentState", output_dir="Reports"):
    """
    Generate a PDF containing all analyses from the state.
    First generates a markdown file, then converts it to PDF.
    """
    # First generate the markdown file
    markdown_path = generate_markdown_report(state, output_dir)
    
    # Then convert it to PDF
    pdf_path = markdown_to_pdf(markdown_path, output_dir)
    
    return pdf_path

def generate_markdown_report(state: AgentState, output_dir="Reports") -> str:
    """
    Generate a markdown report from the agent state and save it to a file.
    Returns the path to the generated markdown file.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert AgentState to dict if needed
    state_dict = state if isinstance(state, dict) else state.model_dump()
    
    # Generate filename with date and topic
    date_str = datetime.strptime(state_dict['today'], "%Y-%m-%d").strftime("%Y%m%d")
    topic_safe = sanitize_filename(state_dict['topic'])
    filename = f"{date_str}_{topic_safe}.md"
    output_path = os.path.join(output_dir, filename)
    
    # If file exists, add a counter
    counter = 1
    base_path = output_path[:-3]  # Remove .md
    while os.path.exists(output_path):
        output_path = f"{base_path}_{counter}.md"
        counter += 1

    # Build the markdown content
    markdown_content = []
    
    # Title and date
    markdown_content.append("# Comprehensive Analysis Report")
    markdown_content.append(f"Generated on: {state_dict['today']}\n")
    
    # Topic
    markdown_content.append("# Topic of Analysis")
    markdown_content.append(state_dict['topic'] + "\n")

    # 1. Executive Summary
    markdown_content.append("# 1. Executive Summary")
    markdown_content.append(state_dict.get('final_analysis', '') + "\n")

    # 2. Impact Analyses
    markdown_content.append("# 2. Impact Analyses")
    
    markdown_content.append("## 2.1 Economic Impact Analysis")
    markdown_content.append(state_dict.get('economic_impact_analysis', '') + "\n")
    
    markdown_content.append("## 2.2 Humanitarian Impact Analysis")
    markdown_content.append(state_dict.get('humanitarian_impact_analysis', '') + "\n")

    # 3. Background Information
    markdown_content.append("# 3. Background Information")
    if isinstance(state_dict.get('background'), list):
        background_text = "\n\n".join(state_dict['background'])
    else:
        background_text = str(state_dict.get('background', ''))
    markdown_content.append(background_text + "\n")

    # 4. Mathematical and Systems Analyses
    markdown_content.append("# 4. Mathematical and Systems Analyses")
    
    markdown_content.append("## 4.1 Complex Systems Analysis")
    markdown_content.append(state_dict.get('complex_system_analysis', '') + "\n")
    
    markdown_content.append("## 4.2 Quantum Analysis")
    markdown_content.append(state_dict.get('quantum_analysis', '') + "\n")
    
    markdown_content.append("## 4.3 Entropy Analysis")
    markdown_content.append(state_dict.get('entropy_analysis', '') + "\n")
    
    markdown_content.append("## 4.4 Recursive Exploration Analysis")
    markdown_content.append(state_dict.get('recursive_exploration_analysis', '') + "\n")
    
    markdown_content.append("## 4.5 Dimensional Trascendence Analysis")
    markdown_content.append(state_dict.get('dimensional_trascendence_analysis', '') + "\n")
    
    markdown_content.append("## 4.6 Actor Mapping Analysis")
    markdown_content.append(state_dict.get('actor_mapping_analysis', '') + "\n")

    # Annex
    markdown_content.append("# Annex: News and Current Events")
    markdown_content.append("This section contains relevant news articles and current events related to the analysis.\n")
    if isinstance(state_dict.get('news'), list):
        news_text = "\n\n".join(state_dict['news'])
    else:
        news_text = str(state_dict.get('news', ''))
    markdown_content.append(news_text)

    # Write the markdown content to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_content))
    
    return output_path

def markdown_to_pdf(markdown_path: str, output_dir="Reports") -> str:
    """
    Convert a markdown file to PDF using markdown -> HTML -> PDF pipeline.
    Returns the path to the generated PDF file.
    """
    # Read markdown content
    with open(markdown_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=['extra', 'smarty', 'tables']  # Add more extensions as needed
    )
    
    # Add CSS styling
    css = CSS(string='''
        @page {
            margin: 1in;
            size: A4;
            @top-right {
                content: counter(page);
            }
        }
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 100%;
            margin: 0;
            padding: 0;
        }
        h1 {
            font-size: 24px;
            color: #2c3e50;
            margin-top: 2em;
            margin-bottom: 1em;
            page-break-before: always;
        }
        h1:first-of-type {
            page-break-before: avoid;
        }
        h2 {
            font-size: 20px;
            color: #34495e;
            margin-top: 1.5em;
            margin-bottom: 0.8em;
        }
        p {
            margin-bottom: 1em;
            text-align: justify;
        }
        ul, ol {
            margin-bottom: 1em;
            padding-left: 2em;
        }
        li {
            margin-bottom: 0.5em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1em;
        }
        th, td {
            padding: 8px;
            border: 1px solid #ddd;
            text-align: left;
        }
        th {
            background-color: #f5f5f5;
        }
        blockquote {
            margin: 1em 0;
            padding-left: 1em;
            border-left: 4px solid #ddd;
            color: #666;
        }
        code {
            font-family: monospace;
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
        }
        pre {
            background-color: #f5f5f5;
            padding: 1em;
            border-radius: 3px;
            overflow-x: auto;
        }
    ''')

    # Wrap HTML content in a proper document structure
    full_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body>
        {html_content}
    </body>
    </html>
    '''
    
    # Generate PDF filename
    pdf_path = os.path.splitext(markdown_path)[0] + '.pdf'
    
    # Configure fonts
    font_config = FontConfiguration()
    
    # Convert HTML to PDF
    HTML(string=full_html).write_pdf(
        pdf_path,
        stylesheets=[css],
        font_config=font_config
    )
    
    return pdf_path
