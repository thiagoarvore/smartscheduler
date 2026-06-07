import pytest
from auditlog.models import LogEntry
from auditlog.registry import auditlog
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAccountsAuditlog:
    def test_user_model_is_registered_and_creates_audit_entries_on_save(self):
        user = User.objects.create_user(
            username="audituser",
            email="audit@gradecerta.com",
            password="testpass12345",
            first_name="Audit",
            last_name="User",
        )

        assert User in auditlog._registry
        assert LogEntry.objects.get_for_object(user).filter(action=LogEntry.Action.CREATE).exists()

        user.first_name = "Audited"
        user.save(update_fields=["first_name"])

        entries = LogEntry.objects.get_for_object(user)
        assert entries.filter(action=LogEntry.Action.UPDATE).exists()
