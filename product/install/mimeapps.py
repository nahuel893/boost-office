# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Set and give back default applications in a mimeapps.list (XDG MIME Applications spec), for install.sh and
uninstall.sh. Only the [Default Applications] lines of the given types change; every other line stays as it is.
GLib merges repeated [Default Applications] sections and the last line of a type wins there, while xdg-mime reads
the first one: every line of a type, in every such section, is set and given back.

    mimeapps.py plan FILE     stdin "TYPE DESKTOP" lines; stdout "TYPE DESKTOP PREVIOUS" (the manifest's records)
    mimeapps.py set FILE      stdin "TYPE DESKTOP" lines: make DESKTOP the default for TYPE
    mimeapps.py restore FILE  stdin "TYPE DESKTOP PREVIOUS" lines: where TYPE still opens with DESKTOP, put
                              PREVIOUS back (or drop the line when it is empty); a file left without entries is
                              removed
"""
import os
import sys
import tempfile
from pathlib import Path

SECTION = "[Default Applications]"


def read(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as f:
        return f.read().splitlines(keepends=True)


def write(path, lines):
    path = Path(os.path.realpath(path))  # a mimeapps.list kept as a link (dotfiles) stays a link
    mode = path.stat().st_mode & 0o7777 if path.exists() else 0o644
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".mimeapps.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
            f.write("".join(lines))
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def is_header(line):
    return line.strip().startswith("[")


def key_of(line):
    text = line.strip()
    if not text or text.startswith("#") or is_header(line) or "=" not in text:
        return None
    return text.split("=", 1)[0].strip()


def value_of(line):
    return line.rstrip("\r\n").split("=", 1)[1]


def sections(lines):
    """(header index, end index) of every [Default Applications] section."""
    out = []
    for start, line in enumerate(lines):
        if line.strip() == SECTION:
            end = start + 1
            while end < len(lines) and not is_header(lines[end]):
                end += 1
            out.append((start, end))
    return out


def section(lines):
    """(header index, end index) of the first [Default Applications] section, or None."""
    found = sections(lines)
    return found[0] if found else None


def find_all(lines, mime):
    return [i for start, end in sections(lines) for i in range(start + 1, end) if key_of(lines[i]) == mime]


def entries(value):
    return [entry.strip() for entry in value.split(";") if entry.strip()]


def plan(lines, pairs):
    """For each pair, the value to give back at uninstall: today's default without DESKTOP itself."""
    out = []
    for mime, desktop in pairs:
        found = find_all(lines, mime)
        previous = value_of(lines[found[-1]]) if found else ""  # the line that wins in GLib
        if desktop in entries(previous):
            previous = ";".join(e for e in entries(previous) if e != desktop)
        out.append((mime, desktop, previous))
    return out


def set_defaults(lines, pairs):
    lines = list(lines)
    if section(lines) is None:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(SECTION + "\n")
    for mime, desktop in pairs:
        found = find_all(lines, mime)
        for i in found:
            lines[i] = f"{mime}={desktop}\n"
        if found:
            continue
        start, end = section(lines)
        at = end
        while at > start + 1 and not lines[at - 1].strip():
            at -= 1  # after the section's last entry, before the blank lines that part it from the next one
        if not lines[at - 1].endswith("\n"):
            lines[at - 1] += "\n"
        lines.insert(at, f"{mime}={desktop}\n")
    return lines


def restore(lines, records):
    lines = list(lines)
    for mime, desktop, previous in records:
        # a line gone, or set to another application since by the user, stays theirs
        for i in reversed(find_all(lines, mime)):
            if entries(value_of(lines[i])) != [desktop]:
                continue
            if previous:
                lines[i] = f"{mime}={previous}\n"
            else:
                del lines[i]
    bounds = section(lines)
    if bounds and not any(line.strip() for line in lines[bounds[0] + 1:bounds[1]]):
        del lines[bounds[0]]  # the header set_defaults added to a file that had none
    return lines


def main(argv):
    if len(argv) != 3 or argv[1] not in ("plan", "set", "restore"):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    command, path = argv[1], Path(argv[2])
    rows = [line.rstrip("\n").split(" ", 2) for line in sys.stdin if line.strip()]
    lines = read(path)
    if command == "plan":
        for mime, desktop, previous in plan(lines, [tuple(row[:2]) for row in rows]):
            print(f"{mime} {desktop} {previous}")
    elif command == "set":
        write(path, set_defaults(lines, [tuple(row[:2]) for row in rows]))
    elif path.exists():
        restored = restore(lines, [(row + [""])[:3] for row in rows])
        if not any(line.strip() for line in restored):
            path.unlink()
        elif restored != lines:
            write(path, restored)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
