import json
from unittest.mock import Mock, call, patch

import pytest

import plugins.party as party_module
from plugins.party import PARTY_USER, STATE_FILE, party


def make_master(accounts=None):
    master = Mock()
    master.accounts.accounts = accounts or {}
    master.accounts.readaccounts = Mock()
    master.accounts.writeaccount = Mock()
    master.accounts.publish_members = Mock()
    master.POS.printparty = Mock()
    return master


def test_help_and_member_override():
    plugin = party("SID", make_master())

    assert plugin.help() == {
        "partymodeon": "Enable party mode",
        "partymodeoff": "Disable party mode",
    }
    assert plugin.member_override() is None

    plugin.active = True

    assert plugin.member_override() == [PARTY_USER]


def test_loadstate_missing_file_is_inactive(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plugin = party("SID", make_master())
    plugin.active = True
    plugin.started_amount = 10.0
    plugin.started_at = "old"

    plugin.loadstate()

    assert not plugin.active
    assert plugin.started_amount == 0.0
    assert plugin.started_at == ""


def test_loadstate_invalid_file_is_inactive(tmp_path, monkeypatch, caplog):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / STATE_FILE).write_text("not json", encoding="utf-8")
    plugin = party("SID", make_master())

    plugin.loadstate()

    assert not plugin.active
    assert "party_state_load_failed" in caplog.text


def test_writestate_and_loadstate_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plugin = party("SID", make_master())
    plugin.active = True
    plugin.started_amount = 42.5
    plugin.started_at = "2026-05-28_20:00:00"

    plugin.writestate()

    loaded = party("SID", make_master())
    loaded.loadstate()
    assert loaded.active
    assert loaded.started_amount == 42.5
    assert loaded.started_at == "2026-05-28_20:00:00"


def test_atomic_write_removes_temp_file_when_write_fails(tmp_path, monkeypatch):
    output = tmp_path / "data" / "revbank.party"
    created_temp = tmp_path / "data" / "revbank.party.tmp"

    def fake_mkstemp(prefix, dir, text):  # pylint: disable=unused-argument
        output.parent.mkdir(parents=True, exist_ok=True)
        created_temp.write_text("partial", encoding="utf-8")
        return 123, str(created_temp)

    monkeypatch.setattr(party_module.tempfile, "mkstemp", fake_mkstemp)
    monkeypatch.setattr(
        party_module.os,
        "fdopen",
        Mock(side_effect=OSError("write failed")),
    )

    with pytest.raises(OSError):
        party_module._atomic_write(str(output), {"active": True})

    assert not created_temp.exists()


def test_atomic_write_tolerates_missing_temp_file_on_failure(tmp_path, monkeypatch):
    output = tmp_path / "data" / "revbank.party"

    monkeypatch.setattr(
        party_module.tempfile,
        "mkstemp",
        Mock(return_value=(123, str(tmp_path / "missing.tmp"))),
    )
    monkeypatch.setattr(
        party_module.os,
        "fdopen",
        Mock(side_effect=OSError("write failed")),
    )
    monkeypatch.setattr(
        party_module.os,
        "unlink",
        Mock(side_effect=FileNotFoundError),
    )

    with pytest.raises(OSError):
        party_module._atomic_write(str(output), {"active": True})


