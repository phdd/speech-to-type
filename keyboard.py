import time
from evdev import UInput, ecodes as e

# Hinweis: Dieses Modul setzt ein deutsches QWERTZ-Tastaturlayout voraus.
# Ggf. vorher aktivieren: setxkbmap de
# oder: setxkbmap de nodeadkeys  (verhindert Probleme mit Tottasten)

# DE-QWERTZ Mapping: Zeichen -> (keycode, shift_erforderlich)
# Basiert auf dem physischen Layout einer deutschen Tastatur.
CHAR_MAP = {
    # Kleinbuchstaben
    "a": (e.KEY_A, False),
    "b": (e.KEY_B, False),
    "c": (e.KEY_C, False),
    "d": (e.KEY_D, False),
    "e": (e.KEY_E, False),
    "f": (e.KEY_F, False),
    "g": (e.KEY_G, False),
    "h": (e.KEY_H, False),
    "i": (e.KEY_I, False),
    "j": (e.KEY_J, False),
    "k": (e.KEY_K, False),
    "l": (e.KEY_L, False),
    "m": (e.KEY_M, False),
    "n": (e.KEY_N, False),
    "o": (e.KEY_O, False),
    "p": (e.KEY_P, False),
    "q": (e.KEY_Q, False),
    "r": (e.KEY_R, False),
    "s": (e.KEY_S, False),
    "t": (e.KEY_T, False),
    "u": (e.KEY_U, False),
    "v": (e.KEY_V, False),
    "w": (e.KEY_W, False),
    "x": (e.KEY_X, False),
    "y": (e.KEY_Z, False),
    "z": (e.KEY_Y, False),
    # Großbuchstaben (Shift)
    "A": (e.KEY_A, True),
    "B": (e.KEY_B, True),
    "C": (e.KEY_C, True),
    "D": (e.KEY_D, True),
    "E": (e.KEY_E, True),
    "F": (e.KEY_F, True),
    "G": (e.KEY_G, True),
    "H": (e.KEY_H, True),
    "I": (e.KEY_I, True),
    "J": (e.KEY_J, True),
    "K": (e.KEY_K, True),
    "L": (e.KEY_L, True),
    "M": (e.KEY_M, True),
    "N": (e.KEY_N, True),
    "O": (e.KEY_O, True),
    "P": (e.KEY_P, True),
    "Q": (e.KEY_Q, True),
    "R": (e.KEY_R, True),
    "S": (e.KEY_S, True),
    "T": (e.KEY_T, True),
    "U": (e.KEY_U, True),
    "V": (e.KEY_V, True),
    "W": (e.KEY_W, True),
    "X": (e.KEY_X, True),
    "Y": (e.KEY_Z, True),
    "Z": (e.KEY_Y, True),
    # Ziffern
    "1": (e.KEY_1, False),
    "2": (e.KEY_2, False),
    "3": (e.KEY_3, False),
    "4": (e.KEY_4, False),
    "5": (e.KEY_5, False),
    "6": (e.KEY_6, False),
    "7": (e.KEY_7, False),
    "8": (e.KEY_8, False),
    "9": (e.KEY_9, False),
    "0": (e.KEY_0, False),
    # Sonderzeichen auf Zifferntasten mit Shift (DE-Layout)
    "!": (e.KEY_1, True),  # Shift+1
    '"': (e.KEY_2, True),  # Shift+2
    "§": (e.KEY_3, True),  # Shift+3
    "$": (e.KEY_4, True),  # Shift+4
    "%": (e.KEY_5, True),  # Shift+5
    "&": (e.KEY_6, True),  # Shift+6
    "/": (e.KEY_7, True),  # Shift+7
    "(": (e.KEY_8, True),  # Shift+8
    ")": (e.KEY_9, True),  # Shift+9
    "=": (e.KEY_0, True),  # Shift+0
    # Umlaute und ß (physische Tasten auf DE-Layout)
    "ä": (e.KEY_APOSTROPHE, False),  # physisch: Taste rechts von Ö
    "Ä": (e.KEY_APOSTROPHE, True),
    "ö": (e.KEY_SEMICOLON, False),  # physisch: Taste rechts von L
    "Ö": (e.KEY_SEMICOLON, True),
    "ü": (e.KEY_LEFTBRACE, False),  # physisch: Taste rechts von P
    "Ü": (e.KEY_LEFTBRACE, True),
    "ß": (e.KEY_MINUS, False),  # physisch: Taste rechts von 0
    # Satzzeichen
    " ": (e.KEY_SPACE, False),
    "\n": (e.KEY_ENTER, False),
    "\t": (e.KEY_TAB, False),
    ",": (e.KEY_COMMA, False),
    ";": (e.KEY_COMMA, True),  # Shift+,
    ".": (e.KEY_DOT, False),
    ":": (e.KEY_DOT, True),  # Shift+.
    "-": (e.KEY_SLASH, False),  # physisch: Taste rechts von .
    "_": (e.KEY_SLASH, True),  # Shift+-
    "#": (e.KEY_BACKSLASH, False),
    "'": (e.KEY_BACKSLASH, True),  # Shift+#
    "?": (e.KEY_MINUS, True),  # Shift+ß
    "+": (e.KEY_RIGHTBRACE, False),
    "*": (e.KEY_RIGHTBRACE, True),  # Shift++
}

