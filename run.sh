#!/bin/bash
# Launches the recompiled game (HeartGold or SoulSilver). Extra arguments are
# passed through, e.g. ./run.sh --fullscreen --layout side
HERE="$(cd "$(dirname "$0")" && pwd)"
# setup.sh records which ROM to use; otherwise the decompilation's SoulSilver build
# next to this folder.
ROM="$HERE/../pokeheartgold/build/soulsilver.us/pokesoulsilver.us.nds"
[ -f "$HERE/ssrecomp.rom" ] && ROM="$(head -n1 "$HERE/ssrecomp.rom")"
# Each game keeps its own save, so switching between them never overwrites progress.
# The game code is at offset 0x0C of the cartridge header ("IPKE", "IPGE").
SAVE="soulsilver.sav"
if [ -f "$ROM" ]; then
    case "$(dd if="$ROM" bs=1 skip=12 count=4 2>/dev/null)" in
        IPKE) SAVE="heartgold.sav" ;;
        IPGE) SAVE="soulsilver.sav" ;;
    esac
fi
BUILD="$HERE/build"
[ "$(uname -s)" = Darwin ] && BUILD="$HERE/build-macos-$(uname -m)"
if [ ! -x "$BUILD/ssrecomp" ] || [ ! -f "$ROM" ]; then
    if [ "$(uname -s)" = Darwin ]; then
        echo "Not set up yet: run python3 ssrecomp_setup.py first." >&2
    else
        echo "Not set up yet: run ./setup.sh first." >&2
    fi
    exit 1
fi
# The messages also go to game.log here (made new each time), for bug reports: started from
# Steam or a desktop shortcut there is no terminal to see them in.
"$BUILD/ssrecomp" "$ROM" --save "$HERE/$SAVE" "$@" 2>&1 | tee "$HERE/game.log"
exit "${PIPESTATUS[0]}"
