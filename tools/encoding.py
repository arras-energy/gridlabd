"""Unicode encoding support"""

NONASCII = {
    "\xe1" : "a",
    "\xe9" : "e",
    "\xed" : "i",
    "\xc1" : "A",
    "\xcd" : "I",
    "\xd1" : "N",
    "\xd3" : "O",
    "\xdc" : "U",
    "\xf1" : "n",
    "\xf3" : "o",
    "\xfc" : "u",
    # may need to add others someday
}

def strict_ascii(text:str) -> str:
    """Convert non-ASCII codes to nearest ASCII equivalent"""
    return ''.join([NONASCII[x] if x in NONASCII else x for x in text])

