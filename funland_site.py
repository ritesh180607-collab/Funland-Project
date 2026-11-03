#!/usr/bin/env python3
"""
FunLand Park - a website-style amusement park front end, built with Tkinter only.

Pages : Home, Rides, Tickets, Checkout, My Tickets, Park Info
Feel  : fixed nav bar with sliding indicator, page transitions, smooth scrolling,
        staggered section entrances and springy buttons. The easing curves are the
        ones anime.js uses (easeOutBack / Elastic / Bounce / Expo, easeInBack),
        re-implemented in Python because Tkinter cannot run JavaScript.

Run   : python funland_site.py      (Python 3.8+, standard library only)
This is a demo front end: no data leaves the app and no real payment is taken.
"""
import datetime
import math
import random
import re
import time
import tkinter as tk
import tkinter.font as tkfont

# --------------------------------------------------------------------------- #
#  Theme & data
# --------------------------------------------------------------------------- #
W = 1100           # page width
HH = 100           # fixed header height
BLUE, NAVY, LBLUE = "#1E6FE0", "#12357A", "#E3F0FF"
RED, WHITE, GREY = "#E8333A", "#FFFFFF", "#5B6E99"
SKIN, CHEEK = "#FFD9B8", "#FF9AA2"
SKY_TOP, SKY_BOT = (74, 168, 255), (214, 238, 255)
FONT_CHOICES = ["Comic Sans MS", "Comic Neue", "Chalkboard SE", "Baloo 2", "Fredoka",
                "Arial Rounded MT Bold", "Nunito", "Verdana", "DejaVu Sans", "Helvetica"]

ORDER = ["adult", "child", "senior", "toddler"]
TYPES = {
    "adult":   dict(name="Adults",   one="Adult",   ages="Ages 13-59", price=25, line="Big kids at heart"),
    "child":   dict(name="Children", one="Child",   ages="Ages 3-12",  price=15, line="Loop-de-loop ready"),
    "senior":  dict(name="Seniors",  one="Senior",  ages="Ages 60+",   price=18, line="Coaster legends"),
    "toddler": dict(name="Toddlers", one="Toddler", ages="Under 3",    price=0,  line="Tiny & totally free"),
}
MAX_PER_TYPE = 10
FASTPASS_PRICE = 10
CHIPS = {"student": ("Student", 0.10), "military": ("Military", 0.15), "member": ("Member", 0.20)}
PROMOS = {"FUN10": 0.10, "SUMMER25": 0.25, "FUNLAND30": 0.30}
HOURS = [("Monday", "10am - 8pm"), ("Tuesday", "10am - 8pm"), ("Wednesday", "10am - 8pm"),
         ("Thursday", "10am - 8pm"), ("Friday", "10am - 10pm"), ("Saturday", "9am - 11pm"),
         ("Sunday", "9am - 9pm")]
RIDES = [  # name, category, description, thrill 1-5, min height cm (0 = all), wait min
    ("Sky Screamer", "thrill", "A 60 m drop tower with the best view in town. Hold on to your hat!", 5, 140, 35),
    ("Loop-de-Loop Coaster", "thrill", "Three loops, two corkscrews and one very happy scream.", 4, 130, 25),
    ("Pirate Plunge", "water", "Sail with Captain Splash, then drop straight into the lagoon.", 4, 120, 20),
    ("Splash Canyon", "water", "Log boats, big waves and guaranteed soggy socks.", 3, 110, 15),
    ("Bumper Bonanza", "family", "Bonk, bump and giggle in glowing bumper cars.", 2, 110, 10),
    ("Teacup Twirl", "family", "Spin as fast (or as slow) as you like in giant teacups.", 2, 0, 10),
    ("Starlight Ferris Wheel", "family", "A slow, sparkly ride 40 m above the whole park.", 1, 0, 15),
    ("Mini Rockets", "kids", "Little astronauts blast off in tiny rockets.", 1, 0, 5),
    ("Choo-Choo Express", "kids", "A gentle train ride all the way around the park.", 1, 0, 5),
]
FAQ = [
    ("Do I need to print my tickets?",
     "Nope! Show the ticket on your phone at the gate. We scan the barcode and you're in."),
    ("Are toddlers really free?",
     "Yes! Kids under 3 get in free, but they still need a ticket so we know how many little ones are inside."),
    ("Can children visit without an adult?",
     "Guests under 13 must be with an adult or senior ticket holder at all times."),
    ("What does Fast Pass do?",
     "Fast Pass lets you use the express lane on every ride, all day long. Perfect for busy weekends."),
    ("Can I combine discounts?",
     "Discounts don't stack. We automatically apply the single best deal on your order."),
    ("What happens if it rains?",
     "Most rides run in light rain. If the park closes for weather, your ticket is valid any day in the next 6 months."),
]
PAGES = ["home", "rides", "tickets", "checkout", "mytickets", "info"]
NAV = [("home", "Home"), ("rides", "Rides"), ("tickets", "Tickets"), ("info", "Park Info"), ("mytickets", "My Tickets")]


# --------------------------------------------------------------------------- #
#  Easing (same formulas anime.js / easings.net use)
# --------------------------------------------------------------------------- #
def linear(t): return t
def ease_out_cubic(t): return 1 - (1 - t) ** 3
def ease_out_quad(t): return 1 - (1 - t) ** 2
def ease_out_expo(t): return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)
def ease_out_back(t, s=1.70158): return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2
def ease_in_back(t, s=1.70158): return (s + 1) * t ** 3 - s * t * t


def ease_out_elastic(t):
    if t <= 0 or t >= 1:
        return float(t >= 1)
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


def ease_out_bounce(t):
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + 0.9375
    t -= 2.625 / d
    return n * t * t + 0.984375


# --------------------------------------------------------------------------- #
#  Drawing helpers
# --------------------------------------------------------------------------- #
def hexrgb(rgb):
    return "#%02x%02x%02x" % tuple(int(v) for v in rgb)


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return hexrgb([a[i] + (b[i] - a[i]) * t for i in range(3)])


def sky_at(y, span=700):
    t = max(0.0, min(1.0, y / span))
    return hexrgb([SKY_TOP[i] + (SKY_BOT[i] - SKY_TOP[i]) * t for i in range(3)])


def rrect_pts(x1, y1, x2, y2, r):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    return [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r,
            x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1]


def rrect(c, x1, y1, x2, y2, r, **kw):
    return c.create_polygon(rrect_pts(x1, y1, x2, y2, r), smooth=True, **kw)


def star_pts(cx, cy, r):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts += [cx + rr * math.cos(a), cy + rr * math.sin(a)]
    return pts


def star(c, cx, cy, r, **kw):
    return c.create_polygon(star_pts(cx, cy, r), **kw)


def heart_pts(cx, cy, s):
    pts = []
    for i in range(40):
        t = i / 40 * 2 * math.pi
        pts += [cx + s * 16 * math.sin(t) ** 3,
                cy - s * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) - s * 2]
    return pts


def pick_family(root):
    have = {f.lower(): f for f in tkfont.families(root)}
    for f in FONT_CHOICES:
        if f.lower() in have:
            return have[f.lower()]
    return "TkDefaultFont"


def luhn_ok(num):
    total = 0
    for i, ch in enumerate(reversed(num)):
        d = int(ch)
        if i % 2:
            d *= 2
            d -= 9 if d > 9 else 0
        total += d
    return total % 10 == 0


# --------------------------------------------------------------------------- #
#  Animation engine
# --------------------------------------------------------------------------- #
class Animator:
    def __init__(self, root):
        self.root, self.tweens, self.tickers, self._n = root, {}, [], 0
        self.last = time.perf_counter()
        self._loop()

    def tween(self, frm, to, dur, setter, easing=ease_out_cubic, delay=0, done=None, key=None):
        if key is None:
            self._n += 1
            key = ("anon", self._n)
        self.tweens[key] = [time.perf_counter() + delay / 1000, dur / 1000, frm, to, setter, easing, done]
        return key

    def cancel(self, key):
        self.tweens.pop(key, None)

    def _loop(self):
        self.root.after(15, self._loop)
        now = time.perf_counter()
        dt, self.last = now - self.last, now
        for key, tw in list(self.tweens.items()):
            start, dur, frm, to, setter, easing, done = tw
            if now < start:
                continue
            t = 1.0 if dur <= 0 else min(1.0, (now - start) / dur)
            setter(frm + (to - frm) * easing(t))
            if t >= 1 and self.tweens.get(key) is tw:
                del self.tweens[key]
                if done:
                    done()
        for f in list(self.tickers):
            f(now, dt)


class Group:
    """Canvas items sharing a tag, offset together. Groups can nest."""
    def __init__(self, canvas, tag, parent=None):
        self.c, self.tag, self.parent, self.dx, self.dy = canvas, tag, parent, 0.0, 0.0
        self.intro = True

    def ox(self):
        return self.dx + (self.parent.ox() if self.parent else 0)

    def oy(self):
        return self.dy + (self.parent.oy() if self.parent else 0)

    def chain(self):
        return [self.tag] + (self.parent.chain() if self.parent else [])

    def set_offset(self, dx, dy):
        self.c.move(self.tag, dx - self.dx, dy - self.dy)
        self.dx, self.dy = dx, dy


# --------------------------------------------------------------------------- #
#  Interactive canvas widgets
# --------------------------------------------------------------------------- #
class PopButton:
    """Chunky cartoon button: grows on hover, squishes on press, springs back."""
    def __init__(self, app, cx, cy, w, h, text, command=None, fill=RED, fg=WHITE, outline=NAVY,
                 size=16, shape="round", group=None, layer="main", cv=None, page=True, fixed=False):
        self.app, self.cv = app, cv or app.c
        on_page = self.cv is app.c and page
        self.page = app.page_tag if on_page else None
        self.group = group if group is not None else (app.sec if on_page else None)
        self.cx, self.cy, self.w, self.h, self.text, self.command = cx, cy, w, h, text, command
        self.fill, self.fg, self.outline, self.size, self.shape = fill, fg, outline, size, shape
        self.layer, self.fixed = layer, fixed
        self.tag = "btn%d" % id(self)
        self.scale, self.pulse, self.sx = 1.0, 1.0, 0.0
        self.pressed = self.hover = self.dead = False
        self.visible = True
        app.hoverables.append(self)
        self.redraw()

    def pos(self):
        gx = self.group.ox() if self.group else 0
        gy = self.group.oy() if self.group else 0
        return self.cx + gx + self.sx, self.cy + gy

    def contains(self, x, y):
        if not self.visible:
            return False
        px, py = self.pos()
        return abs(x - px) <= self.w / 2 and abs(y - py) <= self.h / 2

    def tags(self):
        t = [self.tag] + (self.group.chain() if self.group else [])
        if self.page:
            t.append(self.page)
        if self.layer == "modal":
            t.append("modal")
        if self.fixed:
            t.append("fixed")
        return t

    def redraw(self):
        if self.dead:
            return
        c = self.cv
        c.delete(self.tag)
        if not self.visible:
            return
        tags = self.tags()
        s = self.scale * self.pulse
        px, py = self.pos()
        w, h = self.w * s / 2, self.h * s / 2
        p = 3 * s if self.pressed else 0
        sh = 5 * s
        gloss = LBLUE if self.fill == WHITE else mix(self.fill, WHITE, 0.45)
        if self.shape == "circle":
            c.create_oval(px - w, py - h + sh, px + w, py + h + sh, fill=self.outline, outline="", tags=tags)
            c.create_oval(px - w, py - h + p, px + w, py + h + p, fill=self.fill, outline=self.outline, width=3, tags=tags)
            c.create_arc(px - w * 0.62, py - h * 0.62 + p, px + w * 0.62, py + h * 0.62 + p, start=100, extent=60,
                         style="arc", outline=gloss, width=max(2, int(3 * s)), tags=tags)
        else:
            r = min(h, 26 * s)
            rrect(c, px - w, py - h + sh, px + w, py + h + sh, r, fill=self.outline, outline="", tags=tags)
            rrect(c, px - w, py - h + p, px + w, py + h + p, r, fill=self.fill, outline=self.outline, width=3, tags=tags)
            if "\n" not in self.text:
                c.create_line(px - w + r * 0.9, py - h + 7 * s + p, px - w + r * 0.9 + w * 0.4, py - h + 7 * s + p,
                              fill=gloss, width=max(2, int(3 * s)), capstyle="round", tags=tags)
        c.create_text(px, py + p, text=self.text, fill=self.fg, justify="center",
                      font=self.app.font(max(6, int(round(self.size * s)))), tags=tags)
        if c is self.app.c:
            self.app.restack()
        else:
            c.tag_raise("badge")

    def _scale_to(self, target, dur, easing):
        self.app.anim.tween(self.scale, target, dur, self._set_scale, easing, key=(self.tag, "scale"))

    def _set_scale(self, v):
        self.scale = v
        self.redraw()

    def on_enter(self):
        self.hover = True
        self._scale_to(1.07, 260, ease_out_back)

    def on_leave(self):
        self.hover = self.pressed = False
        self._scale_to(1.0, 260, ease_out_back)

    def on_press(self):
        self.pressed = True
        self._scale_to(0.9, 110, ease_out_quad)

    def on_release(self, inside):
        self.pressed = False
        self._scale_to(1.07 if self.hover else 1.0, 750, ease_out_elastic)
        if inside and self.command:
            self.command()

    def shake(self):
        def setter(v):
            self.sx = math.sin(v * math.pi * 6) * 12 * (1 - v)
            self.redraw()
        self.app.anim.tween(0, 1, 520, setter, linear, key=(self.tag, "shake"))

    def set_style(self, fill=None, fg=None, text=None):
        self.fill, self.fg = fill or self.fill, fg or self.fg
        self.text = text if text is not None else self.text
        self.redraw()


