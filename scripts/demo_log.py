"""Writes a synthetic UE_game.log so the app can be tried without the game.

    python -I scripts/demo_log.py <output.log> [--maps N] [--speed X]

Point the app at the file (Settings -> Game log -> Choose file) and watch a
few map runs play out in real time. --speed 10 makes a 60 s map take 6 s.
The line formats mirror what the game prints with "Enable Log" turned on.
"""

import argparse
import random
import time
from datetime import datetime, timezone
from pathlib import Path

PLAYER_ID = "900000000000000001"
FE = "100300"
BEACON = "400015"  # Blistering Lava Sea Beacon (Timemark 8)
COMPASS = "10250"  # Sandlord Compass
LOOT_POOL = ["6007", "6118", "6003", "5029", "410102", "8310", "370201", "10140", "5144"]


class Log:
    def __init__(self, path: Path, speed: float):
        self.f = path.open("a", encoding="utf-8", newline="\n")
        self.speed = speed
        self.frame = 1

    def ts(self) -> str:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y.%m.%d-%H.%M.%S:") + f"{now.microsecond // 1000:03d}"

    def line(self, text: str, cat: str = "TLGame") -> None:
        self.frame += 1
        self.f.write(f"[{self.ts()}][{self.frame % 1000:3d}]{cat}: Display: [Game] {text}\n")

    def raw(self, text: str) -> None:
        self.f.write(text + "\n")

    def noise(self, n: int = 5) -> None:
        for _ in range(n):
            self.line("UIManager@ tick")

    def wait(self, seconds: float) -> None:
        self.f.flush()
        time.sleep(seconds / self.speed)


class Bag:
    def __init__(self):
        self.stacks = {}  # item_id -> (qty, page, slot)
        self.next_slot = {102: 0, 103: 0}

    def stack_for(self, base: str, page: int) -> str:
        for item_id in self.stacks:
            if item_id.startswith(base + "_"):
                return item_id
        item_id = f"{base}_{random.randrange(16**8):08x}"
        self.stacks[item_id] = (0, page, self.next_slot[page])
        self.next_slot[page] += 1
        return item_id

    def change(self, base: str, delta: int, page: int) -> str:
        item_id = self.stack_for(base, page)
        qty, page, slot = self.stacks[item_id]
        qty = max(0, qty + delta)
        self.stacks[item_id] = (qty, page, slot)
        verb = "Add" if qty == delta else ("Delete" if qty == 0 else "Update")
        num = "" if qty == 0 else f"BagNum={qty} "
        return f"ItemChange@ {verb} Id={item_id} {num}in PageId={page} SlotId={slot}"


def message(log: Log, direction: str, action: str, tree: list[str]) -> None:
    log.line(f"----Socket {direction} STT----{action}----SynId = {random.randint(1000, 99999)}", "GameLog")
    for t in tree:
        log.raw(t)
    log.line(f"----Socket {direction} End----", "GameLog")


def item_block(log: Log, proto: str, lines: list[str]) -> None:
    log.line(f"ItemChange@ ProtoName={proto} start")
    for l in lines:
        log.line(l)
    log.line(f"ItemChange@ ProtoName={proto} end")


def join_fight(log: Log, area_id: str, map_id: str, town: bool) -> None:
    log.line("SwitchBattleAreaUtil:_JoinFightSuccess()")
    log.raw(f"+areaId [{area_id}]")
    log.raw(f"+worldInitArgs+ownerPlayerId [{PLAYER_ID}]")
    log.raw(f"|             +seed [{random.randint(1, 2**31)}]")
    log.raw(f"+mapId [{map_id}]")
    log.raw("+maptype [MainCity]" if town else "+maptype [S4Map]")
    if town:
        log.raw("+checkType [MainCity]")
    log.noise(3)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--maps", type=int, default=5)
    ap.add_argument("--speed", type=float, default=6.0)
    args = ap.parse_args()

    log = Log(args.out, args.speed)
    bag = Bag()
    log.raw("Log file open, demo")
    message(log, "RecvMessage", "GetPlayerData", [
        f"+player+PlayerId [{PLAYER_ID}]",
        "|      +SeasonId [1601]",
        "|      +Name [DemoHero]",
    ])
    join_fight(log, "110_hideout", "111000", town=True)

    # Calibrate: the game re-sends the currency and other pages.
    bag.change(FE, 1200, 102)
    bag.change(BEACON, 20, 103)
    bag.change(COMPASS, 15, 103)
    for page in (102, 103):
        log.line(f"ItemChange@ Reset PageId={page}")
        for item_id, (qty, p, slot) in bag.stacks.items():
            if p == page:
                log.line(f"ItemChange@ Add Id={item_id} BagNum={qty} in PageId={page} SlotId={slot}")
    log.noise()
    log.wait(2)

    for n in range(args.maps):
        print(f"map {n + 1}/{args.maps}")
        item_block(log, "Spv3Open", [bag.change(BEACON, -1, 103), bag.change(COMPASS, -1, 103)])
        log.wait(1)
        join_fight(log, f"1061100_demo{n}_{random.randrange(10**6)}", "1061100", town=False)
        for _ in range(random.randint(5, 9)):
            log.wait(random.uniform(4, 9))
            picks = [bag.change(FE, random.randint(3, 25), 102)]
            if random.random() < 0.6:
                picks.append(bag.change(random.choice(LOOT_POOL), random.randint(1, 2), 103))
            item_block(log, "PickItems", picks)
            log.noise(2)
        log.wait(3)
        join_fight(log, "110_hideout", "111000", town=True)
        log.wait(random.uniform(5, 10))
    log.f.flush()
    print("done")


if __name__ == "__main__":
    main()
