"""Character set definitions for the font generator."""


def get_uppercase():
    return [chr(c) for c in range(ord('A'), ord('Z') + 1)]


def get_lowercase():
    return [chr(c) for c in range(ord('a'), ord('z') + 1)]


def get_digits():
    return [chr(c) for c in range(ord('0'), ord('9') + 1)]


def get_punctuation():
    return list("!@#$%^&*()-_=+[]{};:'\",.<>/?\\|`~ ")


def get_chinese_chars():
    """Get GB2312 Level 1 Chinese characters (~3755 most common)."""
    chars = []
    for row in range(0xB0, 0xD7 + 1):
        for col in range(0xA1, 0xFE + 1):
            if row == 0xD7 and col > 0xF9:
                break
            try:
                c = bytes([row, col]).decode('gb2312')
                chars.append(c)
            except (UnicodeDecodeError, ValueError):
                pass
    return chars


def get_all_chars():
    """Return all characters organized by category."""
    return [
        ("Uppercase A-Z", get_uppercase()),
        ("Lowercase a-z", get_lowercase()),
        ("Digits 0-9", get_digits()),
        ("Punctuation", get_punctuation()),
        ("Chinese", get_chinese_chars()),
    ]


def get_flat_char_list():
    """Return a flat list of all characters."""
    result = []
    for _, chars in get_all_chars():
        result.extend(chars)
    return result
