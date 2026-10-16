"""Seed the isolated development data once. Never reads production data."""

from pathlib import Path
import shutil

data = Path("data")
data.mkdir(exist_ok=True)
if not (data / "revbank.accounts").exists():
    for source in Path("fakedata").glob("revbank.*"):
        shutil.copyfile(source, data / source.name)

    names = [
        "alice", "bob", "charlie", "dana", "eddie", "floris", "grace", "hugo",
        "iris", "jules", "kim", "lars", "mara", "noor", "oscar", "pim", "quinn",
        "raboof", "robin", "sam", "tess", "uma", "vincent", "wouter", "yara", "zoe",
    ]
    balances = [24.50, 8.75, -4.20, 42.00, 15.80, 31.25, 6.50, -18.50]
    (data / "revbank.accounts").write_text(
        "".join(f"{name:20} {balances[i % len(balances)]:+8.2f} 2026-10-16_12:00:00\n"
                for i, name in enumerate(names))
        + "guest                  +12.50 2026-10-16_12:00:00\n",
        encoding="utf-8",
    )
    (data / "revbank.members").write_text("\n".join(names) + "\n", encoding="utf-8")
    (data / "revbank.products").write_text(
        """# Beer
clubmatebeer 2.50 Club-Mate beer
grolsch 1.50 Grolsch pilsner
ipa 3.25 India pale ale
radler 1.75 Radler 0.0%
weizen 2.75 Weizen
tripel 3.50 Belgian tripel
stout 3.00 Coffee stout
# Soft drinks
clubmate 2.00 Club-Mate
cola 1.25 Coca-Cola
colazero 1.25 Coca-Cola Zero
gingerbeer 2.25 Ginger beer
icetea 1.50 Ice tea
tonic 1.75 Tonic water
sparkling 1.00 Sparkling water
orangejuice 1.50 Orange juice
# Hot drinks
coffee 0.50 Coffee
espresso 0.75 Espresso
tea 0.50 Tea
hotchocolate 1.00 Hot chocolate
# Snacks
crisps 1.00 Paprika crisps
stroopwafel 0.75 Stroopwafel
chocolate 1.25 Chocolate bar
nuts 1.50 Salted peanuts
noodles 1.75 Instant noodles
pizza 4.50 Pizza margherita
""",
        encoding="utf-8",
    )
    (data / "revbank.stock").write_text(
        "".join(f"{name} 42\n" for name in ["grolsch", "ipa", "clubmate", "cola", "coffee", "crisps"]),
        encoding="utf-8",
    )
