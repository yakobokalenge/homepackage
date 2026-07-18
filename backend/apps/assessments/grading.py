from decimal import Decimal
from apps.content.models import Question, QuestionOption
from rapidfuzz import fuzz


def fuzzy_match(student_answer, correct_answers, threshold=85):
    """
    Checks if student_answer is similar to any of the correct_answers.
    Returns (is_match, similarity_score).
    """
    if not student_answer or not correct_answers:
        return False, 0.0
    
    student_clean = student_answer.strip().lower()
    best_ratio = 0.0
    
    for correct in correct_answers:
        correct_clean = correct.strip().lower()
        if not correct_clean:
            continue
        ratio = fuzz.ratio(student_clean, correct_clean)
        if ratio > best_ratio:
            best_ratio = ratio
            
    return (best_ratio >= threshold), best_ratio



def grade_response(response, points_override=None):
    """
    Auto-grades an AnswerResponse instance.
    Updates response.is_correct, response.points_awarded, and response.auto_graded.
    Does not call save().
    """
    question = response.question
    points = Decimal(str(points_override)) if points_override is not None else question.points
    
    # By default, not auto-graded or incorrect
    response.is_correct = False
    response.points_awarded = Decimal('0.00')
    response.auto_graded = True

    # 1. Multiple Choice (MCQ)
    if question.question_type == Question.QuestionType.MCQ:
        if response.selected_options:
            selected_id = response.selected_options[0]
            try:
                option = question.options.get(id=selected_id)
                if option.is_correct:
                    response.is_correct = True
                    response.points_awarded = points
            except QuestionOption.DoesNotExist:
                pass

    # 2. Multiple Select (MULTI_SELECT)
    elif question.question_type == Question.QuestionType.MULTI_SELECT:
        if response.selected_options:
            correct_option_ids = set(
                str(opt_id) for opt_id in question.options.filter(is_correct=True).values_list('id', flat=True)
            )
            selected_option_ids = set(str(opt_id) for opt_id in response.selected_options)
            
            if correct_option_ids == selected_option_ids:
                response.is_correct = True
                response.points_awarded = points
            else:
                # Partial credit: award proportional points for correct selections with NO incorrect selections
                all_option_ids = set(
                    str(opt_id) for opt_id in question.options.values_list('id', flat=True)
                )
                incorrect_selections = selected_option_ids - correct_option_ids
                if not incorrect_selections and len(selected_option_ids) > 0:
                    fraction = Decimal(len(selected_option_ids)) / Decimal(len(correct_option_ids))
                    response.points_awarded = round(points * fraction, 2)
                    # We still mark is_correct as False because it wasn't a 100% match, or we can set it to True if fully correct

    # 3. True/False (TRUE_FALSE)
    elif question.question_type == Question.QuestionType.TRUE_FALSE:
        # Same as MCQ
        if response.selected_options:
            selected_id = response.selected_options[0]
            try:
                option = question.options.get(id=selected_id)
                if option.is_correct:
                    response.is_correct = True
                    response.points_awarded = points
            except QuestionOption.DoesNotExist:
                pass
        elif response.text_answer:
            # Fallback to text check ('true'/'false' or swahili equivalent)
            ans = response.text_answer.strip().lower()
            correct_opt = question.options.filter(is_correct=True).first()
            if correct_opt and correct_opt.text.strip().lower() == ans:
                response.is_correct = True
                response.points_awarded = points

    # 4. Fill in the Blank (FILL_BLANK)
    elif question.question_type == Question.QuestionType.FILL_BLANK:
        if response.text_answer:
            correct_texts = [
                opt.text.strip().lower() for opt in question.options.filter(is_correct=True)
            ]
            is_match, score = fuzzy_match(response.text_answer, correct_texts, threshold=85)
            if is_match:
                response.is_correct = True
                response.points_awarded = points

    # 5. Matching (MATCHING)
    elif question.question_type == Question.QuestionType.MATCHING:
        if response.matching_pairs:
            correct_count = 0
            total_pairs = question.options.count()
            
            for option_id, match_text in response.matching_pairs.items():
                try:
                    option = question.options.get(id=option_id)
                    if option.match_pair.strip().lower() == match_text.strip().lower():
                        correct_count += 1
                except QuestionOption.DoesNotExist:
                    pass
            
            if correct_count == total_pairs:
                response.is_correct = True
                response.points_awarded = points
            elif correct_count > 0 and total_pairs > 0:
                # Proportional grading
                fraction = Decimal(correct_count) / Decimal(total_pairs)
                response.points_awarded = round(points * fraction, 2)

    # 6. Ordering (ORDERING)
    elif question.question_type == Question.QuestionType.ORDERING:
        if response.ordering_sequence:
            correct_order = list(question.options.order_by('order').values_list('id', flat=True))
            # Convert UUIDs to strings to avoid type issues in comparison
            correct_order_strs = [str(x) for x in correct_order]
            student_order_strs = [str(x) for x in response.ordering_sequence]
            
            if correct_order_strs == student_order_strs:
                response.is_correct = True
                response.points_awarded = points

    # 7. Short Answer (SHORT_ANSWER)
    elif question.question_type == Question.QuestionType.SHORT_ANSWER:
        correct_opts = question.options.filter(is_correct=True)
        if correct_opts.exists():
            correct_texts = [opt.text.strip().lower() for opt in correct_opts]
            is_match, score = fuzzy_match(response.text_answer, correct_texts, threshold=80)
            if is_match:
                response.is_correct = True
                response.points_awarded = points
            else:
                response.auto_graded = False  # Mark for manual review since it doesn't match correct templates
        else:
            response.auto_graded = False

    # 8. Essay (ESSAY)
    elif question.question_type == Question.QuestionType.ESSAY:
        response.auto_graded = False  # Always manual grading

    return response.auto_graded
