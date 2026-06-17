"""Shared fixtures for the camt053-lsp test suite."""

import pytest

_RECORD = {
    "statement_msg_id": "RVSL-STMT-0001",
    "creation_date_time": "2026-06-15T08:00:00",
    "statement_id": "RVSL-STMT-0001",
    "electronic_seq_nb": "1",
    "account_id": "GB29NWBK60161331926819",
    "account_currency": "EUR",
    "account_owner_name": "Acme Treasury Ltd",
    "account_servicer_bic": "NWBKGB2LXXX",
    "bal_type_code": "CLBD",
    "bal_amount": "10000.00",
    "bal_currency": "EUR",
    "bal_credit_debit": "CRDT",
    "bal_date": "2026-06-15",
    "entry_ref": "RVSL-NTRY-0001",
    "original_ref": "NTRY-0001",
    "amount": "1500.00",
    "currency": "EUR",
    "credit_debit": "DBIT",
    "reversal_indicator": "true",
    "status": "BOOK",
    "booking_date": "2026-06-15",
    "value_date": "2026-06-15",
    "end_to_end_id": "E2E-0001",
    "tx_id": "TX-0001",
    "reason_code": "AC04",
    "additional_info": "Reversal of NTRY-0001: Closed Account Number",
    "counterparty_name": "Globex SA",
    "counterparty_account": "DE89370400440532013000",
}


@pytest.fixture
def reversal_record() -> dict:
    """A complete, valid flat reversing-entry record."""
    return dict(_RECORD)
