from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Avg, Count, Q, Sum
from apps.content.models import Subject, Topic
from apps.assessments.models import Assessment, AssessmentAttempt, AnswerResponse


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_overview(request):
    """Student's performance overview."""
    attempts = AssessmentAttempt.objects.filter(student=request.user, status__in=('submitted', 'graded'))
    total = attempts.count()
    avg = attempts.aggregate(avg=Avg('percentage'))['avg'] or 0
    by_subject = (
        attempts.values('assessment__subject__name')
        .annotate(avg_score=Avg('percentage'), count=Count('id'))
        .order_by('-avg_score')
    )
    return Response({
        'total_assessments': total,
        'average_score': round(avg, 1),
        'by_subject': list(by_subject),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weak_topics(request):
    """Identify student's weak topics based on incorrect answers."""
    responses = AnswerResponse.objects.filter(
        attempt__student=request.user, is_correct=False
    ).values('question__topic__name', 'question__subject__name').annotate(
        wrong_count=Count('id')
    ).order_by('-wrong_count')[:10]
    return Response(list(responses))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_class_performance(request):
    """Teacher's class-level analytics."""
    attempts = AssessmentAttempt.objects.filter(
        assessment__created_by=request.user
    )
    total_students = attempts.values('student').distinct().count()
    assessments_created = Assessment.objects.filter(created_by=request.user).count()
    
    avg_score = attempts.aggregate(avg=Avg('percentage'))['avg'] or 0
    
    by_assessment = (
        attempts.values('assessment__title')
        .annotate(avg_score=Avg('percentage'), total=Count('id'))
        .order_by('-avg_score')
    )

    common_mistakes = (
        AnswerResponse.objects.filter(
            question__created_by=request.user,
            is_correct=False
        )
        .values('question__text', 'question__subject__name')
        .annotate(wrong_count=Count('id'))
        .order_by('-wrong_count')[:5]
    )
    
    return Response({
        'total_students': total_students,
        'assessments_created': assessments_created,
        'average_score': round(avg_score, 1),
        'proctored_exams': 0,
        'total_submissions': attempts.count(),
        'by_assessment': list(by_assessment),
        'common_mistakes': list(common_mistakes),
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
