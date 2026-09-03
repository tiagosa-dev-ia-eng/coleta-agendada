"""Seed do catálogo de exames com preço para o laboratório demo (G-01).

Uso: python manage.py seed_catalog
Cria exames básicos e precifica para o primeiro laboratório encontrado.
"""
from django.core.management.base import BaseCommand

from apps.catalog.models import Exam, ExamPrice
from apps.organizations.models import Laboratory

EXAMS = [
    ("HEMO", "Hemograma completo", "35.00"),
    ("GLI", "Glicemia de jejum", "18.00"),
    ("TSH", "TSH (tireoestimulante)", "42.00"),
    ("T4L", "T4 livre", "38.00"),
    ("PCR", "Proteína C reativa", "25.00"),
    ("UR", "Urina tipo 1", "20.00"),
]


class Command(BaseCommand):
    help = "Seed do catálogo de exames + preços do laboratório (MVP G-01)."

    def handle(self, *args, **options):
        created = 0
        for code, name, _price in EXAMS:
            _exam, was_created = Exam.objects.get_or_create(code=code, defaults={"name": name})
            created += int(was_created)
        lab = Laboratory.objects.order_by("pk").first()
        if lab is not None:
            for code, _name, price in EXAMS:
                exam = Exam.objects.get(code=code)
                ExamPrice.objects.update_or_create(
                    laboratory=lab, exam=exam, defaults={"price": price, "active": True}
                )
            msg = f"seed_catalog OK: {len(EXAMS)} exames precificados para {lab.name}."
            self.stdout.write(self.style.SUCCESS(msg))
        else:
            self.stdout.write(self.style.WARNING("Nenhum laboratório; apenas exames criados."))
