#!/usr/bin/env python3
"""WORLD NEWS front page for Tuesday, 24 November 2026.

Draws a visual newspaper front page (1024x1024 PNG) with a hand-written
5x7 bitmap font and a hand-written PNG encoder. Pure standard library,
no network, fully deterministic: the same bytes on every run.

Stories verified live on 24 November 2026:
  LEAD  Asian stocks soar as Nvidia's Jensen Huang return revives the
        AI trade (Reuters, 24 Nov 2026).
  2     Russian strikes kill at least 12 in Ukraine's Kyiv region
        (reported 24 Nov 2026).
  3     South Korea reshuffles cabinet: new foreign minister and the
        country's first woman spy chief (24 Nov 2026).
  4     Australia, Canada, Italy and Britain jointly press Israel to
        open Gaza aid access as flooding hits (24 Nov 2026).
  5     Modi and Nepal PM Balendra Shah flag off the Saryu-Kamala
        Express linking Ayodhya and Janakpur (24 Nov 2026).
"""
import os
import struct
import zlib
from hashlib import sha256

W, H = 1024, 1024
PAPER = (255, 255, 255)
INK = (17, 17, 17)
RED = (160, 0, 0)
GREY = (130, 130, 130)

# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs, written from scratch. '#' is a set pixel.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", ".#.#.", ".#.#.", "..#..", "..#..", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.###", "#..##"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "/": ("....#", "...#.", "...#.", "..#..", "..#..", ".#...", "#...."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
}


def char_width(scale):
    return 5 * scale + scale


def text_width(text, scale):
    return len(text) * char_width(scale) - scale


