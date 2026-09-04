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

    def test_version_internal_endpoint(self):
        resp = self.client.get("/version")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["name"], "coleta-agendada-api")
        self.assertRegex(resp.json()["version"], r"^\d+\.\d+\.\d+$")
