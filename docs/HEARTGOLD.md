# HeartGold

The project builds **Pokémon HeartGold (US)** as well as SoulSilver, on the same
platforms and with the same single-screen view. Nothing of either game is in the
repository: `gen/` is recompiled from your own ROM on your own machine, and the
layout files hold addresses and checksums only.

## What is different from SoulSilver

HeartGold and SoulSilver come from one source and share almost all of their code,
so the merged single-screen layouts, widescreen renderer, 60 fps mode and controls
work unchanged. A few screens are compiled differently:

| File | Difference |
|---|---|
| `title_screen.c` | Ho-Oh instead of Lugia; different 3D object numbers |
| `credits.c` | which title message is shown |
| Pokédex (`ov18`) | flavour-text and hardware-data file numbers |
| intro movie | opening file numbers, one scroll direction |
| naming screen | default names |
| `rock_smash_item.c` | the Ruins of Alph item table |
| `intro_title` overlay | 32 bytes more data at the end (all of its code is before it) |

Because of these, each game needs its own `gen/` and its own layout. The frontend
itself only uses the game for the names the player sees.

## Files per game

| | SoulSilver | HeartGold |
|---|---|---|
| Cartridge game code | `IPGE` | `IPKE` |
| Layout | `layouts/soulsilver-us.json` | `layouts/heartgold-us.json` |
| Save | `soulsilver.sav` | `heartgold.sav` |
| Android APK | `SoulSilver-ssrecomp.apk` | `HeartGold-ssrecomp.apk` |

`ssrecomp.cfg` (settings) is shared. The setup program and `run.sh` read the game
code at offset `0x0C` of the ROM header and pick the row above; the game's window
title and pause menu say which game is running.

## Windows, from this repository

The released setup programs build SoulSilver. For HeartGold, build from source:

1. Install [MSYS2](https://www.msys2.org) in its default place (`C:\msys64`).
2. Open **MSYS2 UCRT64** and install the compiler, libraries and Python/Tk:

       pacman -S --needed mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-cmake \
           mingw-w64-ucrt-x86_64-ninja mingw-w64-ucrt-x86_64-SDL2 \
           mingw-w64-ucrt-x86_64-libpng mingw-w64-ucrt-x86_64-zlib \
           mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-tk

3. Go to the checkout and start the setup program:

       cd /c/Users/<you>/Documents/pokerecomp
       python ssrecomp_setup.py

4. Choose your HeartGold (US) `.nds`, press **Build**, wait 20–40 minutes, then
   press **Play**. Without the window:

       python ssrecomp_setup.py --rom "/c/Users/<you>/heartgold.nds" --jobs 8

   The ROM is checked against `layouts/heartgold-us.json`; the setup says
   `ROM: Pokemon HeartGold (US), correct.` when it matches.

5. To play without the setup window afterwards:

       ./run.sh --fullscreen

   `run.sh` records nothing itself; setup wrote `ssrecomp.rom`, and the save goes
   to `heartgold.sav` beside the scripts. Running `build/ssrecomp.exe` directly
   works too:

       build/ssrecomp.exe heartgold.nds --save heartgold.sav --fullscreen

## Linux and macOS

The same program, no extra steps for HeartGold:

    python3 ssrecomp_setup.py --rom /path/to/heartgold.nds
    ./run.sh --fullscreen

`./setup.sh --game heartgold` builds the game through the decompilation instead
(see "Layouts" below); it needs the decompilation's ARM toolchain.

## Android

Build the APK on the PC as usual, choosing the HeartGold ROM:

    python3 ssrecomp_setup.py --rom /path/to/heartgold.nds --android

or press **Build for Android** in the window. The result is
`HeartGold-ssrecomp.apk`, signed with the same key as the SoulSilver one, so it
installs beside it and keeps its own save. Building the APK needs only CMake and
Ninja; the first build downloads the Android NDK and SDL2.

## Layouts

`layouts/heartgold-us.json` is what lets the recompiler work from your ROM instead
of from a decompilation build. It contains, per code section, the load address,
where the bytes are in the ROM, a SHA-1 and which ranges are ARM or Thumb code,
plus the addresses of the functions the frontend watches. It contains no game
code or data.

The file in this repository was derived from the SoulSilver layout, because both
games are linked from the same files in the same order and every HeartGold section
has the same size as its SoulSilver counterpart; one overlay (`intro_title`) ends
with 32 extra bytes of data after all of its code. `tools/derive_layout.py`
rechecks that and recomputes the checksums:

    python3 tools/derive_layout.py layouts/soulsilver-us.json heartgold.nds \
        layouts/heartgold-us.json

The authoritative layout comes from a HeartGold build of the decompilation, which
has that game's own symbols:

    git clone https://github.com/pret/pokeheartgold.git
    make -C pokeheartgold heartgold        # needs its INSTALL.md requirements

    sha1sum pokeheartgold/build/heartgold.us/pokeheartgold.us.nds
    # 4fcded0e2713dc03929845de631d0932ea2b5a37

    python3 tools/make_layout.py \
        pokeheartgold/build/heartgold.us \
        pokeheartgold/build/heartgold.us/pokeheartgold.us.nds \
        layouts/heartgold-us.json

Commit only the resulting JSON (addresses and checksums), never the build
directory, the ROM or `gen/`.

## Verifying a build

The recompiled code must behave exactly like the interpreter. After building:

    build/ssrecomp <rom> --lockstep --frames 3000

It runs an interpreter and the recompiled console side by side and compares
registers, flags, cycles and timestamps after every ARM9 instruction; it stops at
the first difference and prints `PASS` when they agree. For the title screen and
intro this covers the code that differs most between the games.

For the merged picture, without a window:

    build/ssrecomp <rom> --headless --compose 1280x720 \
        --shot-dir shots --shot-at 600,1200

and for a snapshot from the overworld or a battle, use `--state-load` with
`--frames`. A longer check, including a save-state resume, is
`tests/validate_game.py <build/ssrecomp> <rom>`.

## Switching games

`gen/` and `build/` hold one game at a time. Building the other game replaces
`gen/` and recompiles everything (20–40 minutes); the saves
(`heartgold.sav`, `soulsilver.sav`) and `ssrecomp.cfg` are kept. Setup only
allows **Build** when the matching layout is present.

## If something goes wrong

- **"Pokemon HeartGold needs layouts/heartgold-us.json"** — the file is missing.
  Make it with `tools/make_layout.py` (decompilation build) or
  `tools/derive_layout.py` (from the SoulSilver layout and your ROM), as above.
- **"This is not the exact ROM the layout was made for"** — the SHA-1 differs.
  The build still runs if the code is identical; if the recompiler then reports a
  section that differs, the dump is another region or revision. Use a US dump.
- **The build fails after switching games** — delete `build/` (or let setup
  reconfigure it) and build again; `gen/` and the executable must come from the
  same game.
- **A controller or picture problem** — `game.log` is written beside the scripts;
  include it in a bug report.
