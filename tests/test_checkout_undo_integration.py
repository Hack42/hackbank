from unittest.mock import Mock, patch

import kassa
from plugins.POS import POS
from plugins.accounts import accounts
from plugins.products import products
from plugins.receipt import receipt
from plugins.stock import stock
from plugins.undo import undo


def make_session():
    session = kassa.Session("SID", Mock())
    receipt_plugin = receipt("SID", session)
    undo_plugin = undo("SID", session)
    session.plugins = {"undo": undo_plugin, "receipt": receipt_plugin}
    session.receipt = receipt_plugin
    session.transID = 123
    return session, receipt_plugin, undo_plugin


def make_checkout_session():
    session = kassa.Session("SID", Mock())
    receipt_plugin = receipt("SID", session)
    accounts_plugin = accounts("SID", session)
    products_plugin = products("SID", session)
    stock_plugin = stock("SID", session)
    pos_plugin = POS("SID", session)
    session.plugins = {
        "POS": pos_plugin,
        "accounts": accounts_plugin,
        "products": products_plugin,
        "receipt": receipt_plugin,
        "stock": stock_plugin,
    }
    session.receipt = receipt_plugin
    session.accounts = accounts_plugin
    session.products = products_plugin
    session.stock = stock_plugin
    session.POS = pos_plugin
    return (
        session,
        receipt_plugin,
        accounts_plugin,
        products_plugin,
        stock_plugin,
        pos_plugin,
    )


def test_checkout_stores_undo_snapshot_after_receipt_checkout():
    session, receipt_plugin, undo_plugin = make_session()

    receipt_plugin.add(True, 2.5, "Product -you-", 2, None, "product1")

    with patch.object(undo_plugin, "loadundo"), patch.object(undo_plugin, "writeundo"):
        session.callhook("checkout", "alice")

    assert undo_plugin.undo[123]["beni"] == "alice"
    assert undo_plugin.undo[123]["totals"] == {"alice": -5.0}
    assert undo_plugin.undo[123]["receipt"] == [
        {
            "Lose": True,
            "description": "Product alice",
            "value": 2.5,
            "count": 2,
            "beni": "alice",
            "total": 5.0,
            "product": "product1",
        }
    ]


def test_doundo_runs_through_session_hooks_and_closes_receipt():
    session, receipt_plugin, undo_plugin = make_session()
    undo_plugin.undo = {
        123: {
            "totals": {"alice": -5.0},
            "receipt": [
                {
                    "Lose": True,
                    "description": "Product alice",
                    "value": 2.5,
                    "count": 2,
                    "beni": "alice",
                    "total": 5.0,
                    "product": "product1",
                }
            ],
            "beni": "alice",
        }
    }
    session.transID = 124

    with patch.object(undo_plugin, "loadundo"), patch.object(undo_plugin, "writeundo"):
        assert undo_plugin.doundo("123")

    assert 123 not in undo_plugin.undo
    assert undo_plugin.undo[124]["totals"] == {"alice": 5.0}
    assert receipt_plugin.receipt == []


def test_restore_runs_undo_then_restores_original_receipt_lines():
    session, receipt_plugin, undo_plugin = make_session()
    undo_plugin.undo = {
        123: {
            "totals": {"alice": -5.0},
            "receipt": [
                {
                    "Lose": True,
                    "description": "Product alice",
                    "value": 2.5,
                    "count": 2,
                    "beni": "alice",
                    "total": 5.0,
                    "product": "product1",
                }
            ],
            "beni": "alice",
        }
    }
    session.transID = 124

    with patch.object(undo_plugin, "loadundo"), patch.object(undo_plugin, "writeundo"):
        assert undo_plugin.dorestore("123")

    assert receipt_plugin.receipt == [
        {
            "Lose": True,
            "description": "Product alice",
            "value": 2.5,
            "count": 2,
            "beni": None,
            "total": 5.0,
            "product": "product1",
        }
    ]


def test_account_checkout_updates_accounts_stock_and_pos_receipt():
    (
        session,
        receipt_plugin,
        accounts_plugin,
        products_plugin,
        stock_plugin,
        pos_plugin,
    ) = make_checkout_session()
    accounts_plugin.accounts = {"alice": {"amount": 20.0, "lastupdate": "old"}}
    products_plugin.products = {
        "cola": {"price": 2.5, "description": "Cola", "aliases": []}
    }
    stock_plugin.stock = {"cola": 10}
    receipt_plugin.add(True, 2.5, "Cola -you-", 2, None, "cola")

    with patch("plugins.accounts.time.time", return_value=1300000123), patch.object(
        accounts_plugin, "readaccounts"
    ), patch.object(accounts_plugin, "writeaccount"), patch.object(
        accounts_plugin, "get_last_updated_accounts"
    ), patch.object(
        stock_plugin, "readstock"
    ), patch.object(
        stock_plugin, "writestock"
    ), patch.object(
        pos_plugin, "loadbons"
    ), patch.object(
        pos_plugin, "writebons"
    ), patch.object(
        pos_plugin, "drawer"
    ) as drawer:
        assert accounts_plugin.input("alice")

    assert session.transID == 123
    assert accounts_plugin.accounts["alice"]["amount"] == 15.0
    assert stock_plugin.stock["cola"] == 8
    assert pos_plugin.lastbonID == 123
    assert pos_plugin.bonnetjes[123]["totals"] == {"alice": -5.0}
    assert b"Cola alice" in pos_plugin.bonnetjes[123]["bon"]
    assert b"Nieuw saldo: 15.00" in pos_plugin.bonnetjes[123]["bon"]
    assert receipt_plugin.receipt == []
    drawer.assert_not_called()


def test_cash_checkout_updates_stock_opens_drawer_and_skips_account():
    (
        session,
        receipt_plugin,
        accounts_plugin,
        products_plugin,
        stock_plugin,
        pos_plugin,
    ) = make_checkout_session()
    accounts_plugin.accounts = {}
    products_plugin.products = {
        "cola": {"price": 2.5, "description": "Cola", "aliases": []}
    }
    stock_plugin.stock = {"cola": 10}
    receipt_plugin.add(True, 2.5, "Cola", 1, "cash", "cola")

    with patch("plugins.accounts.time.time", return_value=1300000124), patch.object(
        accounts_plugin, "readaccounts"
    ), patch.object(accounts_plugin, "writeaccount"), patch.object(
        accounts_plugin, "get_last_updated_accounts"
    ), patch.object(
        stock_plugin, "readstock"
    ), patch.object(
        stock_plugin, "writestock"
    ), patch.object(
        pos_plugin, "loadbons"
    ), patch.object(
        pos_plugin, "writebons"
    ), patch.object(
        pos_plugin, "drawer"
    ) as drawer:
        session.callhook("checkout", "cash")
        session.callhook("endsession", "cash")

    assert session.transID == 124
    assert accounts_plugin.accounts == {}
    assert stock_plugin.stock["cola"] == 9
    assert pos_plugin.lastbonID == 124
    assert pos_plugin.bonnetjes[124]["totals"] == {"cash": -2.5}
    assert b"Nieuw saldo" not in pos_plugin.bonnetjes[124]["bon"]
    assert receipt_plugin.receipt == []
    drawer.assert_called_once()
