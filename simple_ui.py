import locale
try:
    locale.setlocale(locale.LC_ALL, "")
except locale.Error:
    locale.setlocale(locale.LC_ALL, "C.UTF-8")

import curses
import requests

def fetch_customers():
    response = requests.get("https://kml.kiedyprzyjedzie.pl/api/customers")
    if response.status_code == 200:
        return response.json().get("customers", [])
    else:
        return []

def display_ui(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Please ensure your VPN or IP hider is active.")
    stdscr.addstr(1, 0, "Press ENTER to continue...")
    stdscr.refresh()

    # Wait for user to press Enter
    while True:
        key = stdscr.getch()
        if key == curses.KEY_ENTER or key in [10, 13]:
            break

    customers = fetch_customers()
    if not customers:
        stdscr.addstr(0, 0, "No customers found.")
        stdscr.refresh()
        stdscr.getch()
        return

    curses.curs_set(0)
    stdscr.clear()

    search_text = ""
    selected_idx = 0
    max_rows = 8

    while True:
        # Filter customers by search_text
        filtered = [c for c in customers if search_text.lower() in c['name'].lower()]
        total = len(filtered)
        if selected_idx >= total:
            selected_idx = max(0, total - 1)

        # Calculate visible window
        start = max(0, selected_idx - max_rows // 2)
        end = min(start + max_rows, total)
        start = max(0, end - max_rows)

        stdscr.clear()
        stdscr.addstr(0, 0, f"Search: {search_text}")
        for idx, customer in enumerate(filtered[start:end]):
            row = idx + 1
            name = customer['name']
            if start + idx == selected_idx:
                stdscr.addstr(row, 0, f"> {name}", curses.A_REVERSE)
            else:
                stdscr.addstr(row, 0, f"  {name}")
        if not filtered:
            stdscr.addstr(2, 0, "No matches.")

        stdscr.refresh()
        key = stdscr.get_wch() # get_wch supports wide chars

        if isinstance(key, str):
            if key in ('\b', '\x7f', '\x08'):
                search_text = search_text[:-1]
                selected_idx = 0
            elif key == '\n':
                if filtered:
                    return filtered[selected_idx]
            elif key.isprintable():
                search_text += key
                selected_idx = 0
        elif isinstance(key, int):
            if key == curses.KEY_UP and selected_idx > 0:
                selected_idx -= 1
            elif key == curses.KEY_DOWN and selected_idx < total - 1:
                selected_idx += 1
            elif key == curses.KEY_BACKSPACE or key == 127:
                search_text = search_text[:-1]
                selected_idx = 0