from django.test import TestCase


class HealthChecksTests(TestCase):
    def test_health_liveness(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")
        self.assertEqual(resp.json()["service"], "coleta-agendada-api")

    def test_ready_readiness(self):
        resp = self.client.get("/ready")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["checks"]["database"], "ok")
