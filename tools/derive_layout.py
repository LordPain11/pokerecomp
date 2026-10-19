#!/usr/bin/env python3
"""Makes the layout of another game from one that is already known, using only
that game's ROM.

usage: derive_layout.py <existing layout> <ROM> <new layout>

HeartGold and SoulSilver come from the same source and are linked from the same
files in the same order, so their code sits at the same addresses even though a
few constants differ and one section ends with a little more data. That makes the
addresses in the SoulSilver layout valid for HeartGold too, and only the checksums
have to be taken from the new ROM.

This is the fallback for when the decompilation build is not at hand. The layout
made by tools/make_layout.py from a build is the authoritative one: it takes the
function boundaries and the watched addresses from that game's own symbols. Run
`ssrecomp <rom> --lockstep` after building with a derived layout; it compares every
recompiled instruction with the interpreter and stops at the first difference.

The file written holds addresses and SHA-1s only, no game code or data.
"""
import hashlib
import json
import os
import statistics
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import games
from ndsrom import read_rom
from recomp import autoload_image

# Function starts in compiled DS code are mostly `push {..., lr}` (Thumb 0xB5xx) or
# `push` (0xB4xx). If the code of a section had moved, the layout's range starts
# would land mid-instruction and this share would collapse.
PUSH = (0xB400, 0xB5FF)


def section_image(entry, main, overlays):
    source = entry['source']
    if source == 'main':
        return main
    if source == 'itcm':
        return autoload_image(main, entry['base'])
    if source not in overlays:
        raise SystemExit('this ROM has no overlay %s.' % source)
    return overlays[source][1]


def prologue_rate(entry, image):
    """The share of Thumb function starts that begin with a push, or None when the
    section has too few functions for the number to mean anything."""
    starts = good = 0
    for start, _end, thumb in entry['ranges']:
        if not thumb:
            continue
        offset = start - entry['base']
        if offset + 2 > len(image):
            continue
        starts += 1
        word = struct.unpack_from('<H', image, offset)[0]
        if PUSH[0] <= word <= PUSH[1] or word == 0x4770:
            good += 1
    return good / starts if starts >= 16 else None


def main():
    if len(sys.argv) != 4:
        raise SystemExit('usage: derive_layout.py <existing layout> <ROM> <new layout>')
    base_path, rom_path, out_path = sys.argv[1:4]
    base = json.load(open(base_path))
    serial = games.rom_serial(rom_path)
    game = games.for_serial(serial)
    if game is None:
        raise SystemExit('this ROM is not a game this project knows (game code %r); '
                         'make its layout with tools/make_layout.py from a build.' % serial)

    main_image, overlays = read_rom(rom_path)
    sections, checks, grown = [], [], []
    for entry in base['sections']:
        image = section_image(entry, main_image, overlays)
        if len(image) < entry['size']:
            raise SystemExit('section %s of this ROM is smaller than in %s (0x%X against 0x%X); '
                             'the code is laid out differently. Make this layout with '
                             'tools/make_layout.py instead.' % (entry['name'], base['game'],
                                                               len(image), entry['size']))
        if len(image) > entry['size']:
            grown.append((entry['name'], len(image) - entry['size']))
        rate = prologue_rate(entry, image)
        if rate is not None:
            checks.append((entry['name'], rate))
        sections.append({
            'name': entry['name'], 'base': entry['base'], 'source': entry['source'],
            'size': len(image), 'sha1': hashlib.sha1(image).hexdigest(),
            'ranges': entry['ranges'], 'named': entry['named'],
        })

    # A moved section would show up as almost no region starting with a push. Some
    # overlays split their code at literal pools, so this is a warning, not a refusal:
    # `--lockstep` on the built game is the real check.
    if checks:
        typical = statistics.median(rate for _name, rate in checks)
        for name, rate in checks:
            if rate < typical - 0.25:
                print('note: section %s has an unusual share of push prologues (%.0f%%, typical %.0f%%); '
                      'mapping symbols can split it at data. Check the build with --lockstep.'
                      % (name, 100 * rate, 100 * typical))

    layout = {
        'game': 'Pokemon %s (USA)' % game.name,
        'serial': serial,
        'save': game.save,
        'rom_sha1': games.rom_sha1(rom_path),
        'sections': sections,
        'apps': base['apps'],
        'focus': base['focus'],
    }
    with open(out_path, 'w') as f:
        json.dump(layout, f, separators=(',', ':'))
    for name, extra in grown:
        print('section %s: %d extra bytes after its code' % (name, extra))
    print('%s: %d sections from %s, function boundaries and watched addresses kept -> %s'
          % (layout['game'], len(sections), base['game'], out_path))


if __name__ == '__main__':
    main()