@patch("plugins.party.time.strftime", return_value="2026-05-28_20:00:00")
def test_partymodeon_persists_state_and_publishes_party_member(
    _mock_strftime, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    master = make_master(
        {"party": {"amount": 100.0, "lastupdate": "2026-05-28_19:00:00"}}
    )
    plugin = party("SID", master)

    assert plugin.input("partymodeon") is True

    master.accounts.readaccounts.assert_called_once()
    master.accounts.writeaccount.assert_not_called()
    master.accounts.publish_members.assert_called_once()
    master.send_message.assert_has_calls(
        [
            call(
                True,
                "accounts/party",
                json.dumps({"amount": 100.0, "lastupdate": "2026-05-28_19:00:00"}),
            ),
            call(True, "message", "Party mode on; started with EUR 100.00"),
        ]
    )
    data = json.loads((tmp_path / STATE_FILE).read_text(encoding="utf-8"))
    assert data == {
        "active": True,
        "started_amount": 100.0,
        "started_at": "2026-05-28_20:00:00",
    }


@patch("plugins.party.time.strftime", return_value="2026-05-28_20:00:00")
def test_partymodeon_creates_party_account(_mock_strftime, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    master = make_master({})
    plugin = party("SID", master)

    assert plugin.input("partymodeon") is True

    assert master.accounts.accounts[PARTY_USER] == {
        "amount": 0.0,
        "lastupdate": "2026-05-28_20:00:00",
    }
    master.accounts.writeaccount.assert_called_once()


def test_partymodeon_when_already_active_keeps_started_amount(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / STATE_FILE).write_text(
        json.dumps(
            {
                "active": True,
                "started_amount": 75.0,
                "started_at": "2026-05-28_19:00:00",
            }
        ),
        encoding="utf-8",
    )
    master = make_master(
        {"party": {"amount": 50.0, "lastupdate": "2026-05-28_20:00:00"}}
    )
    plugin = party("SID", master)

    assert plugin.input("partymodeon") is True

    assert plugin.active
    assert plugin.started_amount == 75.0
    master.send_message.assert_any_call(True, "message", "Party mode is already on")


def test_startup_restores_active_party_mode(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / STATE_FILE).write_text(
        json.dumps(
            {
                "active": True,
                "started_amount": 100.0,
                "started_at": "2026-05-28_20:00:00",
            }
        ),
        encoding="utf-8",
    )
    master = make_master(
        {"party": {"amount": 80.0, "lastupdate": "2026-05-28_21:00:00"}}
    )
    plugin = party("SID", master)

    plugin.startup()

    assert plugin.member_override() == [PARTY_USER]
    master.accounts.readaccounts.assert_called_once()
    master.accounts.publish_members.assert_called_once()


def test_partymodeoff_prints_receipt_and_restores_members(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / STATE_FILE).write_text(
        json.dumps(
            {
                "active": True,
                "started_amount": 100.0,
                "started_at": "2026-05-28_20:00:00",
            }
        ),
        encoding="utf-8",
    )
    master = make_master(
        {"party": {"amount": 72.5, "lastupdate": "2026-05-28_22:00:00"}}
    )
    plugin = party("SID", master)

    assert plugin.input("partymodeoff") is True

    master.POS.printparty.assert_called_once_with(
        100.0, 72.5, 27.5, "2026-05-28_20:00:00"
    )
    master.accounts.publish_members.assert_called_once()
    master.send_message.assert_any_call(
        True,
        "message",
        "Party mode off; started EUR 100.00, left EUR 72.50, settled EUR 27.50",
    )
    data = json.loads((tmp_path / STATE_FILE).read_text(encoding="utf-8"))
    assert data["active"] is False


def test_partymodeoff_without_active_mode_does_not_print(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plugin = party("SID", make_master())

    assert plugin.input("partymodeoff") is True

    plugin.master.POS.printparty.assert_not_called()
    plugin.master.send_message.assert_called_once_with(
        True, "message", "Party mode is not on"
    )


def test_partymodeoff_keeps_active_when_print_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / STATE_FILE).write_text(
        json.dumps(
            {
                "active": True,
                "started_amount": 100.0,
                "started_at": "2026-05-28_20:00:00",
            }
        ),
        encoding="utf-8",
    )
    master = make_master(
        {"party": {"amount": 72.5, "lastupdate": "2026-05-28_22:00:00"}}
    )
    master.POS.printparty.side_effect = OSError("printer unreachable")
    plugin = party("SID", master)

    assert plugin.input("partymodeoff") is True

    data = json.loads((tmp_path / STATE_FILE).read_text(encoding="utf-8"))
    assert data["active"] is True
    master.accounts.publish_members.assert_not_called()
    master.send_message.assert_any_call(
        True,
        "message",
        "Party mode receipt print failed: printer unreachable",
    )


def test_input_ignores_other_text():
    assert party("SID", make_master()).input("other") is None
