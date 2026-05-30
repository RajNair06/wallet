import pytest

import middleware.idempotency


class TestConcurrency:
    async def test_concurrent_lock_returns_409(self, client, auth_token, wallet):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "concurrent-lock-test",
        }
        payload = {"amount": 100, "currency": "USD"}

        await middleware.idempotency.redis.set(
            "lock:concurrent-lock-test", "locked", nx=True, ex=10
        )

        resp = await client.patch("/transaction/deposit", json=payload, headers=headers)
        assert resp.status_code == 409
        detail = resp.json().get("detail", "")
        assert "already being processed" in detail.lower()

        await middleware.idempotency.redis.delete("lock:concurrent-lock-test")

    async def test_completed_request_returns_cached_not_409(self, client, auth_token, wallet):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "completed-then-cached",
        }
        payload = {"amount": 100, "currency": "USD"}

        resp1 = await client.patch("/transaction/deposit", json=payload, headers=headers)
        assert resp1.status_code == 200

        resp2 = await client.patch("/transaction/deposit", json=payload, headers=headers)
        assert resp2.status_code == 200
        assert resp2.headers.get("x-cache-lookup") == "HIT"

    async def test_different_keys_not_blocked(self, client, auth_token, wallet):
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {"amount": 100, "currency": "USD"}

        await middleware.idempotency.redis.set(
            "lock:blocked-key", "locked", nx=True, ex=10
        )

        resp = await client.patch(
            "/transaction/deposit",
            json=payload,
            headers={**headers, "X-Idempotency-Key": "free-key"},
        )
        assert resp.status_code == 200

        await middleware.idempotency.redis.delete("lock:blocked-key")

    async def test_lock_released_after_request(self, client, auth_token, wallet):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "lock-release-test",
        }
        payload = {"amount": 100, "currency": "USD"}

        resp = await client.patch("/transaction/deposit", json=payload, headers=headers)
        assert resp.status_code == 200

        lock_exists = await middleware.idempotency.redis.get("lock:lock-release-test")
        assert lock_exists is None

    async def test_withdraw_concurrent_lock(self, client, auth_token, wallet):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "concurrent-withdraw",
        }
        payload = {"amount": 200, "currency": "USD"}

        await middleware.idempotency.redis.set(
            "lock:concurrent-withdraw", "locked", nx=True, ex=10
        )

        resp = await client.patch("/transaction/withdraw", json=payload, headers=headers)
        assert resp.status_code == 409

        await middleware.idempotency.redis.delete("lock:concurrent-withdraw")

    async def test_transfer_concurrent_lock(self, client, auth_token, wallet, wallet2):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "concurrent-transfer",
        }
        payload = {"amount": 500, "currency": "USD", "to_account_id": wallet2.id}

        await middleware.idempotency.redis.set(
            "lock:concurrent-transfer", "locked", nx=True, ex=10
        )

        resp = await client.patch("/transaction/transfer", json=payload, headers=headers)
        assert resp.status_code == 409

        await middleware.idempotency.redis.delete("lock:concurrent-transfer")
