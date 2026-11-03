# FunLand Park – Ticket Website (Tkinter)

A cartoony, website-style amusement park ticket front end built with **Python + Tkinter only**
(standard library, no `pip install` needed).

Pages: Home, Rides, Tickets (Adults / Children / Seniors / Toddlers, Fast Pass, discounts & promo codes),
Checkout (with form validation), My Tickets, Park Info.

![Home](screenshots/home.png)
![Tickets](screenshots/tickets.png)

## How to run it on any laptop

### 1. Install Python 3.8 or newer
- **Windows / macOS:** download from <https://www.python.org/downloads/> and install.
  On Windows, tick **"Add python.exe to PATH"** on the first installer screen.
  Tkinter is included automatically.
- **Linux (Ubuntu/Debian):** `sudo apt install python3 python3-tk`

Check it works:
```
python --version          (Windows)
python3 --version         (macOS / Linux)
```

### 2. Get the code
**Option A – download ZIP (easiest):** on this GitHub page click the green **Code** button →
**Download ZIP**, then unzip it.

**Option B – git:**
```
git clone https://github.com/SenCruCiAl/Funland-.git
cd Funland-
```

### 3. Run it
Open a terminal (Windows: *Command Prompt*; macOS: *Terminal*) inside the unzipped folder and run:
```
python funland_site.py        (Windows)
python3 funland_site.py       (macOS / Linux)
```
On Windows you can also just double-click `funland_site.py`.

## Try it out
- Promo codes: `FUN10`, `SUMMER25`, `FUNLAND30`
- Test card at checkout: `4242 4242 4242 4242`, any future expiry (e.g. `12/29`), any 3-digit CVV

## Notes
- Demo only: no real payment is taken and no email is sent. Orders are lost when the app closes.
- `ModuleNotFoundError: No module named 'tkinter'` → on Linux run `sudo apt install python3-tk`;
  on macOS reinstall Python from python.org (Homebrew Python may need `brew install python-tk`).
- On macOS the see-through overlay behind the payment spinner shows as solid dark blue (a Tk limitation).
