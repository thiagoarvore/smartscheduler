from auditlog.registry import auditlog

from .models import ClassGroup, Period, Series, TeachingLevel, Unit

auditlog.register(Unit)
auditlog.register(TeachingLevel)
auditlog.register(Period)
auditlog.register(Series)
auditlog.register(ClassGroup)
