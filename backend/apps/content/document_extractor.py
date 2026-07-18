import os
import io
import re
import uuid
import logging
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

class DocumentExtractor:
    """
    Unified extraction utility supporting:
    - PDF: Text, tables, and images (using PyMuPDF)
    - Word (DOCX): Paragraphs, list items, tables, and images (using python-docx)
    - Excel/CSV: Direct structured row parsing (using pandas)
    """

    def __init__(self):
        # Ensure extracted_images folder exists under settings.MEDIA_ROOT
        self.media_subpath = 'extracted_images'
        self.output_dir = os.path.join(settings.MEDIA_ROOT, self.media_subpath)
        os.makedirs(self.output_dir, exist_ok=True)

    def save_extracted_image(self, image_bytes, extension='png'):
        """Saves image bytes locally and returns the public media URL path."""
        filename = f"img_{uuid.uuid4().hex}.{extension}"
        relative_path = f"{self.media_subpath}/{filename}"
        
        # Save using Django default storage system (handles local or Cloudinary/S3)
        saved_path = default_storage.save(relative_path, ContentFile(image_bytes))
        return default_storage.url(saved_path)

    def extract_pdf(self, file_bytes):
        """
        Extracts pages containing:
        - text: string
        - images: list of image URLs found on page
        - tables: list of HTML tables parsed
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("PyMuPDF is not installed. Failed to parse PDF.")
            raise RuntimeError("PDF extraction engine is not available on this server.")

        pages_data = []
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        for page_idx, page in enumerate(doc):
            page_num = page_idx + 1
            images_found = []
            tables_found = []
            tables_list = []
            table_bboxes = []

            # 1. Extract Images from Page
            try:
                image_list = page.get_images(full=True)
                for img_info in image_list:
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    if base_image:
                        img_bytes = base_image["image"]
                        img_ext = base_image["ext"]
                        img_url = self.save_extracted_image(img_bytes, img_ext)
                        images_found.append(img_url)
            except Exception as e:
                logger.warning(f"Failed to extract images on page {page_num}: {e}")

            # 2. Extract Tables from Page (Requires PyMuPDF >= 1.23.0)
            try:
                tables = page.find_tables()
                for table in tables:
                    table_data = table.extract()
                    if table_data:
                        table_bboxes.append(table.bbox)
                        # Build HTML Table
                        html = '<table class="border-collapse border border-gray-300 my-4 text-xs md:text-sm w-full font-medium">\n'
                        for row_idx, row in enumerate(table_data):
                            html += '  <tr>\n'
                            for cell in row:
                                cell_val = str(cell or '').strip()
                                tag = 'th' if row_idx == 0 else 'td'
                                html += f'    <{tag} class="border border-gray-300 p-2 text-left">{cell_val}</{tag}>\n'
                            html += '  </tr>\n'
                        html += '</table>'
                        tables_found.append(html)
                        # Use top vertical coordinate (y0) for sorting
                        tables_list.append((table.bbox[1], html))
            except Exception as e:
                logger.warning(f"Failed to extract tables on page {page_num}: {e}")

            # Helper function for overlap check
            def rect_overlap(r1, r2):
                return not (r1[2] < r2[0] or r1[0] > r2[2] or r1[3] < r2[1] or r1[1] > r2[3])

            # 3. Extract Text Outside Table Bounding Boxes
            blocks = page.get_text("blocks")
            page_elements = []
            for b in blocks:
                bx0, by0, bx1, by1, btext, block_no, block_type = b
                # Check if block overlaps with any table bbox
                overlaps = False
                for t_bbox in table_bboxes:
                    if rect_overlap((bx0, by0, bx1, by1), t_bbox):
                        overlaps = True
                        break
                if not overlaps:
                    page_elements.append((by0, btext.strip()))

            # Add HTML tables to page elements
            for ty0, html_table in tables_list:
                page_elements.append((ty0, html_table))

            # Sort all elements on page by y0 coordinate (top to bottom)
            page_elements.sort(key=lambda x: x[0])
            text = "\n\n".join([elem[1] for elem in page_elements if elem[1]])

            # 4. Post-Process Page Text: Inject image markers if there were images
            for img_url in images_found:
                # Add image reference tag if not already present
                if f"[IMAGE: {img_url}]" not in text:
                    text += f"\n\n[IMAGE: {img_url}]\n"

            pages_data.append({
                'page_num': page_num,
                'text': text,
                'images': images_found,
                'tables': tables_found
            })

        doc.close()
        return pages_data

    def extract_docx(self, file_bytes):
        """
        Extracts content from DOCX:
        - Groups paragraphs, table data, and images into pages (best-effort page separation by page breaks)
        """
        try:
            import docx
        except ImportError:
            logger.error("python-docx is not installed. Failed to parse DOCX.")
            raise RuntimeError("Word document extraction engine is not available on this server.")

        doc = docx.Document(io.BytesIO(file_bytes))
        pages_data = []
        
        current_page_num = 1
        current_text = ""
        images_found = []
        tables_found = []

        def flush_page():
            nonlocal current_text, images_found, tables_found, current_page_num
            if current_text.strip() or images_found or tables_found:
                pages_data.append({
                    'page_num': current_page_num,
                    'text': current_text,
                    'images': list(images_found),
                    'tables': list(tables_found)
                })
                current_page_num += 1
                current_text = ""
                images_found = []
                tables_found = []

        # Parse inline document images
        doc_images = {}
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                try:
                    img_bytes = rel.target_part.blob
                    # Guess extension
                    ext = rel.target_ref.split('.')[-1] if '.' in rel.target_ref else 'png'
                    if len(ext) > 4: ext = 'png'
                    img_url = self.save_extracted_image(img_bytes, ext)
                    # Rel ID mapping
                    doc_images[rel.rId] = img_url
                except Exception as e:
                    logger.warning(f"Failed to extract DOCX image: {e}")

        # Iterate elements in document body order
        for element in doc.element.body:
            if element.tag.endswith('p'):  # Paragraph
                p = docx.text.paragraph.Paragraph(element, doc)
                p_text = p.text.strip()
                
                # Check for manual page breaks
                if 'w:br' in element.xml and 'type="page"' in element.xml or 'w:lastRenderedPageBreak' in element.xml:
                    flush_page()

                # Find any inline XML drawing / graphic / image relations
                rIds = re.findall(r'r:embed="([^"]+)"', element.xml)
                for rId in rIds:
                    if rId in doc_images:
                        img_url = doc_images[rId]
                        images_found.append(img_url)
                        current_text += f"\n[IMAGE: {img_url}]\n"

                if p_text:
                    # Detect list items
                    if p.style.name.startswith('List'):
                        current_text += f"\n- {p_text}"
                    else:
                        current_text += f"\n{p_text}"

            elif element.tag.endswith('tbl'):  # Table
                t = docx.table.Table(element, doc)
                html = '<table class="border-collapse border border-gray-300 my-4 text-xs md:text-sm w-full font-medium">\n'
                for row_idx, row in enumerate(t.rows):
                    html += '  <tr>\n'
                    for cell in row.cells:
                        tag = 'th' if row_idx == 0 else 'td'
                        html += f'    <{tag} class="border border-gray-300 p-2 text-left">{cell.text.strip()}</{tag}>\n'
                    html += '  </tr>\n'
                html += '</table>'
                tables_found.append(html)
                current_text += f"\n\n{html}\n\n"

        # Final flush
        flush_page()
        return pages_data

    def extract_csv_or_excel(self, file_bytes, is_excel=False):
        """
        Parses structured questions from CSV/Excel sheets directly.
        Returns a list of normalized question dictionaries ready to review.
        """
        try:
            import pandas as pd
        except ImportError:
            logger.error("pandas is not installed. Failed to parse CSV/Excel.")
            raise RuntimeError("Spreadsheet parser engine is not available on this server.")

        file_obj = io.BytesIO(file_bytes)
        if is_excel:
            df = pd.read_excel(file_obj)
        else:
            df = pd.read_csv(file_obj)

        df.columns = [str(c).strip().lower() for c in df.columns]
        questions = []

        for idx, row in df.iterrows():
            text = str(row.get('text', '')).strip()
            if not text or text.lower() == 'nan':
                continue

            q_type = str(row.get('question_type', row.get('type', 'mcq'))).strip().lower()
            if q_type not in ('mcq', 'multi_select', 'true_false', 'fill_blank', 'short_answer', 'essay', 'matching', 'ordering'):
                q_type = 'mcq'

            difficulty = str(row.get('difficulty', 'medium')).strip().lower()
            if difficulty not in ('easy', 'medium', 'hard'):
                difficulty = 'medium'

            explanation = str(row.get('explanation', '')).strip()
            if explanation.lower() == 'nan':
                explanation = ''

            try:
                points = float(row.get('points', row.get('marks', 5.0)))
            except (ValueError, TypeError):
                points = 5.0

            options = []
            
            # Match options columns: option_1, option_1_correct, option_2, option_2_correct, etc.
            # Or option_a, option_b, etc.
            option_cols = [c for c in df.columns if c.startswith('option_') and not c.endswith('_correct') and not c.endswith('_match')]
            
            for o_idx, col in enumerate(sorted(option_cols)):
                opt_text = str(row.get(col, '')).strip()
                if not opt_text or opt_text.lower() == 'nan':
                    continue

                # Check correctness
                correct_col = f"{col}_correct"
                is_correct = False
                if correct_col in df.columns:
                    val = str(row.get(correct_col, '')).strip().lower()
                    is_correct = val in ('true', '1', 'yes', 'correct', 'y')

                # Check matching pair
                match_col = f"{col}_match"
                match_pair = ''
                if match_col in df.columns:
                    match_pair = str(row.get(match_col, '')).strip()
                    if match_pair.lower() == 'nan':
                        match_pair = ''

                options.append({
                    'text': opt_text,
                    'is_correct': is_correct,
                    'order': o_idx + 1,
                    'match_pair': match_pair
                })

            # If True/False and options are empty, initialize them
            if q_type == 'true_false' and not options:
                # Guess correct from 'correct_answer' column
                correct_ans = str(row.get('correct_answer', '')).strip().lower()
                options = [
                    {'text': 'True', 'is_correct': correct_ans in ('true', '1', 'yes', 't'), 'order': 1},
                    {'text': 'False', 'is_correct': correct_ans in ('false', '0', 'no', 'f'), 'order': 2}
                ]
            # If MCQ/Multi-select/Fill-blank/Short-answer with a correct_answer column but no explicit option correct marks
            elif q_type in ('mcq', 'fill_blank', 'short_answer') and options:
                correct_ans = str(row.get('correct_answer', '')).strip().lower()
                if correct_ans and correct_ans != 'nan':
                    has_correct = any(o['is_correct'] for o in options)
                    if not has_correct:
                        for opt in options:
                            if opt['text'].strip().lower() == correct_ans:
                                opt['is_correct'] = True

            questions.append({
                'text': text,
                'question_type': q_type,
                'difficulty': difficulty,
                'explanation': explanation,
                'points': points,
                'options': options,
                'metadata': {'row_num': idx + 1}
            })

        return questions