# Alle genutzten Keycodes für UInput-Capabilities
ALL_KEYS = list(set(keycode for keycode, _ in CHAR_MAP.values())) + [
    e.KEY_LEFTSHIFT,
]


def key_press(ui: UInput, keycode: int, shift: bool = False) -> None:
    """Einzelne Taste drücken, optional mit Shift."""
    if shift:
        ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
    ui.write(e.EV_KEY, keycode, 1)
    ui.write(e.EV_KEY, keycode, 0)
    if shift:
        ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
    ui.syn()
    time.sleep(0.01)


def type_text(text: str) -> None:
    """Text tippen – unterstützt DE-QWERTZ inkl. Umlaute und Satzzeichen."""
    with UInput({e.EV_KEY: ALL_KEYS}, name="virtual-keyboard-de") as ui:  # type: ignore[arg-type]
        for char in text:
            if char in CHAR_MAP:
                keycode, shift = CHAR_MAP[char]
                key_press(ui, keycode, shift)
            else:
                print(f"Warnung: Zeichen '{char}' (U+{ord(char):04X}) nicht im Mapping")


if __name__ == "__main__":
    print("Teste in 3 Sekunden – wechsle jetzt in ein Textfeld!")
    time.sleep(3)

    with UInput({e.EV_KEY: ALL_KEYS}, name="virtual-keyboard-de") as ui:  # type: ignore[arg-type]
        # --- Test 1: Einzelne Taste ---
        print("Test 1: Drücke 'H'")
        key_press(ui, e.KEY_H, shift=True)

        # --- Test 2: Kleinbuchstaben ---
        print("Test 2: Tippe 'hallo welt'")
        for char in "hallo welt":
            keycode, shift = CHAR_MAP[char]
            key_press(ui, keycode, shift)
        key_press(ui, e.KEY_ENTER)

        # --- Test 3: Großbuchstaben ---
        print("Test 3: Tippe 'Hallo Welt'")
        for char in "Hallo Welt":
            keycode, shift = CHAR_MAP[char]
            key_press(ui, keycode, shift)
        key_press(ui, e.KEY_ENTER)

        # --- Test 4: Umlaute ---
        print("Test 4: Tippe Umlaute 'äöüÄÖÜß'")
        for char in "äöüÄÖÜß":
            keycode, shift = CHAR_MAP[char]
            key_press(ui, keycode, shift)
        key_press(ui, e.KEY_ENTER)

        # --- Test 5: Satzzeichen ---
        print("Test 5: Tippe Satzzeichen")
        for char in "Hallo, Welt! Wie geht's? Gut – danke.":
            if char in CHAR_MAP:
                keycode, shift = CHAR_MAP[char]
                key_press(ui, keycode, shift)
            else:
                print(f"Warnung: '{char}' nicht im Mapping")
        key_press(ui, e.KEY_ENTER)

        # --- Test 6: Gemischter Text mit Ziffern ---
        print("Test 6: Gemischter Text mit Ziffern")
        for char in "Am 3. März 2026 kostet das 42 Euro & 50 Cent (inkl. MwSt.).":
            if char in CHAR_MAP:
                keycode, shift = CHAR_MAP[char]
                key_press(ui, keycode, shift)
            else:
                print(f"Warnung: '{char}' nicht im Mapping")
        key_press(ui, e.KEY_ENTER)

        # --- Test 7: Langer Text mit Umlauten ---
        print("Test 7: Längerer Text (Lorem Ipsum DE)")
        lorem_de = (
            "Löräm ipsum dolor sit ämet, consectetur adipiscing elit. "
            "Über die Größe des Universums lässt sich trefflich streiten."
        )
        for char in lorem_de:
            if char in CHAR_MAP:
                keycode, shift = CHAR_MAP[char]
                key_press(ui, keycode, shift)
            else:
                print(f"Warnung: '{char}' nicht im Mapping")
        key_press(ui, e.KEY_ENTER)

    print("Fertig!")
