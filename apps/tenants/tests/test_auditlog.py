import pytest
from auditlog.models import LogEntry
from auditlog.registry import auditlog

from apps.tenants.models import Tenant


@pytest.mark.django_db
class TestTenantAuditlog:
    def test_tenant_model_is_registered_and_creates_audit_entries_on_save(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")

        assert Tenant in auditlog._registry
        assert LogEntry.objects.get_for_object(tenant).filter(action=LogEntry.Action.CREATE).exists()
