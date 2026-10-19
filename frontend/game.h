// Which game the loaded ROM is, for the names the player sees.
//
// The recompiled code in gen/ belongs to one game; HeartGold and SoulSilver are
// built separately because a few of their screens compile differently. Nothing in
// the frontend depends on the game beyond these names, so they are read from the
// cartridge header at start: the window title, the pause menu heading, and the
// save file name the Android build uses when no --save is given.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>

struct GameName
{
    const char* windowTitle;
    const char* menuTitle;
    const char* saveName;
};

// The cartridge header's game code sits at offset 0x0C: "IPKE" is HeartGold (US),
// "IPGE" is SoulSilver (US). Other regions and games keep the SoulSilver names the
// project has always shown, since a build only ever runs the game it was made from.
inline GameName IdentifyGame(const uint8_t* rom, std::size_t size)
{
    static const GameName soulSilver = { "Pokemon SoulSilver", "POKEMON SOULSILVER", "soulsilver.sav" };
    static const GameName heartGold = { "Pokemon HeartGold", "POKEMON HEARTGOLD", "heartgold.sav" };
    if (rom && size >= 0x10)
    {
        if (std::memcmp(rom + 0x0C, "IPKE", 4) == 0) return heartGold;
        if (std::memcmp(rom + 0x0C, "IPGE", 4) == 0) return soulSilver;
    }
    return soulSilver;
}
