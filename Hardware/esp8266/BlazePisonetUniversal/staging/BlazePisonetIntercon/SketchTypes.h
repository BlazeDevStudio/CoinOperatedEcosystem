#pragma once
#include <stdint.h>
// Kept ahead of Arduino automatic prototype generation. This avoids the
// longstanding ChimeKind "not declared" build failure in single-file sketches.
enum class ChimeKind : uint8_t { None, Welcome, Coin, NearEnd, Timeout, Manual };
enum class ChimeSource : uint8_t { None, Ram, Progmem };
