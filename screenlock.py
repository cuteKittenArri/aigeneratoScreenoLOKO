#!/usr/bin/env python3
"""
screenlock.py - a personal privacy lock for your own X11 session.

Purpose: when you step away from a shared PC, cover your screen and stop
casual passers-by from poking at your session (Super, Alt+Tab, clicking
other windows). It unlocks with your password.

This is NOT a security boundary. Anyone with real know-how and physical
access can still get around it (switching virtual terminals with
Ctrl+Alt+F1..F7, an existing SSH session, or pulling the power). Blocking
those needs root, which you don't have -- and shouldn't need for this.
This deters tampering; it does not defeat a determined attacker.

--- How it works (and why the earlier version locked me out) ---
It uses Tkinter's OWN global grab, `grab_set_global()`, which performs a
real X11 active keyboard + pointer grab. Two facts make this correct:
  1. An active grab overrides the window manager's passive hotkey grabs,
     so Super / Alt+Tab / Ctrl+Alt+T come to THIS window and are ignored.
  2. The grab is owned by the SAME client (Tkinter) that reads the events,
     so your keystrokes actually reach the password box.
The earlier version grabbed on a separate python-xlib connection that
never read events, so every key was routed to a dead connection -> total
lockout. This version was verified with an injected synthetic keystroke.

--- SAFETY: test it first ---
Set a failsafe so it auto-unlocks after N seconds while you try it:
    SCREENLOCK_MAX_SECONDS=20 python3 screenlock.py
Once you trust it, run it normally (no failsafe):
    python3 screenlock.py

Requires: X11 session (not Wayland) and python3-tk. Pillow is optional
(only needed for JPG backgrounds; PNG works without it).
"""

import os
import sys
import time
import tkinter as tk

# ============================ CONFIGURATION ============================
# Unlock password. The SCREENLOCK_PASS env var overrides this, so you can
# keep the password out of the file:  SCREENLOCK_PASS=secret python3 ...
PASSWORD = os.environ.get("SCREENLOCK_PASS", "arri")

# Background image. PNG works out of the box; JPG needs Pillow (PIL).
# Relative paths resolve next to this script.
LOCK_IMAGE = "lock_bg.png"

# Failsafe: auto-unlock after this many seconds. 0 disables it.
# Overridable per-run with SCREENLOCK_MAX_SECONDS. USE IT WHILE TESTING.
MAX_SECONDS = int(os.environ.get("SCREENLOCK_MAX_SECONDS", "0") or "0")
# ======================================================================


class LockScreen:
    def __init__(self):
        self.buf = ""              # typed password (kept in memory only)
        self.grabbed = False

        self.root = tk.Tk()
        self.root.title("Screen Lock")
        self.root.configure(bg="black")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        # The WM must never be able to close it.
        self.root.protocol("WM_DELETE_WINDOW", lambda: "break")

        self._load_background()

        # No visible UI: just the picture. The password is typed blind.
        # Handle every key ourselves at the application level. Under the
        # global grab, all keys arrive here regardless of widget focus.
        self.root.bind_all("<Key>", self._on_key)

        # Grab must happen after the window is actually on screen.
        self.root.update_idletasks()
        try:
            self.root.wait_visibility(self.root)
        except tk.TclError:
            pass
        self._acquire_grab()

        if MAX_SECONDS > 0:
            self.root.after(MAX_SECONDS * 1000, self._failsafe)
        self._watchdog()

    # -------------------------------------------------------- background
    def _load_background(self):
        path = LOCK_IMAGE
        if not os.path.isabs(path):
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        try:
            try:
                from PIL import Image, ImageTk
                img = Image.open(path).resize((w, h), Image.LANCZOS)
                self._bg = ImageTk.PhotoImage(img)
            except ImportError:
                self._bg = tk.PhotoImage(file=path)      # PNG/GIF only
            tk.Label(self.root, image=self._bg, bd=0).place(
                x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"[info] no background image ({e}); using solid black.")

    # ------------------------------------------------------------- grab
    def _acquire_grab(self):
        """Try Tk's global grab, retrying briefly (it can fail transiently
        if a launch key is still held or the GNOME overview is open)."""
        for _ in range(40):
            try:
                self.root.grab_set_global()
                self.grabbed = True
                return
            except tk.TclError:
                self.grabbed = False
                try:
                    self.root.update()
                except tk.TclError:
                    pass
                time.sleep(0.05)
        print("[warn] could not acquire global grab; hotkeys may still work. "
              "You can still type the password to close this window.")

    def _watchdog(self):
        """Stay on top and re-assert the grab if we ever lose it."""
        try:
            if not self.root.grab_current():
                try:
                    self.root.grab_set_global()
                    self.grabbed = True
                except tk.TclError:
                    pass
            self.root.attributes("-topmost", True)
            self.root.lift()
        except Exception:
            pass
        self.root.after(1000, self._watchdog)

    # ------------------------------------------------------------ input
    def _on_key(self, e):
        ks = e.keysym
        if ks in ("Return", "KP_Enter"):
            if self.buf:
                self._check()
        elif ks == "BackSpace":
            self.buf = self.buf[:-1]
        elif len(e.char) == 1 and e.char.isprintable():
            self.buf += e.char
        # all other keys (modifiers, Super, Tab, F-keys, arrows) are ignored
        return "break"

    def _check(self):
        if self.buf == PASSWORD:
            self._unlock()
        else:
            self.buf = ""      # wrong: silently reset, keep the clean picture

    # ---------------------------------------------------------- teardown
    def _unlock(self):
        try:
            self.root.grab_release()
        except Exception:
            pass
        self.root.after(100, self.root.destroy)

    def _failsafe(self):
        print(f"[failsafe] auto-unlocking after {MAX_SECONDS}s.")
        self._unlock()

    def run(self):
        self.root.mainloop()


def main():
    if os.environ.get("WAYLAND_DISPLAY") and not os.environ.get("DISPLAY"):
        sys.exit("Error: Wayland session detected; keyboard grabs need X11.")
    if not os.environ.get("DISPLAY"):
        sys.exit("Error: no X11 DISPLAY found. This tool needs an X11 session.")
    try:
        LockScreen().run()
    except tk.TclError as e:
        sys.exit(f"Error creating the lock window: {e}\n"
                 "Is python3-tk installed and are you in a graphical session?")


if __name__ == "__main__":
    main()
