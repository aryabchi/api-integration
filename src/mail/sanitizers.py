import re


def sanitize_filename(filename):
    """Removes illegal characters from filenames to prevent OS errors."""
    # Remove characters that are invalid in Windows/Linux filenames
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()
