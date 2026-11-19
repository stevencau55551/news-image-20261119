#!/usr/bin/env python3
"""news-image-20261119: draw one newspaper page summing up the world news
of Thursday 19 November 2026. Pure Python stdlib, no network, deterministic:
the same bytes are written on every run."""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)
INK = (24, 24, 24)
NAVY = (20, 38, 74)
GOLD = (201, 162, 39)
WHITE = (255, 255, 255)
GREY = (90, 90, 90)
RED = (178, 34, 34)
BLUE = (46, 92, 158)
TEAL = (22, 122, 122)
PURPLE = (102, 72, 148)
GREEN = (46, 125, 87)
DARKGOLD = (150, 112, 20)

# ------------------------------------------------------- 5x7 pixel font
# Each glyph: 7 rows of 5 characters ('#' = on, '.' = off).
FONT = {
    'A': ("..#..", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '(': ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ')': ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    '/': ("....#", "...#.", "...#.", "..#..", "..#..", ".#...", "#...."),
    '%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    '&': (".###.", "#...#", "#...#", ".#.#.", "#..#.", "#.#..", ".##.#"),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '*': (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines, each fitting max_width.
    A single word longer than max_width is hard-split so it can never
    overflow its panel."""
    char_w = 6 * scale
    max_chars = max(1, (max_width + scale) // char_w)
    words = []
    for word in text.split(" "):
        while len(word) > max_chars:
            words.append(word[:max_chars])
            word = word[max_chars:]
        words.append(word)
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def hline(self, x0, x1, y, color, thick=1):
        for t in range(thick):
            self.fill_rect(x0, y + t, x1 - x0, 1, color)

    def vline(self, x, y0, y1, color, thick=1):
        for t in range(thick):
            self.fill_rect(x + t, y0, 1, y1 - y0, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            self.fill_rect(x - thick // 2, y - thick // 2, thick, thick, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def circle(self, cx, cy, r, color, thick=2):
        import math
        steps = max(24, int(2 * math.pi * r))
        for i in range(steps):
            a = 2 * math.pi * i / steps
            self.fill_rect(int(cx + r * math.cos(a)) - thick // 2,
                           int(cy + r * math.sin(a)) - thick // 2,
                           thick, thick, color)

    def draw_text(self, text, x, y, scale, color):
        text = text.upper()
        cx = x
        for ch in text:
            glyph = FONT.get(ch, FONT['?'])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '#':
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += 6 * scale
        return cx

    def draw_text_centered(self, text, cx, y, scale, color):
        w = text_width(text, scale)
        self.draw_text(text, cx - w // 2, y, scale, color)

    def draw_wrapped(self, text, x, y, max_width, scale, color, leading=2):
        lines = wrap_text(text, max_width, scale)
        for i, ln in enumerate(lines):
            self.draw_text(ln, x, y + i * (7 * scale + leading), scale, color)
        return len(lines)


# ------------------------------------------------------------------- icons
def icon_controller(c, cx, cy, s, color):
    # game controller: body + d-pad + buttons + sticks
    bw, bh = 92 * s, 40 * s
    x0, y0 = cx - bw // 2, cy - bh // 2
    c.fill_rect(x0, y0, bw, bh, color)
    c.fill_circle(x0 + 8 * s, y0 + bh - 4 * s, 10 * s, color)
    c.fill_circle(x0 + bw - 8 * s, y0 + bh - 4 * s, 10 * s, color)
    # d-pad (plus)
    px, py = x0 + 20 * s, y0 + 18 * s
    c.fill_rect(px - 3 * s, py - 9 * s, 6 * s, 18 * s, WHITE)
    c.fill_rect(px - 9 * s, py - 3 * s, 18 * s, 6 * s, WHITE)
    # four buttons
    bx, by = x0 + bw - 22 * s, y0 + 16 * s
    for dx, dy in ((-8, 0), (8, 0), (0, -8), (0, 8)):
        c.fill_circle(bx + dx * s, by + dy * s, 3 * s, WHITE)
    # sticks
    c.fill_circle(x0 + 38 * s, y0 + 24 * s, 4 * s, WHITE)
    c.fill_circle(x0 + bw - 40 * s, y0 + 24 * s, 4 * s, WHITE)


def icon_capitol(c, cx, cy, s, color):
    # dome + columns (US Capitol suggestion)
    x0 = cx - 46 * s
    base_y = cy + 34 * s
    c.fill_rect(x0, base_y, 92 * s, 6 * s, color)
    for i in range(5):
        col_x = x0 + 8 * s + i * 17 * s
        c.fill_rect(col_x, base_y - 26 * s, 6 * s, 26 * s, color)
    c.fill_rect(x0, base_y - 32 * s, 92 * s, 6 * s, color)
    # dome: stacked shrinking rows
    for i, wdt in enumerate((64, 56, 46, 34, 20)):
        c.fill_rect(cx - wdt * s // 2, base_y - 38 * s - i * 6 * s,
                    wdt * s, 6 * s, color)
    c.fill_rect(cx - 2 * s, base_y - 74 * s, 4 * s, 8 * s, color)
    c.fill_circle(cx, base_y - 76 * s, 3 * s, color)


def icon_coin(c, cx, cy, s, color):
    c.fill_circle(cx, cy, 40 * s, color)
    c.circle(cx, cy, 32 * s, GOLD, 3)
    c.draw_text_centered("45", cx, cy - 22 * s, 3 * s, WHITE)
    c.draw_text_centered("BN", cx, cy + 8 * s, 2 * s, WHITE)


def icon_cyclone(c, cx, cy, s, color):
    import math
    # spiral: archimedean, drawn as polyline
    pts = []
    for i in range(0, 260):
        a = i * 0.09
        r = 4 + i * 0.14
        pts.append((int(cx + r * math.cos(a) * s),
                    int(cy + r * math.sin(a) * s)))
    for i in range(len(pts) - 1):
        c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], color, 3)
    c.fill_circle(cx, cy, 5 * s, color)


def icon_voyager(c, cx, cy, s, color):
    # satellite probe: body + solar panels + antenna + stars
    c.fill_rect(cx - 46 * s, cy - 6 * s, 30 * s, 12 * s, color)
    c.fill_rect(cx + 16 * s, cy - 6 * s, 30 * s, 12 * s, color)
    c.fill_rect(cx - 14 * s, cy - 12 * s, 28 * s, 24 * s, color)
    c.fill_rect(cx - 16 * s, cy - 12 * s, 2 * s, 24 * s, PAPER)
    c.fill_rect(cx + 14 * s, cy - 12 * s, 2 * s, 24 * s, PAPER)
    c.line(cx, cy - 12 * s, cx + 18 * s, cy - 36 * s, color, 3)
    c.fill_circle(cx + 20 * s, cy - 38 * s, 4 * s, color)
    for sx, sy in ((-52, -30), (52, -28), (-40, 30), (46, 32), (-8, -44)):
        c.fill_circle(cx + sx * s, cy + sy * s, 2 * s, GOLD)


def icon_shield(c, cx, cy, s, color):
    # shield outline + check mark
    pts_top = [(cx - 34 * s, cy - 30 * s), (cx + 34 * s, cy - 30 * s),
               (cx + 34 * s, cy + 4 * s)]
    c.fill_rect(cx - 34 * s, cy - 30 * s, 68 * s, 34 * s, color)
    # bottom point: triangle rows
    for i in range(30):
        wdt = 68 * s - 2 * i * s
        if wdt <= 0:
            break
        c.fill_rect(cx - wdt // 2, cy + 4 * s + i * s, wdt, s, color)
    c.line(cx - 18 * s, cy + 2 * s, cx - 4 * s, cy + 16 * s, WHITE, 5)
    c.line(cx - 4 * s, cy + 16 * s, cx + 22 * s, cy - 14 * s, WHITE, 5)


# ------------------------------------------------------------------- layout
def draw_panel(c, x, y, w, h, accent, tag, headline, body, icon, source):
    c.fill_rect(x, y, w, h, WHITE)
    c.fill_rect(x, y, w, 8, accent)
    # thin border
    c.hline(x, x + w, y + h - 1, (200, 192, 172))
    c.vline(x, y, y + h, (200, 192, 172))
    c.vline(x + w - 1, y, y + h, (200, 192, 172))
    c.draw_text(tag, x + 14, y + 20, 2, accent)
    icon(c, x + w // 2, y + 92, 1, accent)
    hy = y + 148
    n = c.draw_wrapped(headline, x + 14, hy, w - 28, 3, INK, leading=4)
    by = hy + n * (7 * 3 + 4) + 10
    # Guard: never let the body run into the source rule at y+h-34.
    # Keep only the lines that end at least 2px above it.
    body_lines = wrap_text(body, w - 28, 2)
    line_h = 7 * 2 + 3
    max_lines = (y + h - 36 - by - 14) // line_h + 1
    body_lines = body_lines[:max(0, max_lines)]
    for i, ln in enumerate(body_lines):
        c.draw_text(ln, x + 14, by + i * line_h, 2, (60, 60, 60))
    c.hline(x + 14, x + w - 14, y + h - 34, (220, 214, 196))
    c.draw_text("SOURCE: " + source, x + 14, y + h - 24, 2, GREY)


def draw():
    c = Canvas(W, H, PAPER)

    # ---- masthead
    c.fill_rect(0, 0, W, 150, NAVY)
    c.draw_text_centered("THE WORLD IN ONE DAY", W // 2, 16, 2, GOLD)
    c.draw_text_centered("THURSDAY 19 NOVEMBER 2026", W // 2, 44, 6, WHITE)
    c.hline(60, W - 60, 108, GOLD, 3)
    c.draw_text_centered("SIX STORIES THAT DEFINED THE DAY", W // 2, 120, 2,
                         (200, 205, 220))

    # ---- lead story: GTA VI
    lx, ly, lw, lh = 16, 162, W - 32, 232
    c.fill_rect(lx, ly, lw, lh, WHITE)
    c.fill_rect(lx, ly, lw, 8, RED)
    c.hline(lx, lx + lw, ly + lh - 1, (200, 192, 172))
    c.vline(lx, ly, ly + lh, (200, 192, 172))
    c.vline(lx + lw - 1, ly, ly + lh, (200, 192, 172))
    c.draw_text("CULTURE  -  LEAD STORY", lx + 20, ly + 24, 2, RED)
    icon_controller(c, lx + 130, ly + 140, 1, NAVY)
    c.draw_text("GTA VI IS HERE", lx + 268, ly + 52, 6, INK)
    c.draw_wrapped("AFTER 13 YEARS, ROCKSTAR'S EPIC ROLLS OUT "
                   "WORLDWIDE AT MIDNIGHT, NEW ZEALAND FIRST. "
                   "CRITICS SCORE IT 99 OF 100.",
                   lx + 268, ly + 122, lw - 268 - 24, 3, (60, 60, 60),
                   leading=6)
    c.hline(lx + 20, lx + lw - 20, ly + lh - 34, (220, 214, 196))
    c.draw_text("PS5 - XBOX SERIES X/S - $79.99 - NO PC VERSION YET",
                lx + 20, ly + lh - 24, 2, GREY)

    # ---- row A: three panels
    py, ph = 406, 292
    pw = 320
    draw_panel(c, 16, py, pw, ph, BLUE, "USA - POLITICS",
               "JEFFRIES FOR SPEAKER",
               "DEMOCRATS NOMINATE THE FIRST BLACK LAWMAKER "
               "FOR SPEAKER.",
               icon_capitol, "BBC - NDTV")
    draw_panel(c, 352, py, pw, ph, DARKGOLD, "EUROPE - UKRAINE",
               "EU PLANS 45BN LOAN FOR UKRAINE",
               "45 BILLION EUROS FOR KYIV, "
               "REPAYABLE AFTER RUSSIA PAYS UP.",
               icon_coin, "FINANCIAL TIMES")
    draw_panel(c, 688, py, pw, ph, TEAL, "INDIA - WEATHER",
               "CYCLONE AKVAN BEARS DOWN",
               "STORM TO HIT INDIA'S EAST COAST BETWEEN "
               "MACHILIPATNAM AND PURI.",
               icon_cyclone, "THE HINDU")

    # ---- row B: two panels
    py2, ph2, pw2 = 710, 284, 488
    draw_panel(c, 16, py2, pw2, ph2, PURPLE, "SPACE - NASA",
               "ONE LIGHT-DAY FROM EARTH",
               "NASA MARKS VOYAGER 1'S RECORD: 16 BILLION MILES "
               "OUT, 49 YEARS AFTER LAUNCH. BRIEFING TODAY.",
               icon_voyager, "NASA - REUTERS")
    draw_panel(c, 520, py2, pw2, ph2, GREEN, "AUSTRALIA - MIDDLE EAST",
               "CANBERRA SANCTIONS SETTLERS",
               "AUSTRALIA SANCTIONS ISRAELI SETTLERS AND GROUPS "
               "OVER WEST BANK EXPANSION.",
               icon_shield, "THE DAILY JAGRAN")

    # ---- footer
    c.draw_text_centered(
        "REPORTED 19 NOVEMBER 2026 - AP, BBC, REUTERS, FT, NASA",
        W // 2, 1002, 2, GREY)
    return c


# ---------------------------------------------------------------------- png
def png_bytes(c):
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    raw = bytearray()
    for y in range(c.h):
        raw.append(0)  # filter: none
        start = y * c.w * 3
        raw += c.px[start:start + c.w * 3]
    ihdr = struct.pack(">IIBBBBB", c.w, c.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
