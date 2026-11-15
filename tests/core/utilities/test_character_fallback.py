"""
Copyright (c) Cutleast
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.config.user_config import UserConfig
from core.database.exporter import Exporter
from core.database.translation import Translation
from core.file_types.plugin.string import PluginString
from core.mod_file.mod_file import ModFile
from core.mod_instance.mod_instance import ModInstance
from core.string.string_status import StringStatus
from core.string.types import StringList
from core.utilities.character_fallback import CharacterFallback


class TestCharacterFallback:
    """
    Tests `core.utilities.character_fallback` and its integration with `UserConfig`
    and `Exporter`.
    """

    APPLY_DATA: list[tuple[CharacterFallback, str, str]] = [
        # Disabled leaves everything untouched
        (CharacterFallback.Disabled, "ğĞşŞıİ öÖüÜçÇ", "ğĞşŞıİ öÖüÜçÇ"),
        (CharacterFallback.Disabled, "", ""),
        # Minimal replaces only characters missing from standard Skyrim fonts
        (CharacterFallback.Minimal, "ğĞşŞıİ öÖüÜçÇ", "gGsSiI öÖüÜçÇ"),
        (CharacterFallback.Minimal, "Kılıç ve Kalkan", "Kiliç ve Kalkan"),
        (CharacterFallback.Minimal, "İğneada Şehir", "Igneada Sehir"),
        (CharacterFallback.Minimal, "Über Straße", "Über Straße"),
        (CharacterFallback.Minimal, "Zażółć gęślą jaźń", "Zazólc gesla jazn"),
        (CharacterFallback.Minimal, "Příliš žluťoučký kůň", "Príliš žlutoucký kun"),
        (CharacterFallback.Minimal, "Știință și Țară", "Stiinta si Tara"),
        # Ascii converts all extended Latin characters to plain ASCII
        (CharacterFallback.Ascii, "ğĞşŞıİ öÖüÜçÇ", "gGsSiI oOuUcC"),
        (CharacterFallback.Ascii, "Kılıç ve Kalkan", "Kilic ve Kalkan"),
        (CharacterFallback.Ascii, "Über Straße", "Uber Strasse"),
        (CharacterFallback.Ascii, "Ægir & Cœur, Øresund, Đorđe", "AEgir & Coeur, Oresund, Dorde"),
        # Placeholders and empty/plain strings are preserved
        (
            CharacterFallback.Minimal,
            "<Alias=Player> için [0x01] Şifa İksiri\n",
            "<Alias=Player> için [0x01] Sifa Iksiri\n",
        ),
        (
            CharacterFallback.Ascii,
            "<Alias=Player> için [0x01] Güç İksiri\n",
            "<Alias=Player> icin [0x01] Guc Iksiri\n",
        ),
        (CharacterFallback.Minimal, "", ""),
        (CharacterFallback.Ascii, "", ""),
        (CharacterFallback.Ascii, "Iron Sword", "Iron Sword"),
    ]

    @pytest.mark.parametrize("mode, text, expected", APPLY_DATA)
    def test_apply(self, mode: CharacterFallback, text: str, expected: str) -> None:
        """
        Tests `CharacterFallback.apply()`.
        """

        assert mode.apply(text) == expected

    def test_user_config_defaults_to_disabled(self) -> None:
        """
        Tests that `UserConfig.character_fallback` defaults to `Disabled`.
        """

        config: UserConfig = UserConfig.create()
        assert config.character_fallback == CharacterFallback.Disabled

    def test_exporter_applies_fallback_only_to_exported_copy(
        self, tmp_path: Path
    ) -> None:
        """
        Tests that `Exporter.export_translation` and `Exporter.build_output_mod`
        apply `CharacterFallback` to exported strings without mutating the database.
        """

        plugin_path = Path("TestMod.esp")
        translated = PluginString(
            form_id="00012EB7",
            type="WEAP FULL",
            original="Iron Sword",
            string="Demir Kılıç (Şifa)",
            status=StringStatus.TranslationComplete,
        )
        untranslated = PluginString(
            form_id="00012EB8",
            type="WEAP FULL",
            original="Steel Sword",
            string=None,
            status=StringStatus.NoneStatus,
        )
        translation = Translation(
            name="TestMod",
            path=tmp_path / "db" / "TestMod",
            strings_={plugin_path: [translated, untranslated]},
        )

        dumped_calls: list[StringList] = []
        mock_modfile = MagicMock(spec=ModFile)
        mock_modfile.dump_strings.side_effect = lambda strings, **_: dumped_calls.append(
            strings
        )

        mock_mod_instance = MagicMock(spec=ModInstance)
        mock_mod_instance.get_modfile.return_value = mock_modfile

        user_config: UserConfig = UserConfig.create()
        user_config.character_fallback = CharacterFallback.Minimal

        output_path: Path = tmp_path / "output"
        Exporter().build_output_mod(
            output_path=output_path,
            mod_instance=mock_mod_instance,
            translations=[translation],
            user_config=user_config,
        )

        assert len(dumped_calls) == 1
        exported_strings: StringList = dumped_calls[0]
        assert exported_strings[0].string == "Demir Kiliç (Sifa)"
        assert exported_strings[1].string is None

        # Original database string must remain unchanged
        assert translation.strings[plugin_path][0].string == "Demir Kılıç (Şifa)"