class Hotspot:
    """Invisible clickable rectangle with optional hover callbacks."""
    def __init__(self, app, x1, y1, x2, y2, command, group=None, layer="main", cv=None, page=True,
                 enter=None, leave=None):
        self.app, self.cv = app, cv or app.c
        on_page = self.cv is app.c and page
        self.page = app.page_tag if on_page else None
        self.group = group if group is not None else (app.sec if on_page else None)
        self.box, self.command, self.layer, self.enter, self.leave = (x1, y1, x2, y2), command, layer, enter, leave
        self.dead = False
        app.hoverables.append(self)

    def contains(self, x, y):
        gx = self.group.ox() if self.group else 0
        gy = self.group.oy() if self.group else 0
        x1, y1, x2, y2 = self.box
        return x1 + gx <= x <= x2 + gx and y1 + gy <= y <= y2 + gy

    def on_enter(self):
        if self.enter:
            self.enter()

    def on_leave(self):
        if self.leave:
            self.leave()

    def on_press(self):
        pass

    def on_release(self, inside):
        if inside:
            self.command()


class Field:
    """A rounded-looking text input living on the page canvas."""
    def __init__(self, app, x1, cy, w, h=44, value="", show="", placeholder="", size=17, justify="left",
                 multiline=False):
        self.app, self.group, self.base = app, app.sec, (x1 + w / 2, cy)
        self.placeholder, self.show = placeholder, show
        self.frame = tk.Frame(app.c, bg=WHITE, highlightthickness=3, highlightbackground=BLUE, highlightcolor=BLUE)
        kw = dict(font=app.font(size, "normal"), relief="flat", bd=0, highlightthickness=0, bg=WHITE, fg=NAVY,
                  insertbackground=RED)
        if multiline:
            self.entry = tk.Text(self.frame, wrap="word", height=3, **kw)
            self.entry.pack(fill="both", expand=True, padx=10, pady=6)
        else:
            self.entry = tk.Entry(self.frame, justify=justify, show=show, **kw)
            self.entry.pack(fill="both", expand=True, padx=12, pady=2)
        self.multiline = multiline
        self.win = app.c.create_window(*self.base, window=self.frame, width=w, height=h, tags=app.T())
        app.page_widgets.append(self.frame)
        app.page_windows.append(self.win)
        self.error = False
        self.ph_on = False
        if value:
            self._insert(value)
        else:
            self._show_ph()
        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)

    def _insert(self, v):
        if self.multiline:
            self.entry.insert("1.0", v)
        else:
            self.entry.insert(0, v)

    def _raw(self):
        return self.entry.get("1.0", "end-1c") if self.multiline else self.entry.get()

    def _clear(self):
        if self.multiline:
            self.entry.delete("1.0", "end")
        else:
            self.entry.delete(0, "end")

    def _show_ph(self):
        if self.placeholder and not self.show:
            self._clear()
            self._insert(self.placeholder)
            self.entry.config(fg="#9AA9C9")
            self.ph_on = True

    def _focus_in(self, e):
        if self.ph_on:
            self._clear()
            self.entry.config(fg=NAVY)
            self.ph_on = False
        if not self.error:
            self.frame.config(highlightbackground=NAVY)

    def _focus_out(self, e):
        if not self._raw().strip():
            self._show_ph()
        if not self.error:
            self.frame.config(highlightbackground=BLUE)

    def get(self):
        return "" if self.ph_on else self._raw().strip()

    def set(self, v):
        self._clear()
        self.ph_on = False
        self.entry.config(fg=NAVY)
        if v:
            self._insert(v)
        else:
            self._show_ph()

    def set_error(self, on):
        self.error = on
        self.frame.config(highlightbackground=RED if on else BLUE)

    def shake(self):
        x, y = self.base

        def setter(v):
            self.app.c.coords(self.win, x + self.group.ox() + math.sin(v * math.pi * 7) * 14 * (1 - v),
                              y + self.group.oy())
        self.app.anim.tween(0, 1, 560, setter, linear, key=(self.win, "shake"))


# --------------------------------------------------------------------------- #
#  Cartoon art
# --------------------------------------------------------------------------- #
def draw_face(c, kind, cx, cy, tags):
    r = 34 if kind == "toddler" else 42
    if kind == "senior":
        for dx in (-1, 1):
            c.create_oval(cx + dx * 36 - 16, cy - 30, cx + dx * 36 + 16, cy + 2, fill=WHITE, outline=NAVY, width=3, tags=tags)
    c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=SKIN, outline=NAVY, width=3, tags=tags)
    ey = cy - (2 if kind != "toddler" else 0)
    for dx in (-1, 1):
        ex = cx + dx * r * 0.36
        c.create_oval(ex - 5, ey - 7, ex + 5, ey + 7, fill=NAVY, outline="", tags=tags)
        c.create_oval(ex - 2, ey - 5, ex + 1, ey - 2, fill=WHITE, outline="", tags=tags)
        c.create_oval(ex + dx * 6 - 7, ey + 9, ex + dx * 6 + 7, ey + 16, fill=CHEEK, outline="", tags=tags)
    if kind == "toddler":
        c.create_oval(cx - 9, cy + 12, cx + 9, cy + 26, fill=RED, outline=NAVY, width=2, tags=tags)
        c.create_oval(cx - 4, cy + 16, cx + 4, cy + 22, fill=WHITE, outline="", tags=tags)
        c.create_arc(cx - 8, cy - r - 12, cx + 8, cy - r + 6, start=200, extent=260, style="arc",
                     outline=NAVY, width=3, tags=tags)
    else:
        c.create_arc(cx - 16, cy - 2, cx + 16, cy + 24, start=200, extent=140, style="arc",
                     outline=NAVY, width=3, tags=tags)
    if kind == "adult":
        c.create_arc(cx - r - 2, cy - r - 10, cx + r + 2, cy + r - 26, start=0, extent=180, style="chord",
                     fill=RED, outline=NAVY, width=3, tags=tags)
        rrect(c, cx - 6, cy - 22, cx + r + 20, cy - 12, 5, fill=RED, outline=NAVY, width=3, tags=tags)
        c.create_oval(cx - 5, cy - r - 14, cx + 5, cy - r - 4, fill=WHITE, outline=NAVY, width=2, tags=tags)
    elif kind == "child":
        c.create_arc(cx - r, cy - r - 6, cx + r, cy + r - 26, start=0, extent=180, style="chord",
                     fill=BLUE, outline=NAVY, width=3, tags=tags)
        c.create_arc(cx - r * 0.35, cy - r - 6, cx + r * 0.35, cy + r - 26, start=0, extent=180, style="chord",
                     fill=WHITE, outline=NAVY, width=2, tags=tags)
        c.create_line(cx, cy - r - 6, cx, cy - r - 16, fill=NAVY, width=3, tags=tags)
        c.create_oval(cx - 22, cy - r - 22, cx - 1, cy - r - 13, fill=RED, outline=NAVY, width=2, tags=tags)
        c.create_oval(cx + 1, cy - r - 22, cx + 22, cy - r - 13, fill=RED, outline=NAVY, width=2, tags=tags)
    elif kind == "senior":
        for dx in (-1, 1):
            ex = cx + dx * r * 0.36
            c.create_oval(ex - 11, ey - 11, ex + 11, ey + 11, outline=NAVY, width=3, tags=tags)
        c.create_line(cx - 4, ey, cx + 4, ey, fill=NAVY, width=3, tags=tags)


def icon_coaster(c, cx, cy, t):
    pts = []
    for i in range(21):
        x = cx - 60 + i * 6
        pts += [x, cy + 10 - 26 * math.sin(i / 20 * math.pi * 1.5)]
    for i in (2, 8, 14, 19):
        c.create_line(pts[i * 2], pts[i * 2 + 1], pts[i * 2], cy + 36, fill=NAVY, width=3, tags=t)
    c.create_line(*pts, fill=RED, width=6, smooth=True, capstyle="round", tags=t)
    rrect(c, cx - 22, cy - 34, cx + 4, cy - 18, 5, fill=BLUE, outline=NAVY, width=2, tags=t)
    c.create_oval(cx - 19, cy - 21, cx - 11, cy - 13, fill=NAVY, outline="", tags=t)
    c.create_oval(cx - 7, cy - 21, cx + 1, cy - 13, fill=NAVY, outline="", tags=t)


def icon_waves(c, cx, cy, t):
    c.create_polygon(cx, cy - 40, cx - 14, cy - 14, cx + 14, cy - 14, fill=BLUE, outline="", smooth=True, tags=t)
    c.create_oval(cx - 14, cy - 28, cx + 14, cy, fill=BLUE, outline=NAVY, width=2, tags=t)
    c.create_oval(cx - 8, cy - 22, cx - 2, cy - 14, fill=WHITE, outline="", tags=t)
    for k, col in enumerate([BLUE, NAVY]):
        pts = []
        for i in range(25):
            x = cx - 60 + i * 5
            pts += [x, cy + 14 + k * 16 + 6 * math.sin(i / 3)]
        c.create_line(*pts, fill=col, width=5, smooth=True, capstyle="round", tags=t)


def icon_teacup(c, cx, cy, t):
    c.create_oval(cx - 48, cy + 14, cx + 48, cy + 34, fill=WHITE, outline=NAVY, width=3, tags=t)
    c.create_oval(cx + 22, cy - 18, cx + 50, cy + 10, outline=NAVY, width=5, tags=t)
    c.create_arc(cx - 36, cy - 50, cx + 36, cy + 30, start=180, extent=180, style="chord",
                 fill=RED, outline=NAVY, width=3, tags=t)
    for dx in (-18, 0, 18):
        c.create_oval(cx + dx - 4, cy - 2, cx + dx + 4, cy + 6, fill=WHITE, outline="", tags=t)
    for dx in (-10, 8):
        c.create_line(cx + dx, cy - 18, cx + dx + 6, cy - 32, cx + dx, cy - 44, fill=GREY, width=3, smooth=True, tags=t)


def icon_rocket(c, cx, cy, t):
    c.create_polygon(cx - 14, cy + 14, cx - 30, cy + 34, cx - 14, cy + 30, fill=RED, outline=NAVY, width=2, tags=t)
    c.create_polygon(cx + 14, cy + 14, cx + 30, cy + 34, cx + 14, cy + 30, fill=RED, outline=NAVY, width=2, tags=t)
    c.create_polygon(cx - 7, cy + 30, cx, cy + 46, cx + 7, cy + 30, fill="#FF9A3C", outline="", tags=t)
    rrect(c, cx - 15, cy - 20, cx + 15, cy + 32, 12, fill=WHITE, outline=NAVY, width=3, tags=t)
    c.create_polygon(cx - 15, cy - 14, cx, cy - 44, cx + 15, cy - 14, fill=RED, outline=NAVY, width=3, tags=t)
    c.create_oval(cx - 8, cy - 6, cx + 8, cy + 10, fill=BLUE, outline=NAVY, width=2, tags=t)


def icon_tent(c, cx, cy, t):
    c.create_rectangle(cx - 34, cy - 4, cx + 34, cy + 32, fill=WHITE, outline=NAVY, width=3, tags=t)
    for i in range(3):
        c.create_rectangle(cx - 34 + i * 23 + 6, cy - 4, cx - 34 + i * 23 + 17, cy + 32, fill=RED, outline="", tags=t)
    c.create_rectangle(cx - 34, cy - 4, cx + 34, cy + 32, outline=NAVY, width=3, tags=t)
    c.create_polygon(cx - 10, cy + 32, cx, cy + 6, cx + 10, cy + 32, fill=NAVY, tags=t)
    c.create_polygon(cx - 44, cy - 2, cx, cy - 38, cx + 44, cy - 2, fill=RED, outline=NAVY, width=3, tags=t)
    c.create_line(cx, cy - 38, cx, cy - 54, fill=NAVY, width=3, tags=t)
    c.create_polygon(cx, cy - 54, cx + 16, cy - 49, cx, cy - 44, fill=BLUE, outline=NAVY, tags=t)


def icon_icecream(c, cx, cy, t):
    c.create_polygon(cx - 18, cy + 2, cx + 18, cy + 2, cx, cy + 44, fill="#F5C77E", outline=NAVY, width=3, tags=t)
    for x1, y1, col in [(-22, -14, BLUE), (-4, -14, RED), (-14, -34, WHITE)]:
        c.create_oval(cx + x1, cy + y1, cx + x1 + 26, cy + y1 + 24, fill=col, outline=NAVY, width=3, tags=t)
    c.create_oval(cx - 5, cy - 44, cx + 5, cy - 34, fill=RED, outline=NAVY, width=2, tags=t)


RIDE_ICON = {"thrill": icon_coaster, "water": icon_waves, "family": icon_teacup, "kids": icon_rocket}
CAT_COLOR = {"thrill": RED, "water": BLUE, "family": NAVY, "kids": RED}


