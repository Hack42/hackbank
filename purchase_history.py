"""Bounded, incremental read-only index of the existing checkout log."""

from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
import re

CHECKOUT = re.compile(
    r"^(\S+) CHECKOUT\s+(\d+)\s+(\S+)\s+([\d.-]+) \*\s+([\d.-]+) "
    r"(LOSE|GAIN) EUR\s+([\d.-]+) # (.*)$"
)
MAX_READ = 8 * 1024 * 1024


class PurchaseIndex:
    def __init__(self, path="data/revbank.log"):
        self.path = Path(path)
        self.identity = None
        self.offset = 0
        self.signature = None
        self.records = defaultdict(lambda: deque(maxlen=10))
        self.last_purchase = {}
        self.coverage_start = None
        self.complete = False
        self.available = False

    def refresh(self):
        try:
            stat = self.path.stat()
            signature = (stat.st_ino, stat.st_size, stat.st_mtime_ns)
            if signature == self.signature:
                self.available = True
                return self
            reset = (self.identity != stat.st_ino or stat.st_size < self.offset
                     or (stat.st_size == self.offset and signature != self.signature))
            skip_partial = False
            if reset:
                self.records.clear()
                self.last_purchase.clear()
                self.coverage_start = None
                self.complete = stat.st_size <= MAX_READ
                self.offset = max(0, stat.st_size - MAX_READ)
                skip_partial = self.offset > 0
            if stat.st_size - self.offset > MAX_READ:
                self.records.clear()
                self.last_purchase.clear()
                self.coverage_start = None
                self.complete = False
                self.offset = stat.st_size - MAX_READ
                skip_partial = True
            with self.path.open("rb") as source:
                source.seek(self.offset)
                if skip_partial:
                    source.readline()  # Skip a partial first line at the window boundary.
                data = source.read(MAX_READ)
                end = data.rfind(b"\n") + 1
                self.offset = source.tell() - (len(data) - end)
            for line in data[:end].decode("utf-8", errors="replace").splitlines():
                if len(line) >= 19 and line[4:5] == "-":
                    if self.coverage_start is None:
                        self.coverage_start = line[:19]
                match = CHECKOUT.match(line)
                if not match:
                    continue
                date, transaction, user, count, price, direction, total, description = match.groups()
                try:
                    count, price, total = float(count), float(price), float(total)
                except ValueError:
                    continue
                if (direction != "LOSE" or count <= 0 or price <= 0
                        or description.startswith(("Undo ", "Give to ", "Taken by ", "Pfand "))
                        or description == "Declaratie"):
                    continue
                self.last_purchase[user] = max(self.last_purchase.get(user, date), date)
                record = {
                    "date": date, "transaction": int(transaction), "count": count,
                    "price": price, "total": total, "description": description,
                }
                self.records[user] = deque(sorted([*self.records[user], record], key=lambda item: item["date"])[-10:], maxlen=10)
            self.identity = stat.st_ino
            self.signature = signature
            self.available = True
        except OSError:
            self.available = False
        return self

    def activity(self):
        self.refresh()
        cutoff = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d_%H:%M:%S")
        covered = self.complete or (self.coverage_start is not None and self.coverage_start <= cutoff)
        return {"available": self.available and covered, "cutoff": cutoff,
                "last_purchase": dict(self.last_purchase)}

    def recent(self, user):
        self.refresh()
        return [dict(record) for record in reversed(self.records.get(user, []))] if self.available else []


purchase_index = PurchaseIndex()
