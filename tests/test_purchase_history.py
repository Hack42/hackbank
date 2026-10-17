from unittest.mock import patch

from purchase_history import PurchaseIndex


def sale(user, number=1, description="Cola", date="2026-10-15_12:00:00"):
    return f"{date} CHECKOUT {number} {user} 1 * 1.25 LOSE EUR 1.25 # {description}\n"


def test_recent_ten_are_exact_user_matches_and_incremental(tmp_path):
    path = tmp_path / "sales.log"
    path.write_text("".join(sale("Jos", n) for n in range(12)) + sale("Jos2", 99))
    index = PurchaseIndex(path)
    assert len(index.recent("Jos")) == 10
    assert all(row["transaction"] != 99 for row in index.recent("Jos"))
    offset = index.offset
    with path.open("a") as output:
        output.write(sale("Jos", 100, date="2026-10-16_12:00:00"))
    assert index.recent("Jos")[0]["transaction"] == 100
    assert index.offset > offset
    assert index.activity()["available"]


def test_cache_skips_reads_and_does_not_leak_profile_mutations(tmp_path):
    path = tmp_path / "sales.log"
    path.write_text(sale("Jos"))
    index = PurchaseIndex(path)
    records = index.recent("Jos")
    records[0]["description"] = "changed by caller"
    with patch.object(type(path), "open", side_effect=AssertionError("re-read unchanged log")):
        assert index.recent("Jos")[0]["description"] == "Cola"


def test_missing_rotated_and_partial_logs(tmp_path):
    path = tmp_path / "sales.log"
    index = PurchaseIndex(path)
    assert not index.activity()["available"]
    path.write_text(sale("Jos")[:-1])
    assert index.recent("Jos") == []
    with path.open("a") as output:
        output.write("\n")
    assert len(index.recent("Jos")) == 1
    path.unlink()
    assert index.recent("Jos") == []
    path.write_text(sale("nino"))
    assert index.recent("Jos") == []
    assert len(index.recent("nino")) == 1


def test_large_logs_have_a_read_limit_and_do_not_claim_full_year_coverage(tmp_path, monkeypatch):
    path = tmp_path / "sales.log"
    path.write_text(sale("Jos", date="2026-10-16_12:00:00") * 100)
    monkeypatch.setattr("purchase_history.MAX_READ", 512)
    index = PurchaseIndex(path)
    assert len(index.recent("Jos")) < 10
    assert not index.activity()["available"]


def test_refunds_and_undo_entries_are_not_purchase_history(tmp_path):
    path = tmp_path / "sales.log"
    path.write_text(sale("Jos") + sale("Jos", 2, "Undo 1")
                    + sale("Jos", 3).replace("LOSE", "GAIN"))
    assert len(PurchaseIndex(path).recent("Jos")) == 1
