import os
import re

BASE_PATH = os.path.dirname(__file__)


def try_decode_hex(s: str) -> str:
    """Try to decode a continuous hex string to text."""
    try:
        return bytes.fromhex(s).decode('utf-8', errors='replace')
    except Exception:
        return ''


def main():
    with open(os.path.join(BASE_PATH, "input.txt"), 'r') as f:
        data = f.read()

    data = data.strip()
    if not data:
        print('(no data in output.txt)')
        return

    # 1) Handle C-style \xHH escapes
    if '\\x' in data:
        try:
            decoded = bytes(data, 'utf-8').decode('unicode_escape')
            print('Decoded (\\x escapes):', repr(decoded))
            return
        except Exception:
            pass

    # 2) Find brace-enclosed hex groups like {73656374...}
    matches = re.findall(r"\{([0-9A-Fa-f]{4,})\}", data)
    if matches:
        for i, m in enumerate(matches, 1):
            dec = try_decode_hex(m)
            if dec:
                print(f'Decoded group {i}:', repr(dec))
            else:
                print(f'Group {i} looks like hex but could not decode.')
        return

    # 3) If the whole file is a continuous hex string
    # Accept both continuous hex and space-separated byte hex (e.g. '20 41 42')
    if re.fullmatch(r'[0-9A-Fa-f]+', data) or re.fullmatch(r'(?:[0-9A-Fa-f]{2}\s*)+', data):
        hex_clean = re.sub(r'\s+', '', data)
        dec = try_decode_hex(hex_clean)
        if dec:
            # print('Decoded (full hex):', repr(dec))
            with open(os.path.join(BASE_PATH,'output.txt'), 'w') as f:
                f.write(repr(dec))
            return

    # # 4) Fallback: show original content
    # print('Original data:')
    # print(data)


if __name__ == '__main__':
    main()