# --------------------------------------------------------------------------- #
#  Ticket type card (Tickets page)
# --------------------------------------------------------------------------- #
class TicketCard:
    def __init__(self, app, idx, kind, x, y):
        self.app, self.kind, self.box = app, kind, (x, y, x + 320, y + 150)
        c = app.c
        self.group = Group(c, "%s_card%d" % (app.page_tag, idx), parent=app.sec)
        t = app.T(group=self.group)
        info = TYPES[kind]
        rrect(c, x + 6, y + 7, x + 326, y + 157, 26, fill=NAVY, outline="", tags=t)
        rrect(c, x, y, x + 320, y + 150, 26, fill=WHITE, outline=BLUE, width=4, tags=t)
        rrect(c, x + 14, y + 14, x + 112, y + 136, 20, fill=LBLUE, outline="", tags=t)
        draw_face(c, kind, x + 63, y + 80, t)
        c.create_text(x + 124, y + 32, text=info["name"], anchor="w", fill=NAVY, font=app.font(25), tags=t)
        c.create_text(x + 125, y + 60, text=info["ages"], anchor="w", fill=GREY, font=app.font(14, "normal"), tags=t)
        price = "FREE!" if info["price"] == 0 else "$%d" % info["price"]
        rrect(c, x + 123, y + 78, x + 213, y + 108, 15, fill=RED, outline=NAVY, width=3, tags=t)
        c.create_text(x + 168, y + 93, text=price, fill=WHITE, font=app.font(18), tags=t)
        c.create_text(x + 125, y + 128, text=info["line"], anchor="w", fill=BLUE,
                      font=app.font(13, "normal", "italic"), tags=t)
        rrect(c, x + 262, y + 12, x + 308, y + 138, 23, fill=LBLUE, outline="", tags=t)
        self.count_item = c.create_text(x + 285, y + 76, text=str(app.counts[kind]), fill=NAVY,
                                        font=app.font(30), tags=t)
        self.plus = PopButton(app, x + 285, y + 33, 40, 40, "+", lambda: app.change(kind, +1),
                              fill=RED, size=26, shape="circle", group=self.group)
        self.minus = PopButton(app, x + 285, y + 116, 40, 40, "−", lambda: app.change(kind, -1),
                               fill=BLUE, size=26, shape="circle", group=self.group)
        self.hover = False

    def contains(self, x, y):
        x1, y1, x2, y2 = self.box
        return x1 <= x <= x2 and y1 <= y <= y2

    def lift(self, on):
        self.hover = on
        self.app.anim.tween(self.group.dy, -7 if on else 0, 300, lambda v: self.group.set_offset(0, v),
                            ease_out_back, key=(self.group.tag, "dy"))

    def set_count(self, n):
        a = self.app
        a.c.itemconfig(self.count_item, text=str(n))
        a.anim.tween(1, 0, 800, lambda v: a.c.itemconfig(self.count_item, font=a.font(int(30 + 22 * v))),
                     ease_out_elastic, key=(self.group.tag, "pop"))
        base = -7 if self.hover else 0
        a.anim.tween(0, 1, 420, lambda v: self.group.set_offset(0, base - 16 * math.sin(math.pi * v)),
                     ease_out_quad, key=(self.group.tag, "dy"))


