from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Avg, Count, Q, Sum
from apps.content.models import Subject, Topic
from apps.assessments.models import Assessment, AssessmentAttempt, AnswerResponse


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_overview(request):
    """Student's performance overview querying real attempts."""
    student = request.user
    attempts = AssessmentAttempt.objects.filter(student=student, status='graded')
    
    total_assessments = attempts.count()
    avg_score = attempts.aggregate(avg=Avg('percentage'))['avg'] or 0.0

    # Aggregate by subject
    by_subject = []
    subjects = Subject.objects.filter(assessments__attempts__student=student).distinct()
    for sub in subjects:
        sub_attempts = attempts.filter(assessment__subject=sub)
        sub_count = sub_attempts.count()
        sub_avg = sub_attempts.aggregate(avg=Avg('percentage'))['avg'] or 0.0
        if sub_count > 0:
            by_subject.append({
                'subject_id': str(sub.id),
                'subject_name': sub.name,
                'subject_code': sub.code,
                'attempts_count': sub_count,
                'average_score': round(float(sub_avg), 2),
            })

    return Response({
        'total_assessments': total_assessments,
        'average_score': round(float(avg_score), 2),
        'by_subject': by_subject,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weak_topics(request):
    """Identify student's weak topics based on incorrect answers."""
    student = request.user
    # Find all incorrect answer responses
    incorrect_responses = AnswerResponse.objects.filter(
        attempt__student=student,
        is_correct=False,
        question__topic__isnull=False
    ).select_related('question__topic__subject')

    topic_counts = {}
    for resp in incorrect_responses:
        topic = resp.question.topic
        if topic:
            if topic.id not in topic_counts:
                topic_counts[topic.id] = {
                    'topic_name': topic.name,
                    'subject_name': topic.subject.name,
                    'incorrect_count': 0
                }
            topic_counts[topic.id]['incorrect_count'] += 1

    # Sort topics by incorrect count descending
    sorted_topics = sorted(topic_counts.values(), key=lambda x: x['incorrect_count'], reverse=True)
    return Response(sorted_topics[:5])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_class_performance(request):
    """Teacher's class-level analytics querying real classrooms and attempts."""
    teacher = request.user
    if teacher.role != 'teacher':
        return Response({'error': 'Only teachers can access class performance metrics.'}, status=403)

    from apps.schools.models import Classroom
    from apps.accounts.models import StudentProfile
    
    # Classrooms where the teacher is class_teacher
    classrooms = Classroom.objects.filter(class_teacher=teacher)
    classroom_ids = classrooms.values_list('id', flat=True)
    
    # Total students in those classrooms
    total_students = StudentProfile.objects.filter(classroom__in=classroom_ids).count()
    
    # Assessments created by this teacher
    assessments = Assessment.objects.filter(created_by=teacher)
    assessments_created = assessments.count()
    
    # Attempts on teacher's assessments
    attempts = AssessmentAttempt.objects.filter(assessment__created_by=teacher, status__in=['submitted', 'graded'])
    total_submissions = attempts.count()
    
    graded_attempts = attempts.filter(status='graded')
    avg_score = graded_attempts.aggregate(avg=Avg('percentage'))['avg'] or 0.0
    
    proctored_exams = assessments.filter(is_proctored=True).count()

    # Performance by assessment
    by_assessment = []
    for ass in assessments:
        ass_attempts = graded_attempts.filter(assessment=ass)
        ass_avg = ass_attempts.aggregate(avg=Avg('percentage'))['avg'] or 0.0
        ass_count = ass_attempts.count()
        by_assessment.append({
            'assessment_id': str(ass.id),
            'title': ass.title,
            'assessment_type': ass.assessment_type,
            'submissions_count': ass_count,
            'average_score': round(float(ass_avg), 2),
        })

    # Common mistakes: questions with highest incorrect rates on teacher's assessments
    common_mistakes = []
    incorrect_questions = AnswerResponse.objects.filter(
        attempt__assessment__created_by=teacher,
        is_correct=False
    ).values('question__id', 'question__text').annotate(
        incorrect_count=Count('id')
    ).order_by('-incorrect_count')[:5]

    for item in incorrect_questions:
        common_mistakes.append({
            'question_id': str(item['question__id']),
            'question_text': item['question__text'][:100],
            'incorrect_count': item['incorrect_count']
        })

    return Response({
        'total_students': total_students,
        'assessments_created': assessments_created,
        'average_score': round(float(avg_score), 2),
        'proctored_exams': proctored_exams,
        'total_submissions': total_submissions,
        'by_assessment': by_assessment,
        'common_mistakes': common_mistakes,
    })



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_overview(request):
    """Super admin overview metrics."""
    if request.user.role not in ('super_admin', 'admin'):
        return Response({'error': 'Unauthorized'}, status=403)
        
    from apps.accounts.models import User, StudentProfile, TeacherProfile
    from apps.payments.models import Transaction
    
    revenue = Transaction.objects.filter(status='success').aggregate(total=Sum('amount'))['total'] or 0
    
    students_by_region = (
        StudentProfile.objects.filter(user__is_active=True)
        .values('region')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    teachers_by_region = (
        TeacherProfile.objects.filter(user__is_active=True)
        .values('region')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    region_counts = {}
    for item in students_by_region:
        reg = item['region'] or 'Unknown'
        region_counts[reg] = region_counts.get(reg, 0) + item['count']
    for item in teachers_by_region:
        reg = item['region'] or 'Unknown'
        region_counts[reg] = region_counts.get(reg, 0) + item['count']
        
    regions_list = [{'region': k, 'count': v} for k, v in sorted(region_counts.items(), key=lambda x: x[1], reverse=True)]
    
    return Response({
        'total_revenue_tzs': float(revenue),
        'active_users_count': User.objects.filter(is_active=True).count(),
        'active_users_per_region': regions_list
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_financial_csv(request):
    if request.user.role not in ('super_admin', 'admin'):
        return Response({'error': 'Unauthorized'}, status=403)
    import csv
    from django.http import HttpResponse
    from apps.payments.models import Transaction
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="financial_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Transaction ID', 'User', 'Amount', 'Payment Method', 'Status', 'Date'])
    for tx in Transaction.objects.all().select_related('user'):
        writer.writerow([tx.id, tx.user.full_name, tx.amount, tx.payment_method, tx.status, tx.created_at])
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_subscriptions_csv(request):
    if request.user.role not in ('super_admin', 'admin'):
        return Response({'error': 'Unauthorized'}, status=403)
    import csv
    from django.http import HttpResponse
    from apps.subscriptions.models import Subscription
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subscription_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Subscription ID', 'User', 'Plan', 'Status', 'Start Date', 'End Date'])
    for sub in Subscription.objects.all().select_related('user', 'plan'):
        writer.writerow([sub.id, sub.user.full_name, sub.plan.name, sub.status, sub.start_date, sub.end_date])
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_regional_csv(request):
    if request.user.role not in ('super_admin', 'admin'):
        return Response({'error': 'Unauthorized'}, status=403)
    import csv
    from django.http import HttpResponse
    from apps.accounts.models import StudentProfile, TeacherProfile
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="regional_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Region', 'User Role', 'User Name', 'Email'])
    for profile in StudentProfile.objects.all().select_related('user'):
        writer.writerow([profile.region or 'Unknown', 'Student', profile.user.full_name, profile.user.email])
    for profile in TeacherProfile.objects.all().select_related('user'):
        writer.writerow([profile.school.region if profile.school else 'Unknown', 'Teacher', profile.user.full_name, profile.user.email])
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_tutor_chat(request):
    """AI Homework Assistant chatbot simulation."""
    user_message = request.data.get('message', '')
    if not user_message:
        return Response({'error': 'Message is required.'}, status=400)
    response_text = (
        f"Great question! To solve your query about '{user_message}', let's break it down into 3 simple learning steps:\n"
        f"1. Understand the core definitions related to the question.\n"
        f"2. Use the standard formula/concept matching Tanzania's syllabus standards.\n"
        f"3. Verify your results. Let me know if you want to try a practice quiz together!"
    )
    return Response({'reply': response_text})
