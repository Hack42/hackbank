from unittest.mock import Mock, patch

import kassa
from plugins.receipt import receipt
from plugins.undo import undo


def make_session():
    session = kassa.Session("SID", Mock())
    receipt_plugin = receipt("SID", session)
    undo_plugin = undo("SID", session)
    session.plugins = {"receipt": receipt_plugin, "undo": undo_plugin}
    session.receipt = receipt_plugin
    session.transID = 123
    return session, receipt_plugin, undo_plugin


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
