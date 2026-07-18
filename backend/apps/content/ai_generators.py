"""
AI-powered question generation service for HomePackage.

Supports multiple AI providers (OpenAI, Google Gemini, Anthropic Claude) via raw
HTTP requests.  Falls back to a rich template-based generator when no API keys are
configured or when all providers fail.
"""

import json
import logging
import random
import re
import hashlib

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider name labels (used in response messages)
# ---------------------------------------------------------------------------
PROVIDER_LABELS = {
    'openai': 'OpenAI',
    'gemini': 'Gemini',
    'claude': 'Claude',
    'auto': 'Auto',
    'fallback': 'Template',
}


class AIQuestionGenerator:
    """Multi-provider AI question generator.

    Usage::

        gen = AIQuestionGenerator(provider='auto')
        questions = gen.generate(
            subject_name='Mathematics',
            topic_name='Algebra',
            question_types=['mcq', 'true_false'],
            difficulty='medium',
            count=5,
            custom_prompt='Focus on quadratic equations',
        )
        # questions -> list[dict]  each dict matches the Question model schema
    """

    PROVIDERS = {
        'openai': '_generate_openai',
        'gemini': '_generate_gemini',
        'claude': '_generate_claude',
        'auto': '_generate_auto',
    }

    def __init__(self, provider='auto'):
        self.provider = provider if provider in self.PROVIDERS else 'auto'
        self.used_provider = 'fallback'

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, subject_name, topic_name, question_types, difficulty,
                 count, custom_prompt=''):
        """Generate *count* questions and return a list of question dicts.

        Each dict has keys: text, question_type, difficulty, explanation,
        points, options (list of {text, is_correct, order}).
        """
        count = max(1, min(count, 50))  # clamp

        system_prompt, user_prompt = self._build_prompt(
            subject_name, topic_name, question_types, difficulty, count,
            custom_prompt,
        )

        method_name = self.PROVIDERS.get(self.provider, '_generate_auto')
        method = getattr(self, method_name)

        try:
            questions = method(system_prompt, user_prompt, count)
            if questions and isinstance(questions, list) and len(questions) > 0:
                return self._normalise(questions, question_types, difficulty, count)
        except Exception:
            logger.exception('AI generation failed for provider=%s', self.provider)

        # Ultimate fallback – template-based generation always works
        logger.info('Falling back to template-based question generation.')
        self.used_provider = 'fallback'
        return self._generate_fallback(
            subject_name, topic_name, question_types, difficulty, count,
        )

    def convert_pdf_text(self, pdf_text, subject_name, topic_name=None):
        """Convert extracted PDF/Word text into structured questions."""
        system_prompt = (
            "You are an expert educational content parser. Your job is to extract questions from "
            "the provided raw text of an assessment worksheet/PDF, and convert them into structured JSON. "
            "You must ensure the converted questions look EXACTLY the same as they did in the PDF format.\n\n"
            "CRITICAL RULES:\n"
            "1. IGNORE NON-QUESTION CONTENT: Do not extract document headers, title blocks, candidate metadata lines (e.g. name, date, index number), "
            "instructions to candidates, marks distributions tables, page numbers, or footers. Exclude these completely from your JSON output. "
            "Note: Some instructions may be numbered (e.g., '1. Remember to write your three names properly.', '2. Answer all questions.', '3. Read questions carefully.'). "
            "Do NOT extract these numbered lines as questions. Also ignore candidate details like 'NAME: ________________ CLASS: ________' and section headers "
            "like 'SECTION A: MATHEMATICAL OPERATIONS (20 MARKS)'.\n"
            "2. PRESERVE ORIGINAL FORMATTING: Do not simplify or split complex questions. If a question has sub-parts "
            "(e.g., (a), (b), (i), (ii)), has multi-line layouts, custom tables, or specialized formatting, keep them "
            "exactly as they appear in the PDF. Put the entire layout inside the 'text' field.\n"
            "3. RENDER LAYOUT: In the 'text' field, preserve the original spacing, indentation, and newlines exactly. "
            "You can use raw newlines or simple HTML tags (such as <br>, <strong>, <u>, <ol>, <ul>, <li>, <table>) "
            "to make it match the original PDF layout perfectly.\n"
            "4. QUESTION TYPES: If a question is multiple-choice with options A, B, C, D, classify it as 'mcq' and populate the options list. "
            "If it is a free-form question, has sub-questions, or does not fit a simple question type, classify it as 'essay' so that the "
            "student has a clean written answer box to respond to the entire question layout.\n"
            "5. Return ONLY a valid JSON array – no markdown code block backticks (like ```json), no commentary.\n"
            "6. Each element must have keys: text, question_type, difficulty, explanation, points, options.\n"
            "7. Set points to 5.0 for all questions.\n"
            "8. ILLUSTRATIONS & DIAGRAMS: The text may contain image references like '[IMAGE: /media/extracted_images/xyz.png]' or page-level graphics like '[Page N Illustrations: Image A: /media/extracted_images/abc.png]'. If a question refers to or requires an image, graph, diagram, or illustration, you MUST insert a standard HTML image tag: <img src=\"/media/extracted_images/xyz.png\" class=\"my-4 max-w-full rounded-xl shadow-sm block\" /> inside the 'text' field of the question at the exact position it belongs.\n"
            "9. DO NOT TRUNCATE QUESTIONS: Make sure every question is fully captured. Do not omit any sub-parts, equations, trailing instructions (like 'Explain your choice'), or details. Ensure the question text makes complete sense on its own.\n"


        )
        
        user_prompt = (
            f"Here is the raw text extracted from the \"{subject_name}\" assessment PDF:\n\n"
            "--- START OF TEXT ---\n"
            f"{pdf_text}\n"
            "--- END OF TEXT ---\n\n"
            "Extract ONLY the actual questions from the text above. Ignore all non-question elements such as exam header details, "
            "instructions to candidates, and index number/name blocks. Match the original spacing and subparts "
            "exactly for the question text. Return them as a JSON array matching this schema:\n"
            "[\n"
            "  {\n"
            "    \"text\": \"Question text block matching PDF layout\",\n"
            "    \"question_type\": \"mcq\",\n"
            "    \"difficulty\": \"medium\",\n"
            "    \"explanation\": \"\",\n"
            "    \"points\": 5.0,\n"
            "    \"options\": [\n"
            "      {\"text\": \"Option A\", \"is_correct\": true, \"order\": 1},\n"
            "      {\"text\": \"Option B\", \"is_correct\": false, \"order\": 2}\n"
            "    ]\n"
            "  }\n"
            "]"
        )

        method_name = self.PROVIDERS.get(self.provider, '_generate_auto')
        method = getattr(self, method_name)

        try:
            questions = method(system_prompt, user_prompt, count=25)
            if questions and isinstance(questions, list) and len(questions) > 0:
                return self._normalise(questions, None, 'medium', len(questions))
        except Exception:
            logger.exception('AI PDF conversion failed for provider=%s', self.provider)

        # Fallback if AI fails or is not configured: parse text heuristically using regex patterns
        logger.info('Falling back to heuristic document text parser.')
        self.used_provider = 'fallback'
        parsed = self._parse_heuristically(pdf_text)
        if parsed:
            return parsed

        return self._generate_fallback(subject_name, topic_name or '', ['mcq'], 'medium', 5)

    def _parse_heuristically(self, text):
        """Fallback heuristic parser to extract questions from raw text when AI is unavailable."""
        import re
        questions = []
        
        # 1. Pre-parse PDF page illustrations mappings
        # Map of {(page_num, label): url}
        illustrations = {}
        ill_pattern = re.compile(r'\[Page\s*(\d+)\s*Illustrations:\s*([^\]]+)\]', re.I)
        for match in ill_pattern.finditer(text):
            page_num = int(match.group(1))
            ill_str = match.group(2)
            parts = [p.strip() for p in ill_str.split(',') if ':' in p]
            for part in parts:
                key_val = part.split(':', 1)
                img_label = key_val[0].strip().replace('Image ', '').replace('image ', '').strip().upper()
                img_url = key_val[1].strip()
                illustrations[(page_num, img_label)] = img_url

        # 1b. Pre-process mid-line questions (e.g. side-by-side columns)
        # In worksheets, questions might be extracted horizontally like: "1. 3+2=  2. 5+4="
        # We split them onto separate lines so the line-by-line parser handles them correctly.
        processed_text = []
        for raw_line in text.split('\n'):
            line_processed = raw_line
            # Loop re.sub to handle consecutive/overlapping column number matches (e.g. "9. 47.")
            # We match only dot separators to avoid matching parentheses in math expressions like "(36 + 64)"
            while True:
                new_line = re.sub(r'(?<=\S)[^\S\n]+(\d+)\.\s+(?!\d+\.\s+)', r'\n\1. ', line_processed)
                if new_line == line_processed:
                    break
                line_processed = new_line
            processed_text.append(line_processed)
        text = '\n'.join(processed_text)

        # Split text into lines and clean
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        current_question = None
        current_page_num = 1
        expected_q_num = 1
        
        # Matches patterns like: "1. ", "2) ", "Q3: ", "Question 4: "
        q_pattern = re.compile(r'^(?:(?:[qQ]uestion|[qQ])\s*)?(\d+)[.\s)]\s*(.*)$')
        # Matches options like: "A. Option", "B) Option", "(C) Option", "a. Option"
        opt_pattern = re.compile(r'^[(\s]*([A-Da-d])[.\s)]\s*(.*)$')
        page_indicator_pattern = re.compile(r'^\[Page\s*(\d+)\s*Illustrations:', re.I)
        
        # Heuristic noise matching (boilerplate and candidate metadata)
        noise_patterns = [
            re.compile(r'^page\s*\d+', re.I),
            re.compile(r'^\d+\s*of\s*\d+$', re.I),
            re.compile(r'^turn\s*over\b', re.I),
            re.compile(r'^p\.t\.o\b', re.I),
            re.compile(r'^name\b\s*:', re.I),
            re.compile(r'^index\b\s*(?:number)?\s*:', re.I),
            re.compile(r'^date\b\s*:', re.I),
            re.compile(r'^class\b\s*:', re.I),
            re.compile(r'^signature\b', re.I),
            re.compile(r'^time\b\s*:', re.I),
            re.compile(r'^marks?\b\s*:', re.I),
            re.compile(r'^subject\b\s*:', re.I),
            re.compile(r'^instructions\b', re.I),
            re.compile(r'^candidate\b', re.I),
            re.compile(r'^school\b\s*:', re.I),
            re.compile(r'^sections?\b', re.I),
            re.compile(r'^parts?\b', re.I),
            re.compile(r'^choose\s+(?:the|all|any|correct)\b', re.I),
            re.compile(r'^answer\s+(?:the|all|any|each|following)\b', re.I),
            re.compile(r'^mid[- ]term\b', re.I),
            re.compile(r'^terminal\s+exam\b', re.I),
            re.compile(r'^annual\s+exam\b', re.I),
            re.compile(r'^test\s+paper\b', re.I),
            re.compile(r'^maximum\s+marks\b', re.I),
            re.compile(r'^time\s+allowed\b', re.I),
            re.compile(r'^hours?\s*$', re.I),
            re.compile(r'^footer\b', re.I),
            re.compile(r'^end\s+of\b', re.I)
        ]
        
        def is_boilerplate(q_text):
            return self._is_invalid_question(q_text)

        for line in lines:
            # Track current page number
            page_match = page_indicator_pattern.match(line)
            if page_match:
                current_page_num = int(page_match.group(1))
                continue

            # Clean inline images in the line
            if '[IMAGE:' in line:
                line = re.sub(r'\[IMAGE:\s*([^\s\]]+)\]', r'<img src="\1" class="my-4 max-w-full rounded-xl shadow-sm block" />', line)

            # Check if line is purely exam header noise / metadata
            is_noise = False
            for pat in noise_patterns:
                if pat.search(line):
                    is_noise = True
                    break
            if is_noise:
                continue
                
            q_match = q_pattern.match(line)
            is_new_question = False
            if q_match:
                q_num = int(q_match.group(1))
                q_text = q_match.group(2).strip()
                # Check that this matched line is not instruction boilerplate before setting as new question.
                # We only check is_boilerplate if the extracted text has content to avoid flagging empty question numbers.
                is_bp = False
                if len(q_text) >= 6:
                    is_bp = is_boilerplate(q_text)
                
                if not is_bp:
                    if expected_q_num == 1 or (q_num >= expected_q_num and q_num <= expected_q_num + 3):
                        is_new_question = True
                        expected_q_num = q_num + 1

            if is_new_question and q_match:
                if current_question:
                    if not is_boilerplate(current_question['text']):
                        questions.append(current_question)
                
                q_num_str = q_match.group(1)
                q_text = q_match.group(2).strip()
                
                current_question = {
                    'text': q_text,
                    'question_type': 'essay',  # default type
                    'difficulty': 'medium',
                    'explanation': f'Extracted from question {q_num_str}.',
                    'points': 5.0,
                    'options': [],
                    'page_num': current_page_num
                }
                continue
                
            if current_question:
                opt_match = opt_pattern.match(line)
                if opt_match:
                    opt_letter = opt_match.group(1).upper()
                    opt_text = opt_match.group(2).strip()
                    
                    # If we find options, it's an MCQ
                    current_question['question_type'] = 'mcq'
                    
                    # Simple heuristic: first option is correct
                    is_correct = len(current_question['options']) == 0
                    
                    current_question['options'].append({
                        'text': opt_text,
                        'is_correct': is_correct,
                        'order': len(current_question['options']) + 1
                    })
                else:
                    # Append extra text line (like subparts or suffix instructions) to current question
                    current_question['text'] += "\n" + line

                        
        if current_question:
            if not is_boilerplate(current_question['text']):
                questions.append(current_question)
            
        # Post-process questions to detect type and map PDF illustrations
        final_questions = []
        for idx, q in enumerate(questions):
            q_text = q['text'].lower()
            q_page = q.get('page_num', 1)
            
            # Map illustration if mentioned
            page_ills = {lbl: url for (pg, lbl), url in illustrations.items() if pg == q_page}
            for lbl, url in page_ills.items():
                lbl_lower = lbl.lower()
                patterns = [
                    r'\bdiagram\s*' + lbl_lower + r'\b',
                    r'\bimage\s*' + lbl_lower + r'\b',
                    r'\bfigure\s*' + lbl_lower + r'\b',
                    r'\bgraph\s*' + lbl_lower + r'\b',
                    r'\bshape\s*' + lbl_lower + r'\b',
                    r'\b' + lbl_lower + r'\b'
                ]
                has_mention = False
                for pat in patterns:
                    if re.search(pat, q_text):
                        has_mention = True
                        break
                
                if not has_mention and len(page_ills) == 1:
                    if any(w in q_text for w in ('diagram', 'figure', 'illustration', 'graph', 'shape', 'triangle', 'rectangle', 'circle', 'angle')):
                        has_mention = True
                        
                if has_mention:
                    img_tag = f'<img src="{url}" class="my-4 max-w-full rounded-xl shadow-sm block" />'
                    if img_tag not in q['text']:
                        q['text'] += "\n" + img_tag

            if not q['options']:
                if '___' in q_text or 'fill' in q_text:
                    q['question_type'] = 'fill_blank'
                    q['options'] = [{'text': 'Answer', 'is_correct': True, 'order': 1}]
                elif 'true' in q_text and 'false' in q_text:
                    q['question_type'] = 'true_false'
                    q['options'] = [
                        {'text': 'True', 'is_correct': True, 'order': 1},
                        {'text': 'False', 'is_correct': False, 'order': 2}
                    ]
                else:
                    q['question_type'] = 'essay'
            
            # Clean up temporary page_num key
            if 'page_num' in q:
                del q['page_num']
            
            import html
            q['text'] = html.unescape(q['text'])
            q['explanation'] = html.unescape(q.get('explanation', ''))
            if 'options' in q:
                for opt in q['options']:
                    opt['text'] = html.unescape(opt['text'])
                
            final_questions.append(q)
                    
        return final_questions

    # ------------------------------------------------------------------
    # Prompt builder
    # ------------------------------------------------------------------

    def _build_prompt(self, subject_name, topic_name, question_types,
                      difficulty, count, custom_prompt):
        """Return (system_prompt, user_prompt) for the AI."""

        types_str = ', '.join(question_types) if question_types else 'mcq'
        topic_clause = f' on the topic "{topic_name}"' if topic_name else ''
        custom_clause = (
            f'\n\nAdditional teacher instructions / focus area:\n{custom_prompt}'
            if custom_prompt else ''
        )

        # JSON schema example
        schema_example = json.dumps([
            {
                "text": "What is 2 + 2?",
                "question_type": "mcq",
                "difficulty": "easy",
                "explanation": "Basic addition: 2 + 2 equals 4.",
                "points": 5.0,
                "options": [
                    {"text": "4", "is_correct": True, "order": 1},
                    {"text": "3", "is_correct": False, "order": 2},
                    {"text": "5", "is_correct": False, "order": 3},
                    {"text": "22", "is_correct": False, "order": 4},
                ],
            },
        ], indent=2)

        system_prompt = (
            "You are an expert educational content creator specialising in "
            "generating high-quality assessment questions for secondary-school "
            "and primary-school students following the Tanzanian and East African "
            "curriculum. Your questions must be accurate, pedagogically sound, "
            "syllabus-aligned, and free of bias.\n\n"
            "RULES:\n"
            "1. Return ONLY a valid JSON array – no markdown fences, no commentary.\n"
            "2. Each element must have keys: text, question_type, difficulty, "
            "explanation, points, options.\n"
            "3. For MCQ / true_false questions: provide 4 options (2 for true_false) "
            "with exactly ONE marked is_correct=true.\n"
            "4. For fill_blank: the 'text' should contain a blank indicated by "
            "'______'. Provide one option with is_correct=true (the answer).\n"
            "5. For short_answer: provide one option with is_correct=true (model answer).\n"
            "6. For essay: options should be an empty array [].\n"
            "7. For matching: each option should have a 'match_pair' field.\n"
            "8. For ordering: options order field indicates the correct sequence.\n"
            "9. Set points to 5.0 for all questions.\n"
            "10. explanation should briefly explain WHY the correct answer is correct.\n"
        )

        user_prompt = (
            f"Generate exactly {count} assessment question(s) for the subject "
            f"\"{subject_name}\"{topic_clause}.\n\n"
            f"Question type(s) to use (distribute evenly): {types_str}\n"
            f"Difficulty level: {difficulty}\n\n"
            f"Return the result as a JSON array matching this schema:\n"
            f"{schema_example}\n"
            f"{custom_clause}"
        )

        return system_prompt, user_prompt

    # ------------------------------------------------------------------
    # Provider implementations (raw HTTP via requests)
    # ------------------------------------------------------------------

    def _generate_openai(self, system_prompt, user_prompt, count):
        """Call OpenAI Chat Completions API."""
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            raise ValueError('OPENAI_API_KEY is not configured.')

        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': 'gpt-4o-mini',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': 0.7,
            'max_tokens': 4096,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        text = data['choices'][0]['message']['content']
        self.used_provider = 'openai'
        return self._parse_ai_response(text)

    def _generate_gemini(self, system_prompt, user_prompt, count):
        """Call Google Gemini generateContent API."""
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            raise ValueError('GEMINI_API_KEY is not configured.')

        url = (
            'https://generativelanguage.googleapis.com/v1beta/'
            f'models/gemini-2.0-flash:generateContent?key={api_key}'
        )
        headers = {'Content-Type': 'application/json'}
        payload = {
            'system_instruction': {
                'parts': [{'text': system_prompt}],
            },
            'contents': [
                {
                    'parts': [{'text': user_prompt}],
                },
            ],
            'generationConfig': {
                'temperature': 0.7,
                'maxOutputTokens': 8192,
                'responseMimeType': 'application/json',
            },
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        text = data['candidates'][0]['content']['parts'][0]['text']
        self.used_provider = 'gemini'
        return self._parse_ai_response(text)

    def _generate_claude(self, system_prompt, user_prompt, count):
        """Call Anthropic Messages API."""
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
        if not api_key:
            raise ValueError('ANTHROPIC_API_KEY is not configured.')

        url = 'https://api.anthropic.com/v1/messages'
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 4096,
            'system': system_prompt,
            'messages': [
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': 0.7,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        text = data['content'][0]['text']
        self.used_provider = 'claude'
        return self._parse_ai_response(text)

    def _generate_auto(self, system_prompt, user_prompt, count):
        """Try providers in order until one succeeds.

        Order: gemini → openai → claude.
        """
        provider_order = [
            ('gemini', '_generate_gemini'),
            ('openai', '_generate_openai'),
            ('claude', '_generate_claude'),
        ]
        last_error = None
        for name, method_name in provider_order:
            try:
                result = getattr(self, method_name)(system_prompt, user_prompt, count)
                if result:
                    return result
            except Exception as exc:
                logger.info('Auto-mode: %s failed (%s), trying next.', name, exc)
                last_error = exc

        # All providers exhausted – raise so caller triggers fallback
        raise RuntimeError(
            f'All AI providers failed. Last error: {last_error}'
        )

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_ai_response(self, text):
        """Extract a JSON array of question dicts from raw AI output.

        Handles:
        - Clean JSON arrays
        - JSON wrapped in ```json ... ``` markdown fences
        - JSON with trailing commas (light cleanup)
        """
        if not text:
            return []

        # Strip markdown code fences if present
        cleaned = text.strip()
        fence_pattern = re.compile(
            r'```(?:json)?\s*\n?(.*?)\n?\s*```', re.DOTALL,
        )
        match = fence_pattern.search(cleaned)
        if match:
            cleaned = match.group(1).strip()

        # Try parsing directly
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                # Some models wrap in {"questions": [...]}
                for key in ('questions', 'data', 'results'):
                    if key in parsed and isinstance(parsed[key], list):
                        return parsed[key]
                return [parsed]
        except json.JSONDecodeError:
            pass

        # Try to find a JSON array substring
        arr_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if arr_match:
            try:
                return json.loads(arr_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning('Could not parse AI response as JSON: %s…', cleaned[:200])
        return []

    # ------------------------------------------------------------------
    # Post-processing / normalisation
    # ------------------------------------------------------------------

    def _is_invalid_question(self, text):
        """Check if a question is boilerplate text or candidate details, instead of a real question."""
        text_lower = text.strip().lower()
        
        # Drop too short question texts
        if len(text_lower) < 6:
            return True
            
        # Highly specific boilerplate substring matches (should never appear in actual questions)
        metadata_substrings = [
            'instructions to candidates', 'answer all questions', 'write your name',
            'signature of candidate', 'candidate name:', 'student name:', 'index number:',
            'mobile phones are not allowed', 'calculators are not allowed', 'do not open this booklet',
            'verify that this paper consists of', 'name of student:', 'name of candidate:',
            'remember to write', 'names properly', 'read all questions', 'read carefully',
            'holiday package', 'returned to school', 'when we open', 'answer as per instructions',
            'mathematical operations', 'marks', 'section a', 'section b', 'section c',
            'part a', 'part b', 'part c', 'general instructions', 'time allowed',
            'show all steps', 'show your working', 'without borrowing', 'do not open',
            'write index number', 'write your three names'
        ]
        for sub in metadata_substrings:
            if sub in text_lower:
                return True

        # Header metadata prefix patterns (labels at the start of text)
        prefix_patterns = [
            r'^(?:candidate|student|school|class|subject|date|time|marks|duration|instruction|stream|academic year|index number)\s*:',
            r'^(?:mid-term|terminal exam|annual exam|test paper|examination council|maximum marks|time allowed)\b',
            r'^name\s*:?\s*[_.\s]{3,}',
            r'^class\s*:?\s*[_.\s]{3,}',
            r'^index\b',
            r'^section\b',
            r'^part\b',
            r'^instructions\b',
            r'^answer all\b',
            r'^write your\b',
            r'^read the\b',
            r'^remember to\b'
        ]
        import re
        for pattern in prefix_patterns:
            if re.search(pattern, text_lower):
                return True

        # Exact matching for sections or metadata labels
        exact_matches = {
            'instructions', 'instruction', 'section a', 'section b', 'section c', 
            'general instructions', 'part a', 'part b', 'part c', 'candidate', 
            'invigilator', 'supervisor', 'signature', 'date', 'class', 'school',
            'subject', 'stream', 'hours', 'hour'
        }
        if text_lower in exact_matches:
            return True
            
        return False

    def _normalise(self, questions, question_types, difficulty, count):
        """Ensure every question dict has all required keys and correct types."""
        import html
        normalised = []
        for idx, q in enumerate(questions):
            if not isinstance(q, dict):
                continue

            q_text = html.unescape(str(q.get('text', ''))).strip()
            if self._is_invalid_question(q_text):
                continue

            q_type = q.get('question_type', 'mcq')
            if q_type not in (
                'mcq', 'multi_select', 'true_false', 'fill_blank',
                'short_answer', 'essay', 'matching', 'ordering',
            ):
                q_type = question_types[idx % len(question_types)] if question_types else 'mcq'

            raw_options = q.get('options', [])
            options = []
            for oi, opt in enumerate(raw_options):
                if not isinstance(opt, dict):
                    continue
                options.append({
                    'text': html.unescape(str(opt.get('text', ''))),
                    'is_correct': bool(opt.get('is_correct', False)),
                    'order': int(opt.get('order', oi + 1)),
                })

            normalised.append({
                'text': q_text,
                'question_type': q_type,
                'difficulty': q.get('difficulty', difficulty) or difficulty,
                'explanation': html.unescape(str(q.get('explanation', ''))),
                'points': float(q.get('points', 5.0)),
                'options': options,
            })

            if len(normalised) >= count:
                break

        return normalised

    # ------------------------------------------------------------------
    # Fallback template-based generator
    # ------------------------------------------------------------------

    def _generate_fallback(self, subject_name, topic_name, question_types,
                           difficulty, count):
        """Generate realistic questions without any AI API.

        Covers: Mathematics, Biology, Physics, Chemistry, English, Kiswahili,
        History, Geography, and a generic pool for any other subject.
        """
        sub = subject_name.lower()

        # Deterministic-ish seed so re-running with same params gives
        # different questions each time (uses random but seeded per call).
        seed_str = f'{subject_name}{topic_name}{difficulty}{count}{random.random()}'
        rng = random.Random(hashlib.md5(seed_str.encode()).hexdigest())

        pool = self._get_question_pool(sub, topic_name, difficulty)

        # Shuffle the pool
        rng.shuffle(pool)

        generated = []
        type_list = question_types if question_types else ['mcq']

        for i in range(count):
            current_type = type_list[i % len(type_list)]
            template = pool[i % len(pool)]

            q = self._adapt_template(template, current_type, difficulty, i)
            generated.append(q)

        return generated

    # ------------------------------------------------------------------
    # Subject question pools
    # ------------------------------------------------------------------

    def _get_question_pool(self, sub, topic_name, difficulty):
        """Return a list of raw template dicts for the subject."""

        if 'math' in sub:
            return self._pool_mathematics(difficulty)
        elif 'bio' in sub:
            return self._pool_biology(difficulty)
        elif 'physic' in sub:
            return self._pool_physics(difficulty)
        elif 'chem' in sub:
            return self._pool_chemistry(difficulty)
        elif 'english' in sub or 'eng' in sub:
            return self._pool_english(difficulty)
        elif 'kiswa' in sub or 'swahili' in sub:
            return self._pool_kiswahili(difficulty)
        elif 'hist' in sub:
            return self._pool_history(difficulty)
        elif 'geo' in sub:
            return self._pool_geography(difficulty)
        else:
            return self._pool_generic(sub, topic_name, difficulty)

    # ---- Mathematics ----
    def _pool_mathematics(self, difficulty):
        return [
            {
                'text': 'Simplify the expression: 3(2x - 4) + 5x.',
                'explanation': 'Distribute: 6x - 12 + 5x = 11x - 12.',
                'options': [
                    {'text': '11x - 12', 'is_correct': True, 'order': 1},
                    {'text': '11x + 12', 'is_correct': False, 'order': 2},
                    {'text': '6x - 12', 'is_correct': False, 'order': 3},
                    {'text': '11x - 4', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Solve for x: 2x + 7 = 15.',
                'explanation': '2x = 15 - 7 = 8, so x = 4.',
                'options': [
                    {'text': 'x = 4', 'is_correct': True, 'order': 1},
                    {'text': 'x = 8', 'is_correct': False, 'order': 2},
                    {'text': 'x = 3', 'is_correct': False, 'order': 3},
                    {'text': 'x = 11', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'What is the area of a circle with radius 7 cm? (Use π = 22/7)',
                'explanation': 'A = πr² = (22/7) × 49 = 154 cm².',
                'options': [
                    {'text': '154 cm²', 'is_correct': True, 'order': 1},
                    {'text': '44 cm²', 'is_correct': False, 'order': 2},
                    {'text': '22 cm²', 'is_correct': False, 'order': 3},
                    {'text': '308 cm²', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'If f(x) = 2x² - 3x + 1, find f(2).',
                'explanation': 'f(2) = 2(4) - 3(2) + 1 = 8 - 6 + 1 = 3.',
                'options': [
                    {'text': '3', 'is_correct': True, 'order': 1},
                    {'text': '5', 'is_correct': False, 'order': 2},
                    {'text': '7', 'is_correct': False, 'order': 3},
                    {'text': '1', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The sum of interior angles of a hexagon is:',
                'explanation': '(n-2) × 180° = (6-2) × 180° = 720°.',
                'options': [
                    {'text': '720°', 'is_correct': True, 'order': 1},
                    {'text': '540°', 'is_correct': False, 'order': 2},
                    {'text': '1080°', 'is_correct': False, 'order': 3},
                    {'text': '360°', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'What is the value of log₁₀(1000)?',
                'explanation': '10³ = 1000, so log₁₀(1000) = 3.',
                'options': [
                    {'text': '3', 'is_correct': True, 'order': 1},
                    {'text': '10', 'is_correct': False, 'order': 2},
                    {'text': '100', 'is_correct': False, 'order': 3},
                    {'text': '2', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'A triangle has sides 3 cm, 4 cm, and 5 cm. Is it a right triangle?',
                'explanation': '3² + 4² = 9 + 16 = 25 = 5². By the Pythagorean theorem it is a right triangle.',
                'options': [
                    {'text': 'True', 'is_correct': True, 'order': 1},
                    {'text': 'False', 'is_correct': False, 'order': 2},
                ],
            },
            {
                'text': 'Convert 0.75 to a fraction in simplest form.',
                'explanation': '0.75 = 75/100 = 3/4.',
                'options': [
                    {'text': '3/4', 'is_correct': True, 'order': 1},
                    {'text': '7/5', 'is_correct': False, 'order': 2},
                    {'text': '75/10', 'is_correct': False, 'order': 3},
                    {'text': '1/4', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Solve the inequality: 3x - 5 > 10.',
                'explanation': '3x > 15, therefore x > 5.',
                'options': [
                    {'text': 'x > 5', 'is_correct': True, 'order': 1},
                    {'text': 'x > 3', 'is_correct': False, 'order': 2},
                    {'text': 'x < 5', 'is_correct': False, 'order': 3},
                    {'text': 'x > 15', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'What is the gradient of the line y = 3x + 7?',
                'explanation': 'In y = mx + c, the gradient m = 3.',
                'options': [
                    {'text': '3', 'is_correct': True, 'order': 1},
                    {'text': '7', 'is_correct': False, 'order': 2},
                    {'text': '-3', 'is_correct': False, 'order': 3},
                    {'text': '1/3', 'is_correct': False, 'order': 4},
                ],
            },
        ]

    # ---- Biology ----
    def _pool_biology(self, difficulty):
        return [
            {
                'text': 'What is the primary function of mitochondria in a cell?',
                'explanation': 'Mitochondria are the powerhouses of the cell, producing ATP through cellular respiration.',
                'options': [
                    {'text': 'Energy production (ATP synthesis)', 'is_correct': True, 'order': 1},
                    {'text': 'Protein synthesis', 'is_correct': False, 'order': 2},
                    {'text': 'Cell division', 'is_correct': False, 'order': 3},
                    {'text': 'Lipid storage', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Which organelle is responsible for photosynthesis in plant cells?',
                'explanation': 'Chloroplasts contain chlorophyll and are the site of photosynthesis.',
                'options': [
                    {'text': 'Chloroplast', 'is_correct': True, 'order': 1},
                    {'text': 'Nucleus', 'is_correct': False, 'order': 2},
                    {'text': 'Ribosome', 'is_correct': False, 'order': 3},
                    {'text': 'Golgi apparatus', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'DNA replication occurs during which phase of the cell cycle?',
                'explanation': 'DNA replication takes place during the S (synthesis) phase of interphase.',
                'options': [
                    {'text': 'S phase', 'is_correct': True, 'order': 1},
                    {'text': 'G1 phase', 'is_correct': False, 'order': 2},
                    {'text': 'M phase', 'is_correct': False, 'order': 3},
                    {'text': 'G2 phase', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The process by which plants lose water vapour through stomata is called:',
                'explanation': 'Transpiration is the loss of water vapour from plant leaves through stomata.',
                'options': [
                    {'text': 'Transpiration', 'is_correct': True, 'order': 1},
                    {'text': 'Evaporation', 'is_correct': False, 'order': 2},
                    {'text': 'Osmosis', 'is_correct': False, 'order': 3},
                    {'text': 'Diffusion', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Which blood cells are responsible for fighting infections?',
                'explanation': 'White blood cells (leukocytes) defend the body against pathogens.',
                'options': [
                    {'text': 'White blood cells', 'is_correct': True, 'order': 1},
                    {'text': 'Red blood cells', 'is_correct': False, 'order': 2},
                    {'text': 'Platelets', 'is_correct': False, 'order': 3},
                    {'text': 'Plasma', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Enzymes are biological catalysts made primarily of:',
                'explanation': 'Enzymes are proteins that speed up biochemical reactions.',
                'options': [
                    {'text': 'Proteins', 'is_correct': True, 'order': 1},
                    {'text': 'Carbohydrates', 'is_correct': False, 'order': 2},
                    {'text': 'Lipids', 'is_correct': False, 'order': 3},
                    {'text': 'Nucleic acids', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The vascular tissue that transports water from roots to leaves is:',
                'explanation': 'Xylem vessels transport water and dissolved minerals upward from roots.',
                'options': [
                    {'text': 'Xylem', 'is_correct': True, 'order': 1},
                    {'text': 'Phloem', 'is_correct': False, 'order': 2},
                    {'text': 'Cambium', 'is_correct': False, 'order': 3},
                    {'text': 'Epidermis', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'In genetics, a heterozygous organism has:',
                'explanation': 'Heterozygous means having two different alleles for a particular gene (e.g. Aa).',
                'options': [
                    {'text': 'Two different alleles for a gene', 'is_correct': True, 'order': 1},
                    {'text': 'Two identical alleles for a gene', 'is_correct': False, 'order': 2},
                    {'text': 'No alleles', 'is_correct': False, 'order': 3},
                    {'text': 'Three alleles for a gene', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The exchange of gases in humans primarily occurs in the:',
                'explanation': 'Gas exchange occurs in the alveoli of the lungs where oxygen and carbon dioxide are exchanged.',
                'options': [
                    {'text': 'Alveoli', 'is_correct': True, 'order': 1},
                    {'text': 'Bronchi', 'is_correct': False, 'order': 2},
                    {'text': 'Trachea', 'is_correct': False, 'order': 3},
                    {'text': 'Nasal cavity', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Which of the following is NOT a characteristic of living organisms?',
                'explanation': 'Combustion is a chemical process, not a characteristic of living organisms.',
                'options': [
                    {'text': 'Combustion', 'is_correct': True, 'order': 1},
                    {'text': 'Respiration', 'is_correct': False, 'order': 2},
                    {'text': 'Reproduction', 'is_correct': False, 'order': 3},
                    {'text': 'Excretion', 'is_correct': False, 'order': 4},
                ],
            },
        ]

    # ---- Physics ----
    def _pool_physics(self, difficulty):
        return [
            {
                'text': 'What is the SI unit of force?',
                'explanation': 'The SI unit of force is the Newton (N), named after Sir Isaac Newton.',
                'options': [
                    {'text': 'Newton (N)', 'is_correct': True, 'order': 1},
                    {'text': 'Joule (J)', 'is_correct': False, 'order': 2},
                    {'text': 'Watt (W)', 'is_correct': False, 'order': 3},
                    {'text': 'Pascal (Pa)', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'A car accelerates from rest to 20 m/s in 5 seconds. What is its acceleration?',
                'explanation': 'a = (v - u) / t = (20 - 0) / 5 = 4 m/s².',
                'options': [
                    {'text': '4 m/s²', 'is_correct': True, 'order': 1},
                    {'text': '100 m/s²', 'is_correct': False, 'order': 2},
                    {'text': '25 m/s²', 'is_correct': False, 'order': 3},
                    {'text': '15 m/s²', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': "According to Newton's Third Law, for every action there is:",
                'explanation': "Newton's Third Law states that every action has an equal and opposite reaction.",
                'options': [
                    {'text': 'An equal and opposite reaction', 'is_correct': True, 'order': 1},
                    {'text': 'A greater reaction', 'is_correct': False, 'order': 2},
                    {'text': 'No reaction', 'is_correct': False, 'order': 3},
                    {'text': 'A delayed reaction', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'An object of mass 10 kg is lifted to a height of 5 m. What is its potential energy? (g = 10 m/s²)',
                'explanation': 'PE = mgh = 10 × 10 × 5 = 500 J.',
                'options': [
                    {'text': '500 J', 'is_correct': True, 'order': 1},
                    {'text': '50 J', 'is_correct': False, 'order': 2},
                    {'text': '250 J', 'is_correct': False, 'order': 3},
                    {'text': '100 J', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The speed of light in a vacuum is approximately:',
                'explanation': 'The speed of light in vacuum is approximately 3 × 10⁸ m/s.',
                'options': [
                    {'text': '3 × 10⁸ m/s', 'is_correct': True, 'order': 1},
                    {'text': '3 × 10⁶ m/s', 'is_correct': False, 'order': 2},
                    {'text': '3 × 10¹⁰ m/s', 'is_correct': False, 'order': 3},
                    {'text': '3 × 10⁵ m/s', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'What happens to the resistance of a metallic conductor when its temperature increases?',
                'explanation': 'In metals, resistance increases with temperature because increased atomic vibrations impede electron flow.',
                'options': [
                    {'text': 'Resistance increases', 'is_correct': True, 'order': 1},
                    {'text': 'Resistance decreases', 'is_correct': False, 'order': 2},
                    {'text': 'Resistance remains constant', 'is_correct': False, 'order': 3},
                    {'text': 'Resistance becomes zero', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'A wave has a frequency of 50 Hz and a wavelength of 2 m. What is its speed?',
                'explanation': 'v = fλ = 50 × 2 = 100 m/s.',
                'options': [
                    {'text': '100 m/s', 'is_correct': True, 'order': 1},
                    {'text': '25 m/s', 'is_correct': False, 'order': 2},
                    {'text': '52 m/s', 'is_correct': False, 'order': 3},
                    {'text': '48 m/s', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Which type of mirror is used in vehicle headlights?',
                'explanation': 'Concave (converging) mirrors are used in headlights to produce a parallel beam of light.',
                'options': [
                    {'text': 'Concave mirror', 'is_correct': True, 'order': 1},
                    {'text': 'Convex mirror', 'is_correct': False, 'order': 2},
                    {'text': 'Plane mirror', 'is_correct': False, 'order': 3},
                    {'text': 'Cylindrical mirror', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Pressure is defined as:',
                'explanation': 'Pressure = Force / Area. It measures force per unit area.',
                'options': [
                    {'text': 'Force per unit area', 'is_correct': True, 'order': 1},
                    {'text': 'Force times area', 'is_correct': False, 'order': 2},
                    {'text': 'Mass per unit volume', 'is_correct': False, 'order': 3},
                    {'text': 'Energy per unit time', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Sound cannot travel through:',
                'explanation': 'Sound requires a material medium to propagate and cannot travel through a vacuum.',
                'options': [
                    {'text': 'A vacuum', 'is_correct': True, 'order': 1},
                    {'text': 'Water', 'is_correct': False, 'order': 2},
                    {'text': 'Steel', 'is_correct': False, 'order': 3},
                    {'text': 'Air', 'is_correct': False, 'order': 4},
                ],
            },
        ]

    # ---- Chemistry ----
    def _pool_chemistry(self, difficulty):
        return [
            {
                'text': 'What is the chemical formula for water?',
                'explanation': 'Water consists of two hydrogen atoms bonded to one oxygen atom: H₂O.',
                'options': [
                    {'text': 'H₂O', 'is_correct': True, 'order': 1},
                    {'text': 'HO₂', 'is_correct': False, 'order': 2},
                    {'text': 'H₂O₂', 'is_correct': False, 'order': 3},
                    {'text': 'OH', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'What is the pH of a neutral solution at 25°C?',
                'explanation': 'A neutral solution has equal concentrations of H⁺ and OH⁻ ions, giving pH = 7.',
                'options': [
                    {'text': '7', 'is_correct': True, 'order': 1},
                    {'text': '0', 'is_correct': False, 'order': 2},
                    {'text': '14', 'is_correct': False, 'order': 3},
                    {'text': '1', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Which of the following is a noble gas?',
                'explanation': 'Neon is a noble gas in Group 18 of the periodic table with a full valence shell.',
                'options': [
                    {'text': 'Neon', 'is_correct': True, 'order': 1},
                    {'text': 'Nitrogen', 'is_correct': False, 'order': 2},
                    {'text': 'Chlorine', 'is_correct': False, 'order': 3},
                    {'text': 'Sodium', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'What type of bond is formed when electrons are shared between two atoms?',
                'explanation': 'A covalent bond involves the sharing of electron pairs between atoms.',
                'options': [
                    {'text': 'Covalent bond', 'is_correct': True, 'order': 1},
                    {'text': 'Ionic bond', 'is_correct': False, 'order': 2},
                    {'text': 'Metallic bond', 'is_correct': False, 'order': 3},
                    {'text': 'Hydrogen bond', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Rusting of iron is an example of:',
                'explanation': 'Rusting is a slow oxidation process where iron reacts with oxygen and moisture.',
                'options': [
                    {'text': 'Oxidation', 'is_correct': True, 'order': 1},
                    {'text': 'Reduction', 'is_correct': False, 'order': 2},
                    {'text': 'Neutralisation', 'is_correct': False, 'order': 3},
                    {'text': 'Decomposition', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'What is the atomic number of Carbon?',
                'explanation': 'Carbon has 6 protons in its nucleus, giving it an atomic number of 6.',
                'options': [
                    {'text': '6', 'is_correct': True, 'order': 1},
                    {'text': '12', 'is_correct': False, 'order': 2},
                    {'text': '8', 'is_correct': False, 'order': 3},
                    {'text': '14', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Which gas is produced when an acid reacts with a metal?',
                'explanation': 'When an acid reacts with a metal, hydrogen gas is produced along with a salt.',
                'options': [
                    {'text': 'Hydrogen', 'is_correct': True, 'order': 1},
                    {'text': 'Oxygen', 'is_correct': False, 'order': 2},
                    {'text': 'Carbon dioxide', 'is_correct': False, 'order': 3},
                    {'text': 'Nitrogen', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The process of converting a liquid to a gas is called:',
                'explanation': 'Evaporation (or boiling/vaporisation) converts a liquid into a gas.',
                'options': [
                    {'text': 'Evaporation', 'is_correct': True, 'order': 1},
                    {'text': 'Condensation', 'is_correct': False, 'order': 2},
                    {'text': 'Sublimation', 'is_correct': False, 'order': 3},
                    {'text': 'Freezing', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'An element with atomic number 11 belongs to which group?',
                'explanation': 'Sodium (Na) has atomic number 11 and belongs to Group 1 (alkali metals).',
                'options': [
                    {'text': 'Group 1', 'is_correct': True, 'order': 1},
                    {'text': 'Group 2', 'is_correct': False, 'order': 2},
                    {'text': 'Group 11', 'is_correct': False, 'order': 3},
                    {'text': 'Group 17', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'What is the molar mass of NaCl?',
                'explanation': 'Na = 23 g/mol, Cl = 35.5 g/mol. NaCl = 23 + 35.5 = 58.5 g/mol.',
                'options': [
                    {'text': '58.5 g/mol', 'is_correct': True, 'order': 1},
                    {'text': '40 g/mol', 'is_correct': False, 'order': 2},
                    {'text': '78 g/mol', 'is_correct': False, 'order': 3},
                    {'text': '35.5 g/mol', 'is_correct': False, 'order': 4},
                ],
            },
        ]

    # ---- English ----
    def _pool_english(self, difficulty):
        return [
            {
                'text': 'Choose the correct form: "She ______ to school every day."',
                'explanation': '"Goes" is correct because the subject "She" requires the third-person singular present tense.',
                'options': [
                    {'text': 'goes', 'is_correct': True, 'order': 1},
                    {'text': 'go', 'is_correct': False, 'order': 2},
                    {'text': 'going', 'is_correct': False, 'order': 3},
                    {'text': 'gone', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Identify the figure of speech: "The wind whispered through the trees."',
                'explanation': 'Personification gives human qualities (whispering) to a non-human entity (wind).',
                'options': [
                    {'text': 'Personification', 'is_correct': True, 'order': 1},
                    {'text': 'Simile', 'is_correct': False, 'order': 2},
                    {'text': 'Metaphor', 'is_correct': False, 'order': 3},
                    {'text': 'Hyperbole', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Which sentence is grammatically correct?',
                'explanation': '"Their" is the correct possessive pronoun for "children\'s toys."',
                'options': [
                    {'text': 'The children played with their toys.', 'is_correct': True, 'order': 1},
                    {'text': 'The children played with they toys.', 'is_correct': False, 'order': 2},
                    {'text': 'The children played with there toys.', 'is_correct': False, 'order': 3},
                    {'text': "The children played with they're toys.", 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'What is the past tense of "write"?',
                'explanation': '"Write" is an irregular verb; its past tense is "wrote."',
                'options': [
                    {'text': 'wrote', 'is_correct': True, 'order': 1},
                    {'text': 'writed', 'is_correct': False, 'order': 2},
                    {'text': 'written', 'is_correct': False, 'order': 3},
                    {'text': 'writing', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'A word that has the opposite meaning of another word is called:',
                'explanation': 'An antonym is a word opposite in meaning to another (e.g., hot/cold).',
                'options': [
                    {'text': 'Antonym', 'is_correct': True, 'order': 1},
                    {'text': 'Synonym', 'is_correct': False, 'order': 2},
                    {'text': 'Homonym', 'is_correct': False, 'order': 3},
                    {'text': 'Acronym', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Which of the following is a compound sentence?',
                'explanation': 'A compound sentence joins two independent clauses with a coordinating conjunction.',
                'options': [
                    {'text': 'I wanted to go, but it was raining.', 'is_correct': True, 'order': 1},
                    {'text': 'Running quickly.', 'is_correct': False, 'order': 2},
                    {'text': 'The big red ball.', 'is_correct': False, 'order': 3},
                    {'text': 'She sings beautifully.', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'What is the plural of "child"?',
                'explanation': '"Child" has an irregular plural form: "children."',
                'options': [
                    {'text': 'children', 'is_correct': True, 'order': 1},
                    {'text': 'childs', 'is_correct': False, 'order': 2},
                    {'text': 'childes', 'is_correct': False, 'order': 3},
                    {'text': 'childrens', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'In the sentence "The cat sat on the mat", what part of speech is "on"?',
                'explanation': '"On" is a preposition that shows the relationship between "sat" and "mat."',
                'options': [
                    {'text': 'Preposition', 'is_correct': True, 'order': 1},
                    {'text': 'Conjunction', 'is_correct': False, 'order': 2},
                    {'text': 'Adverb', 'is_correct': False, 'order': 3},
                    {'text': 'Adjective', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': '"To let the cat out of the bag" means:',
                'explanation': 'This idiom means to reveal a secret unintentionally.',
                'options': [
                    {'text': 'To reveal a secret', 'is_correct': True, 'order': 1},
                    {'text': 'To release an animal', 'is_correct': False, 'order': 2},
                    {'text': 'To make a mistake', 'is_correct': False, 'order': 3},
                    {'text': 'To start a fight', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Which word is an adverb in: "She quickly finished her homework"?',
                'explanation': '"Quickly" modifies the verb "finished" and describes how the action was done.',
                'options': [
                    {'text': 'quickly', 'is_correct': True, 'order': 1},
                    {'text': 'finished', 'is_correct': False, 'order': 2},
                    {'text': 'homework', 'is_correct': False, 'order': 3},
                    {'text': 'her', 'is_correct': False, 'order': 4},
                ],
            },
        ]

    # ---- Kiswahili ----
    def _pool_kiswahili(self, difficulty):
        return [
            {
                'text': 'Nomino "mti" iko katika ngeli gani?',
                'explanation': 'Neno "mti" ni katika ngeli ya M-MI: mti (umoja), miti (wingi).',
                'options': [
                    {'text': 'Ngeli ya M-MI', 'is_correct': True, 'order': 1},
                    {'text': 'Ngeli ya A-WA', 'is_correct': False, 'order': 2},
                    {'text': 'Ngeli ya KI-VI', 'is_correct': False, 'order': 3},
                    {'text': 'Ngeli ya U-I', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Wingi wa neno "kitabu" ni:',
                'explanation': '"Kitabu" ni katika ngeli ya KI-VI. Wingi wake ni "vitabu."',
                'options': [
                    {'text': 'vitabu', 'is_correct': True, 'order': 1},
                    {'text': 'makitabu', 'is_correct': False, 'order': 2},
                    {'text': 'mitabu', 'is_correct': False, 'order': 3},
                    {'text': 'kitabu', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Kitenzi "soma" kikiwa katika wakati uliopita ni:',
                'explanation': 'Wakati uliopita wa "soma" ni "alisoma" (nafsi ya tatu umoja).',
                'options': [
                    {'text': 'alisoma', 'is_correct': True, 'order': 1},
                    {'text': 'anasoma', 'is_correct': False, 'order': 2},
                    {'text': 'atasoma', 'is_correct': False, 'order': 3},
                    {'text': 'amesoma', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Ni aina gani ya sentensi hii: "Je, umekula?"',
                'explanation': 'Sentensi hii inaanza na "Je" na inauliza swali, hivyo ni sentensi ya kuuliza (swali).',
                'options': [
                    {'text': 'Sentensi ya kuuliza', 'is_correct': True, 'order': 1},
                    {'text': 'Sentensi ya taarifa', 'is_correct': False, 'order': 2},
                    {'text': 'Sentensi ya amri', 'is_correct': False, 'order': 3},
                    {'text': 'Sentensi ya hisi', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': '"Mwalimu" akifanywa wingi inakuwa:',
                'explanation': '"Mwalimu" iko katika ngeli ya A-WA. Wingi ni "walimu."',
                'options': [
                    {'text': 'walimu', 'is_correct': True, 'order': 1},
                    {'text': 'mwalimu', 'is_correct': False, 'order': 2},
                    {'text': 'malimu', 'is_correct': False, 'order': 3},
                    {'text': 'wamwalimu', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Nahau "kupiga maji" ina maana gani?',
                'explanation': 'Nahau "kupiga maji" maana yake ni kupoteza muda bure / kufanya jambo bure.',
                'options': [
                    {'text': 'Kupoteza muda bure', 'is_correct': True, 'order': 1},
                    {'text': 'Kuogelea', 'is_correct': False, 'order': 2},
                    {'text': 'Kupika chakula', 'is_correct': False, 'order': 3},
                    {'text': 'Kusafisha nguo', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Tashbihi ni tamathali ya usemi inayotumia maneno:',
                'explanation': 'Tashbihi hutumia maneno ya kulinganisha kama "kama", "mithili ya", "sawa na."',
                'options': [
                    {'text': 'kama, mithili ya, sawa na', 'is_correct': True, 'order': 1},
                    {'text': 'lakini, ila, bali', 'is_correct': False, 'order': 2},
                    {'text': 'na, pia, pamoja', 'is_correct': False, 'order': 3},
                    {'text': 'kwa sababu, ili, ingawa', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Kirai tenzi ni:',
                'explanation': 'Kirai tenzi ni kikundi cha maneno ambacho kitenzi ndicho kichwa chake.',
                'options': [
                    {'text': 'Kikundi cha maneno chenye kitenzi kama kichwa', 'is_correct': True, 'order': 1},
                    {'text': 'Kikundi cha maneno chenye nomino kama kichwa', 'is_correct': False, 'order': 2},
                    {'text': 'Neno moja pekee', 'is_correct': False, 'order': 3},
                    {'text': 'Sentensi kamili', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Neno "haraka" ni aina gani ya neno?',
                'explanation': '"Haraka" ni kielezi kinachoeleza jinsi kitendo kinavyofanyika.',
                'options': [
                    {'text': 'Kielezi', 'is_correct': True, 'order': 1},
                    {'text': 'Kivumishi', 'is_correct': False, 'order': 2},
                    {'text': 'Nomino', 'is_correct': False, 'order': 3},
                    {'text': 'Kitenzi', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Methali "Asiyefunzwa na mamaye hufunzwa na ulimwengu" ina maana gani?',
                'explanation': 'Methali hii inamaanisha kwamba mtu asiyesikiliza ushauri wa wazazi wake atajifunza masomo magumu kutoka maishani.',
                'options': [
                    {'text': 'Mtu asiyesikiliza ushauri atajifunza kwa njia ngumu', 'is_correct': True, 'order': 1},
                    {'text': 'Mama ndiye mwalimu bora', 'is_correct': False, 'order': 2},
                    {'text': 'Ulimwengu ni shule kubwa', 'is_correct': False, 'order': 3},
                    {'text': 'Watoto lazima wasikilize walimu', 'is_correct': False, 'order': 4},
                ],
            },
        ]

    # ---- History ----
    def _pool_history(self, difficulty):
        return [
            {
                'text': 'The Berlin Conference of 1884-1885 led to:',
                'explanation': 'The Berlin Conference formalised the Scramble for Africa and set rules for European colonisation of the continent.',
                'options': [
                    {'text': 'The partition (scramble) of Africa among European powers', 'is_correct': True, 'order': 1},
                    {'text': 'The end of World War I', 'is_correct': False, 'order': 2},
                    {'text': 'The formation of the United Nations', 'is_correct': False, 'order': 3},
                    {'text': 'The independence of Germany', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Tanzania gained independence from Britain in which year?',
                'explanation': 'Tanganyika gained independence on 9 December 1961. Zanzibar followed in 1963, and they united to form Tanzania in 1964.',
                'options': [
                    {'text': '1961', 'is_correct': True, 'order': 1},
                    {'text': '1963', 'is_correct': False, 'order': 2},
                    {'text': '1957', 'is_correct': False, 'order': 3},
                    {'text': '1970', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Who was the first President of Tanzania?',
                'explanation': 'Julius Kambarage Nyerere was the first President of Tanzania, serving from 1964 to 1985.',
                'options': [
                    {'text': 'Julius Nyerere', 'is_correct': True, 'order': 1},
                    {'text': 'Ali Hassan Mwinyi', 'is_correct': False, 'order': 2},
                    {'text': 'Benjamin Mkapa', 'is_correct': False, 'order': 3},
                    {'text': 'Abeid Karume', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The Maji Maji Rebellion (1905-1907) was a resistance against:',
                'explanation': 'The Maji Maji Rebellion was an armed uprising against German colonial rule in German East Africa.',
                'options': [
                    {'text': 'German colonial rule', 'is_correct': True, 'order': 1},
                    {'text': 'British colonial rule', 'is_correct': False, 'order': 2},
                    {'text': 'Portuguese traders', 'is_correct': False, 'order': 3},
                    {'text': 'Arab slave traders', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The Industrial Revolution began in which country?',
                'explanation': 'The Industrial Revolution started in Britain in the late 18th century.',
                'options': [
                    {'text': 'Britain', 'is_correct': True, 'order': 1},
                    {'text': 'France', 'is_correct': False, 'order': 2},
                    {'text': 'Germany', 'is_correct': False, 'order': 3},
                    {'text': 'United States', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The Arusha Declaration of 1967 promoted:',
                'explanation': 'The Arusha Declaration outlined Tanzania\'s policy of Ujamaa (African socialism) and self-reliance.',
                'options': [
                    {'text': 'Ujamaa (African socialism) and self-reliance', 'is_correct': True, 'order': 1},
                    {'text': 'Capitalism and free trade', 'is_correct': False, 'order': 2},
                    {'text': 'Military expansion', 'is_correct': False, 'order': 3},
                    {'text': 'Union with Kenya', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'World War II ended in:',
                'explanation': 'World War II ended in 1945 with the surrender of Germany in May and Japan in September.',
                'options': [
                    {'text': '1945', 'is_correct': True, 'order': 1},
                    {'text': '1939', 'is_correct': False, 'order': 2},
                    {'text': '1918', 'is_correct': False, 'order': 3},
                    {'text': '1950', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The slave trade in East Africa was primarily conducted by:',
                'explanation': 'Arab and Swahili traders dominated the East African slave trade, with Zanzibar as a major hub.',
                'options': [
                    {'text': 'Arab and Swahili traders', 'is_correct': True, 'order': 1},
                    {'text': 'Chinese merchants', 'is_correct': False, 'order': 2},
                    {'text': 'Indian traders only', 'is_correct': False, 'order': 3},
                    {'text': 'American settlers', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The Organisation of African Unity (OAU) was founded in:',
                'explanation': 'The OAU was established on 25 May 1963 in Addis Ababa, Ethiopia.',
                'options': [
                    {'text': '1963', 'is_correct': True, 'order': 1},
                    {'text': '1945', 'is_correct': False, 'order': 2},
                    {'text': '1975', 'is_correct': False, 'order': 3},
                    {'text': '1960', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The Trans-Atlantic slave trade primarily transported enslaved Africans to:',
                'explanation': 'The majority of enslaved Africans were taken across the Atlantic to the Americas (Caribbean, South America, North America).',
                'options': [
                    {'text': 'The Americas', 'is_correct': True, 'order': 1},
                    {'text': 'Europe', 'is_correct': False, 'order': 2},
                    {'text': 'Asia', 'is_correct': False, 'order': 3},
                    {'text': 'Australia', 'is_correct': False, 'order': 4},
                ],
            },
        ]

    # ---- Geography ----
    def _pool_geography(self, difficulty):
        return [
            {
                'text': 'What is the largest lake in Africa by surface area?',
                'explanation': 'Lake Victoria, shared by Tanzania, Uganda, and Kenya, is the largest lake in Africa.',
                'options': [
                    {'text': 'Lake Victoria', 'is_correct': True, 'order': 1},
                    {'text': 'Lake Tanganyika', 'is_correct': False, 'order': 2},
                    {'text': 'Lake Malawi', 'is_correct': False, 'order': 3},
                    {'text': 'Lake Chad', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Mount Kilimanjaro is located in which country?',
                'explanation': 'Mount Kilimanjaro, Africa\'s highest peak at 5,895 m, is located in northeastern Tanzania.',
                'options': [
                    {'text': 'Tanzania', 'is_correct': True, 'order': 1},
                    {'text': 'Kenya', 'is_correct': False, 'order': 2},
                    {'text': 'Uganda', 'is_correct': False, 'order': 3},
                    {'text': 'Ethiopia', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The process of wearing away of the earth\'s surface by natural agents is called:',
                'explanation': 'Erosion is the process by which soil and rock are removed from the Earth\'s surface by wind, water, or ice.',
                'options': [
                    {'text': 'Erosion', 'is_correct': True, 'order': 1},
                    {'text': 'Weathering', 'is_correct': False, 'order': 2},
                    {'text': 'Deposition', 'is_correct': False, 'order': 3},
                    {'text': 'Sedimentation', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Which imaginary line divides the Earth into Northern and Southern hemispheres?',
                'explanation': 'The Equator (0° latitude) divides the Earth into the Northern and Southern hemispheres.',
                'options': [
                    {'text': 'The Equator', 'is_correct': True, 'order': 1},
                    {'text': 'The Prime Meridian', 'is_correct': False, 'order': 2},
                    {'text': 'The Tropic of Cancer', 'is_correct': False, 'order': 3},
                    {'text': 'The International Date Line', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The Great Rift Valley runs through which continent(s)?',
                'explanation': 'The Great Rift Valley stretches from Lebanon in Asia through Eastern Africa to Mozambique.',
                'options': [
                    {'text': 'Africa and Asia', 'is_correct': True, 'order': 1},
                    {'text': 'Africa only', 'is_correct': False, 'order': 2},
                    {'text': 'Asia only', 'is_correct': False, 'order': 3},
                    {'text': 'Europe and Africa', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'What type of climate is found near the Equator?',
                'explanation': 'Equatorial (tropical) climate is characterised by high temperatures and heavy rainfall throughout the year.',
                'options': [
                    {'text': 'Equatorial (tropical) climate', 'is_correct': True, 'order': 1},
                    {'text': 'Mediterranean climate', 'is_correct': False, 'order': 2},
                    {'text': 'Desert climate', 'is_correct': False, 'order': 3},
                    {'text': 'Tundra climate', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'The longest river in Africa is:',
                'explanation': 'The Nile River, at approximately 6,650 km, is the longest river in Africa.',
                'options': [
                    {'text': 'River Nile', 'is_correct': True, 'order': 1},
                    {'text': 'River Congo', 'is_correct': False, 'order': 2},
                    {'text': 'River Niger', 'is_correct': False, 'order': 3},
                    {'text': 'River Zambezi', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'A map scale of 1:50,000 means:',
                'explanation': '1 cm on the map represents 50,000 cm (500 m or 0.5 km) on the ground.',
                'options': [
                    {'text': '1 cm on the map = 0.5 km on the ground', 'is_correct': True, 'order': 1},
                    {'text': '1 cm on the map = 50 km on the ground', 'is_correct': False, 'order': 2},
                    {'text': '1 cm on the map = 5 km on the ground', 'is_correct': False, 'order': 3},
                    {'text': '1 cm on the map = 500 km on the ground', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Volcanic mountains are formed by:',
                'explanation': 'Volcanic mountains form when magma erupts through the Earth\'s crust and accumulates in layers.',
                'options': [
                    {'text': 'Accumulation of lava and volcanic material', 'is_correct': True, 'order': 1},
                    {'text': 'Folding of rock layers', 'is_correct': False, 'order': 2},
                    {'text': 'Faulting of the crust', 'is_correct': False, 'order': 3},
                    {'text': 'Erosion by rivers', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': 'Which ocean borders East Africa?',
                'explanation': 'The Indian Ocean lies to the east of the African continent.',
                'options': [
                    {'text': 'Indian Ocean', 'is_correct': True, 'order': 1},
                    {'text': 'Atlantic Ocean', 'is_correct': False, 'order': 2},
                    {'text': 'Pacific Ocean', 'is_correct': False, 'order': 3},
                    {'text': 'Arctic Ocean', 'is_correct': False, 'order': 4},
                ],
            },
        ]

    # ---- Generic (any other subject) ----
    def _pool_generic(self, sub, topic_name, difficulty):
        topic_label = topic_name if topic_name else sub.title()
        return [
            {
                'text': f'Which of the following best describes the core principle of {topic_label}?',
                'explanation': f'Understanding the fundamental principles of {topic_label} is essential for building deeper knowledge.',
                'options': [
                    {'text': f'A systematic study and application of key concepts in {topic_label}', 'is_correct': True, 'order': 1},
                    {'text': 'A random collection of unrelated facts', 'is_correct': False, 'order': 2},
                    {'text': 'An outdated field with no modern relevance', 'is_correct': False, 'order': 3},
                    {'text': 'A subject that requires no prior knowledge', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': f'Explain one key concept you have learned in {topic_label} and how it applies to everyday life.',
                'explanation': f'Students should connect theoretical knowledge of {topic_label} to practical, real-world applications.',
                'options': [],
            },
            {
                'text': f'True or False: {topic_label} is important for understanding the world around us.',
                'explanation': f'All academic subjects, including {topic_label}, help us understand different aspects of our environment and society.',
                'options': [
                    {'text': 'True', 'is_correct': True, 'order': 1},
                    {'text': 'False', 'is_correct': False, 'order': 2},
                ],
            },
            {
                'text': f'List three important topics covered in the study of {topic_label}.',
                'explanation': f'Identifying key topics demonstrates a broad understanding of the {topic_label} curriculum.',
                'options': [],
            },
            {
                'text': f'The study of {topic_label} helps students develop:',
                'explanation': f'Studying {topic_label} develops critical thinking, analytical skills, and subject-specific competencies.',
                'options': [
                    {'text': 'Critical thinking and analytical skills', 'is_correct': True, 'order': 1},
                    {'text': 'Only memorisation skills', 'is_correct': False, 'order': 2},
                    {'text': 'No useful skills', 'is_correct': False, 'order': 3},
                    {'text': 'Only physical abilities', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': f'Which method is most effective for studying {topic_label}?',
                'explanation': 'Active learning methods such as practice, discussion, and application are more effective than passive reading.',
                'options': [
                    {'text': 'Practice, discussion, and real-world application', 'is_correct': True, 'order': 1},
                    {'text': 'Only reading textbooks without practice', 'is_correct': False, 'order': 2},
                    {'text': 'Ignoring the subject entirely', 'is_correct': False, 'order': 3},
                    {'text': 'Memorising without understanding', 'is_correct': False, 'order': 4},
                ],
            },
            {
                'text': f'Describe the relationship between {topic_label} and technology in modern society.',
                'explanation': f'Technology and {topic_label} are increasingly interlinked as digital tools transform how knowledge is applied.',
                'options': [],
            },
            {
                'text': f'A student studying {topic_label} should be able to:',
                'explanation': 'Curriculum goals typically include analysis, evaluation, and practical application of learned concepts.',
                'options': [
                    {'text': 'Analyse, evaluate, and apply concepts', 'is_correct': True, 'order': 1},
                    {'text': 'Only recall facts from memory', 'is_correct': False, 'order': 2},
                    {'text': 'Avoid asking questions', 'is_correct': False, 'order': 3},
                    {'text': 'Copy answers without understanding', 'is_correct': False, 'order': 4},
                ],
            },
        ]

    # ------------------------------------------------------------------
    # Template adaptation to different question types
    # ------------------------------------------------------------------

    def _adapt_template(self, template, target_type, difficulty, index):
        """Convert a pool template into the requested question_type."""
        q = {
            'text': template['text'],
            'question_type': target_type,
            'difficulty': difficulty,
            'explanation': template.get('explanation', ''),
            'points': 5.0,
            'options': [],
        }

        source_options = template.get('options', [])

        if target_type == 'essay':
            # No options for essay – just the question text
            q['options'] = []

        elif target_type == 'short_answer':
            # Provide the correct answer as the single option
            correct = next((o for o in source_options if o.get('is_correct')), None)
            if correct:
                q['options'] = [{'text': correct['text'], 'is_correct': True, 'order': 1}]
            else:
                q['options'] = [{'text': 'Correct answer', 'is_correct': True, 'order': 1}]

        elif target_type == 'true_false':
            # Keep only first two options, or generate True/False
            if len(source_options) >= 2 and source_options[0]['text'] in ('True', 'False'):
                q['options'] = source_options[:2]
            else:
                # Reframe: the correct answer makes the statement true
                correct = next((o for o in source_options if o.get('is_correct')), None)
                if correct:
                    q['text'] = f'True or False: The answer to "{template["text"]}" is "{correct["text"]}".'
                q['options'] = [
                    {'text': 'True', 'is_correct': True, 'order': 1},
                    {'text': 'False', 'is_correct': False, 'order': 2},
                ]

        elif target_type == 'fill_blank':
            # Transform text to include a blank and put answer as option
            correct = next((o for o in source_options if o.get('is_correct')), None)
            if correct:
                answer_text = correct['text']
                q['text'] = template['text'].replace('?', '').rstrip('.') + ': ______.'
                q['options'] = [{'text': answer_text, 'is_correct': True, 'order': 1}]
            else:
                q['options'] = source_options

        elif target_type in ('matching', 'ordering'):
            # Re-use options with order preserved
            q['options'] = [
                {
                    'text': o['text'],
                    'is_correct': o.get('is_correct', False),
                    'order': o.get('order', idx + 1),
                }
                for idx, o in enumerate(source_options)
            ]

        else:
            # mcq, multi_select – use full options
            q['options'] = [
                {
                    'text': o['text'],
                    'is_correct': o.get('is_correct', False),
                    'order': o.get('order', idx + 1),
                }
                for idx, o in enumerate(source_options)
            ]
            # Ensure at least 4 options for MCQ
            if target_type == 'mcq' and len(q['options']) < 4:
                while len(q['options']) < 4:
                    q['options'].append({
                        'text': f'Option {len(q["options"]) + 1}',
                        'is_correct': False,
                        'order': len(q['options']) + 1,
                    })

        return q
