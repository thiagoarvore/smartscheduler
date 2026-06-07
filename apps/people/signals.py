from auditlog.registry import auditlog

from .models import Teacher, TeacherAvailability, TeacherQualification

auditlog.register(Teacher)
auditlog.register(TeacherQualification)
auditlog.register(TeacherAvailability)
