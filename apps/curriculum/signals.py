from auditlog.registry import auditlog

from .models import (
    CurriculumMatrix,
    InheritanceRule,
    LocalException,
    Subject,
    SubjectRule,
    WorkloadItem,
)

auditlog.register(Subject)
auditlog.register(CurriculumMatrix)
auditlog.register(WorkloadItem)
auditlog.register(SubjectRule)
auditlog.register(InheritanceRule)
auditlog.register(LocalException)
