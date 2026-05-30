import pytest


class TestIdempotency:
    async def test_same_key_returns_cached_response(self, client, auth_token, wallet):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "unique-key-1",
        }
        payload = {"amount": 100, "currency": "USD"}

        resp1 = await client.patch("/transaction/deposit", json=payload, headers=headers)
        assert resp1.status_code == 200
        data1 = resp1.json()

        resp2 = await client.patch("/transaction/deposit", json=payload, headers=headers)
        assert resp2.status_code == 200
        assert resp2.headers.get("x-cache-lookup") == "HIT"
        assert resp2.json() == data1

    async def test_different_keys_are_independent(self, client, auth_token, wallet):
        common_headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {"amount": 100, "currency": "USD"}

        resp1 = await client.patch(
            "/transaction/deposit",
            json=payload,
            headers={**common_headers, "X-Idempotency-Key": "key-a"},
        )
        resp2 = await client.patch(
            "/transaction/deposit",
            json=payload,
            headers={**common_headers, "X-Idempotency-Key": "key-b"},
        )
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.headers.get("x-cache-lookup") is None
        assert resp2.headers.get("x-cache-lookup") is None

    async def test_get_requests_are_not_idempotency_checked(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}", "X-Idempotency-Key": "key-get"}
        resp1 = await client.get("/transaction/history", headers=headers)
        assert resp1.status_code == 404
        resp2 = await client.get("/transaction/history", headers=headers)
        assert resp2.status_code == 404

    async def test_withdraw_idempotency(self, client, auth_token, wallet):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "withdraw-key-1",
        }
        payload = {"amount": 200, "currency": "USD"}

        resp1 = await client.patch("/transaction/withdraw", json=payload, headers=headers)
        assert resp1.status_code == 200
        data1 = resp1.json()

        resp2 = await client.patch("/transaction/withdraw", json=payload, headers=headers)
        assert resp2.status_code == 200
        assert resp2.headers.get("x-cache-lookup") == "HIT"
        assert resp2.json() == data1

    async def test_transfer_idempotency(self, client, auth_token, wallet, wallet2):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "transfer-key-1",
        }
        payload = {"amount": 500, "currency": "USD", "to_account_id": wallet2.id}

        resp1 = await client.patch("/transaction/transfer", json=payload, headers=headers)
        assert resp1.status_code == 200
        data1 = resp1.json()

        resp2 = await client.patch("/transaction/transfer", json=payload, headers=headers)
        assert resp2.status_code == 200
        assert resp2.headers.get("x-cache-lookup") == "HIT"
        assert resp2.json() == data1

    async def test_no_idempotency_key_returns_validation_error(self, client, auth_token, wallet):
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {"amount": 50, "currency": "USD"}
        resp = await client.patch("/transaction/deposit", json=payload, headers=headers)
        assert resp.status_code == 422
