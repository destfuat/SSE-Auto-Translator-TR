"""
Copyright (c) Cutleast
"""

import unicodedata
from typing import override

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from PySide6.QtWidgets import QApplication

# Characters missing from Skyrim's standard Windows-1252 / Latin-1 font tables.
# Preserves characters already supported by standard fonts (e.g. ö, ü, ç, ä, é, ß).
_MINIMAL_CHAR_MAP: dict[str, str] = {
    # Turkish
    "ğ": "g",
    "Ğ": "G",
    "ş": "s",
    "Ş": "S",
    "ı": "i",
    "İ": "I",
    # Polish
    "ą": "a",
    "Ą": "A",
    "ę": "e",
    "Ę": "E",
    "ł": "l",
    "Ł": "L",
    "ś": "s",
    "Ś": "S",
    "ź": "z",
    "Ź": "Z",
    "ż": "z",
    "Ż": "Z",
    "ć": "c",
    "Ć": "C",
    "ń": "n",
    "Ń": "N",
    # Czech / Slovak
    "č": "c",
    "Č": "C",
    "ř": "r",
    "Ř": "R",
    "ě": "e",
    "Ě": "E",
    "ď": "d",
    "Ď": "D",
    "ť": "t",
    "Ť": "T",
    "ň": "n",
    "Ň": "N",
    "ů": "u",
    "Ů": "U",
    # Romanian
    "ă": "a",
    "Ă": "A",
    "ș": "s",
    "Ș": "S",
    "ț": "t",
    "Ț": "T",
}

_MINIMAL_TRANS_TABLE: dict[int, str] = str.maketrans(_MINIMAL_CHAR_MAP)

# Characters that do not decompose into base ASCII via Unicode NFKD.
_ASCII_SPECIAL_MAP: dict[str, str] = {
    "ı": "i",
    "ł": "l",
    "Ł": "L",
    "ø": "o",
    "Ø": "O",
    "đ": "d",
    "Đ": "D",
    "ß": "ss",
    "ẞ": "SS",
    "æ": "ae",
    "Æ": "AE",
    "œ": "oe",
    "Œ": "OE",
}

_ASCII_TRANS_TABLE: dict[int, str] = str.maketrans(_ASCII_SPECIAL_MAP)


class CharacterFallback(LocalizedEnum):
    """
    Enum for character fallback modes applied during translation export.
    """

    Disabled = "Disabled"
    """No character replacement is performed."""

    Minimal = "Minimal"
    """Replaces only characters missing from standard Skyrim fonts (e.g. ğ, ş, ı, İ)."""

    Ascii = "Ascii"
    """Converts all extended Latin characters to plain ASCII equivalents."""

    def apply(self, text: str) -> str:
        """
        Applies the character fallback transformation to the given text.

        Args:
            text (str): The input text to transform.

        Returns:
            str: The transformed text.
        """

        if not text:
            return text

        match self:
            case CharacterFallback.Disabled:
                return text
            case CharacterFallback.Minimal:
                return text.translate(_MINIMAL_TRANS_TABLE)
            case CharacterFallback.Ascii:
                mapped: str = text.translate(_ASCII_TRANS_TABLE)
                normalized: str = unicodedata.normalize("NFKD", mapped)
                return "".join(
                    ch for ch in normalized if unicodedata.category(ch) != "Mn"
                )

    @override
    def get_localized_name(self) -> str:
        match self:
            case CharacterFallback.Disabled:
                return QApplication.translate("CharacterFallback", "Disabled")
            case CharacterFallback.Minimal:
                return QApplication.translate(
                    "CharacterFallback", "Minimal (ğ/ş/ı/İ → g/s/i/I)"
                )
            case CharacterFallback.Ascii:
                return QApplication.translate("CharacterFallback", "Full ASCII")

    @override
    def get_localized_description(self) -> str:
        match self:
            case CharacterFallback.Disabled:
                return QApplication.translate(
                    "CharacterFallback",
                    "Keep all characters unchanged (requires a font that supports your language).",
                )
            case CharacterFallback.Minimal:
                return QApplication.translate(
                    "CharacterFallback",
                    "Replace only characters missing from standard Skyrim fonts during export (keeps ö, ü, ç, ä, é).",
                )
            case CharacterFallback.Ascii:
                return QApplication.translate(
                    "CharacterFallback",
                    "Convert all extended Latin characters to plain ASCII during export.",
                )