# --------------------------------------------------------------------------- #
#  The website
# --------------------------------------------------------------------------- #
class FunLandSite:
    def __init__(self, root):
        self.root = root
        root.title("FunLand Park")
        total = max(560, min(800, root.winfo_screenheight() - 90))
        root.geometry("%dx%d" % (W, total))
        root.minsize(W, 520)
        root.resizable(False, True)
        self.family = pick_family(root)
        self._fonts = {}
        self.anim = Animator(root)

        # interaction + page bookkeeping
        self.hoverables, self.hovered, self.press_target = [], None, None
        self.layer = "main"
        self.page_tag = self.page_name = None
        self.page_n = 0
        self.sec = None
        self.sections, self.page_widgets, self.page_windows = [], [], []
        self.page_tickers, self.page_motion, self.page_leave, self.page_clouds = [], [], [], []
        self.page_h = total - HH
        self.view_h = total - HH
        self.scroll_pos = self.scroll_target = 0.0
        self.toast_token, self.toast_top = 0, 0.0
        self.particles = []

        # shop state (persists across pages)
        self.counts = {k: 0 for k in ORDER}
        self.fastpass, self.chip, self.promo, self.date_idx = False, None, None, 0
        self.total_shown = 0.0
        self.prev_auto = {"family": False, "group": False}
        self.form = {}
        self.orders = []
        self.just_paid = False
        self.favs = set()
        self.ride_filter = "all"

        self.hc = tk.Canvas(root, width=W, height=HH, highlightthickness=0, bg=hexrgb(SKY_TOP))
        self.hc.pack(side="top", fill="x")
        self.c = tk.Canvas(root, width=W, height=self.view_h, highlightthickness=0, bg=hexrgb(SKY_BOT))
        self.c.pack(side="top", fill="both", expand=True)
        self.c.bind("<Configure>", self._on_resize)

        self.build_header()
        self.thumb = self.c.create_polygon(0, 0, 0, 0, fill=NAVY, outline="", smooth=True, tags=("thumb",))
        self.totop = PopButton(self, W - 56, 0, 52, 52, "↑", lambda: self.scroll_to(0, 700), fill=RED,
                               size=26, shape="circle", page=False, fixed=True)
        self.totop.visible = False
        self.totop.redraw()

        self.anim.tickers += [self.tick_page, self.tick_confetti]
        for cv in (self.hc, self.c):
            cv.bind("<Motion>", lambda e, cv=cv: self.on_motion(cv, e))
            cv.bind("<ButtonPress-1>", lambda e, cv=cv: self.on_press(cv, e))
            cv.bind("<ButtonRelease-1>", lambda e, cv=cv: self.on_release(cv, e))
            cv.bind("<Leave>", lambda e: self.set_hover(None))
        root.bind_all("<MouseWheel>", self.on_wheel)
        root.bind_all("<Button-4>", self.on_wheel)
        root.bind_all("<Button-5>", self.on_wheel)
        root.after(60, lambda: self.navigate("home"))
        root.after(1800, lambda: self.toast("Welcome to FunLand! Scroll down to explore", BLUE))

    # ===================================================================== #
    #  Infrastructure
    # ===================================================================== #
    def font(self, px, weight="bold", slant="roman"):
        key = (px, weight, slant)
        if key not in self._fonts:
            self._fonts[key] = (self.family, -px, weight) + (("italic",) if slant == "italic" else ())
        return self._fonts[key]

    def restack(self):
        for tag in ("fixed", "modal", "confetti", "toast", "thumb"):
            self.c.tag_raise(tag)

    def section(self, intro=True):
        g = Group(self.c, "%s_s%d" % (self.page_tag, len(self.sections)))
        g.intro = intro
        self.sections.append(g)
        self.sec = g
        return g

    def T(self, *extra, group=None):
        g = group or self.sec
        return (self.page_tag,) + tuple(g.chain()) + extra

    def panel(self, x1, y1, x2, y2, r=26, fill=WHITE, outline=BLUE, shadow=NAVY, tags=None):
        t = tags or self.T()
        rrect(self.c, x1 + 6, y1 + 7, x2 + 6, y2 + 7, r, fill=shadow, outline="", tags=t)
        return rrect(self.c, x1, y1, x2, y2, r, fill=fill, outline=outline, width=4, tags=t)

    def text(self, x, y, s, size=16, color=NAVY, anchor="w", weight="bold", slant="roman", tags=None, **kw):
        return self.c.create_text(x, y, text=s, anchor=anchor, fill=color, font=self.font(size, weight, slant),
                                  tags=tags or self.T(), **kw)

    def shadow_title(self, x, y, s, size=42, anchor="w"):
        self.text(x + 3, y + 4, s, size, NAVY, anchor)
        self.text(x, y, s, size, WHITE, anchor)

    def link_text(self, x, y, s, command, color=WHITE, hover="#9CCBFF", size=16, anchor="w", tags=None):
        item = self.text(x, y, s, size, color, anchor, tags=tags)
        x1, y1, x2, y2 = self.c.bbox(item)
        Hotspot(self, x1 - 4, y1 - 4, x2 + 4, y2 + 4, command,
                enter=lambda: self.c.itemconfig(item, fill=hover), leave=lambda: self.c.itemconfig(item, fill=color))
        return item

    # ---------------- scrolling ------------------------------------------
    def _on_resize(self, e):
        self.view_h = e.height
        self._set_region()
        self.scroll_to(self.scroll_target, 1)

    def _set_region(self):
        self.region_h = max(self.page_h, self.view_h)
        self.c.config(scrollregion=(0, 0, W, self.region_h))

    def scroll_to(self, y, dur=380):
        y = max(0.0, min(float(y), self.region_h - self.view_h))
        self.scroll_target = y
        self.anim.tween(self.scroll_pos, y, dur, self._set_scroll, ease_out_cubic, key="scroll")

    def _set_scroll(self, v):
        self.scroll_pos = v
        self.c.yview_moveto(v / self.region_h if self.region_h else 0)
        self._update_fixed()

    def on_wheel(self, e):
        if self.layer != "main":
            return
        if getattr(e, "num", None) == 4:
            steps = -1
        elif getattr(e, "num", None) == 5:
            steps = 1
        else:
            steps = -e.delta / 120 if abs(e.delta) >= 120 else -e.delta / 10
        self.scroll_to(self.scroll_target + steps * 110, 380)

    def _update_fixed(self):
        top = self.c.canvasy(0)
        vh = self.view_h
        if self.region_h > vh + 1:
            th = max(40, vh * vh / self.region_h)
            ty = top + (top / (self.region_h - vh)) * (vh - th)
            self.c.coords(self.thumb, *rrect_pts(W - 10, ty + 4, W - 4, ty + th - 4, 3))
            self.c.itemconfig(self.thumb, state="normal")
        else:
            self.c.itemconfig(self.thumb, state="hidden")
        show = top > 250 and self.layer == "main"
        cy = top + vh - 46
        if show != self.totop.visible or (show and abs(cy - self.totop.cy) > 0.5):
            self.totop.visible, self.totop.cy = show, cy
            self.totop.redraw()
        if top != self.toast_top:
            self.c.move("toast", 0, top - self.toast_top)
            self.toast_top = top

    # ---------------- pointer routing ------------------------------------
    def usable(self, h):
        if h.dead:
            return False
        if h.layer == "nav":
            return self.layer == "main"
        return h.layer == self.layer and (h.page is None or h.page == self.page_tag)

    def target_at(self, cv, x, y):
        for h in reversed(self.hoverables):
            if h.cv is cv and self.usable(h) and h.contains(x, y):
                return h
        return None

    def set_hover(self, tgt):
        if tgt is self.hovered:
            return
        if self.hovered and not self.hovered.dead:
            self.hovered.on_leave()
        self.hovered = tgt
        if tgt:
            tgt.on_enter()
        for cv in (self.hc, self.c):
            cv.config(cursor="hand2" if tgt and tgt.cv is cv else "")

    def on_motion(self, cv, e):
        x, y = cv.canvasx(e.x), cv.canvasy(e.y)
        self.set_hover(self.target_at(cv, x, y))
        if cv is self.c and self.layer == "main":
            for f in self.page_motion:
                f(x, y)

    def on_press(self, cv, e):
        self.root.focus_set()  # clicking the page leaves any text box
        x, y = cv.canvasx(e.x), cv.canvasy(e.y)
        self.press_target = self.target_at(cv, x, y)
        if self.press_target:
            self.press_target.on_press()

    def on_release(self, cv, e):
        tgt, self.press_target = self.press_target, None
        if tgt and not tgt.dead:
            x, y = cv.canvasx(e.x), cv.canvasy(e.y)
            tgt.on_release(tgt.cv is cv and tgt.contains(x, y) and self.usable(tgt))

    # ---------------- page routing ---------------------------------------
    def navigate(self, name, force=False):
        if self.layer == "transition":
            return
        if name == self.page_name and not force:
            self.scroll_to(0, 600)
            return
        self.set_nav_active(name)
        self.set_hover(None)
        old, old_name = self.page_tag, self.page_name
        self.layer = "transition"
        self._update_fixed()
        if old:
            for f in self.page_leave:
                f()
            self.page_leave = []
            forward = PAGES.index(name) >= PAGES.index(old_name)
            g = Group(self.c, old)
            self.anim.tween(0, -W if forward else W, 380, lambda v: g.set_offset(v, 0), ease_in_back,
                            done=lambda: self._build_page(name), key="pageout")
        else:
            self._build_page(name)

    def _teardown(self):
        if not self.page_tag:
            return
        for h in self.hoverables:
            if h.page == self.page_tag:
                h.dead = True
        self.hoverables = [h for h in self.hoverables if not h.dead]
        if self.hovered and self.hovered.dead:
            self.hovered = None
        for w in self.page_widgets:
            w.destroy()
        self.page_widgets, self.page_windows = [], []
        self.page_tickers, self.page_motion, self.page_clouds = [], [], []
        self.c.delete(self.page_tag)

    def _build_page(self, name):
        self._teardown()
        self.page_n += 1
        self.page_tag, self.page_name = "pg%d" % self.page_n, name
        self.sections, self.sec = [], None
        self.page_h = getattr(self, "page_" + name)()
        self._set_region()
        self.scroll_pos = self.scroll_target = 0.0
        self.anim.cancel("scroll")
        self.c.yview_moveto(0)
        k = 0
        for g in self.sections:  # anime.js-style staggered entrance
            if not g.intro:
                continue
            g.set_offset(0, 70)
            self.anim.tween(70, 0, 800, lambda v, g=g: g.set_offset(g.dx, v), ease_out_back,
                            delay=40 + k * 90, key=(g.tag, "intro"))
            k += 1
        self.root.after(160, self._page_ready)
        self._update_fixed()
        self.restack()

    def _page_ready(self):
        if self.layer == "transition":
            self.layer = "main"
            self._update_fixed()

    def page_bg(self, h):
        t = (self.page_tag, "bg")
        for y in range(0, h, 10):
            self.c.create_rectangle(0, y, W, y + 10, fill=sky_at(y), outline="", tags=t)
        rnd = random.Random(self.page_n)
        for i in range(max(3, h // 230)):
            x, y, s = rnd.uniform(0, W), rnd.uniform(40, h - 260), rnd.uniform(0.7, 1.15)
            tag = "%s_cloud%d" % (self.page_tag, i)
            for ox, oy, rx, ry in [(0, 0, 40, 22), (-30, 8, 28, 18), (30, 8, 30, 18), (5, -14, 26, 20)]:
                self.c.create_oval(x + (ox - rx) * s, y + (oy - ry) * s, x + (ox + rx) * s, y + (oy + ry) * s,
                                   fill=WHITE, outline="", tags=t + (tag,))
            self.page_clouds.append([tag, x, rnd.uniform(8, 22)])

    def tick_page(self, now, dt):
        for cl in self.page_clouds:
            self.c.move(cl[0], cl[2] * dt, 0)
            cl[1] += cl[2] * dt
            if cl[1] > W + 90:
                self.c.move(cl[0], -(W + 200), 0)
                cl[1] -= W + 200
        for f in list(self.page_tickers):
            f(now, dt)
        # header logo wheel
        cx, cy = 48, 64
        for i, sp in enumerate(self.logo_spokes):
            a = now * 1.2 + i * math.pi / 3
            self.hc.coords(sp, cx, cy, cx + 17 * math.cos(a), cy + 17 * math.sin(a))

    # ===================================================================== #
    #  Header / nav bar
    # ===================================================================== #
    def build_header(self):
        hc = self.hc
        for y in range(0, HH, 4):
            hc.create_rectangle(0, y, W, y + 4, fill=sky_at(y), outline="")
        sw = 40
        for i in range(W // sw + 1):
            col, x = (RED if i % 2 == 0 else WHITE), i * sw
            hc.create_rectangle(x, 0, x + sw, 16, fill=col, outline="")
            hc.create_arc(x, 2, x + sw, 30, start=180, extent=180, style="chord", fill=col, outline="")
            hc.create_arc(x, 2, x + sw, 30, start=180, extent=180, style="arc", outline=NAVY, width=2)
        hc.create_line(0, 2, W, 2, fill=NAVY, width=4)
        rrect(hc, 19, 43, 1091, 95, 26, fill=NAVY, outline="")
        rrect(hc, 14, 38, 1086, 90, 26, fill=WHITE, outline=BLUE, width=3)
        # logo
        self.logo_spokes = [hc.create_line(0, 0, 0, 0, fill=BLUE, width=3) for _ in range(6)]
        hc.create_oval(29, 45, 67, 83, outline=RED, width=4)
        hc.create_oval(44, 60, 52, 68, fill=RED, outline=NAVY, width=2)
        f = tkfont.Font(family=self.family, size=-30, weight="bold")
        hc.create_text(78, 64, text="Fun", anchor="w", fill=RED, font=self.font(30))
        hc.create_text(78 + f.measure("Fun"), 64, text="Land", anchor="w", fill=BLUE, font=self.font(30))
        Hotspot(self, 26, 42, 80 + f.measure("FunLand"), 86, lambda: self.navigate("home"), layer="nav", cv=hc)
        # links
        fl = tkfont.Font(family=self.family, size=-18, weight="bold")
        x = 330
        self.nav_items = {}
        for key, label in NAV:
            w = fl.measure(label)
            item = hc.create_text(x, 62, text=label, anchor="w", fill=NAVY, font=self.font(18))
            self.nav_items[key] = (item, x, x + w)
            Hotspot(self, x - 10, 44, x + w + 10, 86, lambda k=key: self.navigate(k), layer="nav", cv=hc,
                    enter=lambda i=item: self._nav_hover(i, True), leave=lambda i=item: self._nav_hover(i, False))
            x += w + 36
        self.nav_ind = hc.create_polygon(0, 0, 0, 0, fill=RED, outline="", smooth=True)
        self.nav_pos = (330.0, 330.0)
        self.nav_active = None
        self.cart_btn = PopButton(self, 1010, 64, 128, 40, "Cart", self.go_cart, fill=RED, size=18,
                                  cv=hc, layer="nav")
        self.badge = [hc.create_oval(0, 0, 0, 0, fill=NAVY, outline=WHITE, width=2, tags=("badge",)),
                      hc.create_text(1066, 44, text="", fill=WHITE, font=self.font(13), tags=("badge",))]
        hc.itemconfig("badge", state="hidden")

    def _nav_hover(self, item, on):
        active = self.nav_items.get(self.nav_active, (None,))[0]
        self.hc.itemconfig(item, fill=RED if on or item == active else NAVY)

    def set_nav_active(self, name):
        name = "tickets" if name == "checkout" else name
        self.nav_active = name
        for k, (item, x1, x2) in self.nav_items.items():
            self.hc.itemconfig(item, fill=RED if k == name else NAVY)
        a0, b0 = self.nav_pos
        _, a1, b1 = self.nav_items[name]

        def setter(v):
            a, b = a0 + (a1 - a0) * v, b0 + (b1 - b0) * v
            self.nav_pos = (a, b)
            self.hc.coords(self.nav_ind, *rrect_pts(a, 76, max(b, a + 6), 82, 3))
        self.anim.tween(0, 1, 700, setter, ease_out_elastic, key="navind")

    def update_badge(self):
        n = sum(self.counts.values())
        hc = self.hc
        if not n:
            hc.itemconfig("badge", state="hidden")
            return
        hc.itemconfig("badge", state="normal")
        hc.itemconfig(self.badge[1], text=str(n))
        hc.tag_raise("badge")

        def setter(v):
            r = 13 * v
            hc.coords(self.badge[0], 1066 - r, 44 - r, 1066 + r, 44 + r)
        self.anim.tween(0.4, 1, 700, setter, ease_out_elastic, key="badge")

    def go_cart(self):
        if sum(self.counts.values()):
            self.navigate("checkout")
        else:
            self.toast("Your cart is empty - pick some tickets first!", RED)
            self.navigate("tickets")

    # ===================================================================== #
    #  Shared page pieces
    # ===================================================================== #
    def footer(self, y0, group=None):
        if group is None:
            self.section(intro=False)
        t = self.T()
        c = self.c
        c.create_line(0, y0 + 4, W, y0 + 4, fill=NAVY, width=3, tags=t)
        cols = [RED, WHITE, BLUE]
        for i, x in enumerate(range(0, W, 40)):
            c.create_polygon(x + 4, y0 + 4, x + 36, y0 + 4, x + 20, y0 + 30, fill=cols[i % 3], outline=NAVY,
                             width=2, tags=t)
        c.create_rectangle(0, y0 + 42, W, y0 + 200, fill=NAVY, outline="", tags=t)
        self.text(40, y0 + 82, "FunLand Park", 28, WHITE)
        self.text(40, y0 + 116, "1 Rollercoaster Road, Joyville  -  Open every day", 14, "#B9D4FF", weight="normal")
        self.text(40, y0 + 170, "(c) 2026 FunLand Park  -  Demo website: no real payments are taken.", 12, "#8FA9D9",
                  weight="normal")
        x = 560
        for key, label in NAV:
            item = self.link_text(x, y0 + 82, label, lambda k=key: self.navigate(k), size=16)
            x = self.c.bbox(item)[2] + 26
        self.text(560, y0 + 118, "Call 555-FUN-LAND   -   hello@funland.example", 14, "#B9D4FF", weight="normal")
        return y0 + 200

    def steps(self, active):
        c, t = self.c, self.T()
        c.create_line(800, 52, 1000, 52, fill=WHITE, width=6, tags=t)
        if active > 1:
            c.create_line(800, 52, 800 + 100 * (active - 1), 52, fill=RED, width=6, tags=t)
        for i, name in enumerate(["Tickets", "Checkout", "Done"]):
            x = 800 + 100 * i
            fill = RED if i + 1 == active else (BLUE if i + 1 < active else WHITE)
            c.create_oval(x - 17, 35, x + 17, 69, fill=fill, outline=NAVY, width=3, tags=t)
            self.text(x, 52, str(i + 1), 16, NAVY if fill == WHITE else WHITE, "center")
            self.text(x, 86, name, 13, NAVY, "center")

    def page_header(self, title, sub, step=None):
        self.section()
        self.shadow_title(42, 50, title)
        self.text(45, 92, sub, 17, NAVY, weight="normal")
        if step:
            self.steps(step)

    # ===================================================================== #
    #  HOME
    # ===================================================================== #
    def page_home(self):
        h = 1300
        self.page_bg(h)
        c = self.c
        # hero
        sec = self.section()
        self.panel(30, 24, 1070, 404, r=36, fill=BLUE, outline=NAVY)
        for bx, by, br in [(560, 60, 18), (610, 360, 26), (690, 92, 10), (520, 330, 12), (640, 210, 8)]:
            c.create_oval(bx - br, by - br, bx + br, by + br, outline=mix(BLUE, WHITE, 0.35), width=3, tags=self.T())
        today_hours = HOURS[datetime.date.today().weekday()][1].upper()
        rrect(c, 70, 52, 400, 88, 18, fill=RED, outline=NAVY, width=3, tags=self.T())
        self.text(235, 70, "OPEN TODAY  " + today_hours, 15, WHITE, "center")
        for i, line in enumerate(["The Happiest Day", "Out in Town!"]):
            self.text(73, 143 + i * 64, line, 52, NAVY)
            self.text(70, 139 + i * 64, line, 52, WHITE)
        self.text(72, 248, "42 rides, 12 live shows and a mountain of cotton candy.\n"
                           "Grab your tickets online and skip the queue at the gate!", 18, WHITE, "nw", "normal")
        PopButton(self, 170, 350, 200, 60, "Get Tickets", lambda: self.navigate("tickets"), fill=RED, size=22)
        PopButton(self, 395, 350, 210, 60, "Explore Rides", lambda: self.navigate("rides"), fill=WHITE, fg=BLUE,
                  size=22)
        cx, cy, R = 875, 205, 145
        t = self.T()
        c.create_line(cx, cy, cx - 85, 396, fill=NAVY, width=9, tags=t)
        c.create_line(cx, cy, cx + 85, 396, fill=NAVY, width=9, tags=t)
        spokes = [c.create_line(0, 0, 0, 0, fill=WHITE, width=3, tags=t) for _ in range(12)]
        c.create_oval(cx - R, cy - R, cx + R, cy + R, outline=RED, width=7, tags=t)
        c.create_oval(cx - R + 14, cy - R + 14, cx + R - 14, cy + R - 14, outline=WHITE, width=2, tags=t)
        c.create_oval(cx - 16, cy - 16, cx + 16, cy + 16, fill=RED, outline=NAVY, width=3, tags=t)
        cabins = [c.create_rectangle(0, 0, 0, 0, fill=RED if i % 2 else WHITE, outline=NAVY, width=3, tags=t)
                  for i in range(12)]

        def spin(now, dt):
            ox, oy = sec.ox(), sec.oy()
            a0 = now * 0.35
            for i in range(12):
                a = a0 + i * math.pi / 6
                x, y = cx + ox + R * math.cos(a), cy + oy + R * math.sin(a)
                c.coords(spokes[i], cx + ox, cy + oy, x, y)
                c.coords(cabins[i], x - 12, y - 2, x + 12, y + 20)
        self.page_tickers.append(spin)

        # stats with count-up numbers
        self.section()
        for i, (num, suffix, label) in enumerate([(42, "", "Thrilling rides"), (12, "", "Live shows daily"),
                                                  (30, "", "Snack stands"), (98, "%", "Smiles guaranteed")]):
            x1 = 30 + i * 266
            self.panel(x1, 440, x1 + 242, 560, r=24)
            item = self.text(x1 + 121, 484, "0" + suffix, 44, RED, "center")
            self.text(x1 + 121, 532, label, 16, NAVY, "center")
            self.anim.tween(0, num, 1700, lambda v, it=item, s=suffix: c.itemconfig(it, text="%d%s" % (round(v), s)),
                            ease_out_expo, delay=650 + i * 130)

        # features
        self.section()
        self.shadow_title(550, 612, "Why kids (and grown-ups) love us", 32, "center")
        feats = [(icon_coaster, "Wild Rides", "From gentle teacups to the 60 m Sky Screamer drop tower.", "rides"),
                 (icon_tent, "Big Top Shows", "Clowns, acrobats and a sparkly parade every single evening.", "info"),
                 (icon_icecream, "Yummy Treats", "Churros, ice cream and our famous blue cotton candy.", "info")]
        for i, (icon, title, body, dest) in enumerate(feats):
            x1 = 30 + i * 353
            fx = x1 + 167
            self.panel(x1, 650, x1 + 334, 912, r=28)
            c.create_oval(fx - 50, 664, fx + 50, 764, fill=LBLUE, outline="", tags=self.T())
            icon(c, fx, 714, self.T())
            self.text(fx, 790, title, 23, NAVY, "center")
            self.text(fx, 810, body, 15, GREY, "n", "normal", width=290, justify="center")
            PopButton(self, fx, 878, 160, 40, "Learn more", lambda d=dest: self.navigate(d), fill=WHITE, fg=BLUE,
                      size=15)

        # promo banner
        self.section()
        self.panel(30, 950, 1070, 1064, r=32, fill=RED, outline=NAVY)
        for sx, sy, sr in [(610, 978, 9), (650, 1040, 6), (700, 990, 5), (780, 1030, 8)]:
            star(c, sx, sy, sr, fill=WHITE, outline="", tags=self.T())
        self.text(70, 988, "Family Pack: 15% off!", 30, WHITE)
        self.text(72, 1030, "2+ grown-ups and 2+ kids? We apply the discount automatically.", 16, WHITE,
                  weight="normal")
        PopButton(self, 950, 1007, 190, 56, "Book now", lambda: self.navigate("tickets"), fill=WHITE, fg=RED,
                  size=22)
        return self.footer(1100)

    # ===================================================================== #
    #  RIDES
    # ===================================================================== #
    def page_rides(self):
        h = 1240
        self.page_bg(h)
        self.page_header("Rides & Attractions", "Tap a heart to save your favourites. Filter by how brave you feel!")
        self.section()
        self.panel(30, 118, 1070, 180, r=30)
        self.filter_btns = {}
        for i, key in enumerate(["all", "thrill", "family", "kids", "water"]):
            on = key == self.ride_filter
            b = PopButton(self, 102 + i * 124, 149, 112, 40, key.capitalize(), lambda k=key: self.set_filter(k),
                          fill=BLUE if on else WHITE, fg=WHITE if on else BLUE, size=16)
            self.filter_btns[key] = b
        self.c.create_polygon(heart_pts(845, 149, 0.8), fill=RED, outline=NAVY, width=2, smooth=True, tags=self.T())
        self.fav_item = self.text(866, 149, "Favourites: %d" % len(self.favs), 17, NAVY)
        self.grid_sec = self.section()
        self.heart_spots = []
        self.draw_ride_grid(animate=False)
        return self.footer(1040)

    def draw_ride_grid(self, animate=True):
        c = self.c
        for hs in self.heart_spots:
            hs.dead = True
        self.hoverables = [h for h in self.hoverables if not h.dead]
        self.heart_spots = []
        gtag = self.page_tag + "_ridecards"
        c.delete(gtag)
        rides = [r for r in RIDES if self.ride_filter in ("all", r[1])]
        prev_sec, self.sec = self.sec, self.grid_sec
        for i, (name, cat, desc, thrill, minh, wait) in enumerate(rides):
            x, y = 30 + (i % 3) * 353, 205 + (i // 3) * 272
            g = Group(c, "%s_ride%d" % (self.page_tag, i), parent=self.grid_sec)
            t = self.T(gtag, group=g)
            rrect(c, x + 6, y + 7, x + 340, y + 257, 26, fill=NAVY, outline="", tags=t)
            rrect(c, x, y, x + 334, y + 250, 26, fill=WHITE, outline=BLUE, width=4, tags=t)
            rrect(c, x + 12, y + 12, x + 322, y + 112, 20, fill=LBLUE, outline="", tags=t)
            RIDE_ICON[cat](c, x + 167, y + 62, t)
            fl = tkfont.Font(family=self.family, size=-12, weight="bold")
            pw = fl.measure(cat.upper()) + 20
            rrect(c, x + 22, y + 22, x + 22 + pw, y + 46, 12, fill=CAT_COLOR[cat], outline="", tags=t)
            self.text(x + 22 + pw / 2, y + 34, cat.upper(), 12, WHITE, "center", tags=t)
            rrect(c, x + 206, y + 82, x + 314, y + 106, 12, fill=WHITE, outline=BLUE, width=2, tags=t)
            self.text(x + 260, y + 94, "Wait ~%d min" % wait, 12, NAVY, "center", tags=t)
            c.create_oval(x + 278, y + 18, x + 318, y + 58, fill=WHITE, outline=BLUE, width=2, tags=t)
            heart = c.create_polygon(heart_pts(x + 298, y + 39, 0.8), smooth=True, width=2, outline=RED,
                                     fill=RED if name in self.favs else WHITE, tags=t)
            self.text(x + 20, y + 136, name, 21, NAVY, tags=t)
            self.text(x + 20, y + 156, desc, 14, GREY, "nw", "normal", tags=t, width=296)
            self.text(x + 20, y + 225, "Thrill", 13, NAVY, tags=t)
            for k in range(5):
                star(c, x + 82 + k * 20, y + 225, 8, fill=RED if k < thrill else LBLUE, outline="", tags=t)
            lab = "Min %d cm" % minh if minh else "All ages"
            lw = tkfont.Font(family=self.family, size=-13, weight="bold").measure(lab) + 22
            rrect(c, x + 314 - lw, y + 211, x + 314, y + 239, 14, fill=LBLUE, outline="", tags=t)
            self.text(x + 314 - lw / 2, y + 225, lab, 13, BLUE, "center", tags=t)
            hs = Hotspot(self, x + 276, y + 16, x + 320, y + 60,
                         lambda n=name, it=heart, cx=x + 298, cy=y + 39, g=g: self.toggle_fav(n, it, cx, cy, g),
                         group=g)
            self.heart_spots.append(hs)
            if animate:
                g.set_offset(0, 50)
                self.anim.tween(50, 0, 650, lambda v, g=g: g.set_offset(0, v), ease_out_back, delay=i * 70)
        if not rides:
            self.text(550, 300, "No rides here yet!", 24, NAVY, "center", tags=self.T(gtag))
        self.sec = prev_sec
        self.restack()

    def set_filter(self, key):
        self.ride_filter = key
        for k, b in self.filter_btns.items():
            b.set_style(fill=BLUE if k == key else WHITE, fg=WHITE if k == key else BLUE)
        self.draw_ride_grid()

    def toggle_fav(self, name, item, cx, cy, g):
        on = name not in self.favs
        (self.favs.add if on else self.favs.discard)(name)
        self.c.itemconfig(item, fill=RED if on else WHITE)
        self.c.itemconfig(self.fav_item, text="Favourites: %d" % len(self.favs))
        self.anim.tween(1.5 if on else 0.5, 0.8, 700,
                        lambda v: self.c.coords(item, *heart_pts(cx + g.ox(), cy + g.oy(), v)),
                        ease_out_elastic, key=("heart", name))
        if on:
            self.confetti(cx + g.ox(), cy + g.oy(), 14, 0.4)
            self.toast("Saved %s to your favourites!" % name, BLUE)

    # ===================================================================== #
    #  TICKETS
    # ===================================================================== #
    def page_tickets(self):
        OY = 65
        h = 1040
        self.page_bg(h)
        c = self.c
        self.page_header("Buy Tickets", "Pick a date, choose your crew and grab a deal.", step=1)
        # date picker
        self.section()
        self.panel(30, 120, 1070, 188, r=30)
        self.text(52, 154, "Visit date:", 19, NAVY)
        self.date_btns = []
        today = datetime.date.today()
        for i in range(7):
            d = today + datetime.timedelta(days=i)
            top = "Today" if i == 0 else "Tomorrow" if i == 1 else d.strftime("%a")
            on = i == self.date_idx
            b = PopButton(self, 250 + i * 118, 152, 110, 50, "%s\n%s" % (top, d.strftime("%d %b")),
                          lambda i=i: self.pick_date(i), fill=BLUE if on else WHITE, fg=WHITE if on else BLUE,
                          size=14)
            self.date_btns.append(b)
        # ticket cards
        self.section()
        self.cards = [TicketCard(self, i, k, *pos) for i, (k, pos) in
                      enumerate(zip(ORDER, [(30, 140 + OY), (370, 140 + OY), (30, 305 + OY), (370, 305 + OY)]))]
        self.page_motion.append(self._card_hover)
        # pass type switch
        self.pass_sec = self.section()
        t = self.T()
        rrect(c, 36, 478 + OY, 696, 532 + OY, 27, fill=NAVY, outline="", tags=t)
        rrect(c, 30, 472 + OY, 690, 526 + OY, 27, fill=WHITE, outline=BLUE, width=4, tags=t)
        self.text(52, 499 + OY, "Pass Type:", 19, NAVY)
        self.knob = Group(c, self.page_tag + "_knob", parent=self.pass_sec)
        rrect(c, 182, 479 + OY, 434, 519 + OY, 20, fill=RED, outline=NAVY, width=3, tags=self.T(group=self.knob))
        self.pass_txt = [self.text(308, 499 + OY, "Standard Day Pass", 16, WHITE, "center"),
                         self.text(558, 499 + OY, "FAST PASS  +$%d/guest" % FASTPASS_PRICE, 16, NAVY, "center")]
        Hotspot(self, 182, 479 + OY, 434, 519 + OY, lambda: self.set_fastpass(False))
        Hotspot(self, 434, 479 + OY, 686, 519 + OY, lambda: self.set_fastpass(True))
        if self.fastpass:
            self.knob.set_offset(252, 0)
            c.itemconfig(self.pass_txt[0], fill=NAVY)
            c.itemconfig(self.pass_txt[1], fill=WHITE)
        # discounts
        self.disc_sec = self.section()
        self.panel(30, 545 + OY, 690, 725 + OY)
        star(c, 56, 574 + OY, 13, fill=RED, outline=NAVY, width=2, tags=self.T())
        self.text(76, 574 + OY, "Discounts & Deals", 22, BLUE)
        self.text(676, 574 + OY, "Psst... try code FUN10", 13, GREY, "e", "normal", "italic")
        self.chip_btns = {}
        for i, (key, (name, pct)) in enumerate(CHIPS.items()):
            on = key == self.chip
            self.chip_btns[key] = PopButton(self, 100 + i * 140, 614 + OY, 128, 38, "%s -%d%%" % (name, pct * 100),
                                            lambda k=key: self.toggle_chip(k), fill=BLUE if on else WHITE,
                                            fg=WHITE if on else BLUE, size=15)
        self.promo_field = Field(self, 50, 667 + OY, 210, 42, value=self.promo or "", placeholder="PROMO CODE",
                                 size=18, justify="center")
        self.promo_field.entry.bind("<Return>", lambda e: self.apply_promo())
        self.apply_btn = PopButton(self, 330, 667 + OY, 112, 42, "APPLY", self.apply_promo, fill=RED, size=17)
        msg = ("Code %s is active." % self.promo) if self.promo else "Discounts never stack - we pick your best deal!"
        self.promo_msg = self.text(52, 706 + OY, msg, 13, BLUE if self.promo else GREY, weight="normal")
        c.create_line(458, 596 + OY, 458, 712 + OY, fill=LBLUE, width=3, tags=self.T())
        self.text(476, 604 + OY, "Auto Deals", 16, BLUE)
        self.auto_dots = {}
        for key, y, title, sub in [("family", 642 + OY, "Family Pack -15%", "2+ grown-ups & 2+ kids"),
                                   ("group", 688 + OY, "Big Group -20%", "10+ guests in total")]:
            self.auto_dots[key] = (c.create_oval(476, y - 11, 498, y + 11, fill=WHITE, outline=BLUE, width=3,
                                                 tags=self.T()), y)
            self.text(508, y - 8, title, 15, NAVY)
            self.text(508, y + 11, sub, 12, GREY, weight="normal")
        # order summary
        self.sum_sec = self.section()
        x1, y1, x2, y2 = 722, 140 + OY, 1075, 722 + OY
        self.panel(x1, y1, x2, y2, r=28)
        rrect(c, x1 + 10, y1 + 10, x2 - 10, y1 + 64, 20, fill=RED, outline=NAVY, width=3, tags=self.T())
        self.text((x1 + x2) / 2, y1 + 37, "YOUR TICKETS", 27, WHITE, "center")
        star(c, x1 + 34, y1 + 37, 12, fill=WHITE, outline=NAVY, width=2, tags=self.T())
        star(c, x2 - 34, y1 + 37, 12, fill=WHITE, outline=NAVY, width=2, tags=self.T())
        ny = 476 + OY
        c.create_line(x1 + 28, ny, x2 - 28, ny, fill=BLUE, width=3, dash=(8, 6), tags=self.T())
        for nx in (x1, x2):
            c.create_oval(nx - 17, ny - 17, nx + 17, ny + 17, fill=sky_at(ny), outline="", tags=self.T())
            c.create_arc(nx - 17, ny - 17, nx + 17, ny + 17, start=-90 if nx == x1 else 90, extent=180,
                         style="arc", outline=BLUE, width=4, tags=self.T())
        self.text(x1 + 26, 510 + OY, "TOTAL", 22, NAVY)
        self.total_item = self.text(x2 - 26, 546 + OY, "$0.00", 42, RED, "e")
        self.save_item = self.text(x1 + 26, 548 + OY, "", 14, BLUE)
        self.buy_btn = PopButton(self, (x1 + x2) / 2, 628 + OY, 300, 66, "CHECKOUT", self.to_checkout,
                                 fill=RED, size=27)
        PopButton(self, (x1 + x2) / 2, 692 + OY, 150, 34, "Start over", self.reset, fill=WHITE, fg=BLUE, size=14)
        self.page_tickers.append(self._buy_pulse)
        self.OY = OY
        self._prev_rows, self._prev_deal = {}, None
        self.total_shown = 0.0
        self.update_summary(animate=False)
        self.anim.tween(0, self.compute()["total"], 1200, self._set_total, ease_out_expo, delay=700, key="total")
        self.page_leave.append(lambda: setattr(self, "cards", []))
        return self.footer(840)

    def _card_hover(self, x, y):
        for card in self.cards:
            inside = card.contains(x, y)
            if inside != card.hover:
                card.lift(inside)

    def _buy_pulse(self, now, dt):
        if self.layer != "main" or self.buy_btn.pressed:
            return
        target = 1 + 0.035 * math.sin(now * 4.2) if sum(self.counts.values()) else 1.0
        if abs(target - self.buy_btn.pulse) > 0.002:
            self.buy_btn.pulse = target
            self.buy_btn.redraw()

    def pick_date(self, i):
        self.date_idx = i
        for k, b in enumerate(self.date_btns):
            b.set_style(fill=BLUE if k == i else WHITE, fg=WHITE if k == i else BLUE)
        d = datetime.date.today() + datetime.timedelta(days=i)
        self.toast("Visit date: %s" % d.strftime("%A, %d %B"), BLUE)

    def visit_date(self):
        return datetime.date.today() + datetime.timedelta(days=self.date_idx)

    def set_fastpass(self, on):
        if on == self.fastpass:
            return
        self.fastpass = on
        self.anim.tween(self.knob.dx, 252 if on else 0, 650, lambda v: self.knob.set_offset(v, 0),
                        ease_out_elastic, key="knob")
        self.c.itemconfig(self.pass_txt[0], fill=NAVY if on else WHITE)
        self.c.itemconfig(self.pass_txt[1], fill=WHITE if on else NAVY)
        if on:
            self.toast("Zoom! Fast Pass skips the long lines", BLUE)
        self.update_summary()

    def toggle_chip(self, key):
        self.chip = None if self.chip == key else key
        for k, b in self.chip_btns.items():
            on = k == self.chip
            b.set_style(fill=BLUE if on else WHITE, fg=WHITE if on else BLUE)
        if self.chip:
            name, pct = CHIPS[key]
            self.say("%s discount selected (-%d%%). Please show ID at the gate." % (name, pct * 100), BLUE)
        self.update_summary()

    def say(self, text, color):
        self.c.itemconfig(self.promo_msg, text=text, fill=color)

    def apply_promo(self):
        code = self.promo_field.get().upper()
        if not code:
            if self.promo:
                self.say("Promo %s removed." % self.promo, GREY)
                self.promo = None
                self.update_summary()
            else:
                self.promo_field.shake()
                self.say("Type a promo code first!", RED)
            return
        if code in PROMOS:
            self.promo = code
            self.promo_field.set_error(False)
            self.say("Yay! %s unlocked: %d%% off!" % (code, PROMOS[code] * 100), BLUE)
            bx, by = self.apply_btn.pos()
            self.confetti(bx, by, 45, 0.7)
            self.update_summary()
        else:
            self.promo_field.shake()
            self.apply_btn.shake()
            self.say("Oops! \"%s\" isn't a magic word. Try again!" % code[:12], RED)

    def compute(self):
        n = self.counts
        sub = sum(n[k] * TYPES[k]["price"] for k in ORDER)
        paying = n["adult"] + n["child"] + n["senior"]
        fast = FASTPASS_PRICE * paying if self.fastpass else 0
        guests = sum(n.values())
        auto = {"family": n["adult"] + n["senior"] >= 2 and n["child"] >= 2, "group": guests >= 10}
        deals = []
        if self.chip:
            deals.append((CHIPS[self.chip][1], "%s ID" % CHIPS[self.chip][0]))
        if self.promo:
            deals.append((PROMOS[self.promo], "Code %s" % self.promo))
        if auto["family"]:
            deals.append((0.15, "Family Pack"))
        if auto["group"]:
            deals.append((0.20, "Big Group"))
        best = max(deals) if deals else None
        base = sub + fast
        disc = round(base * best[0], 2) if best and base else 0.0
        return dict(sub=sub, fast=fast, paying=paying, guests=guests, auto=auto, best=best,
                    disc=disc, total=round(base - disc, 2))

    def bill_rows(self, b):
        rows = []
        for k in ORDER:
            if self.counts[k]:
                p = TYPES[k]["price"]
                rows.append((k, "%d x %s" % (self.counts[k], TYPES[k]["one" if self.counts[k] == 1 else "name"]),
                             "FREE" if p == 0 else "$%.2f" % (self.counts[k] * p), NAVY))
        if b["fast"]:
            rows.append(("fast", "Fast Pass x %d" % b["paying"], "$%.2f" % b["fast"], BLUE))
        return rows

    def update_summary(self, animate=True):
        if self.page_name != "tickets":
            return
        c, OY = self.c, self.OY
        b = self.compute()
        rtag = self.page_tag + "_rows"
        for key in [k for k in self.anim.tweens if isinstance(k, tuple) and k[0] == "slide"]:
            self.anim.cancel(key)
        c.delete(rtag)
        x1, x2 = 748, 1049
        gx, gy = self.sum_sec.ox(), self.sum_sec.oy()
        T = lambda *e: self.T(rtag, *e, group=self.sum_sec)
        rows = self.bill_rows(b)
        if not rows:
            self.text(898 + gx, 270 + OY + gy, "No tickets yet!", 24, NAVY, "center", tags=T())
            self.text(898 + gx, 304 + OY + gy, "Tap a red  +  to add some fun", 15, GREY, "center", "normal", tags=T())
            rrect(c, 828 + gx, 344 + OY + gy, 968 + gx, 412 + OY + gy, 12, fill=LBLUE, outline=BLUE, width=3,
                  dash=(6, 4), tags=T())
            star(c, 898 + gx, 378 + OY + gy, 20, fill=WHITE, outline=BLUE, width=2, tags=T())
        for i, (key, left, right, col) in enumerate(rows):
            y = 232 + OY + i * 34 + gy
            tag = "%s_row_%s" % (self.page_tag, key)
            self.text(x1 + gx, y, left, 17, col, tags=T(tag))
            self.text(x2 + gx, y, right, 17, col, "e", tags=T(tag))
            if animate and self._prev_rows.get(key) != (left, right):
                self._slide_in(tag, i)
        self._prev_rows = {k: (l, r) for k, l, r, _ in rows}
        if rows:
            y = 412 + OY + gy
            c.create_line(x1 + gx, y - 18, x2 + gx, y - 18, fill=LBLUE, width=2, tags=T())
            self.text(x1 + gx, y, "Subtotal", 16, GREY, tags=T())
            self.text(x2 + gx, y, "$%.2f" % (b["sub"] + b["fast"]), 16, GREY, "e", tags=T())
            if b["best"]:
                pct, name = b["best"]
                dtag = self.page_tag + "_row_deal"
                self.text(x1 + gx, y + 30, "%s (-%d%%)" % (name, round(pct * 100)), 16, BLUE, tags=T(dtag))
                self.text(x2 + gx, y + 30, "-$%.2f" % b["disc"], 16, BLUE, "e", tags=T(dtag))
                if animate and self._prev_deal != b["best"]:
                    self._slide_in(dtag, 0)
            else:
                self.text(x1 + gx, y + 30, "No discount yet", 14, GREY, slant="italic", weight="normal", tags=T())
        self._prev_deal = b["best"]
        c.itemconfig(self.save_item, text=("You save $%.2f!" % b["disc"]) if b["disc"] else "")
        for key, (dot, y) in self.auto_dots.items():
            on = b["auto"][key]
            c.itemconfig(dot, fill=BLUE if on else WHITE)
            if on and not self.prev_auto[key] and animate:
                self._pop_dot(dot, y)
                self.toast("%s unlocked!" % ("Family Pack" if key == "family" else "Big Group"), BLUE)
        self.prev_auto = b["auto"]
        if animate:
            self.anim.tween(self.total_shown, b["total"], 700, self._set_total, ease_out_expo, key="total")
        self.restack()

    def _slide_in(self, tag, i):
        g = Group(self.c, tag)
        g.set_offset(40, 0)
        self.anim.tween(40, 0, 450, lambda v: g.set_offset(v, 0), ease_out_back, delay=i * 40, key=("slide", tag))

    def _pop_dot(self, dot, y):
        def setter(v):
            r = 11 * v
            ox, oy = self.disc_sec.ox(), self.disc_sec.oy()
            self.c.coords(dot, 487 - r + ox, y - r + oy, 487 + r + ox, y + r + oy)
        self.anim.tween(0.3, 1, 700, setter, ease_out_elastic, key=("dot", dot))

    def _set_total(self, v):
        self.total_shown = v
        if self.page_name == "tickets":
            self.c.itemconfig(self.total_item, text="$%.2f" % v)

    def change(self, kind, d):
        n = self.counts[kind] + d
        card = self.cards[ORDER.index(kind)]
        if n < 0:
            card.minus.shake()
            return
        if n > MAX_PER_TYPE:
            card.plus.shake()
            self.toast("Whoa! Max %d %s per order" % (MAX_PER_TYPE, TYPES[kind]["name"].lower()), RED)
            return
        self.counts[kind] = n
        card.set_count(n)
        if d > 0:
            px, py = card.plus.pos()
            self.confetti(px, py, 10, 0.35)
        self.update_summary()
        self.update_badge()

    def clear_cart(self):
        self.counts = {k: 0 for k in ORDER}
        self.fastpass, self.chip, self.promo = False, None, None
        self.prev_auto = {"family": False, "group": False}
        self.update_badge()

    def reset(self):
        for k, card in zip(ORDER, self.cards):
            if self.counts[k]:
                self.counts[k] = 0
                card.set_count(0)
        if self.chip:
            self.toggle_chip(self.chip)
        self.promo = None
        self.promo_field.set("")
        self.say("Discounts never stack - we pick your best deal!", GREY)
        if self.fastpass:
            self.set_fastpass(False)
        self.update_summary()
        self.update_badge()
        self.toast("All cleared - let's start fresh!", BLUE)

    def cart_problem(self):
        if sum(self.counts.values()) == 0:
            return "Pick at least one ticket first!"
        if self.counts["adult"] + self.counts["senior"] == 0:
            return "Little ones need a grown-up ticket too!"
        return None

    def to_checkout(self):
        problem = self.cart_problem()
        if problem:
            self.buy_btn.shake()
            self.toast(problem, RED)
            return
        self.navigate("checkout")

    # ===================================================================== #
    #  CHECKOUT
    # ===================================================================== #
    def page_checkout(self):
        h = 980
        self.page_bg(h)
        c = self.c
        self.page_header("Checkout", "Almost there! Tell us who's coming.", step=2)
        problem = self.cart_problem()
        if problem:
            self.section()
            self.panel(250, 140, 850, 470, r=34)
            rrect(c, 480, 180, 620, 250, 14, fill=LBLUE, outline=BLUE, width=3, dash=(6, 4), tags=self.T())
            star(c, 550, 215, 22, fill=WHITE, outline=BLUE, width=2, tags=self.T())
            self.text(550, 300, "Your cart needs a little love", 26, NAVY, "center")
            self.text(550, 340, problem, 17, GREY, "center", "normal")
            PopButton(self, 550, 410, 240, 58, "Choose tickets", lambda: self.navigate("tickets"), size=21)
            return self.footer(560)

        # form
        self.section()
        self.panel(30, 120, 690, 720, r=30)
        self.text(56, 152, "Your details", 22, BLUE)
        f = self.form
        self.fields = {}
        self.errors = {}

        def field(key, label, x1, w, ly, **kw):
            self.text(x1, ly, label, 15, NAVY)
            fld = Field(self, x1, ly + 38, w, 44, value=f.get(key, ""), **kw)
            self.fields[key] = fld
            self.errors[key] = self.text(x1 + 2, ly + 70, "", 12, RED, weight="normal")
            return fld
        field("name", "Full name", 56, 608, 188, placeholder="e.g. Sam Rivera")
        field("email", "Email", 56, 300, 278, placeholder="you@example.com")
        field("phone", "Phone", 376, 288, 278, placeholder="+1 555 123 4567")
        self.text(56, 372, "Payment", 22, BLUE)
        rrect(c, 170, 359, 470, 385, 13, fill=LBLUE, outline="", tags=self.T())
        self.text(320, 372, "DEMO - no real payment is taken", 12, GREY, "center")
        field("card", "Card number", 56, 608, 408, placeholder="1234 5678 9012 3456")
        self.text(664, 408, "Test card: 4242 4242 4242 4242", 12, GREY, "e", "normal", "italic")
        field("expiry", "Expiry (MM/YY)", 56, 190, 498, placeholder="MM/YY")
        field("cvv", "CVV", 270, 140, 498, show="•")
        self.fields["card"].entry.bind("<KeyRelease>", lambda e: self._fmt_card())
        self.fields["expiry"].entry.bind("<KeyRelease>", lambda e: self._fmt_expiry())
        self.fields["cvv"].entry.bind("<KeyRelease>", lambda e: self._fmt_digits("cvv", 4))
        self.checks = {}
        self.checkbox("agree", 56, 600, "I agree to the park rules (be kind, keep arms inside the ride!)")
        self.checkbox("news", 56, 646, "Send me fun news and secret deals (optional)")
        self.errors["agree"] = self.text(92, 624, "", 12, RED, weight="normal")

        # order summary
        self.section()
        b = self.compute()
        x1, x2 = 722, 1075
        self.panel(x1, 120, x2, 740, r=28)
        rrect(c, x1 + 10, 130, x2 - 10, 184, 20, fill=RED, outline=NAVY, width=3, tags=self.T())
        self.text((x1 + x2) / 2, 157, "ORDER SUMMARY", 24, WHITE, "center")
        self.text(748, 212, "Visit: " + self.visit_date().strftime("%a, %d %b %Y"), 16, BLUE)
        self.text(748, 238, "Pass: " + ("Fast Pass" if self.fastpass else "Standard Day Pass"), 16, BLUE)
        y = 280
        for key, left, right, col in self.bill_rows(b):
            self.text(748, y, left, 17, col)
            self.text(1049, y, right, 17, col, "e")
            y += 32
        c.create_line(748, 448, 1049, 448, fill=LBLUE, width=2, tags=self.T())
        self.text(748, 472, "Subtotal", 16, GREY)
        self.text(1049, 472, "$%.2f" % (b["sub"] + b["fast"]), 16, GREY, "e")
        if b["best"]:
            self.text(748, 502, "%s (-%d%%)" % (b["best"][1], round(b["best"][0] * 100)), 16, BLUE)
            self.text(1049, 502, "-$%.2f" % b["disc"], 16, BLUE, "e")
        c.create_line(748, 530, 1049, 530, fill=BLUE, width=3, dash=(8, 6), tags=self.T())
        self.text(748, 566, "TOTAL", 22, NAVY)
        self.text(1049, 604, "$%.2f" % b["total"], 40, RED, "e")
        self.pay_btn = PopButton(self, (x1 + x2) / 2, 668, 300, 62, "PAY $%.2f" % b["total"], self.pay,
                                 fill=RED, size=24)
        self.link_text((x1 + x2) / 2, 718, "Edit tickets", lambda: self.navigate("tickets"), color=BLUE,
                       hover=RED, size=15, anchor="center")
        self.page_leave.append(self._save_form)
        return self.footer(790)

    def checkbox(self, key, x, y, label):
        c, t = self.c, self.T()
        box = rrect(c, x, y - 14, x + 28, y + 14, 8, fill=WHITE, outline=BLUE, width=3, tags=t)
        tick = c.create_line(x + 6, y, x + 6, y, fill=RED, width=5, capstyle="round", joinstyle="round", tags=t)
        item = self.text(x + 40, y, label, 15, NAVY, weight="normal")
        on = bool(self.form.get(key))
        self.checks[key] = on
        sec = self.sec
        path = [(6, 0), (12, 8), (23, -8)]

        def draw(v):  # draw the tick progressively, like an SVG stroke animation
            ox, oy = sec.ox(), sec.oy()
            pts = [x + path[0][0] + ox, y + path[0][1] + oy]
            seg = v * 2
            for i in range(2):
                f = max(0.0, min(1.0, seg - i))
                if f <= 0:
                    break
                (ax, ay), (bx, by) = path[i], path[i + 1]
                pts += [x + ax + (bx - ax) * f + ox, y + ay + (by - ay) * f + oy]
            if len(pts) == 2:
                pts += pts
            c.coords(tick, *pts)
            c.itemconfig(tick, state="normal" if v > 0 else "hidden")
        if on:
            draw(1)

        def toggle():
            now = not self.checks[key]
            self.checks[key] = now
            c.itemconfig(box, outline=BLUE)
            if key in self.errors:
                c.itemconfig(self.errors[key], text="")
            self.anim.tween(0, 1, 320, draw, ease_out_cubic, key=("tick", key)) if now else draw(0)
        x2 = c.bbox(item)[2]
        Hotspot(self, x - 4, y - 18, x2 + 4, y + 18, toggle)
        self.check_boxes = getattr(self, "check_boxes", {})
        self.check_boxes[key] = box

    def _fmt_card(self):
        e = self.fields["card"].entry
        digits = re.sub(r"\D", "", e.get())[:16]
        nice = " ".join(digits[i:i + 4] for i in range(0, len(digits), 4))
        if nice != e.get():
            e.delete(0, "end")
            e.insert(0, nice)

    def _fmt_expiry(self):
        e = self.fields["expiry"].entry
        d = re.sub(r"\D", "", e.get())[:4]
        nice = d[:2] + "/" + d[2:] if len(d) > 2 else d
        if nice != e.get():
            e.delete(0, "end")
            e.insert(0, nice)

    def _fmt_digits(self, key, n):
        e = self.fields[key].entry
        d = re.sub(r"\D", "", e.get())[:n]
        if d != e.get():
            e.delete(0, "end")
            e.insert(0, d)

    def _save_form(self):
        for k, fld in self.fields.items():
            if k != "cvv":
                self.form[k] = fld.get()
        self.form["agree"] = self.checks.get("agree")
        self.form["news"] = self.checks.get("news")

    def validate(self):
        v = {k: fld.get() for k, fld in self.fields.items()}
        err = {}
        if len(v["name"]) < 2 or not re.search(r"[A-Za-z]", v["name"]):
            err["name"] = "Please enter your name."
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v["email"]):
            err["email"] = "That email doesn't look right."
        if not 7 <= len(re.sub(r"\D", "", v["phone"])) <= 15:
            err["phone"] = "Use 7-15 digits."
        card = re.sub(r"\D", "", v["card"])
        if len(card) != 16 or not luhn_ok(card):
            err["card"] = "Card number isn't valid (try the test card)."
        m = re.match(r"^(\d{2})/(\d{2})$", v["expiry"])
        today = datetime.date.today()
        if not m or not 1 <= int(m.group(1)) <= 12:
            err["expiry"] = "Use MM/YY."
        elif (2000 + int(m.group(2)), int(m.group(1))) < (today.year, today.month):
            err["expiry"] = "This card has expired."
        if not re.match(r"^\d{3,4}$", v["cvv"]):
            err["cvv"] = "3 or 4 digits."
        if not self.checks.get("agree"):
            err["agree"] = "Please accept the park rules."
        return v, err

    def pay(self):
        v, err = self.validate()
        for k in self.fields:
            self.fields[k].set_error(k in err)
            self.c.itemconfig(self.errors[k], text=err.get(k, ""))
        self.c.itemconfig(self.errors["agree"], text=err.get("agree", ""))
        self.c.itemconfig(self.check_boxes["agree"], outline=RED if "agree" in err else BLUE)
        if err:
            for k in self.fields:
                if k in err:
                    self.fields[k].shake()
            first = next((k for k in ["name", "email", "phone", "card", "expiry", "cvv"] if k in err), None)
            if first:
                self.fields[first].entry.focus_set()
            self.pay_btn.shake()
            self.toast("Please fix the %d highlighted field%s" % (len(err), "s" if len(err) > 1 else ""), RED)
            return
        self._save_form()
        self.processing(v)

    def processing(self, v):
        self.layer = "modal"
        self.set_hover(None)
        self.root.focus_set()
        self._update_fixed()
        c = self.c
        c.delete("toast")
        for win in self.page_windows:
            c.itemconfig(win, state="hidden")  # Tk widgets always draw above canvas items
        top, vh = c.canvasy(0), self.view_h
        t = (self.page_tag, "modal")
        c.create_rectangle(0, top, W, top + vh, fill=NAVY, stipple="gray50", outline="", tags=t)
        cy = top + vh / 2
        rrect(c, 406, cy - 104, 706, cy + 106, 30, fill=NAVY, outline="", tags=t)
        rrect(c, 400, cy - 110, 700, cy + 100, 30, fill=WHITE, outline=BLUE, width=4, tags=t)
        c.create_oval(520, cy - 80, 580, cy - 20, outline=LBLUE, width=8, tags=t)
        arc = c.create_arc(520, cy - 80, 580, cy - 20, start=0, extent=100, style="arc", outline=RED, width=8, tags=t)
        self.text(550, cy + 20, "Processing payment...", 20, NAVY, "center", tags=t)
        msg = self.text(550, cy + 54, "Counting the cotton candy", 14, GREY, "center", "normal", tags=t)
        self.restack()
        self.page_tickers.append(lambda now, dt: c.itemconfig(arc, start=-(now * 400) % 360,
                                                              extent=60 + 80 * (1 + math.sin(now * 5))))
        self.root.after(900, lambda: c.itemconfig(msg, text="Polishing your tickets"))
        self.root.after(1900, lambda: self.finish_order(v))

    def finish_order(self, v):
        b = self.compute()
        order = dict(bill=b, counts=dict(self.counts), fastpass=self.fastpass, date=self.visit_date(),
                     name=v["name"], email=v["email"],
                     tid="FL-%04d-%04d" % (random.randint(0, 9999), random.randint(0, 9999)))
        self.orders.insert(0, order)
        self.clear_cart()
        self.form["card"] = ""
        self.form["expiry"] = ""
        self.just_paid = True
        self.layer = "main"
        self.navigate("mytickets")

    # ===================================================================== #
    #  MY TICKETS
    # ===================================================================== #
    def page_mytickets(self):
        just, self.just_paid = self.just_paid, False
        n = len(self.orders)
        y = 130 + (110 if just else 0)
        h = max(760, y + n * 370 + 120 + 200)
        self.page_bg(h)
        c = self.c
        self.page_header("My Tickets", "Show these at the gate - no printing needed.", step=3 if just else None)
        if not n:
            self.section()
            self.panel(250, 140, 850, 470, r=34)
            rrect(c, 480, 180, 620, 250, 14, fill=LBLUE, outline=BLUE, width=3, dash=(6, 4), tags=self.T())
            star(c, 550, 215, 22, fill=WHITE, outline=BLUE, width=2, tags=self.T())
            self.text(550, 300, "No tickets yet!", 28, NAVY, "center")
            self.text(550, 340, "Your booked tickets will show up right here.", 17, GREY, "center", "normal")
            PopButton(self, 550, 410, 220, 58, "Get tickets", lambda: self.navigate("tickets"), size=21)
            return self.footer(560)
        if just:
            sec = self.section()
            self.panel(30, 120, 1070, 214, r=30, fill=BLUE, outline=NAVY)
            first = self.orders[0]["name"].split()[0]
            self.text(132, 152, "Hooray, %s! Your order is confirmed." % first, 26, WHITE)
            self.text(134, 188, "We sent a copy to %s (demo - nothing is really emailed)." % self.orders[0]["email"],
                      15, "#D6E8FF", weight="normal")
            circ = c.create_oval(82, 167, 82, 167, fill=WHITE, outline=NAVY, width=3, tags=self.T())
            chk = c.create_line(0, 0, 0, 0, fill=RED, width=6, capstyle="round", joinstyle="round", tags=self.T())

            def pop(v):
                ox, oy = sec.ox(), sec.oy()
                r = 30 * v
                c.coords(circ, 82 - r + ox, 167 - r + oy, 82 + r + ox, 167 + r + oy)
                c.coords(chk, 68 + ox, 168 + oy, 79 + ox, 180 + oy, 97 + ox, 154 + oy)
            pop(0.01)
            self.anim.tween(0.01, 1, 900, pop, ease_out_elastic, delay=500)
        for i, o in enumerate(self.orders):
            self.section()
            self.draw_ticket(o, 160, y + i * 370, stamp_anim=(i == 0 and just))
        self.section()
        PopButton(self, 550, y + n * 370 + 20, 260, 58, "Book more fun", lambda: self.navigate("tickets"), size=21)
        if just:
            self.root.after(900, lambda: (self.confetti(220, self.c.canvasy(0) + self.view_h, 90, 1.1),
                                          self.confetti(W - 220, self.c.canvasy(0) + self.view_h, 90, 1.1)))
            self.root.after(700, lambda: self.toast("Tickets booked! Have a magical day!", BLUE))
        return self.footer(y + n * 370 + 100)

    def draw_ticket(self, o, x1, y1, stamp_anim=False):
        c, t, sec = self.c, self.T(), self.sec
        b = o["bill"]
        X = lambda v: v + x1 - 160
        Y = lambda v: v + y1 - 170
        rrect(c, X(169), Y(180), X(949), Y(510), 28, fill="#0A1F4D", outline="", tags=t)
        rrect(c, X(160), Y(170), X(940), Y(500), 28, fill=WHITE, outline=NAVY, width=4, tags=t)
        rrect(c, X(172), Y(182), X(338), Y(488), 20, fill=RED, outline=NAVY, width=3, tags=t)
        self.text(X(206), Y(335), "ADMIT", 40, WHITE, "center", angle=90)
        self.text(X(282), Y(320), str(b["guests"]), 64, WHITE, "center")
        self.text(X(282), Y(372), "GUEST" + ("S" if b["guests"] != 1 else ""), 16, WHITE, "center")
        c.create_line(X(356), Y(192), X(356), Y(478), fill=NAVY, width=3, dash=(4, 7), tags=t)
        for ny in (170, 500):
            c.create_oval(X(340), Y(ny - 16), X(372), Y(ny + 16), fill=sky_at(Y(ny)), outline=NAVY, width=3, tags=t)
        title = self.text(X(380), Y(212), "FUNLAND PARK", 40, RED)
        star(c, c.bbox(title)[2] + 18, Y(210), 13, fill=BLUE, outline=NAVY, width=2, tags=t)
        self.text(X(382), Y(248), "ONE MAGICAL DAY OF RIDES, SNACKS & GIGGLES", 14, BLUE)
        who = " - ".join("%d %s" % (o["counts"][k], TYPES[k]["one" if o["counts"][k] == 1 else "name"])
                         for k in ORDER if o["counts"][k])
        deal = "%s (-%d%%)" % (b["best"][1], round(b["best"][0] * 100)) if b["best"] else "None"
        lines = ["Guests: " + who, "Pass: " + ("FAST PASS (skip the lines!)" if o["fastpass"] else "Standard Day Pass"),
                 "Date: " + o["date"].strftime("%a, %d %b %Y"), "Deal: " + deal]
        for i, s in enumerate(lines):
            self.text(X(382), Y(286 + i * 27), s, 16, NAVY, weight="normal")
        self.text(X(382), Y(410), "TOTAL PAID", 15, BLUE)
        self.text(X(380), Y(444), "$%.2f" % b["total"], 38, RED)
        self.text(X(382), Y(482), "Ticket #%s  -  %s" % (o["tid"], o["name"]), 13, GREY)
        bx = X(760)
        rng = random.Random(o["tid"])
        while bx < X(912):
            w = rng.choice([2, 2, 3, 4, 6])
            c.create_rectangle(bx, Y(330), bx + w, Y(450), fill=NAVY, outline="", tags=t)
            bx += w + rng.choice([2, 3, 4])
        self.text(X(836), Y(466), o["tid"].replace("-", " "), 12, NAVY, "center", "normal")
        oval = c.create_oval(0, 0, 0, 0, outline=RED, width=5, tags=t)
        txt = self.text(0, 0, "PAID!", 10, RED, "center", angle=18)
        cx, cy = X(836), Y(260)

        def stamp(v):
            r = 46 * v
            ox, oy = sec.ox(), sec.oy()
            c.coords(oval, cx - r + ox, cy - r * 0.62 + oy, cx + r + ox, cy + r * 0.62 + oy)
            c.coords(txt, cx + ox, cy + oy)
            c.itemconfig(txt, font=self.font(max(6, int(26 * v))))
        if stamp_anim:
            stamp(0.01)
            self.anim.tween(3.0, 1.0, 450, stamp, ease_out_bounce, delay=1100)
        else:
            stamp(1)

    # ===================================================================== #
    #  PARK INFO
    # ===================================================================== #
    def page_info(self):
        self.info_base_h = 1470
        self.page_bg(self.info_base_h + 6 * 70)
        c = self.c
        self.page_header("Park Info", "Hours, directions and answers to all the big questions.")
        # hours
        self.section()
        self.panel(30, 120, 530, 420, r=30)
        self.text(56, 152, "Opening Hours", 22, BLUE)
        wd = datetime.date.today().weekday()
        for i, (day, hrs) in enumerate(HOURS):
            y = 196 + i * 31
            if i == wd:
                rrect(c, 46, y - 14, 514, y + 14, 14, fill=LBLUE, outline="", tags=self.T())
                rrect(c, 180, y - 10, 246, y + 10, 10, fill=RED, outline="", tags=self.T())
                self.text(213, y, "TODAY", 11, WHITE, "center")
            self.text(62, y, day, 16, NAVY, weight="bold" if i == wd else "normal")
            self.text(498, y, hrs, 16, NAVY, "e", weight="bold" if i == wd else "normal")
        # getting here
        self.panel(570, 120, 1070, 420, r=30)
        self.text(596, 152, "Getting Here", 22, BLUE)
        for i, (title, detail) in enumerate([("Address", "1 Rollercoaster Road, Joyville"),
                                             ("By bus", "Line 7 stops right at the Main Gate"),
                                             ("Parking", "$8 per day - 2,000 spaces"),
                                             ("Accessibility", "Step-free paths & free wheelchair loan")]):
            y = 204 + i * 54
            col = RED if i % 2 == 0 else BLUE
            c.create_oval(598 - 17, y - 17, 598 + 17, y + 17, fill=col, outline=NAVY, width=3, tags=self.T())
            self.text(598, y, str(i + 1), 15, WHITE, "center")
            self.text(628, y - 10, title, 16, NAVY)
            self.text(628, y + 12, detail, 14, GREY, weight="normal")
        # FAQ accordion
        faq_sec = self.section()
        self.shadow_title(42, 476, "Frequently Asked Questions", 32)
        self.faq = []
        for i, (q, a) in enumerate(FAQ):
            y = 512 + i * 78
            g = Group(c, "%s_faq%d" % (self.page_tag, i), parent=faq_sec)
            t = self.T(group=g)
            shadow = c.create_polygon(rrect_pts(36, y + 5, 1076, y + 69, 22), smooth=True, fill=NAVY, tags=t)
            body = c.create_polygon(rrect_pts(30, y, 1070, y + 64, 22), smooth=True, fill=WHITE, outline=BLUE,
                                    width=3, tags=t)
            self.text(60, y + 32, q, 18, NAVY, tags=t)
            ans = self.text(60, y + 72, a, 15, GREY, "nw", "normal", tags=t, width=960, state="hidden")
            c.create_oval(1012, y + 14, 1048, y + 50, fill=RED, outline=NAVY, width=3, tags=t)
            l1 = c.create_line(0, 0, 0, 0, fill=WHITE, width=4, capstyle="round", tags=t)
            l2 = c.create_line(0, 0, 0, 0, fill=WHITE, width=4, capstyle="round", tags=t)
            item = dict(g=g, y=y, open=False, h=64.0, shadow=shadow, body=body, ans=ans, lines=(l1, l2), rot=0.0)
            self.faq.append(item)
            self._faq_draw(item)
            Hotspot(self, 30, y, 1070, y + 64, lambda it=item: self.toggle_faq(it), group=g)
        # contact form (lives in a group that slides down when answers open)
        self.below = self.section()
        y0 = 512 + len(FAQ) * 78 + 30
        self.panel(30, y0, 1070, y0 + 270, r=30)
        self.text(56, y0 + 34, "Still have questions? Drop us a line!", 22, BLUE)
        self.text(56, y0 + 74, "Your name", 15, NAVY)
        self.contact_name = Field(self, 56, y0 + 110, 340, 44, placeholder="Sam Rivera")
        self.text(56, y0 + 146, "Email", 15, NAVY)
        self.contact_email = Field(self, 56, y0 + 182, 340, 44, placeholder="you@example.com")
        self.text(430, y0 + 74, "Message", 15, NAVY)
        self.contact_msg = Field(self, 430, y0 + 146, 614, 116, multiline=True, size=16)
        self.text(430, y0 + 236, "Or call 555-FUN-LAND  -  hello@funland.example", 14, GREY, weight="normal")
        self.send_btn = PopButton(self, 960, y0 + 236, 160, 46, "Send", self.send_message, fill=RED, size=19)
        self.info_base_h = self.footer(y0 + 320, group=self.below)
        return self.info_base_h

    def _faq_draw(self, it):
        c, g, y = self.c, it["g"], it["y"]
        ox, oy = g.ox(), g.oy()
        c.coords(it["shadow"], *rrect_pts(36 + ox, y + 5 + oy, 1076 + ox, y + it["h"] + 5 + oy, 22))
        c.coords(it["body"], *rrect_pts(30 + ox, y + oy, 1070 + ox, y + it["h"] + oy, 22))
        cx, cy, r = 1030 + ox, y + 32 + oy, 9
        a = math.radians(it["rot"])
        for k, line in enumerate(it["lines"]):
            ang = a + k * math.pi / 2
            c.coords(line, cx - r * math.cos(ang), cy - r * math.sin(ang), cx + r * math.cos(ang), cy + r * math.sin(ang))

    def toggle_faq(self, it):
        it["open"] = not it["open"]
        extra = 70
        c = self.c
        if it["open"]:
            c.itemconfig(it["ans"], state="normal")
            self.anim.tween(24, 0, 450, lambda v: c.coords(it["ans"], 60 + v + it["g"].ox(), it["y"] + 72 + it["g"].oy()),
                            ease_out_cubic, key=("ans", it["ans"]))
        else:
            c.itemconfig(it["ans"], state="hidden")
        h0 = it["h"]

        def grow(v):
            it["h"] = v
            self._faq_draw(it)
        self.anim.tween(h0, 64 + (extra if it["open"] else 0), 450, grow, ease_out_back, key=("faqh", id(it)))
        r0 = it["rot"]

        def spin(v):
            it["rot"] = v
            self._faq_draw(it)
        self.anim.tween(r0, 45 if it["open"] else 0, 450, spin, ease_out_back, key=("faqr", id(it)))
        acc = 0
        for other in self.faq:
            g = other["g"]
            self.anim.tween(g.dy, acc, 450, lambda v, g=g: g.set_offset(0, v), ease_out_cubic, key=(g.tag, "faq"))
            acc += extra if other["open"] else 0
        self.anim.tween(self.below.dy, acc, 450, lambda v: self.below.set_offset(0, v), ease_out_cubic,
                        key=(self.below.tag, "faq"))
        self.page_h = self.info_base_h + acc
        self._set_region()
        self._update_fixed()

    def send_message(self):
        bad = []
        if not self.contact_name.get():
            bad.append(self.contact_name)
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", self.contact_email.get()):
            bad.append(self.contact_email)
        if len(self.contact_msg.get()) < 5:
            bad.append(self.contact_msg)
        for f in (self.contact_name, self.contact_email, self.contact_msg):
            f.set_error(f in bad)
        if bad:
            for f in bad:
                f.shake()
            self.send_btn.shake()
            self.toast("Please fill in your name, a valid email and a message", RED)
            return
        for f in (self.contact_name, self.contact_email, self.contact_msg):
            f.set("")
        bx, by = self.send_btn.pos()
        self.confetti(bx, by, 40, 0.7)
        self.toast("Thanks! We'll write back within one day.", BLUE)

    # ===================================================================== #
    #  Toasts & confetti
    # ===================================================================== #
    def toast(self, msg, color=BLUE):
        self.toast_token += 1
        token = self.toast_token
        c = self.c
        c.delete("toast")
        f = tkfont.Font(family=self.family, size=-18, weight="bold")
        w = f.measure(msg) + 64
        top = c.canvasy(0)
        self.toast_top = top
        x1, y1 = W / 2 - w / 2, top + self.view_h + 10
        rrect(c, x1 + 4, y1 + 5, x1 + w + 4, y1 + 53, 24, fill=NAVY, outline="", tags=("toast",))
        rrect(c, x1, y1, x1 + w, y1 + 48, 24, fill=color, outline=NAVY, width=3, tags=("toast",))
        star(c, x1 + 26, y1 + 24, 9, fill=WHITE, outline="", tags=("toast",))
        c.create_text(W / 2 + 10, y1 + 24, text=msg, fill=WHITE, font=self.font(18), tags=("toast",))
        g = Group(c, "toast")
        self.anim.tween(0, -80, 480, lambda v: g.set_offset(0, v), ease_out_back, key="toast")

        def hide():
            if token == self.toast_token:
                self.anim.tween(g.dy, 0, 360, lambda v: g.set_offset(0, v), ease_in_back, key="toast",
                                done=lambda: token == self.toast_token and c.delete("toast"))
        self.root.after(2500, hide)
        self.restack()

    def confetti(self, x, y, n=60, power=1.0):
        for _ in range(n):
            a = random.uniform(-math.pi * 0.92, -math.pi * 0.08)
            sp = random.uniform(260, 720) * power
            col = random.choice([RED, RED, BLUE, BLUE, WHITE, "#7FBFFF"])
            item = self.c.create_polygon(0, 0, 0, 0, 0, 0, 0, 0, fill=col,
                                         outline=NAVY if col == WHITE else "", tags=("confetti",))
            self.particles.append(dict(item=item, x=x, y=y, vx=math.cos(a) * sp, vy=math.sin(a) * sp,
                                       w=random.uniform(5, 9), h=random.uniform(3, 6), rot=random.uniform(0, 6.3),
                                       vr=random.uniform(-9, 9), flip=random.uniform(0, 6.3), life=0))
        self.restack()

    def tick_confetti(self, now, dt):
        if not self.particles:
            return
        bottom = self.c.canvasy(0) + self.view_h + 30
        alive = []
        for p in self.particles:
            p["vy"] += 900 * dt
            p["vx"] *= 0.985
            p["vy"] *= 0.985
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["rot"] += p["vr"] * dt
            p["flip"] += 8 * dt
            p["life"] += dt
            if p["y"] > bottom or p["life"] > 4:
                self.c.delete(p["item"])
                continue
            w = p["w"] * abs(math.cos(p["flip"])) + 1
            h = p["h"]
            ca, sa = math.cos(p["rot"]), math.sin(p["rot"])
            pts = []
            for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h)):
                pts += [p["x"] + dx * ca - dy * sa, p["y"] + dx * sa + dy * ca]
            self.c.coords(p["item"], *pts)
            alive.append(p)
        self.particles = alive


def main():
    root = tk.Tk()
    FunLandSite(root)
    root.mainloop()


if __name__ == "__main__":
    main()