def wrap(text, scale, max_px):
    """Greedy word wrap; returns a list of lines fitting max_px."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_px:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(PAPER * (w * h))

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def hline(self, x, y, w, thick, color):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, thick, color):
        self.rect(x, y, thick, h, color)

    def glyph(self, x, y, ch, scale, color):
        rows = FONT.get(ch)
        if rows is None:
            return
        for ry, row in enumerate(rows):
            for rx, bit in enumerate(row):
                if bit == "#":
                    self.rect(x + rx * scale, y + ry * scale,
                              scale, scale, color)

    def text(self, x, y, s, scale, color=INK):
        cx = x
        for ch in s:
            self.glyph(cx, y, ch, scale, color)
            cx += char_width(scale)

    def text_center(self, y, s, scale, color=INK, cx=512):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def text_block(self, x, y, lines, scale, pitch, color=INK):
        for i, line in enumerate(lines):
            self.text(x, y + i * pitch, line, scale, color)

    def text_block_center(self, y, lines, scale, pitch, color=INK, cx=512):
        for i, line in enumerate(lines):
            self.text_center(y + i * pitch, line, scale, color, cx)


# ---------------------------------------------------------------- png
def chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: None
        raw += canvas.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


# ---------------------------------------------------------------- page
def draw_page():
    c = Canvas(W, H)

    # Masthead
    c.text_center(18, "WORLD NEWS", 14, INK)
    c.hline(28, 128, 968, 4, RED)
    # Dateline
    c.text_center(142, "TUESDAY, 24 NOVEMBER 2026", 4, INK)
    c.hline(28, 180, 968, 2, INK)

    # ---- LEAD: markets rally
    c.text_center(196, "ASIAN STOCKS SOAR AS", 6, INK)
    c.text_center(240, "HUANG REVIVES AI TRADE", 6, INK)
    deck = wrap(
        "NVIDIA JUMPED 31.5% ON MONDAY, ITS BEST DAY IN 23 YEARS, ADDING "
        "BACK NEARLY $1 TRILLION IN VALUE. ASIAN MARKETS FOLLOWED ON "
        "TUESDAY: MSCI ASIA +4.6%, NIKKEI +4.5%, KOSPI +7.5%, TAIWAN +9.1%.",
        2, 940)
    c.text_block_center(296, deck, 2, 20, INK)

    # Bar strip: Tuesday gains of the four Asian benchmarks
    bars = [("MSCI ASIA", 4.6), ("NIKKEI", 4.5),
            ("KOSPI", 7.5), ("TAIWAN", 9.1)]
    by = 388
    for i, (label, val) in enumerate(bars):
        yy = by + i * 18
        c.text(996 - 0, yy, "", 2, INK)  # no-op keeps layout explicit
        lw = text_width(label, 2)
        c.text(28 + 150 - lw, yy, label, 2, INK)
        bw = int(val * 620 / 9.1)
        c.rect(190, yy + 1, bw, 12, INK if i < 3 else RED)
        c.text(190 + bw + 10, yy, "+%.1f%%" % val, 2, INK)
    c.hline(28, 466, 968, 2, INK)

    # ---- ROW 1: two stories
    col_w = 470
    # Story 2: Kyiv strikes
    c.text(28, 480, "RUSSIAN STRIKES KILL", 3, INK)
    c.text(28, 503, "12 IN KYIV REGION", 3, INK)
    lines = wrap(
        "MISSILES AND DRONES HIT HOMES AND POWER LINES OVERNIGHT. "
        "OFFICIALS SAY AT LEAST 12 PEOPLE ARE DEAD AND SEVERAL ARE "
        "MISSING.", 2, col_w)
    c.text_block(28, 536, lines, 2, 19, INK)
    # Story 3: Seoul reshuffle
    c.text(526, 480, "SEOUL NAMES NEW", 3, INK)
    c.text(526, 503, "FOREIGN MINISTER", 3, INK)
    lines = wrap(
        "THE PRESIDENT RESHUFFLES THE CABINET, NAMING A NEW FOREIGN "
        "MINISTER AND THE COUNTRY'S FIRST WOMAN SPY CHIEF IN A WIDER "
        "SHAKE-UP.", 2, col_w)
    c.text_block(526, 536, lines, 2, 19, INK)
    c.vline(512, 480, 160, 2, GREY)
    c.hline(28, 654, 968, 2, INK)

    # ---- ROW 2: two stories
    # Story 4: Gaza aid plea
    c.text(28, 668, "FOUR NATIONS PRESS", 3, INK)
    c.text(28, 691, "ISRAEL OVER GAZA AID", 3, INK)
    lines = wrap(
        "AUSTRALIA, CANADA, ITALY AND BRITAIN JOINTLY CALL FOR "
        "IMMEDIATE, UNRESTRICTED AID ACCESS AS FLOODING ADDS TO THE "
        "SUFFERING IN GAZA.", 2, col_w)
    c.text_block(28, 724, lines, 2, 19, INK)
    # Story 5: India-Nepal train
    c.text(526, 668, "INDIA-NEPAL EXPRESS", 3, INK)
    c.text(526, 691, "FLAGGED OFF", 3, INK)
    lines = wrap(
        "MODI AND NEPAL'S PM BALENDRA SHAH LAUNCH THE SARYU-KAMALA "
        "EXPRESS, LINKING AYODHYA WITH JANAKPUR DHAM ACROSS THE "
        "BORDER.", 2, col_w)
    c.text_block(526, 724, lines, 2, 19, INK)
    c.vline(512, 668, 160, 2, GREY)
    c.hline(28, 842, 968, 2, INK)

    # ---- IN BRIEF
    c.text(28, 854, "IN BRIEF", 3, RED)
    briefs = [
        "UN CHIEF: AGREE GLOBAL AI SAFETY RULES WITHIN A YEAR",
        "US DETAILS $12BN IN VENEZUELAN OIL AND MINERAL REVENUE",
        "POLAND SEEKS EMERGENCY NATO MEETING AFTER MISSILE INCURSION",
        "CAS TO RULE TODAY ON SENEGAL'S AFRICA CUP TITLE APPEAL",
        "SOUTH KOREA EDUCATION MINISTER QUITS OVER AI CHEATING RULES",
        "BANGLADESH GARMENT WORKERS REJECT PAY OFFER",
    ]
    for i, item in enumerate(briefs):
        col = i % 2
        row = i // 2
        bx = 28 if col == 0 else 526
        byy = 888 + row * 46
        c.rect(bx, byy + 4, 7, 7, RED)
        lines = wrap(item, 2, col_w - 20)
        c.text_block(bx + 16, byy, lines, 2, 19, INK)

    return c


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"
    os.makedirs(outdir, exist_ok=True)
    data = encode_png(draw_page())
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, sha256 %s)"
          % (path, len(data), sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
