from pyrate_limiter import Duration, Limiter, Rate
from fastapi_limiter.depends import RateLimiter

from main import app as _app
from core.limiter import (auth_limiter, deposit_limiter, sensitive_txn_limiter,
                          signup_limiter)


class TestRateLimiting:
    @staticmethod
    def _override_with_fresh_limiter(rate_per_minute: int, original):
        fresh = RateLimiter(limiter=Limiter(Rate(rate_per_minute, Duration.MINUTE)))
        _app.dependency_overrides[original] = fresh
        return fresh

    def _setup_limiters(self, signup=5, auth=5, sensitive=10, deposit=30):
        self._override_with_fresh_limiter(signup, signup_limiter)
        self._override_with_fresh_limiter(auth, auth_limiter)
        self._override_with_fresh_limiter(sensitive, sensitive_txn_limiter)
        self._override_with_fresh_limiter(deposit, deposit_limiter)

    def _teardown_limiters(self):
        _app.dependency_overrides[signup_limiter] = lambda: None
        _app.dependency_overrides[auth_limiter] = lambda: None
        _app.dependency_overrides[sensitive_txn_limiter] = lambda: None
        _app.dependency_overrides[deposit_limiter] = lambda: None

    async def test_signup_rate_limit(self, client):
        self._setup_limiters(signup=3)
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": "new@example.com",
            "password": "password123",
        }

        for i in range(3):
            resp = await client.post(
                "/signup",
                json={**payload, "email": f"new{i}@example.com"},
            )
            assert resp.status_code == 200, f"Request {i+1} failed: {resp.text}"

        resp = await client.post(
            "/signup",
            json={**payload, "email": "overflow@example.com"},
        )
        assert resp.status_code == 429
        self._teardown_limiters()

    async def test_auth_rate_limit(self, client, test_user):
        self._setup_limiters(auth=3)
        for i in range(3):
            resp = await client.post(
                "/token",
                data={"username": "test@example.com", "password": "testpassword123"},
            )
            assert resp.status_code == 200, f"Request {i+1} failed: {resp.text}"

        resp = await client.post(
            "/token",
            data={"username": "test@example.com", "password": "testpassword123"},
        )
        assert resp.status_code == 429
        self._teardown_limiters()

    async def test_sensitive_txn_rate_limit(self, client, auth_token, wallet):
        self._setup_limiters(sensitive=5)
        headers = {"Authorization": f"Bearer {auth_token}"}

        for i in range(5):
            resp = await client.patch(
                "/transaction/withdraw",
                json={"amount": 1, "currency": "USD"},
                headers={**headers, "X-Idempotency-Key": f"txn-rate-{i}"},
            )
            assert resp.status_code == 200, f"Request {i+1} failed: {resp.text}"

        resp = await client.patch(
            "/transaction/withdraw",
            json={"amount": 1, "currency": "USD"},
            headers={**headers, "X-Idempotency-Key": "txn-rate-overflow"},
        )
        assert resp.status_code == 429
        self._teardown_limiters()

    async def test_deposit_rate_limit(self, client, auth_token, wallet):
        self._setup_limiters(deposit=5)
        headers = {"Authorization": f"Bearer {auth_token}"}

        for i in range(5):
            resp = await client.patch(
                "/transaction/deposit",
                json={"amount": 1, "currency": "USD"},
                headers={**headers, "X-Idempotency-Key": f"dep-rate-{i}"},
            )
            assert resp.status_code == 200, f"Request {i+1} failed: {resp.text}"

        resp = await client.patch(
            "/transaction/deposit",
            json={"amount": 1, "currency": "USD"},
            headers={**headers, "X-Idempotency-Key": "dep-rate-overflow"},
        )
        assert resp.status_code == 429
        self._teardown_limiters()

    async def test_different_limits_on_different_endpoints(
        self, client, auth_token, wallet
    ):
        self._setup_limiters(sensitive=3, deposit=10)
        headers = {"Authorization": f"Bearer {auth_token}"}

        for i in range(3):
            resp = await client.patch(
                "/transaction/withdraw",
                json={"amount": 1, "currency": "USD"},
                headers={**headers, "X-Idempotency-Key": f"diff-{i}"},
            )
            assert resp.status_code == 200, f"Withdraw {i+1} failed"

        resp = await client.patch(
            "/transaction/withdraw",
            json={"amount": 1, "currency": "USD"},
            headers={**headers, "X-Idempotency-Key": "diff-overflow"},
        )
        assert resp.status_code == 429

        resp = await client.patch(
            "/transaction/deposit",
            json={"amount": 1, "currency": "USD"},
            headers={**headers, "X-Idempotency-Key": "diff-deposit"},
        )
        assert resp.status_code == 200, "Deposit should still be allowed"
        self._teardown_limiters()
