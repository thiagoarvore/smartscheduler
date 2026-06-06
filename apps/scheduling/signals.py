from auditlog.registry import auditlog

from .models import (
    Conflict,
    LessonAssignment,
    LessonComponent,
    Timetable,
    TimetableSlot,
    TimetableVersion,
    Validation,
)

auditlog.register(Timetable)
auditlog.register(TimetableSlot)
auditlog.register(TimetableVersion)
auditlog.register(LessonAssignment)
auditlog.register(LessonComponent)
auditlog.register(Validation)
auditlog.register(Conflict)
