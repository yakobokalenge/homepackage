import uuid
from django.core.management.base import BaseCommand
from apps.schools.models import School, Classroom

class Command(BaseCommand):
    help = "Seed Tanzania regions and private primary schools with classrooms."

    def handle(self, *args, **kwargs):
        regions = [
            "Arusha", "Dar es Salaam", "Dodoma", "Geita", "Iringa", "Kagera",
            "Katavi", "Kigoma", "Kilimanjaro", "Lindi", "Manyara", "Mara",
            "Mbeya", "Morogoro", "Mtwara", "Mwanza", "Njombe", "Pemba North",
            "Pemba South", "Pwani (Coast)", "Rukwa", "Ruvuma", "Shinyanga",
            "Simiyu", "Singida", "Songwe", "Tabora", "Tanga",
            "Zanzibar Central/South", "Zanzibar North", "Zanzibar Urban/West"
        ]

        private_primary_schools = [
            # Arusha
            ("St. Constantine's International School", "Arusha"),
            ("Braeburn International School Arusha", "Arusha"),
            ("Kennedy House School", "Arusha"),
            ("Arusha Meru International School", "Arusha"),
            ("School of St Jude", "Arusha"),
            ("Jaffery Academy Arusha", "Arusha"),
            ("Mount Mount Meru Flowers School", "Arusha"),
            ("St. Joseph Primary School Arusha", "Arusha"),
            # Dar es Salaam
            ("Feza Primary School", "Dar es Salaam"),
            ("Haven of Peace Academy (HOPAC)", "Dar es Salaam"),
            ("Al Muntazir Islamic Primary School", "Dar es Salaam"),
            ("Dar es Salaam Independent School (DIS)", "Dar es Salaam"),
            ("International School of Tanganyika (IST)", "Dar es Salaam"),
            ("Aga Khan Mzizima Primary School", "Dar es Salaam"),
            ("St. Joseph's Primary School Dar", "Dar es Salaam"),
            ("St. Mary's Primary School Mbezi", "Dar es Salaam"),
            ("Tusiime Primary School", "Dar es Salaam"),
            ("Academic International School", "Dar es Salaam"),
            ("Atlas Primary School", "Dar es Salaam"),
            ("Fountain of Joy Primary School", "Dar es Salaam"),
            ("Mlimani English Medium School", "Dar es Salaam"),
            ("Laureates International School", "Dar es Salaam"),
            ("St. Florence Academy", "Dar es Salaam"),
            ("Elysian Primary School", "Dar es Salaam"),
            ("Kaizirege Primary School", "Dar es Salaam"),
            # Kilimanjaro
            ("Shauritanga Primary School", "Kilimanjaro"),
            ("St. Margaret Primary School", "Kilimanjaro"),
            ("Jude English Medium Primary School", "Kilimanjaro"),
            ("Moshi Co-operative Primary School", "Kilimanjaro"),
            # Mwanza
            ("Holy Spirit Primary School", "Mwanza"),
            ("Ebenezer Primary School", "Mwanza"),
            ("Mwanza Alliance Primary School", "Mwanza"),
            ("Isamilo International School", "Mwanza"),
            ("Lake Primary School", "Mwanza"),
            ("Victoria Primary School", "Mwanza"),
            # Pwani
            ("Marian Primary School", "Pwani (Coast)"),
            ("Baobab Primary School", "Pwani (Coast)"),
            ("St. Augustine Primary School", "Pwani (Coast)"),
            # Mbeya
            ("St. Mary's Primary School Mbeya", "Mbeya"),
            ("Mbeya Peak English Medium School", "Mbeya"),
            ("Ivumwe Primary School", "Mbeya"),
            # Morogoro
            ("Morogoro International School", "Morogoro"),
            ("St. Monica English Medium School", "Morogoro"),
            ("Kihonda Primary School", "Morogoro"),
            # Tanga
            ("Tanga International School", "Tanga"),
            ("St. Joseph's Primary School Tanga", "Tanga"),
            # Dodoma
            ("Blue Sky Primary School", "Dodoma"),
            ("Dodoma English Medium School", "Dodoma"),
            ("Claret English Medium Primary School", "Dodoma"),
            ("St. Gemma Primary School", "Dodoma"),
            ("One World Primary School", "Dodoma"),
            ("Little Treasures English Medium School", "Dodoma"),
            ("Trust Primary School", "Dodoma"),
            ("Good Samaritan Primary School", "Dodoma"),
            ("Fountain Gate Academy", "Dodoma"),
            ("Canon Mwita English Medium Primary School", "Dodoma"),
            ("St. Gaspar Primary School", "Dodoma"),
            ("Martin Luther School Dodoma", "Dodoma"),
        ]

        self.stdout.write("Seeding private primary schools...")
        for school_name, region in private_primary_schools:
            school, created = School.objects.get_or_create(
                name=school_name,
                defaults={
                    "school_type": School.SchoolType.PRIMARY,
                    "ownership": School.Ownership.PRIVATE,
                    "region": region,
                    "country": "Tanzania",
                    "is_active": True,
                    "is_verified": True,
                    "registration_number": f"PRI/{uuid.uuid4().hex[:8].upper()}"
                }
            )
            if created:
                self.stdout.write(f"Created school: {school_name} in {region}")
            
            # Auto-create Standard 1 to Standard 7 classrooms for each school
            for std in range(1, 8):
                class_name = f"Standard {std}"
                classroom, class_created = Classroom.objects.get_or_create(
                    school=school,
                    name=class_name,
                    defaults={
                        "grade_level": class_name,
                        "stream": Classroom.Stream.A,
                        "academic_year": "2026",
                        "is_active": True
                    }
                )
                if class_created:
                    self.stdout.write(f"  Created class: {class_name} for {school_name}")

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
