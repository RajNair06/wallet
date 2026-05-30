import pytest


class TestTransferAtomicity:
    async def test_successful_transfer_updates_both_wallets(
        self, client, auth_token, wallet, wallet2, session
    ):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "atomic-transfer-1",
        }
        payload = {"amount": 1000, "currency": "USD", "to_account_id": wallet2.id}

        resp = await client.patch("/transaction/transfer", json=payload, headers=headers)
        assert resp.status_code == 200

        await session.refresh(wallet)
        await session.refresh(wallet2)
        assert wallet.balance == 9000
        assert wallet2.balance == 6000

    async def test_insufficient_balance_rolls_back(
        self, client, auth_token, wallet, wallet2, session
    ):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "atomic-transfer-2",
        }
        payload = {"amount": 99999, "currency": "USD", "to_account_id": wallet2.id}

        resp = await client.patch("/transaction/transfer", json=payload, headers=headers)
        assert resp.status_code == 400

        await session.refresh(wallet)
        await session.refresh(wallet2)
        assert wallet.balance == 10000
        assert wallet2.balance == 5000

    async def test_invalid_recipient_rolls_back(
        self, client, auth_token, wallet, session
    ):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "atomic-transfer-3",
        }
        payload = {"amount": 500, "currency": "USD", "to_account_id": 99999}

        resp = await client.patch("/transaction/transfer", json=payload, headers=headers)
        assert resp.status_code == 404

        await session.refresh(wallet)
        assert wallet.balance == 10000

    async def test_currency_mismatch_rolls_back(
        self, client, auth_token, wallet, wallet2, session
    ):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "atomic-transfer-4",
        }
        payload = {"amount": 500, "currency": "EUR", "to_account_id": wallet2.id}

        resp = await client.patch("/transaction/transfer", json=payload, headers=headers)
        assert resp.status_code == 400

        await session.refresh(wallet)
        await session.refresh(wallet2)
        assert wallet.balance == 10000
        assert wallet2.balance == 5000

    async def test_transfer_to_self_fails(
        self, client, auth_token, wallet, session
    ):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "atomic-transfer-5",
        }
        payload = {"amount": 500, "currency": "USD", "to_account_id": wallet.id}

        resp = await client.patch("/transaction/transfer", json=payload, headers=headers)
        assert resp.status_code == 400

        await session.refresh(wallet)
        assert wallet.balance == 10000

    async def test_zero_amount_transfer_fails(
        self, client, auth_token, wallet, wallet2, session
    ):
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "atomic-transfer-6",
        }
        payload = {"amount": 0, "currency": "USD", "to_account_id": wallet2.id}

        resp = await client.patch("/transaction/transfer", json=payload, headers=headers)
        assert resp.status_code == 400

        await session.refresh(wallet)
        await session.refresh(wallet2)
        assert wallet.balance == 10000
        assert wallet2.balance == 5000

    async def test_ledger_entries_created(
        self, client, auth_token, wallet, wallet2, session
    ):
        from sqlmodel import select
        from db.models import LedgerEntry, EntryType

        headers = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "atomic-transfer-7",
        }
        payload = {"amount": 2000, "currency": "USD", "to_account_id": wallet2.id}

        resp = await client.patch("/transaction/transfer", json=payload, headers=headers)
        assert resp.status_code == 200

        result = await session.exec(select(LedgerEntry))
        entries = result.all()
        assert len(entries) == 2

        debit = next(e for e in entries if e.entry_type == EntryType.DEBIT)
        credit = next(e for e in entries if e.entry_type == EntryType.CREDIT)
        assert int(debit.wallet_id) == wallet.id
        assert int(credit.wallet_id) == wallet2.id
        assert debit.amount == 2000
        assert credit.amount == 2000
        assert debit.currency == "USD"
        assert credit.currency == "USD"

    async def test_concurrent_withdraw_uses_separate_sessions(
        self, client, auth_token, wallet, session
    ):
        headers1 = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "withdraw-atom-1",
        }
        headers2 = {
            "Authorization": f"Bearer {auth_token}",
            "X-Idempotency-Key": "withdraw-atom-2",
        }
        payload = {"amount": 3000, "currency": "USD"}

        resp1 = await client.patch("/transaction/withdraw", json=payload, headers=headers1)
        assert resp1.status_code == 200

        resp2 = await client.patch("/transaction/withdraw", json=payload, headers=headers2)
        assert resp2.status_code == 200

        await session.refresh(wallet)
        assert wallet.balance == 10000 - 3000 - 3000
