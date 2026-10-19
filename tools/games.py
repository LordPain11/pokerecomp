#!/usr/bin/env python3
"""Which supported game a ROM is, and the files this project keeps for each.

HeartGold and SoulSilver come from the same source and share almost all of their
code, but a few screens are compiled differently (title screen, credits, Pokedex,
intro, naming screen, Rock Smash item tables), so their ARM9 sections differ and
each game needs its own layout file and its own recompiled build. This module
holds what differs for the user: the cartridge's game code, the display name and
the layout, save and APK file names. It contains no game data: the game code is
in the ROM header, and a layout holds addresses and SHA-1s only.
"""
import hashlib
import os
from collections import namedtuple

# serial: the four bytes at 0x0C of the cartridge header ("game code").
# sha1: the whole retail ROM, as a convenience check. HeartGold and SoulSilver
# (USA) differ only in those bytes, the banner and game data, not in the header
# fields used here. A layout made from the game's decompilation build records
# the ROM it was made from, so a different dump still builds if its code matches.
Game = namedtuple('Game', 'key name serial layout save apk sha1')

GAMES = (
    Game('heartgold', 'HeartGold', 'IPKE', 'heartgold-us.json', 'heartgold.sav',
         'HeartGold-ssrecomp.apk', '4fcded0e2713dc03929845de631d0932ea2b5a37'),
    Game('soulsilver', 'SoulSilver', 'IPGE', 'soulsilver-us.json', 'soulsilver.sav',
         'SoulSilver-ssrecomp.apk', 'f8dc38ea20c17541a43b58c5e6d18c1732c7e582'),
)

BY_SERIAL = {game.serial: game for game in GAMES}
# Unreadable or unrecognised ROMs are built as SoulSilver, as the project always
# did; the recompiler checks every section against the layout afterwards and says
# so if the code is another game's.
SOULSILVER = BY_SERIAL['IPGE']

GAME_CODE_OFFSET = 0x0C


def rom_serial(path):
    """The four-letter game code from the cartridge header, or '' if it cannot be read."""
    try:
        with open(path, 'rb') as f:
            header = f.read(GAME_CODE_OFFSET + 4)
    except OSError:
        return ''
    return header[GAME_CODE_OFFSET:].decode('ascii', 'replace') if len(header) >= GAME_CODE_OFFSET + 4 else ''


def for_rom(path):
    """The game this ROM is, or None when the file cannot be read or is another game."""
    return BY_SERIAL.get(rom_serial(path))


def for_serial(serial):
    """The game with this cartridge game code, or None."""
    return BY_SERIAL.get(serial)


def rom_sha1(path):
    """SHA-1 of the whole file, read in blocks so a 128 MB ROM does not sit in memory twice."""
    digest = hashlib.sha1()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def layout_path(root, game):
    """The layout file for a game, inside a project folder."""
    return os.path.join(root, 'layouts', game.layout)
