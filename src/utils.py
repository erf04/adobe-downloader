import re

def sorted_nicely(l):
    """Sorts filenames the way a human would (e.g., file_2, file_10)."""
    def convert(text):
        return int(text) if text.isdigit() else text.lower()
    def alphanum_key(key):
        return [convert(c) for c in re.split('([0-9]+)', str(key))]
    return sorted(l, key=alphanum_key)