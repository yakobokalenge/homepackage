from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from .models import School, Classroom
from .serializers import SchoolSerializer, ClassroomSerializer


class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['school_type', 'region', 'district', 'is_active']
    search_fields = ['name', 'registration_number']
    ordering_fields = ['name', 'created_at']


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.select_related('school', 'class_teacher')
    serializer_class = ClassroomSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['school', 'grade_level', 'academic_year']

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if not user.is_authenticated:
            return qs
        if user.role == 'school_admin':
            try:
                school = user.school_admin_profile.school
                return qs.filter(school=school)
            except Exception:
                return qs.none()
        elif user.role == 'teacher':
            return qs.filter(class_teacher=user)
        return qs

    @action(detail=True, methods=['get'])
    def download_results(self, request, pk=None):
        """Download student results for this classroom in CSV format (Assessments disabled)."""
        import csv
        from django.http import HttpResponse

        classroom = self.get_object()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="results_class_{classroom.name.replace(" ", "_")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Student Name', 'Student Email', 'Phone', 'Assessment Title',
            'Status', 'Score', 'Percentage %', 'Submitted At'
        ])
        return response

