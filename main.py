"""Last Text at One Percent — entry program.

Writes one line (122 chars, gate 1-200) to
/output/entry.txt. Stdlib only, deterministic, no network, no reads.
"""
import os

TEXT = "1% left. I've decided to spend it texting you this instead of calling for help, because honestly, we've both made choices."
MAX_CHARS = 200


def validate(text):
    """Check one candidate line against the scorer's gate (RULES.txt).

    Returns the text unchanged when it passes, else raises ValueError
    naming the violated rule. Rules, in order:
      * str type, so a non-text value fails loudly instead of being coerced
      * encodable as UTF-8 (the gate reads the file as UTF-8 text)
      * 1 to MAX_CHARS characters
      * not whitespace-only
      * no leading or trailing whitespace (a single clean line)
      * single line (no newline or carriage return)
      * no control characters (U+0000-U+001F): a text message has no
        place for them, and a stray control byte would corrupt the
        entry the judge reads
    """
    if not isinstance(text, str):
        raise ValueError("entry text must be str")
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("entry text is not valid UTF-8") from exc
    if any(ord(ch) < 0x20 for ch in text):
        raise ValueError("entry text must not contain control characters")
    if not 1 <= len(text) <= MAX_CHARS:
        raise ValueError(
            f"entry text must be 1-{MAX_CHARS} chars, got {len(text)}"
        )
    if not text.strip():
        raise ValueError("entry text must not be whitespace-only")
    if text != text.strip():
        raise ValueError("entry text must not have leading/trailing whitespace")
    if "\n" in text or "\r" in text:
        raise ValueError("entry text must be a single line")
    return text


def write_entry(text):
    """Validate, then write text atomically to /output/entry.txt.

    Returns the path written. A crash mid-write must never leave a
    truncated entry.txt for the grader to read, so the bytes go to a
    temp file first (name carries the pid so two concurrent grader
    runs never overwrite each other's in-flight file) and are then
    moved into place with os.replace. The file is read back and must
    be byte-identical to the gated text, else we fail loudly instead
    of shipping a corrupt entry.
    """
    text = validate(text)
    out_dir = os.environ.get("OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    tmp_path = os.path.join(out_dir, f".entry.txt.tmp.{os.getpid()}")
    final_path = os.path.join(out_dir, "entry.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, final_path)
    with open(final_path, encoding="utf-8") as f:
        if f.read() != text:
            raise SystemExit("entry.txt read-back mismatch after atomic write")
    return final_path


def main():
    write_entry(TEXT)


if __name__ == "__main__":
    main()
