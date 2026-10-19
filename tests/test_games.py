"""What the project knows about HeartGold versus SoulSilver, without a ROM.

Run: python3 -m unittest discover -s tests
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import games
import ssrecomp_setup as setup


def fake_rom(path, serial):
    """A cartridge header with this game code; the rest is not game content."""
    header = bytearray(0x200)
    header[0x0C:0x10] = serial.encode('ascii')
    Path(path).write_bytes(bytes(header))


class GameIdTests(unittest.TestCase):
    def test_serial_read_from_cartridge_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            hg, ss = Path(tmp) / 'hg.nds', Path(tmp) / 'ss.nds'
            fake_rom(hg, 'IPKE')
            fake_rom(ss, 'IPGE')
            self.assertEqual(games.rom_serial(hg), 'IPKE')
            self.assertEqual(games.for_rom(hg).name, 'HeartGold')
            self.assertEqual(games.for_rom(ss).name, 'SoulSilver')
            self.assertEqual(games.for_rom(hg).save, 'heartgold.sav')
            self.assertEqual(games.for_rom(hg).layout, 'heartgold-us.json')

    def test_unknown_and_missing_roms(self):
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / 'other.nds'
            fake_rom(other, 'IPKJ')       # Japanese HeartGold: not supported
            self.assertIsNone(games.for_rom(other))
            self.assertIsNone(games.for_rom(Path(tmp) / 'missing.nds'))
            self.assertEqual(games.rom_serial(Path(tmp) / 'missing.nds'), '')

    def test_setup_builds_unknown_roms_as_soulsilver(self):
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / 'other.nds'
            fake_rom(other, 'IPKJ')
            self.assertEqual(setup.game_for(other).name, 'SoulSilver')
            self.assertEqual(setup.game_for(Path(tmp) / 'missing.nds').name, 'SoulSilver')

    def test_layout_paths_are_per_game(self):
        self.assertEqual(Path(games.layout_path('root', games.for_serial('IPKE'))),
                         Path('root') / 'layouts' / 'heartgold-us.json')
        self.assertEqual(Path(games.layout_path('root', games.for_serial('IPGE'))),
                         Path('root') / 'layouts' / 'soulsilver-us.json')


class SetupRomTests(unittest.TestCase):
    def test_heartgold_without_its_layout_says_how_to_make_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = Path(tmp) / 'heartgold.nds'
            fake_rom(rom, 'IPKE')
            with patch.object(setup, 'layout_path', return_value=str(Path(tmp) / 'none.json')):
                game, problem = setup.check_rom(str(rom))
            self.assertEqual(game.name, 'HeartGold')
            self.assertIn('heartgold-us.json', problem)
            self.assertIn('build of that game', problem)

    def test_soulsilver_numbers_only_follow_the_expected_sha1(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = Path(tmp) / 'soulsilver.nds'
            fake_rom(rom, 'IPGE')
            with patch.object(setup, 'layout_path', return_value=str(Path(tmp) / 'none.json')):
                game, problem = setup.check_rom(str(rom))
            self.assertEqual(game.name, 'SoulSilver')
            self.assertIn('soulsilver-us.json', problem)

    def test_foreign_rom_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            rom = Path(tmp) / 'other.nds'
            fake_rom(rom, 'IPKJ')
            game, problem = setup.check_rom(str(rom))
            self.assertIsNone(game)
            self.assertIn('not Pokemon HeartGold or SoulSilver', problem)

    def test_play_uses_the_games_own_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / 'ssrecomp.rom'
            rom = Path(tmp) / 'heartgold.nds'
            fake_rom(rom, 'IPKE')
            note.write_text(str(rom) + '\n')
            launched = []

            def spawn(cmd, **kwargs):
                launched.append(cmd)
                kwargs['stdout'].write('')
            with patch.object(setup, 'HERE', tmp), patch.object(setup, 'ROM_NOTE', str(note)), \
                 patch.object(setup, 'EXE', str(Path(tmp) / 'ssrecomp')), \
                 patch.object(setup.subprocess, 'Popen', side_effect=spawn):
                setup.play()
            self.assertIn(os.path.join(tmp, 'heartgold.sav'), launched[0])


if __name__ == '__main__':
    unittest.main()
