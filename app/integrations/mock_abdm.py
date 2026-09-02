from app.integrations.abdm import ABDMClient
from app.services.audit_service import log_action


class MockABDMClient(ABDMClient):
    def sync_patient(self, patient, user_id=None) -> dict:
        result = {
            "status": "simulated",
            "abha_id": patient.abha_id,
            "message": "ABDM sync is simulated in demo mode. No national health ID was contacted.",
        }
        log_action(user_id, "abdm_sync", "patient", patient.id)
        return result
