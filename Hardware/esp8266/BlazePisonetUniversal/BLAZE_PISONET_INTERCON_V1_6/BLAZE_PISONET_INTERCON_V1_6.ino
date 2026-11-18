#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <WiFiUdp.h>
#include "InterconPeerParser.h"
#include <EEPROM.h>
#include <TM1637Display.h>
#include <LittleFS.h>
#include <vector>
#include <stddef.h>


// ------ AudioPatterns.h (bundled) ------

// Generated buzzer-safe tone approximations of the supplied MP3 files.
// A single GPIO tone output cannot reproduce speech/music as literal MP3 audio;
// these compact patterns preserve timing and dominant pitch movement.

static const uint16_t tacosFreq[] PROGMEM = {
  0, 320, 311, 233, 311, 392, 415, 392, 466, 622, 659, 311, 622, 311, 622, 311, 
  330, 392, 880, 311, 233, 392, 311, 0, 539, 311, 330, 392, 0, 349, 311, 247, 
  233, 294, 233, 311, 262, 208, 196, 262, 233, 294, 277, 196, 262, 294, 196, 392, 
  262, 494, 262, 277, 311, 277, 208, 415, 659, 392, 233, 349, 311, 208, 0, 202, 
  208, 262, 208, 415, 427, 0, 202, 208, 392, 233, 349, 220, 311, 0, 214, 208, 
  220, 1175, 1385, 0, 308, 247, 370, 233, 0, 668, 0, 284, 0, 727, 0, 807, 
  0, 720, 311, 621, 0, 196, 685, 0, 845, 294, 196, 0, 245, 196, 409, 0, 
  196, 190, 0, 196, 262, 247, 0, 524, 0, 1017, 0, 417, 523, 449, 0, 697, 
  311, 259, 0, 305, 196, 190, 0, 294, 0, 196, 0, 320, 0, 1523, 1319, 1659, 
  0, 208, 0, 269, 0, 598, 831, 523, 587, 1293, 0, 1142, 1175, 1109, 1111, 0, 
  233, 587, 410, 0, 351, 0, 1109, 466, 343, 0, 229, 262, 523, 538, 0, 229, 
  262, 460, 0, 364, 262, 349, 440, 714, 0, 196, 214, 0, 970, 831, 262, 229, 
  0, 325, 0, 337, 466, 453, 0, 324, 440, 208, 0, 359, 196, 208, 196, 294, 
  0, 815, 0, 248, 311, 0, 698, 466, 407, 0, 408, 0, 592, 0, 262, 0, 
  196, 796, 0, 378, 262, 363
};
static const uint16_t tacosDur[] PROGMEM = {
  80, 80, 80, 240, 80, 240, 240, 240, 80, 320, 160, 320, 160, 240, 160, 480, 
  320, 80, 160, 80, 320, 80, 240, 80, 80, 400, 160, 160, 80, 160, 240, 80, 
  160, 480, 560, 320, 80, 80, 400, 480, 160, 160, 80, 240, 160, 640, 480, 160, 
  240, 240, 80, 160, 240, 80, 640, 80, 160, 240, 160, 160, 1120, 320, 80, 80, 
  240, 160, 160, 80, 80, 80, 80, 80, 240, 240, 640, 80, 320, 80, 80, 80, 
  80, 160, 80, 80, 80, 80, 80, 240, 1120, 160, 160, 160, 560, 160, 240, 160, 
  80, 80, 160, 80, 160, 400, 80, 720, 80, 160, 240, 80, 80, 320, 80, 80, 
  160, 80, 160, 240, 240, 80, 160, 160, 80, 160, 80, 80, 80, 80, 80, 80, 
  160, 80, 240, 80, 80, 80, 160, 160, 80, 160, 80, 160, 80, 80, 80, 80, 
  480, 240, 80, 160, 160, 80, 160, 160, 160, 80, 80, 80, 80, 80, 80, 80, 
  320, 80, 80, 240, 160, 240, 160, 80, 80, 160, 80, 560, 80, 80, 80, 80, 
  80, 80, 160, 80, 80, 480, 80, 80, 80, 160, 80, 80, 80, 80, 80, 80, 
  240, 160, 240, 80, 240, 80, 80, 80, 240, 400, 160, 80, 160, 240, 80, 80, 
  160, 160, 240, 80, 320, 80, 80, 80, 80, 240, 160, 240, 160, 80, 160, 80, 
  160, 80, 160, 80, 80, 80
};
static const size_t tacosCount = sizeof(tacosFreq) / sizeof(tacosFreq[0]);

static const uint16_t timeoutFreq[] PROGMEM = {
  0, 284, 220, 330, 659, 330, 220, 330, 349, 370, 392, 196, 330, 196, 330, 220, 
  330, 220, 330, 659, 330, 311, 330, 196, 220, 330, 622, 659, 330, 220, 622, 659, 
  330, 220, 330, 349, 330, 392, 262, 330, 220, 349, 330, 587, 523, 494, 247, 494, 
  988, 494, 621, 0, 263, 196, 0, 254, 0
};
static const uint16_t timeoutDur[] PROGMEM = {
  560, 80, 400, 320, 160, 480, 160, 1600, 80, 400, 80, 880, 160, 160, 240, 160, 
  640, 160, 560, 160, 2400, 320, 160, 240, 320, 400, 320, 240, 80, 160, 80, 240, 
  640, 320, 400, 160, 240, 480, 880, 240, 160, 240, 720, 320, 880, 560, 240, 160, 
  160, 160, 80, 80, 80, 1200, 560, 160, 876
};
static const size_t timeoutCount = sizeof(timeoutFreq) / sizeof(timeoutFreq[0]);

static const uint16_t faaFreq[] PROGMEM = {
  0, 906, 1319, 1397, 1319, 1480, 1570, 0
};
static const uint16_t faaDur[] PROGMEM = {
  240, 80, 960, 320, 80, 160, 80, 7
};
static const size_t faaCount = sizeof(faaFreq) / sizeof(faaFreq[0]);





// ------ DisplayManager.h (bundled) ------

// Four-digit TM1637 display controller (CLK first, DIO second).
// Startup/self-test is nonblocking: coin handling, countdown and web continue.
// Glyph note: a 7-segment digit cannot draw a true Z; Z uses the segments for 2.
// This driver does not expose the TM1637 ACK, so a self-test is visual only.
class DisplayManager {
public:
  // 0 is the lowest illuminated level, 7 the brightest (not an off switch).
  static constexpr uint8_t kSweepLevels = 8;
  static constexpr uint16_t kSweepStepMs = 220;
  static constexpr uint8_t kScrollFrames = 7;
  // Idle animation: one illuminated segment at a time, never a full digit.
  static constexpr uint8_t kIdleSegmentCount = 28;
  static constexpr uint8_t kSnakeStepCount = 32; // 8 steps per digit: center-to-center
  static constexpr uint16_t kIdleStepMs = 115;
  static constexpr uint16_t kIdlePauseMs = 380;
  static constexpr uint16_t kScrollFrameMs = 650;
  static constexpr uint32_t kSweepDurationMs = (uint32_t)kSweepLevels * kSweepStepMs;
  static constexpr uint32_t kScrollDurationMs = (uint32_t)kScrollFrames * kScrollFrameMs;

  void begin(uint8_t clockPin, uint8_t dataPin, uint8_t level = 7) {
    configuredClk = clockPin;
    configuredDio = dataPin;
    brightness = level <= 7 ? level : 7;
    activate(configuredClk, configuredDio);
    beginTest(false);
  }

  // 0 means immediately after the welcome sequence; otherwise wait this many
  // seconds after the countdown reaches zero. No EEPROM writes from display.
  void setIdleDelaySeconds(uint16_t delay) {
    idleDelaySeconds = delay;
    if (idleActive) {
      idleActive = false;
      idleHoldUntil = 0;
      idleWaiting = true;
      zeroSince = millis();
    }
  }

  uint16_t idleDelay() const { return idleDelaySeconds; }

  void setBrightness(uint8_t level) {
    brightness = level <= 7 ? level : 7;
    // Keep saved level separate from temporary brightness sweep levels.
    // During a sweep, the next step restores its own level automatically.
    if (driver && !testing) driver->setBrightness(brightness, true);
    lastValue = UINT32_MAX;
  }

  // Available through the authenticated /display/test endpoint, as before.
  void beginTest(bool swapped) {
    if (!driver || swapped != currentlySwapped) {
      activate(swapped ? configuredDio : configuredClk,
               swapped ? configuredClk : configuredDio);
    }
    currentlySwapped = swapped;
    testing = true;
    testStarted = millis();
    lastSweepStep = 255;
    lastScrollFrame = 255;
    lastTick = 0;
    lastValue = UINT32_MAX;
    idleActive = false;
    idleHoldUntil = 0;
    idleWaiting = false;
    drawSweepStep(0);  // Make the first 8888 visible immediately.
    Serial.printf("[DISPLAY] START %s CLK=GPIO%u DIO=GPIO%u: brightness 0-7 then 8888 / 1234 / bLA2 / LA2E / A2E_ / 2E__ / E___\n",
                  swapped ? "SWAPPED" : "NORMAL", currentClk, currentDio);
  }

  void update(uint32_t seconds) {
    if (!driver) return;
    const uint32_t now = millis();
    if (testing) {
      // Unsigned subtraction works correctly even across millis() rollover.
      const uint32_t elapsed = (uint32_t)(now - testStarted);
      if (elapsed < kSweepDurationMs) {
        const uint8_t step = (uint8_t)(elapsed / kSweepStepMs);
        if (step != lastSweepStep) drawSweepStep(step);
        return;
      }
      if (elapsed < kSweepDurationMs + kScrollDurationMs) {
        const uint8_t frame = (uint8_t)((elapsed - kSweepDurationMs) / kScrollFrameMs);
        if (frame != lastScrollFrame) drawScrollFrame(frame);
        return;
      }
      // End of welcome scroll: restore configured brightness and countdown.
      testing = false;
      if (currentlySwapped) {
        currentlySwapped = false;
        activate(configuredClk, configuredDio);
      } else {
        driver->setBrightness(brightness, true);
      }
      lastValue = UINT32_MAX;
      idleWaiting = false; // Start the configured idle delay after welcome.
      Serial.println(F("[DISPLAY] Welcome complete; display resumed"));
    }

    // Idle effects only when the paid timer is fully stopped.
    // Active countdown always takes precedence, even mid-animation.
    if (seconds == 0) {
      if (!idleWaiting && !idleActive) {
        idleWaiting = true;
        zeroSince = now;
        lastValue = UINT32_MAX; // Show 00:00 while waiting.
      }
      if (!idleActive &&
          (uint32_t)(now - zeroSince) < (uint32_t)idleDelaySeconds * 1000UL) {
        drawCountdown(0, now);
        return;
      }
      updateIdle(now);
      return;
    }
    if (idleActive || idleWaiting) {
      idleActive = false;
      idleWaiting = false;
      idleHoldUntil = 0;
      lastValue = UINT32_MAX; // Force first countdown frame immediately.
      lastTick = 0;
    }
    drawCountdown(seconds, now);
  }

  void drawCountdown(uint32_t seconds, uint32_t now) {

    // TM1637 is a bit-banged display: avoid continuously retransmitting.
    if (seconds == lastValue && (uint32_t)(now - lastTick) < 3000UL) return;
    if ((uint32_t)(now - lastTick) < 160UL && lastValue != UINT32_MAX) return;
    lastTick = now;
    lastValue = seconds;
    if (seconds > 5999UL) {
      // HH:MM for sessions over 99:59; hours are capped at 99 for 4 digits.
      uint32_t hh = seconds / 3600UL;
      if (hh > 99) hh = 99;
      uint32_t mm = (seconds % 3600UL) / 60UL;
      driver->showNumberDecEx((int)(hh * 100 + mm), 0x40, true);
    } else {
      driver->showNumberDecEx((int)((seconds / 60UL) * 100UL + seconds % 60UL),
                              0x40, true);
    }
  }

  bool testActive() const { return testing; }
  uint8_t clockPin() const { return configuredClk; }
  uint8_t dataPin() const { return configuredDio; }
  uint8_t level() const { return brightness; }
  const char* mode() const {
    if (!testing) return idleActive ? idleModeName() : (idleWaiting ? "idle waiting" : "countdown");
    const uint32_t elapsed = (uint32_t)(millis() - testStarted);
    if (elapsed < kSweepDurationMs) return currentlySwapped ? "brightness swapped" : "brightness normal";
    return currentlySwapped ? "welcome swapped" : "welcome normal";
  }

private:
  TM1637Display* driver = nullptr;
  uint8_t configuredClk = 12, configuredDio = 13;
  uint8_t currentClk = 12, currentDio = 13, brightness = 7;
  uint8_t lastSweepStep = 255, lastScrollFrame = 255;
  bool testing = false, currentlySwapped = false;
  uint32_t testStarted = 0, lastTick = 0, lastValue = UINT32_MAX;
  enum IdleMode : uint8_t { Snake = 0, Chaotic = 1, Sparkle = 2 };
  IdleMode idleMode = Snake;
  bool idleActive = false;
  uint8_t idleStep = 0;
  uint8_t idleOrder[kSnakeStepCount] = {};
  uint8_t idleLength = 0;
  uint8_t idlePreviousDigit = 255;
  uint16_t idleDelaySeconds = 15;
  bool idleWaiting = false;
  uint32_t zeroSince = 0;
  uint32_t idleLastFrame = 0;
  uint32_t idleHoldUntil = 0;

  void activate(uint8_t clk, uint8_t dio) {
    if (driver) { driver->clear(); delete driver; driver = nullptr; }
    currentClk = clk;
    currentDio = dio;
    driver = new TM1637Display(clk, dio, 100);
    if (driver) driver->setBrightness(brightness, true);
  }

  const char* idleModeName() const {
    if (idleMode == Snake) return "idle snake";
    if (idleMode == Chaotic) return "idle chaotic";
    return "idle sparkle";
  }

  // Seven-segment labels: a=top, b=upper-right, c=lower-right,
  // d=bottom, e=lower-left, f=upper-left, g=center.
  // One-hot output: every frame illuminates exactly one segment.
  static uint8_t segmentMask(uint8_t bit) { return (uint8_t)(1U << bit); }

  void startIdlePattern(uint32_t now) {
    // Snake is deliberately the dominant animation.
    const uint8_t pick = (uint8_t)random(100);
    idleMode = pick < 70 ? Snake : (pick < 95 ? Chaotic : Sparkle);
    idleLength = idleMode == Snake ? kSnakeStepCount : kIdleSegmentCount;

    if (idleMode == Snake) {
      // g -> f -> a -> b -> c -> d -> e -> g.
      // Adjacent segments share endpoints. Every digit finishes at g;
      // the next digit begins at g, preventing a top/bottom reset.
      static const uint8_t connectedPath[8] = {6, 5, 0, 1, 2, 3, 4, 6};
      for (uint8_t digit = 0; digit < 4; ++digit)
        for (uint8_t step = 0; step < 8; ++step)
          idleOrder[digit * 8 + step] = digit * 7 + connectedPath[step];
    } else {
      // Seven rounds of four digits. Each round shuffles all four digits;
      // the first digit must differ from the previous round's final digit.
      // Chaotic uses all 7 segments on each digit exactly once per cycle.
      uint8_t segmentOrders[4][7];
      for (uint8_t digit = 0; digit < 4; ++digit) {
        for (uint8_t j = 0; j < 7; ++j) segmentOrders[digit][j] = j;
        for (int j = 6; j > 0; --j) {
          uint8_t k = (uint8_t)random(j + 1);
          uint8_t temp = segmentOrders[digit][j];
          segmentOrders[digit][j] = segmentOrders[digit][k];
          segmentOrders[digit][k] = temp;
        }
      }
      uint8_t lastDigit = idlePreviousDigit;
      for (uint8_t round = 0; round < 7; ++round) {
        uint8_t digits[4] = {0, 1, 2, 3};
        for (int j = 3; j > 0; --j) {
          uint8_t k = (uint8_t)random(j + 1);
          uint8_t temp = digits[j]; digits[j] = digits[k]; digits[k] = temp;
        }
        if (digits[0] == lastDigit) {
          uint8_t swapIndex = 1 + (uint8_t)random(3);
          uint8_t temp = digits[0]; digits[0] = digits[swapIndex];
          digits[swapIndex] = temp;
        }
        for (uint8_t j = 0; j < 4; ++j) {
          uint8_t digit = digits[j];
          uint8_t bit = idleMode == Chaotic ?
                        segmentOrders[digit][round] : (uint8_t)random(7);
          idleOrder[round * 4 + j] = digit * 7 + bit;
        }
        lastDigit = digits[3];
      }
      idlePreviousDigit = lastDigit;
    }

    idleActive = true;
    idleWaiting = false;
    idleStep = 0;
    idleLastFrame = now - kIdleStepMs; // First frame immediately.
    idleHoldUntil = 0;
    driver->setBrightness(brightness, true);
  }

  void updateIdle(uint32_t now) {
    if (!idleActive) startIdlePattern(now);
    if (idleHoldUntil) {
      if ((int32_t)(now - idleHoldUntil) < 0) return;
      startIdlePattern(now);
    }
    if ((uint32_t)(now - idleLastFrame) < kIdleStepMs) return;
    idleLastFrame = now;
    if (idleStep >= idleLength) {
      const uint8_t off[4] = {0, 0, 0, 0};
      driver->setSegments(off);
      idleHoldUntil = now + kIdlePauseMs;
      return;
    }
    const uint8_t position = idleOrder[idleStep++];
    const uint8_t digit = position / 7;
    const uint8_t bit = position % 7;
    const uint8_t oneHot[4] = {
      (uint8_t)(digit == 0 ? segmentMask(bit) : 0),
      (uint8_t)(digit == 1 ? segmentMask(bit) : 0),
      (uint8_t)(digit == 2 ? segmentMask(bit) : 0),
      (uint8_t)(digit == 3 ? segmentMask(bit) : 0)
    };
    driver->setSegments(oneHot);
  }

  void drawSweepStep(uint8_t step) {
    if (!driver) return;
    lastSweepStep = step;
    driver->setBrightness(step, true);
    const uint8_t eight[] = {0x7F, 0x7F, 0x7F, 0x7F};
    driver->setSegments(eight); // Re-send data to apply each brightness command.
    Serial.printf("[DISPLAY] Brightness %u/7\n", step);
  }

  void drawScrollFrame(uint8_t frame) {
    if (!driver) return;
    lastScrollFrame = frame;
    driver->setBrightness(brightness, true); // Return to user setting after sweep.
    // Each ZERO segment byte turns that digit completely off, not character '0'.
    static const uint8_t glyph_b = 0x7C;
    static const uint8_t glyph_L = 0x38;
    static const uint8_t glyph_A = 0x77;
    static const uint8_t glyph_Z = 0x5B; // looks like '2' on a 7-segment module
    static const uint8_t glyph_E = 0x79;
    static const uint8_t frames[kScrollFrames][4] = {
      {0x7F,    0x7F,    0x7F,    0x7F},    // 8888
      {0x06,    0x5B,    0x4F,    0x66},    // 1234
      {glyph_b, glyph_L, glyph_A, glyph_Z}, // bLAZ
      {glyph_L, glyph_A, glyph_Z, glyph_E}, // LAZE
      {glyph_A, glyph_Z, glyph_E, 0x00},    // AZE_ (right digit OFF)
      {glyph_Z, glyph_E, 0x00,   0x00},     // ZE__
      {glyph_E, 0x00,    0x00,   0x00},     // E___
    };
    driver->setSegments(frames[frame]);
    Serial.printf("[DISPLAY] Welcome frame %u/7\n", frame + 1);
  }
};


// ------ TimeControls.h (bundled) ------

// Stateless, tested time validation and arithmetic. Kept separate from GPIO,
// EEPROM, and HTTP so manual adjustments cannot affect sales accounting.
static const uint32_t BLAZE_MAX_SESSION_SECONDS = 7UL * 24UL * 60UL * 60UL;
static const uint64_t BLAZE_TIME_UNITS_PER_SECOND = 100000ULL; // 100x milliseconds

// Strict decimals only: no negative signs, spaces, trailing junk, or overflow.
static inline bool blazeParseTimeField(const String& value, uint16_t maxValue, uint16_t& parsed) {
  if (value.length() == 0 || value.length() > 3) return false;
  uint16_t n = 0;
  for (size_t i = 0; i < value.length(); i++) {
    const char c = value[i];
    if (c < '0' || c > '9') return false;
    n = (uint16_t)(n * 10 + (c - '0'));
  }
  if (n > maxValue) return false;
  parsed = n;
  return true;
}

static inline bool blazeParseManualDuration(const String& hours,
                                             const String& minutes,
                                             const String& seconds,
                                             uint32_t& totalSeconds) {
  uint16_t h=0, m=0, s=0;
  if (!blazeParseTimeField(hours, 168, h) ||
      !blazeParseTimeField(minutes, 59, m) ||
      !blazeParseTimeField(seconds, 59, s)) return false;
  const uint32_t n = (uint32_t)h * 3600UL + (uint32_t)m * 60UL + s;
  if (n == 0 || n > BLAZE_MAX_SESSION_SECONDS) return false;
  totalSeconds = n;
  return true;
}

// Adds to the precise internal counter without rounding away fractional time;
// Set replaces it. Rejects an add that exceeds 7 days (never silently clips).
static inline bool blazeComputeManualTarget(bool replace, uint64_t currentUnits,
                                             uint32_t inputSeconds, uint64_t& targetUnits) {
  if (inputSeconds == 0 || inputSeconds > BLAZE_MAX_SESSION_SECONDS) return false;
  const uint64_t additional = (uint64_t)inputSeconds * BLAZE_TIME_UNITS_PER_SECOND;
  const uint64_t limit = (uint64_t)BLAZE_MAX_SESSION_SECONDS * BLAZE_TIME_UNITS_PER_SECOND;
  if (replace) { targetUnits = additional; return true; }
  if (currentUnits > limit || additional > limit - currentUnits) return false;
  targetUnits = currentUnits + additional;
  return true;
}


// ------ WebUI.h (bundled) ------

// Served directly from program flash. No CDN, gradients, filters or dynamic HTML concatenation.
static const char WEB_UI[] PROGMEM = R"BLAZEHTML(<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#15263b"><title>BLAZE | PisoNet Controller</title>
<style>
:root{--navy:#15263b;--navy2:#223a53;--blue:#185a83;--bg:#edf1f5;--panel:#fff;--ink:#17283a;--muted:#54687b;--line:#cbd5de;--ok:#146647;--bad:#a52f2f;--amber:#865000}
*{box-sizing:border-box}html{font-family:system-ui,-apple-system,Segoe UI,Arial,sans-serif}body{margin:0;background:var(--bg);color:var(--ink)}
header{background:var(--navy);color:white;padding:20px max(16px,calc((100% - 1050px)/2));border-bottom:4px solid var(--blue)}
header h1{font-size:21px;letter-spacing:.3px;margin:0 0 4px}header p{margin:0;color:#c8d8e5;font-size:13px}
main{max-width:1050px;margin:auto;padding:15px}.nav{display:flex;flex-wrap:wrap;gap:7px;margin:2px 0 16px}
button,.button{font:inherit;cursor:pointer;border:1px solid var(--line);border-radius:5px;padding:11px 14px;min-height:43px;color:var(--ink);background:white;font-weight:650}
button:hover,.button:hover{border-color:var(--blue)}button:disabled{opacity:.55;cursor:not-allowed}
.nav button{flex:1}.nav button[aria-current="page"]{background:var(--navy);color:white;border-color:var(--navy)}
.panel{display:none}.panel.active{display:block}.card{background:var(--panel);border:1px solid var(--line);border-radius:7px;padding:19px;margin-bottom:14px}
h2{font-size:17px;margin:0 0 14px}h3{font-size:14px;margin:15px 0 7px}.muted,small{color:var(--muted)}.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:1px;font-weight:750;color:var(--muted)}
.timer{text-align:center;padding:24px 12px}.digits{font-size:clamp(44px,10vw,76px);line-height:1.25;letter-spacing:2px;font-weight:800;font-variant-numeric:tabular-nums;color:var(--navy)}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.three{grid-template-columns:repeat(3,minmax(0,1fr))}
.row{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;padding:9px 0;border-bottom:1px solid var(--line)}.row:last-child{border-bottom:none}
.state{font-weight:800;padding:4px 10px;border-radius:4px;background:#e9eff4;color:var(--navy)}.state.on{color:var(--ok);background:#dcefe5}.state.off{color:var(--bad);background:#f5e4e4}
.primary{background:var(--blue);color:white;border-color:var(--blue)}.danger{background:var(--bad);color:white;border-color:var(--bad)}.quiet{background:#e9eff4;border-color:#bdcbd5}.wide{width:100%}
form{margin:0}.fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}label{display:block;font-size:13px;font-weight:650;color:var(--ink)}
input,select{font:inherit;color:var(--ink);border:1px solid #a9bac9;border-radius:4px;background:#fff;padding:10px;width:100%;margin-top:5px;min-width:0}input[type=checkbox]{width:auto;margin:0 7px 0 0}.checks{display:flex;flex-wrap:wrap;gap:12px;padding:10px 0}.checks label{display:inline-flex;align-items:center}
.help{font-size:12px;color:var(--muted);margin-top:6px;line-height:1.5}.metric{font-size:27px;font-weight:800;color:var(--navy);font-variant-numeric:tabular-nums}
.notice{font-size:13px;background:#fff4dd;border:1px solid #e3cc8c;padding:11px;border-radius:5px;margin-bottom:14px}.note{font-size:13px;line-height:1.55}
#toast{display:none;padding:12px;margin-bottom:14px;background:var(--navy);color:white;border-radius:5px}#toast.show{display:block}
table{width:100%;border-collapse:collapse;font-size:13px}td{padding:8px 4px;border-bottom:1px solid var(--line)}td:first-child{color:var(--muted)}.buttons{display:flex;flex-wrap:wrap;gap:8px;margin-top:11px}
footer{text-align:center;font-size:12px;color:var(--muted);padding:10px 0 25px}
@media(max-width:680px){.grid,.three,.fields{grid-template-columns:1fr}.fields.three{grid-template-columns:repeat(3,minmax(0,1fr))}.card{padding:15px}.nav button{font-size:12px;padding:9px 5px}.buttons button{flex:1}}
</style></head><body>
<header><h1>BLAZE PISONET</h1><p>ESP8266 Station Controller · AP + STA network · INTERCON V1.6 discovery preview</p></header>
<main><div id="toast" role="status"></div>
<div class="nav" role="navigation" aria-label="Sections">
<button aria-current="page" data-tab="dashboard">Overview</button><button data-tab="hardware">Display &amp; GPIO</button>
<button data-tab="settings">Settings</button><button data-tab="sales">Sales</button><button data-tab="audio">Sounds</button></div>
<section id="dashboard" class="panel active">
 <div class="card timer"><div class="eyebrow">Remaining rental time</div><div class="digits" id="time">00:00</div>
 <div id="running" class="muted">Reading station…</div></div>
 <div class="card" id="time-controls"><h2>Manage rental time</h2>
 <p class="note">Add extra time to the active session, or set an exact remaining time. Works while the station is idle or running.</p>
 <div class="buttons" role="group" aria-label="Quick time additions">
 <button type="button" onclick="quickAdd(5)">+5 min</button>
 <button type="button" onclick="quickAdd(10)">+10 min</button>
 <button type="button" onclick="quickAdd(30)">+30 min</button>
 <button type="button" onclick="quickAdd(60)">+1 hour</button></div>
 <form id="manualTimeForm"><h3>Enter custom time</h3>
 <div class="fields three"><label>Hours<input type="number" name="hours" min="0" max="168" value="0" step="1" inputmode="numeric" required></label>
 <label>Minutes<input type="number" name="minutes" min="0" max="59" value="5" step="1" inputmode="numeric" required></label>
 <label>Seconds<input type="number" name="seconds" min="0" max="59" value="0" step="1" inputmode="numeric" required></label></div>
 <div class="buttons" style="margin-top:12px"><button class="primary" type="submit" value="add" name="timeMode">Add time</button>
 <button class="quiet" type="submit" value="set" name="timeMode">Set remaining time</button></div>
 <p class="help">Add keeps the existing countdown. Set replaces it and asks for confirmation. Nonzero time enables the cutoff relay and triggers PC startup only if it is believed off; neither adds to sales or coin counts. Maximum session: 7 days.</p>
 <p class="help" id="timeFeedback" role="status" aria-live="polite"></p></form></div>
 <div class="grid"><div class="card"><h2>Outputs &amp; PC control</h2><div class="row"><strong>Relay 1 · D0 cutoff</strong><span id="r1" class="state">…</span></div>
 <div class="row"><strong>Relay 2 · D6 PWR_SW pulse</strong><span id="r2" class="state">…</span></div>
 <div class="row"><strong>Estimated PC state (not sensed)</strong><span id="pcState" class="state">…</span></div>
 <div class="row"><strong>Shutdown grace</strong><span id="pcGrace">…</span></div>
 <p class="help">Relay 2 is a momentary switch ONLY: never stays energized during rental time. A button pulse may power ON or request shutdown depending on the actual PC state.</p>
 <div class="buttons"><button onclick="act('relay1')">Toggle cutoff (idle only)</button><button onclick="confirmAction('pwrPulse','Press motherboard power button now? This can shut down or start the PC.')">Pulse PC PWR_SW</button></div></div>
 <div class="card"><h2>Coin Slot Enable — D7</h2>
 <div class="row"><strong>CS controller</strong><span id="csState" class="state">…</span></div>
 <p class="note">Disable coin acceptance for closing hours. GPIO13/D7 drives an external CS ENABLE circuit, not the acceptor's power load. State is saved after toggling.</p>
 <div class="buttons"><button class="primary" onclick="setCs(true)">Enable coin slot</button><button onclick="setCs(false)">Disable coin slot</button></div>
 <p class="help">Admin-only; disabling also rejects coin pulses in firmware. Display a clear Out-of-service notice if customers may attempt to insert coins.</p></div>
 <div class="card"><h2>INTERCON peers (read-only)</h2><p class="note">Discovered via the STA/LAN Wi-Fi; unpaired status is informational only. No remote credit is authorized in this firmware.</p>
 <div class="row"><strong>Role</strong><span id="roleState">—</span></div>
 <div class="row"><strong>STA address</strong><span id="staIp">—</span></div>
 <div class="row"><strong>Found peers</strong><span id="peerCount">0</span></div>
 <div id="peerList" class="help">No peers discovered</div></div>
 <div class="card"><h2>Station actions</h2><p class="note">Admin-only actions. A reset ends paid time immediately.</p>
 <div class="buttons"><button onclick="act('warn')">Play warning</button><button class="danger" onclick="confirmAction('resetTimer','End the paid session?')">Reset timer</button></div>
 <p class="help" id="statusline">Status not yet available</p></div></div>
</section>
<section id="hardware" class="panel">
 <div class="notice">A blank TM1637 display is not automatically a firmware failure. Confirm CLK, DIO, VCC, GND and the actual module type. Never apply 5 V to ESP8266 GPIO inputs.</div>
 <div class="grid"><div class="card"><h2>Display diagnosis</h2><table><tr><td>Configured CLK</td><td id="clk">—</td></tr><tr><td>Configured DIO</td><td id="dio">—</td></tr><tr><td>Brightness</td><td id="bright">—</td></tr><tr><td>Test mode</td><td id="displaymode">—</td></tr></table>
 <p class="help">Test runs: brightness sweep (0–7), then 8888, 1234, bLAZ, LAZE, AZE, ZE, E. The Z is rendered with 2-shaped segments.</p>
 <div class="buttons"><button class="primary" onclick="testDisplay('normal')">Test configured pins</button><button onclick="testDisplay('swapped')">Test CLK / DIO swapped</button></div>
 <p class="help">Swapped testing is temporary. The firmware restores saved pins after the complete brightness sweep and welcome sequence.</p></div>
 <div class="card"><h2>Wiring reference</h2><table><tr><td>TM1637 CLK</td><td>GPIO5 / D1 / SCL</td></tr><tr><td>TM1637 DIO</td><td>GPIO4 / D2 / SDA</td></tr><tr><td>Buzzer</td><td>GPIO14 / D5 (fixed)</td></tr><tr><td>Relay 1 cutoff</td><td>GPIO16 / D0</td></tr><tr><td>Relay 2 PWR_SW</td><td>GPIO12 / D6</td></tr><tr><td>Coin</td><td>GPIO0 / D3 (boot-sensitive)</td></tr><tr><td>CS enable</td><td>GPIO13 / D7 (output to external driver EN)</td></tr></table>
 <p class="help">If saved settings have changed the display pin mapping, restoring D1/D2 does not affect paid time or sales.</p>
 <div class="buttons"><button onclick="restoreDisplay()">Restore D1 / D2</button></div></div></div>
</section>
<section id="settings" class="panel"><form id="settingsForm"><div class="card"><h2>Rental settings</h2>
 <div class="fields"><label>Minutes per accepted coin<input name="addMinutes" type="number" min="0" max="180" required></label>
 <label>Seconds per accepted coin<input name="addSeconds" type="number" min="0" max="59" required></label>
 <label>Warning at (seconds)<input name="warningSeconds" type="number" min="0" max="120" required></label>
 <label>Countdown speed bonus (%)<input name="speedPct" type="number" min="0" max="50" required></label>
 <label>Chime maximum (seconds)<input name="chimeDurationSeconds" type="number" min="1" max="120" required></label>
 <label>Display brightness (1–7)<input name="brightness" type="number" min="1" max="7" required></label></div>
 <p class="help">Time per coin must not be 00:00. A speed bonus shortens actual play time and is disabled by default.</p></div>
 <div class="card"><h2>Idle display animation</h2>
 <div class="fields"><label>Start animation after idle (seconds)
 <input name="idleTriggerSeconds" type="number" min="0" max="3600" step="1" required></label></div>
 <p class="help">0 = immediately after the welcome animation or timer expiry. Otherwise show 00:00 until this delay has elapsed. Maximum 3600 seconds (60 minutes). Snake 70%, Chaotic 25%, Sparkle 5%. The countdown always overrides idle effects.</p></div>
 <div class="card"><h2>Power-button shutdown</h2><div class="fields">
 <label>PC shutdown delay after time expires (seconds)<input name="shutdownGraceSeconds" type="number" min="0" max="3600" required></label>
 <label>Relay 2 pulse duration (milliseconds)<input name="pwrPulseMilliseconds" type="number" min="100" max="1000" required></label></div>
 <p class="help">New credit cancels the pending shutdown. A reboot assumes the PC is OFF and pauses saved time until a new credit. This is NOT real power-state detection.</p></div>
 <div class="card"><h2>Coin slot enable circuit</h2>
 <div class="checks"><label><input name="csActiveHigh" type="checkbox">CS ENABLE active HIGH (D7/GPIO13)</label></div>
 <p class="help">Set the polarity for your actual CS driver/enable input. Use GPIO13 only to signal a compatible enable/driver circuit. Never power the coin acceptor directly.</p></div>
 <div class="card"><h2>Hardware assignments</h2><div class="fields">
 <label>Coin GPIO<input name="coinPin" type="number" min="0" max="16" required></label>
 <label>Relay 1 GPIO<input name="relayPin" type="number" min="0" max="16" required></label>
 <label>Relay 2 GPIO<input name="relay2Pin" type="number" min="0" max="16" required></label>
 <label>Display CLK GPIO<input name="displayClk" type="number" min="0" max="16" required></label>
 <label>Display DIO GPIO<input name="displayDio" type="number" min="0" max="16" required></label>
 </div><div class="checks"><label><input name="coinActiveLow" type="checkbox">Coin active-low</label>
 <label><input name="relayActiveLow" type="checkbox">Relay 1 active-low</label><label><input name="relay2ActiveLow" type="checkbox">Relay 2 active-low</label>
 <label><input name="buzzerActiveLow" type="checkbox">Buzzer active-low</label></div>
 <p class="help">D7/GPIO13 is reserved for CS ENABLE. GPIO6–11 are reserved for flash. GPIO0/2/15 have boot restrictions. GPIO14 is reserved for the buzzer. Changing pins on a live station can interrupt equipment; only save when idle.</p></div>
 <div class="card"><h2>Wi-Fi and administrator</h2><div class="fields"><label>Wi-Fi AP name<input name="apName" maxlength="32" required></label>
 <label>New AP password (blank = unchanged)<input name="apPassword" type="password" maxlength="63" placeholder="At least 8 characters"></label>
 <label>New admin password (blank = unchanged)<input name="adminPassword" type="password" minlength="10" maxlength="32" placeholder="10–32 characters"></label></div>
 <p class="help">Changing Wi-Fi AP name or password requires restarting the ESP8266. Change the initial admin password before putting the station in service.</p></div>
 <div class="card"><h2>INTERCON network and roles</h2>
 <div class="notice">Master and Slave are safe preview roles: the physical CS line and incoming local coins are disabled. Remote credit is NOT accepted until authenticated receipt/journal integration is complete.</div>
 <div class="fields">
 <label>Operating role<select name="interconRole"><option value="0">Standard — normal local coin timer</option><option value="1">Master — coin forwarding locked until secure</option><option value="2">Slave — remote credit locked until secure</option></select></label>
 <label>Node name (letters, digits, - or _)<input name="interconNodeName" maxlength="24" required></label>
 <label>Node ID<input name="interconNodeId" type="number" min="1" max="65535" required></label>
 <label>STA Wi-Fi SSID<input name="interconStaSsid" maxlength="32" placeholder="Existing shop router"></label>
 <label>STA WPA password (blank = unchanged)<input name="interconStaPass" type="password" maxlength="63" autocomplete="new-password"></label>
 </div><div class="checks"><label><input name="interconStaEnabled" type="checkbox">Connect to router as STA, keep local AP available</label></div>
 <p class="help">Use AP IP 192.168.4.1 or the router-assigned STA/LAN IP to open this admin page. No public WAN access; restrict clients to a trusted management network. Restart to apply network settings.</p></div>
 <button type="submit" class="primary wide">Save settings</button></form>
 <div class="card"><h2>Apply network settings</h2><button onclick="restartIntercon()">Restart ESP8266 (idle only)</button><p class="help">Restart pauses any saved balance and assumes the PC is off. Never restart during a paid session.</p></div></section>
<section id="sales" class="panel"><div class="grid three"><div class="card"><div class="eyebrow">All accepted pulses</div><div class="metric" id="saleAll">0</div></div>
 <div class="card"><div class="eyebrow">Legacy daily bucket</div><div class="metric" id="saleDay">0</div></div>
 <div class="card"><div class="eyebrow">Legacy monthly bucket</div><div class="metric" id="saleMonth">0</div></div></div>
 <div class="notice">This offline ESP8266 does not have a reliable calendar clock. Daily/monthly bucket labels are legacy counters, NOT verified calendar-day/month sales. Values are pulses, not pesos.</div>
 <div class="card"><h2>Sales maintenance</h2><p class="note">Clearing counters cannot be undone. Timer and hardware settings are preserved.</p><button class="danger" onclick="confirmAction('clearSales','Permanently clear all sales counters?')">Clear all sales counters</button></div></section>
<section id="audio" class="panel"><div class="card"><h2>Chime configuration</h2><p class="note">Firmware supports short tone lists and 8-bit mono PCM WAV-to-tone approximations. It cannot reproduce MP3 or human speech through a single GPIO buzzer.</p>
 <form id="uploadForm" enctype="multipart/form-data"><div class="fields"><label>Event<select name="patternName"><option value="welcome">Welcome</option><option value="coin">Coin</option><option value="warning">Warning</option><option value="timeup">Time expired</option></select></label>
 <label>Audio pattern file<input type="file" name="file" accept=".txt,.wav" required></label></div>
 <p class="help">TXT syntax: 880,120;1000,140;0,100 (frequency Hz, duration ms). Maximum file size 64 KB. Uploaded files take priority over built-in chimes.</p>
 <button class="primary" type="submit">Upload pattern</button></form></div></section>
<footer>Offline controller · Station management over local Wi-Fi · No cloud dependency</footer>
</main><script>
const $=id=>document.getElementById(id);let lastStatus=null;
function msg(t){let e=$('toast');e.textContent=t;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),5500)}
function chooseTab(tab){document.querySelectorAll('.panel').forEach(x=>x.classList.toggle('active',x.id===tab));document.querySelectorAll('.nav button').forEach(b=>b.setAttribute('aria-current',b.dataset.tab===tab?'page':'false'))}
document.querySelectorAll('.nav button').forEach(b=>b.addEventListener('click',()=>chooseTab(b.dataset.tab)));
async function request(path,data){const options={credentials:'same-origin',cache:'no-store'};if(data){options.method='POST';options.body=data}
 const r=await fetch(path,options);let txt=await r.text();if(!r.ok)throw new Error(txt||('HTTP '+r.status));try{return JSON.parse(txt)}catch(e){return txt}}
function put(k,v){let e=$(k);if(e)e.textContent=v}
function populateForm(o){let f=$('settingsForm');for(const k of ['apName','coinPin','relayPin','relay2Pin','displayClk','displayDio','addMinutes','addSeconds','warningSeconds','speedPct','chimeDurationSeconds','brightness','idleTriggerSeconds','shutdownGraceSeconds','pwrPulseMilliseconds','interconNodeName','interconNodeId','interconStaSsid'])if(f.elements[k]&&o[k]!==undefined)f.elements[k].value=o[k];
 if(f.elements.interconRole)f.elements.interconRole.value=String(o.interconRole);
 for(const k of ['coinActiveLow','relayActiveLow','relay2ActiveLow','buzzerActiveLow','csActiveHigh','interconStaEnabled'])if(f.elements[k])f.elements[k].checked=!!o[k]}
function render(o){lastStatus=o;put('time',o.time);
 const roleNames=['Standard','Master (locked)','Slave (locked)'];put('roleState',roleNames[o.interconRole]||'Unknown');
 put('staIp',o.interconStaConnected?o.interconStaIp:'Not connected');put('peerCount',String(o.interconPeerCount||0));
 let peers=$('peerList');peers.replaceChildren();
 if(!o.interconPeers||!o.interconPeers.length)peers.textContent='No online peers found';
 else o.interconPeers.forEach(p=>{let row=document.createElement('div');row.textContent=p.name+' · ID '+p.id+' · '+p.ip+' · '+(roleNames[p.role]||'Unknown')+' · seen '+p.seenSecondsAgo+'s ago';peers.appendChild(row)});
 if(!window.formLoaded){let f=$('settingsForm');if(f&&f.elements.interconRole)f.elements.interconRole.value=String(o.interconRole)}put('running',o.timerRunning?'PAID SESSION ACTIVE':(o.remainingSeconds>0?'SAVED TIME PAUSED · ADD CREDIT TO RESUME':'IDLE / AWAITING COIN'));put('statusline','Uptime '+o.uptimeSeconds+'s · Free heap '+o.heap+' bytes · AP '+o.ip);
 for(const [id,key] of [['r1','relay1On'],['r2','relay2On']]){let e=$(id);e.textContent=o[key]?'ON':'OFF';e.className='state '+(o[key]?'on':'off')}
 put('csState',o.csEnabled?'ENABLED':'DISABLED');$('csState').className='state '+(o.csEnabled?'on':'off');
 put('pcState',o.pcExpectedOn?'EXPECTED ON':'EXPECTED OFF');put('pcGrace',o.shutdownPending?o.shutdownSecondsLeft+'s until pulse':'Not pending');
 put('clk','GPIO'+o.displayClk);put('dio','GPIO'+o.displayDio);put('bright',o.brightness);put('displaymode',o.displayMode);
 put('saleAll',o.salesOverall);put('saleDay',o.salesToday);put('saleMonth',o.salesMonth)}
async function poll(){try{let o=await request('/api/status');render(o);if(!window.formLoaded){populateForm(o);window.formLoaded=true}}catch(e){put('running','Disconnected: '+e.message)}}
// Changes the real ESP8266 timer; these are not browser-only calculations.
function validDuration(h,m,s){
 return [h,m,s].every(Number.isInteger)&&h>=0&&h<=168&&m>=0&&m<=59&&s>=0&&s<=59&&
        (h*3600+m*60+s)>0&&(h*3600+m*60+s)<=604800;
}
async function submitManualTime(mode,h,m,s){
 if(!validDuration(h,m,s)){msg('Enter a positive time up to 7 days.');return}
 if(mode==='set'&&!confirm('Replace the existing remaining time with '+h+'h '+m+'m '+s+'s? This overrides any paid time left.'))return;
 const buttons=$('manualTimeForm').querySelectorAll('button');
 buttons.forEach(b=>b.disabled=true);
 try{
  const result=await request('/api/time',new URLSearchParams({mode,hours:String(h),minutes:String(m),seconds:String(s)}));
  put('timeFeedback',String(result)+' · '+h+'h '+m+'m '+s+'s · Sales unchanged');
  msg(String(result));await poll();
 }catch(e){put('timeFeedback','Adjustment failed: '+e.message);msg('Adjustment failed: '+e.message)}
 finally{buttons.forEach(b=>b.disabled=false)}
}
async function quickAdd(minutes){await submitManualTime('add',Math.floor(minutes/60),minutes%60,0)}
$('manualTimeForm').addEventListener('submit',async e=>{
 e.preventDefault();
 const f=e.currentTarget;
 const mode=e.submitter&&e.submitter.value==='set'?'set':'add';
 await submitManualTime(mode,Number(f.elements.hours.value),Number(f.elements.minutes.value),Number(f.elements.seconds.value));
});
async function restartIntercon(){if(!confirm('Restart this controller now? Saved time will pause and the expected PC state will reset to OFF.'))return;try{await request('/api/intercon/restart',new URLSearchParams({confirm:'yes'}));msg('Controller restarting; reconnect to its AP or STA address.')}catch(e){msg(e.message)}}
async function setCs(enabled){if(!enabled&&!confirm('Disable coin insertion now? This will ignore further coin pulses until re-enabled.'))return;await act(enabled?'csOn':'csOff')}
async function act(name){try{await request('/action',new URLSearchParams({name}));await poll()}catch(e){msg('Action failed: '+e.message)}}
function confirmAction(a,t){if(confirm(t))act(a)}
async function testDisplay(mode){try{await request('/display/test',new URLSearchParams({mode}));msg('Display test started. Observe the module.');await poll()}catch(e){msg(e.message)}}
async function restoreDisplay(){if(!confirm('Restore display pins to GPIO5 (CLK) and GPIO4 (DIO)?'))return;try{await request('/display/default',new URLSearchParams({confirm:'yes'}));msg('Pins restored. Watch the brightness and welcome test.');window.formLoaded=false;await poll()}catch(e){msg(e.message)}}
$('settingsForm').addEventListener('submit',async e=>{e.preventDefault();try{let f=new FormData(e.target);f.set('save','1');await request('/settings',f);msg('Saved. Wi-Fi changes require restart.');window.formLoaded=false;await poll()}catch(err){msg('Settings not saved: '+err.message)}});
$('uploadForm').addEventListener('submit',async e=>{e.preventDefault();try{let f=new FormData(e.target);let result=await request('/upload?patternName='+encodeURIComponent(f.get('patternName')),f);msg(String(result))}catch(err){msg('Upload failed: '+err.message)}});
poll();setInterval(poll,1500);
</script></body></html>)BLAZEHTML";


// ------------------------------
// EEPROM + persistent storage
// ------------------------------
// Keep the existing EEPROM layout and saved timer/sales data. The buzzer pin is
// forced to GPIO14 separately so stale GPIO3 settings cannot return.
const uint32_t EEPROM_MAGIC = 0x5049534F;

struct PersistentState {
  uint32_t magic;
  char apName[33];
  char apPassword[65];

  uint8_t coinPin;
  uint8_t relayPin;
  uint8_t relay2Pin;
  uint8_t buzzerPin;
  uint8_t displayClk;
  uint8_t displayDio;

  bool coinActiveLow;
  bool relayActiveLow;
  bool relay2ActiveLow;
  bool buzzerActiveLow;

  uint16_t addMinutes;
  uint16_t addSeconds;
  uint16_t warningSeconds;
  uint16_t chimeDurationSeconds;
  uint8_t countdownSpeedPercent;

  uint32_t remainingSeconds;
  bool timerRunning;
  uint32_t salesOverall;
  uint32_t salesToday;
  uint32_t salesMonth;
  uint32_t salesDayKey;
  uint32_t salesMonthKey;
  uint8_t displayBrightness;
};

PersistentState state;

// INTERCON V1.6: independent configuration file; legacy EEPROM is unchanged.
// Remote coin/credit/power instructions are deliberately NOT accepted.
// Only passive read-only discovery is enabled until an authenticated and
// crash-durable payment protocol is implemented and hardware-tested.
enum InterconRole : uint8_t { INTERCON_STANDARD=0, INTERCON_MASTER=1, INTERCON_SLAVE=2 };
struct InterconConfig {
  uint32_t magic;
  uint16_t version;
  uint8_t role;
  uint8_t staEnabled;
  uint16_t nodeId;
  char nodeName[25];
  char staSsid[33];
  char staPassword[65];
  uint32_t checksum;
};
static const uint32_t INTERCON_MAGIC=0x49434F4EUL;
static const uint16_t INTERCON_VERSION=1;
// Explicit typed prototypes avoid Arduino's auto-generated declaration issue.
uint32_t interconChecksum(const InterconConfig &c);
bool validInterconConfig(const InterconConfig &c);
bool readInterconFile(const char *path,InterconConfig &result);
bool saveInterconConfig(const InterconConfig &newConfig);
InterconConfig interconConfig;
bool interconConfigHealthy=true;
bool interconFsReady=false;
bool interconStaWasConnected=false;
uint32_t lastStaRetry=0;
uint32_t lastBeacon=0;
WiFiUDP interconUdp;
static const uint16_t INTERCON_DISCOVERY_PORT=4210;
struct InterconPeer {
  blaze_intercon::Hello hello;
  IPAddress ip;
  uint32_t lastSeen;
};
static const size_t INTERCON_MAX_PEERS=12;
InterconPeer interconPeers[INTERCON_MAX_PEERS];
size_t interconPeerCount=0;

uint32_t interconChecksum(const InterconConfig &c) {
  // Noncryptographic checksum detects accidental config corruption only.
  const uint8_t *b=reinterpret_cast<const uint8_t*>(&c);
  uint32_t h=2166136261UL;
  for(size_t i=0;i<offsetof(InterconConfig,checksum);++i){h^=b[i];h*=16777619UL;}
  return h;
}
void interconDefaults(){
  memset(&interconConfig,0,sizeof(interconConfig));
  interconConfig.magic=INTERCON_MAGIC;
  interconConfig.version=INTERCON_VERSION;
  interconConfig.role=INTERCON_STANDARD;
  interconConfig.nodeId=(uint16_t)((ESP.getChipId()%65534UL)+1UL);
  snprintf(interconConfig.nodeName,sizeof(interconConfig.nodeName),"Pisonet-%06lX",(unsigned long)ESP.getChipId());
  interconConfig.checksum=interconChecksum(interconConfig);
}
bool validInterconConfig(const InterconConfig &c){
  if(c.magic!=INTERCON_MAGIC||c.version!=INTERCON_VERSION||c.role>INTERCON_SLAVE||c.staEnabled>1||c.nodeId==0)return false;
  if(!memchr(c.nodeName,0,sizeof(c.nodeName))||!memchr(c.staSsid,0,sizeof(c.staSsid))||!memchr(c.staPassword,0,sizeof(c.staPassword)))return false;
  size_t nameLen=strlen(c.nodeName);
  if(!nameLen||nameLen>24)return false;
  for(size_t i=0;i<nameLen;++i){char ch=c.nodeName[i];if(!((ch>='a'&&ch<='z')||(ch>='A'&&ch<='Z')||(ch>='0'&&ch<='9')||ch=='-'||ch=='_'))return false;}
  if(c.staEnabled && (strlen(c.staSsid)==0||strlen(c.staPassword)<8))return false;
  return c.checksum==interconChecksum(c);
}
bool readInterconFile(const char *path,InterconConfig &result){
  File f=LittleFS.open(path,"r");
  if(!f)return false;
  bool good=f.size()==sizeof(InterconConfig) && f.readBytes((char*)&result,sizeof(result))==sizeof(result);
  f.close();
  return good&&validInterconConfig(result);
}
void loadInterconConfig(bool fsReady){
  interconFsReady=fsReady;
  interconDefaults();
  if(!fsReady){interconConfigHealthy=false;return;}
  if(!LittleFS.exists("/intercon.cfg")&&!LittleFS.exists("/intercon.bak"))return;
  InterconConfig loaded;
  if(readInterconFile("/intercon.cfg",loaded)||readInterconFile("/intercon.bak",loaded)){
    interconConfig=loaded;return;
  }
  // Invalid persisted role: don't silently revert to a coin-accepting Standard.
  interconConfigHealthy=false;
}
bool saveInterconConfig(const InterconConfig &newConfig){
  if(!interconFsReady||!validInterconConfig(newConfig))return false;
  File f=LittleFS.open("/intercon.tmp","w");
  if(!f)return false;
  bool good=f.write((const uint8_t*)&newConfig,sizeof(newConfig))==sizeof(newConfig);
  f.close();
  InterconConfig checked;
  if(!good||!readInterconFile("/intercon.tmp",checked)){LittleFS.remove("/intercon.tmp");return false;}
  // Keep the older valid file as a rollback candidate if the power fails.
  if(LittleFS.exists("/intercon.bak"))LittleFS.remove("/intercon.bak");
  if(LittleFS.exists("/intercon.cfg")&&!LittleFS.rename("/intercon.cfg","/intercon.bak")){
    LittleFS.remove("/intercon.tmp");return false;
  }
  if(!LittleFS.rename("/intercon.tmp","/intercon.cfg")){
    if(LittleFS.exists("/intercon.bak"))LittleFS.rename("/intercon.bak","/intercon.cfg");
    return false;
  }
  interconConfig=newConfig;
  interconConfigHealthy=true;
  return true;
}
extern bool csEnabled; // Defined in the preserved V1.5 runtime below.
extern char AP_NAME[33];
extern char AP_PASSWORD[65];
inline bool localCoinsAllowed(){return interconConfigHealthy && interconConfig.role==INTERCON_STANDARD && csEnabled;}

IPAddress interconBroadcastIP(){
  IPAddress ip=WiFi.localIP(),mask=WiFi.subnetMask();
  return IPAddress(ip[0]|(uint8_t)~mask[0],ip[1]|(uint8_t)~mask[1],ip[2]|(uint8_t)~mask[2],ip[3]|(uint8_t)~mask[3]);
}
void beginInterconNetwork(){
  // Never trade the setup AP for a Station connection.
  WiFi.persistent(false);
  WiFi.mode(WIFI_AP_STA);
  bool apStarted=(strlen(AP_PASSWORD)==0)?WiFi.softAP(AP_NAME):WiFi.softAP(AP_NAME,AP_PASSWORD);
  if(!apStarted){
    Serial.println(F("[WIFI] Saved AP failed; using recovery AP"));
    strcpy(AP_NAME,"ESP8266-Control");strcpy(AP_PASSWORD,"12345678");
    WiFi.softAP(AP_NAME,AP_PASSWORD);
  }
  Serial.print(F("[WIFI] AP IP: "));Serial.println(WiFi.softAPIP());
  if(interconConfig.staEnabled){
    WiFi.begin(interconConfig.staSsid,interconConfig.staPassword);
    lastStaRetry=millis();
  } else {WiFi.disconnect();}
  interconUdp.begin(INTERCON_DISCOVERY_PORT);
}
void scanInterconPeers(){
  bool online=WiFi.status()==WL_CONNECTED;
  if(online && !interconStaWasConnected){
    Serial.print(F("[INTERCON] STA admin IP: "));Serial.println(WiFi.localIP());
  }
  interconStaWasConnected=online;
  const uint32_t now=millis();
  // Nonblocking reconnect. Never stop the independent timer or AP.
  if(interconConfig.staEnabled&&!online && (uint32_t)(now-lastStaRetry)>=15000UL){
    WiFi.begin(interconConfig.staSsid,interconConfig.staPassword);
    lastStaRetry=now;
  }
  for(int n=0;n<4;n++){
    int sz=interconUdp.parsePacket();if(!sz)break;
    if(sz>100){while(interconUdp.available())interconUdp.read();continue;}
    char pkt[101];int count=interconUdp.read(pkt,sizeof(pkt)-1);
    if(count<=0)continue;pkt[count]=0;
    // Untrusted discovery can update ONLY a bounded status list.
    blaze_intercon::Hello h{};
    if(!online||!blaze_intercon::parseHello(pkt,(size_t)count,h)||h.chipId==ESP.getChipId())continue;
    size_t dest=INTERCON_MAX_PEERS;
    for(size_t k=0;k<interconPeerCount;k++)if(interconPeers[k].hello.chipId==h.chipId){dest=k;break;}
    if(dest==INTERCON_MAX_PEERS){
      if(interconPeerCount<INTERCON_MAX_PEERS)dest=interconPeerCount++;
      else {size_t oldest=0;for(size_t k=1;k<interconPeerCount;k++)if((uint32_t)(now-interconPeers[k].lastSeen)>(uint32_t)(now-interconPeers[oldest].lastSeen))oldest=k;dest=oldest;}
    }
    interconPeers[dest].hello=h;interconPeers[dest].ip=interconUdp.remoteIP();interconPeers[dest].lastSeen=now;
  }
  // Discard disconnected entries after 30 seconds; no paid-state changes.
  for(size_t k=0;k<interconPeerCount;){
    if((uint32_t)(now-interconPeers[k].lastSeen)>30000UL){interconPeers[k]=interconPeers[--interconPeerCount];}
    else ++k;
  }
  if(online&&(uint32_t)(now-lastBeacon)>=7000UL){
    char msg[100];
    snprintf(msg,sizeof(msg),"BLAZE1|HELLO|%08lX|%u|%u|%s",(unsigned long)ESP.getChipId(),
             interconConfig.nodeId,(unsigned)interconConfig.role,interconConfig.nodeName);
    interconUdp.beginPacket(interconBroadcastIP(),INTERCON_DISCOVERY_PORT);
    interconUdp.write((const uint8_t*)msg,strlen(msg));interconUdp.endPacket();
    lastBeacon=now;
  }
}

// ------------------------------
// Board defaults
// ------------------------------
char AP_NAME[33] = "ESP8266-Control";
char AP_PASSWORD[65] = "12345678";

ESP8266WebServer server(80);

// Default board mapping
uint8_t coinPin = 0;      // GPIO0 / FLASH button
uint8_t relayPin = 16;    // D0 / equipment-cutoff control
uint8_t relay2Pin = 12;   // D6 / momentary PC PWR_SW
const uint8_t FIXED_BUZZER_PIN = 14;  // D5, kept fixed for the speaker/buzzer module
uint8_t buzzerPin = FIXED_BUZZER_PIN;
uint8_t displayClk = 5;   // D1 / SCL label (TM1637 is not I2C)
uint8_t displayDio = 4;   // D2 / SDA label

bool coinActiveLow = true;
bool relayActiveLow = true;
bool relay2ActiveLow = false;
bool buzzerActiveLow = false;

// Timer config
uint16_t addMinutes = 1;
uint16_t addSeconds = 0;
uint16_t warningSeconds = 10;
uint16_t chimeDurationSeconds = 30;
uint8_t countdownSpeedPercent = 0;   // 0 = normal, max 50

// Runtime state
uint32_t remainingSeconds = 0;
bool timerRunning = false;
bool relayState = false;
bool relay2State = false;
// D7/GPIO13 is reserved for the coin-slot's EN / external power-switch
// DRIVER INPUT; it must never supply the coin-slot's load current.
static const uint8_t CS_ENABLE_PIN = 13;
bool csEnabled = true;
bool csActiveHigh = true;
volatile bool coinInputAllowed = true;
// Relay 2 is a short, timed motherboard power-switch pulse, never latched.
bool pcExpectedOn = false; // Estimated only. No physical state detection.
bool powerPulseActive = false;
uint32_t powerPulseStarted = 0;
uint32_t lastPowerPulse = 0;
bool powerPulseEverSent = false;
bool pcShutdownPending = false;
uint32_t shutdownStarted = 0;
uint16_t shutdownGraceSeconds = 120;
uint16_t pwrPulseMilliseconds = 250;
// Interrupt records complete active pulses; processing stays outside the ISR.
volatile uint32_t coinPulseStartUs = 0;
volatile uint8_t coinQueued = 0;
volatile uint32_t lastAcceptedPulseUs = 0;
const uint32_t COIN_MIN_PULSE_US = 10000UL;
const uint32_t COIN_MAX_PULSE_US = 600000UL;
const uint32_t COIN_REFRACTORY_US = 80000UL;


uint32_t lastCountdownMillis = 0;
// Remaining time is tracked in remainingMs100, not lossy float seconds.

uint32_t buzzerUntil = 0;
uint8_t displayBrightness = 7;
uint16_t idleTriggerSeconds = 15; // 0-3600; separate EEPROM record preserves V1.x layout
uint64_t remainingMs100 = 0; // milliseconds times 100: exact speed scaling without float drift
uint32_t lastRecoveryCheckpoint = 0;
uint32_t chimePlayedMs = 0;
uint32_t lastCoin = 0;

DisplayManager displayUnit;
File uploadFile;
bool uploadSucceeded = false;
String uploadMessage = "No upload received";

// Non-blocking chime scheduler
enum class ChimeKind : uint8_t { None, Welcome, Coin, NearEnd, Timeout, Manual };
// Explicit prototype required by Arduino sketch auto-prototype generation.
void queuePattern(const std::vector<int>& freqs, const std::vector<int>& durs, ChimeKind kind);
enum class ChimeSource : uint8_t { None, Ram, Progmem };

std::vector<int> chimeFreqs;
std::vector<int> chimeDurs;
const uint16_t* progmemChimeFreqs = nullptr;
const uint16_t* progmemChimeDurs = nullptr;
size_t progmemChimeCount = 0;
ChimeSource chimeSource = ChimeSource::None;
ChimeKind currentChime = ChimeKind::None;
uint32_t chimeStepStartedAt = 0;
uint32_t chimeStepDurationMs = 0;
bool chimePlaying = false;
size_t chimeIndex = 0;
uint32_t lastNearEndStartedAt = 0;

// sales counters
uint32_t salesOverall = 0;
uint32_t salesToday = 0;
uint32_t salesMonth = 0;
uint32_t salesDayKey = 0;
uint32_t salesMonthKey = 0;

// Separate auth area does not change the legacy PersistentState layout.
// EEPROM 384..391 is the existing V1.4 idle preference.
// 392..399: coin-slot enable policy; 400..411: PC-switch policy;
// 416..419: pin-map migration marker. None overlaps old paid-time data.
const int CS_PREF_OFFSET = 392;
const int POWER_PREF_OFFSET = 400;
const int PINMAP_OFFSET = 416;
const uint32_t CS_PREF_MAGIC = 0x43533135UL;
const uint32_t POWER_PREF_MAGIC = 0x50573135UL;
const uint32_t PINMAP_MAGIC = 0x504D3135UL;
struct CsPref { uint32_t magic; uint8_t enabled; uint8_t activeHigh; uint8_t inverted; uint8_t reserved; };
struct PowerPref { uint32_t magic; uint16_t grace; uint16_t pulse; uint16_t inverseGrace; uint16_t inversePulse; };
static_assert(sizeof(CsPref) == 8 && sizeof(PowerPref) == 12, "Power config packing changed");
static_assert(PINMAP_OFFSET + sizeof(uint32_t) <= 512, "Power config exceeds EEPROM");
void loadPowerAndCoinPrefs() {
  CsPref cs; EEPROM.get(CS_PREF_OFFSET, cs);
  if (cs.magic == CS_PREF_MAGIC && cs.enabled <= 1 && cs.activeHigh <= 1 &&
      cs.inverted == (uint8_t)~(cs.enabled | (cs.activeHigh << 1))) {
    csEnabled = cs.enabled != 0;
    csActiveHigh = cs.activeHigh != 0;
  } else { csEnabled = true; csActiveHigh = true; }
  PowerPref p; EEPROM.get(POWER_PREF_OFFSET, p);
  if (p.magic == POWER_PREF_MAGIC && p.grace <= 3600 &&
      p.pulse >= 100 && p.pulse <= 1000 &&
      (uint16_t)(p.grace ^ p.inverseGrace) == 0xffffU &&
      (uint16_t)(p.pulse ^ p.inversePulse) == 0xffffU) {
    shutdownGraceSeconds = p.grace;
    pwrPulseMilliseconds = p.pulse;
  } else { shutdownGraceSeconds = 120; pwrPulseMilliseconds = 250; }
}
void saveCsPref() {
  const CsPref cs = { CS_PREF_MAGIC, (uint8_t)csEnabled, (uint8_t)csActiveHigh,
                      (uint8_t)~((uint8_t)csEnabled | ((uint8_t)csActiveHigh << 1)), 0 };
  EEPROM.put(CS_PREF_OFFSET,cs); EEPROM.commit();
}
void savePowerPref() {
  const PowerPref p = { POWER_PREF_MAGIC, shutdownGraceSeconds, pwrPulseMilliseconds,
                        (uint16_t)~shutdownGraceSeconds, (uint16_t)~pwrPulseMilliseconds };
  EEPROM.put(POWER_PREF_OFFSET,p); EEPROM.commit();
}
const uint32_t AUTH_MAGIC = 0x424C415AUL; // BLAZ
// Versioned idle preference is stored outside the legacy PersistentState
// and auth record, preserving paid time and sales when upgrading V1.2/V1.3.
const int IDLE_EEPROM_OFFSET = 384;
const uint32_t IDLE_EEPROM_MAGIC = 0x49444C45UL; // "IDLE"
struct IdlePreferences {
  uint32_t magic;
  uint16_t triggerSeconds;
  uint16_t invertedTriggerSeconds;
};
static_assert(sizeof(IdlePreferences) == 8, "Unexpected idle record size");
static_assert(IDLE_EEPROM_OFFSET + sizeof(IdlePreferences) <= 512,
              "Idle preferences exceed EEPROM allocation");

void loadIdlePreferences() {
  IdlePreferences pref;
  EEPROM.get(IDLE_EEPROM_OFFSET, pref);
  if (pref.magic == IDLE_EEPROM_MAGIC &&
      pref.triggerSeconds <= 3600 &&
      (uint16_t)(pref.triggerSeconds ^ pref.invertedTriggerSeconds) == 0xFFFFU) {
    idleTriggerSeconds = pref.triggerSeconds;
  } else {
    idleTriggerSeconds = 15; // Old firmware defaults to 15 seconds.
  }
}

void saveIdlePreferences() {
  const IdlePreferences pref = {
    IDLE_EEPROM_MAGIC, idleTriggerSeconds, (uint16_t)~idleTriggerSeconds
  };
  EEPROM.put(IDLE_EEPROM_OFFSET, pref);
  EEPROM.commit();
}

const int AUTH_EEPROM_OFFSET = 320;
struct AuthState { uint32_t magic; char pass[33]; uint32_t checksum; };
AuthState authState;
char adminPassword[33] = "blaze-admin";
// Checksum always covers the single persisted auth record. A no-argument
// signature avoids exposing an .ino-defined struct to Arduino's automatically
// generated function prototypes (which may be inserted before the struct).
uint32_t authChecksum() {
  uint32_t h = 2166136261UL;
  const uint8_t* bytes = reinterpret_cast<const uint8_t*>(&authState);
  for (size_t i = 0; i < sizeof(authState.magic) + sizeof(authState.pass); ++i) {
    h = (h ^ bytes[i]) * 16777619UL;
  }
  return h;
}
void saveAdminPassword() {
  memset(&authState, 0, sizeof(authState));
  authState.magic = AUTH_MAGIC;
  strncpy(authState.pass, adminPassword, sizeof(authState.pass)-1);
  authState.checksum = authChecksum();
  EEPROM.put(AUTH_EEPROM_OFFSET, authState);
  EEPROM.commit();
}
void loadAdminPassword() {
  EEPROM.get(AUTH_EEPROM_OFFSET, authState);
  authState.pass[sizeof(authState.pass)-1]='\0';
  if (authState.magic != AUTH_MAGIC || authState.checksum != authChecksum() ||
      strlen(authState.pass)<10 || strlen(authState.pass)>32) {
    strcpy(adminPassword,"blaze-admin");
    saveAdminPassword();
  } else { strcpy(adminPassword,authState.pass); }
}
bool requireAdmin() {
  if (server.authenticate("admin",adminPassword)) return true;
  server.requestAuthentication();
  return false;
}


// Forward declarations used before their definitions. Arduino usually
// auto-generates these for .ino files, but explicit declarations make the
// sketch safer to move between build systems.
void savePersistentState();
void updateBuzzer();
void stopChime();
void resetTimer();
// Declare functions with custom parameter types explicitly so Arduino does not
// synthesize prototypes in an unsafe location in .ino translation units.
void queuePattern(const std::vector<int>& freqs, const std::vector<int>& durs,
                  ChimeKind kind = ChimeKind::Manual);
bool tryUploadedChime(const char* basename, ChimeKind kind);
void queueProgmemPattern(const uint16_t* freqs, const uint16_t* durs, size_t count, ChimeKind kind);

// ------------------------------
// Utilities
// ------------------------------
String formatTimeMMSS(uint32_t totalSeconds) {
  uint32_t mm = totalSeconds / 60;
  uint32_t ss = totalSeconds % 60;

  String s;
  if (mm < 10) s += "0";
  s += String(mm);
  s += ":";
  if (ss < 10) s += "0";
  s += String(ss);

  return s;
}

String htmlEscape(String input) {
  input.replace("&", "&amp;");
  input.replace("\"", "&quot;");
  input.replace("<", "&lt;");
  input.replace(">", "&gt;");
  return input;
}

// Validate AP credentials before storing them. ESP8266 softAP WPA passwords
// should be 8..63 characters. An empty password means an open AP.
bool apConfigIsValid(const String& name, const String& password) {
  if (name.length() < 1 || name.length() > 32) return false;
  if (password.length() == 0) return true;
  return password.length() >= 8 && password.length() <= 63;
}

bool pinSetIsUnique(uint8_t c, uint8_t r1, uint8_t r2, uint8_t bz, uint8_t clk, uint8_t dio) {
  uint8_t pins[] = { c, r1, r2, bz, clk, dio };
  for (uint8_t i = 0; i < 6; i++) {
    if (pins[i] > 16) return false;
    if (pins[i] == 1 || pins[i] == 3) return false; // UART serial reserved
    // GPIO6..GPIO11 are normally wired to the ESP8266 SPI flash.
    if (pins[i] >= 6 && pins[i] <= 11) return false;
    for (uint8_t j = i + 1; j < 6; j++) {
      if (pins[i] == pins[j]) return false;
    }
  }
  // GPIO16 cannot support edge interrupts / input pull-up used by coin reader.
  if (c == 16 || c == 15 || c == 2) return false;
  // Never drive boot strapping GPIOs as relays.
  if (r1 == 0 || r1 == 2 || r1 == 15 || r2 == 0 || r2 == 2 || r2 == 15) return false;
  // Display lines must be regular ESP8266 GPIOs with normal input mode.
  if (clk == 0 || clk == 2 || clk == 15 || clk == 16 ||
      dio == 0 || dio == 2 || dio == 15 || dio == 16) return false;
  if (bz != FIXED_BUZZER_PIN) return false;
  // D7/GPIO13 belongs exclusively to CS enable; never assign it elsewhere.
  for (uint8_t i = 0; i < 6; ++i) if (pins[i] == CS_ENABLE_PIN) return false;
  return true;
}

// ------------------------------
// EEPROM load/save
// ------------------------------
void applyStateToRuntime() {
  // copy from persistent struct to runtime vars
  // EEPROM may contain stale/corrupt bytes even when the magic matches.
  // Copy defensively and force NUL termination.
  strncpy(AP_NAME, state.apName, sizeof(AP_NAME) - 1);
  AP_NAME[sizeof(AP_NAME) - 1] = '\0';
  strncpy(AP_PASSWORD, state.apPassword, sizeof(AP_PASSWORD) - 1);
  AP_PASSWORD[sizeof(AP_PASSWORD) - 1] = '\0';

  coinPin = state.coinPin;
  relayPin = state.relayPin;
  relay2Pin = state.relay2Pin;
  buzzerPin = FIXED_BUZZER_PIN;
  displayClk = state.displayClk;
  displayDio = state.displayDio;

  coinActiveLow = state.coinActiveLow;
  relayActiveLow = state.relayActiveLow;
  relay2ActiveLow = state.relay2ActiveLow;
  buzzerActiveLow = state.buzzerActiveLow;

  addMinutes = state.addMinutes;
  addSeconds = state.addSeconds;
  warningSeconds = state.warningSeconds;
  chimeDurationSeconds = state.chimeDurationSeconds;
  countdownSpeedPercent = state.countdownSpeedPercent;

  remainingSeconds = state.remainingSeconds;
  timerRunning = state.timerRunning;
  salesOverall = state.salesOverall;
  salesToday = state.salesToday;
  salesMonth = state.salesMonth;
  salesDayKey = state.salesDayKey;
  salesMonthKey = state.salesMonthKey;
  // Old sketches left this byte at zero; treat zero as maximum brightness for recovery.
  displayBrightness = (state.displayBrightness >= 1 && state.displayBrightness <= 7) ? state.displayBrightness : 7;
  // Sanity check legacy fields without erasing counters.
  if (!apConfigIsValid(String(AP_NAME), String(AP_PASSWORD))) {
    strcpy(AP_NAME,"ESP8266-Control"); strcpy(AP_PASSWORD,"12345678");
  }
  if ((uint32_t)addMinutes*60UL + addSeconds == 0 || addMinutes > 180 || addSeconds > 59) {
    addMinutes=1; addSeconds=0;
  }
  if (warningSeconds>120) warningSeconds=10;
  if (chimeDurationSeconds<1 || chimeDurationSeconds>120) chimeDurationSeconds=30;
  if (countdownSpeedPercent>50) countdownSpeedPercent=0;
  if (remainingSeconds>604800UL) { remainingSeconds=0; timerRunning=false; }

}

void loadDefaults() {
  strcpy(AP_NAME, "ESP8266-Control");
  strcpy(AP_PASSWORD, "12345678");

  coinPin = 0;
  relayPin = 16;
  relay2Pin = 12;
  buzzerPin = FIXED_BUZZER_PIN;
  displayClk = 5;
  displayDio = 4;

  coinActiveLow = true;
  relayActiveLow = true;
  relay2ActiveLow = false;
  buzzerActiveLow = false;

  addMinutes = 1;
  addSeconds = 0;
  warningSeconds = 10;
  chimeDurationSeconds = 30;
  countdownSpeedPercent = 0;
  displayBrightness = 7;

  remainingSeconds = 0;
  timerRunning = false;

  salesOverall = 0;
  salesToday = 0;
  salesMonth = 0;
  salesDayKey = 0;
  salesMonthKey = 0;

  memset(&state, 0, sizeof(state));
  state.magic = EEPROM_MAGIC;
  strcpy(state.apName, AP_NAME);
  strcpy(state.apPassword, AP_PASSWORD);

  state.coinPin = coinPin;
  state.relayPin = relayPin;
  state.relay2Pin = relay2Pin;
  state.buzzerPin = FIXED_BUZZER_PIN;
  state.displayClk = displayClk;
  state.displayDio = displayDio;

  state.coinActiveLow = coinActiveLow;
  state.relayActiveLow = relayActiveLow;
  state.relay2ActiveLow = relay2ActiveLow;
  state.buzzerActiveLow = buzzerActiveLow;

  state.addMinutes = addMinutes;
  state.addSeconds = addSeconds;
  state.warningSeconds = warningSeconds;
  state.chimeDurationSeconds = chimeDurationSeconds;
  state.countdownSpeedPercent = countdownSpeedPercent;

  state.remainingSeconds = remainingSeconds;
  state.timerRunning = timerRunning;
  state.salesOverall = salesOverall;
  state.salesToday = salesToday;
  state.salesMonth = salesMonth;
  state.salesDayKey = salesDayKey;
  state.salesMonthKey = salesMonthKey;
  state.displayBrightness = displayBrightness;
}

void loadPersistentState() {
  EEPROM.begin(512);
  EEPROM.get(0, state);

  if (state.magic != EEPROM_MAGIC) {
    loadDefaults();
    savePersistentState();
    return;
  }

  applyStateToRuntime();
}

void migratePinMapOnce() {
  uint32_t marker = 0;
  EEPROM.get(PINMAP_OFFSET, marker);
  if (marker == PINMAP_MAGIC) return;
  // Only remap GPIOs, preserving time, sales, Wi-Fi and polarity preferences.
  coinPin=0; relayPin=16; relay2Pin=12; displayClk=5; displayDio=4;
  buzzerPin=FIXED_BUZZER_PIN;
  savePersistentState();
  EEPROM.put(PINMAP_OFFSET,PINMAP_MAGIC); EEPROM.commit();
  Serial.println(F("[GPIO] Migrated to D0=cutoff, D6=PWR_SW, D7=CS, D1/D2=TM1637"));
}

void savePersistentState() {
  state.magic = EEPROM_MAGIC;
  strcpy(state.apName, AP_NAME);
  strcpy(state.apPassword, AP_PASSWORD);

  state.coinPin = coinPin;
  state.relayPin = relayPin;
  state.relay2Pin = relay2Pin;
  state.buzzerPin = FIXED_BUZZER_PIN;
  state.displayClk = displayClk;
  state.displayDio = displayDio;

  state.coinActiveLow = coinActiveLow;
  state.relayActiveLow = relayActiveLow;
  state.relay2ActiveLow = relay2ActiveLow;
  state.buzzerActiveLow = buzzerActiveLow;

  state.addMinutes = addMinutes;
  state.addSeconds = addSeconds;
  state.warningSeconds = warningSeconds;
  state.chimeDurationSeconds = chimeDurationSeconds;
  state.countdownSpeedPercent = countdownSpeedPercent;

  state.remainingSeconds = remainingSeconds;
  state.timerRunning = timerRunning;
  state.salesOverall = salesOverall;
  state.salesToday = salesToday;
  state.salesMonth = salesMonth;
  state.salesDayKey = salesDayKey;
  state.salesMonthKey = salesMonthKey;

  state.displayBrightness = displayBrightness;
  EEPROM.put(0, state);
  EEPROM.commit();
}

bool pinsAreValid() {
  return pinSetIsUnique(coinPin, relayPin, relay2Pin, buzzerPin, displayClk, displayDio);
}

void revertToDefaults() {
  // Recover only the hardware map. Do not destroy sales or a paid timer just
  // because a stored pin assignment became invalid.
  coinPin = 0;
  relayPin = 16;
  relay2Pin = 12;
  buzzerPin = FIXED_BUZZER_PIN;
  displayClk = 5;
  displayDio = 4;

  coinActiveLow = true;
  relayActiveLow = true;
  relay2ActiveLow = false;
  buzzerActiveLow = false;

  savePersistentState();
}


// ------------------------------
// Display: periodic refresh + boot/test sequence (DisplayManager.h)
// ------------------------------
void setupDisplay() {
  displayUnit.begin(displayClk, displayDio, displayBrightness);
}
void showRemaining() { displayUnit.update(remainingSeconds); }

// ------------------------------
// Relays + Buzzer
// ------------------------------
void setRelay1(bool on) {
  relayState = on;
  digitalWrite(relayPin, (on ^ relayActiveLow) ? HIGH : LOW);
  pinMode(relayPin, OUTPUT);
}

void setRelay2(bool on) {
  relay2State = on;
  digitalWrite(relay2Pin, (on ^ relay2ActiveLow) ? HIGH : LOW);
  pinMode(relay2Pin, OUTPUT);
}

void setRelays(bool on) {
  // Compatibility wrapper: time credit can energize only Relay 1.
  setRelay1(on);
}

void writeCsEnable() {
  // Low-cost D7 gate must drive a transistor, optocoupler or EN pin,
  // never the power load of a coin acceptor directly.
  digitalWrite(CS_ENABLE_PIN, (localCoinsAllowed() == csActiveHigh) ? HIGH : LOW);
  pinMode(CS_ENABLE_PIN, OUTPUT);
}

void setCsEnabled(bool enable) {
  // Drain completed pulses while the acceptor is still permitted.
  // If switching OFF, any later pulses (including noise) are discarded.
  if (!enable) {
    noInterrupts();
    coinInputAllowed = false;
    coinQueued = 0;
    coinPulseStartUs = 0;
    interrupts();
  }
  csEnabled = enable;
  writeCsEnable();
  if (enable) {
    noInterrupts();
    coinQueued = 0;
    coinPulseStartUs = 0;
    coinInputAllowed = localCoinsAllowed();
    interrupts();
  }
}

bool powerPulseAllowed() {
  uint32_t now = millis();
  return !powerPulseActive &&
         (!powerPulseEverSent || (uint32_t)(now-lastPowerPulse) >= 5000UL);
}

bool pulsePowerButton() {
  if (!powerPulseAllowed()) return false;
  setRelay2(true);
  powerPulseStarted = millis();
  lastPowerPulse = powerPulseStarted;
  powerPulseEverSent = true;
  powerPulseActive = true;
  return true;
}

void onPaidTimeGranted() {
  pcShutdownPending = false; // credit cancels countdown BEFORE PWR_SW is pressed
  // No power-state sensor: this is an estimate, not a measured state.
  // If pulse was just sent, avoid pressing PWR_SW again during cooldown.
  if (!pcExpectedOn && pulsePowerButton()) pcExpectedOn = true;
}

void updatePcPowerControl() {
  uint32_t now=millis();
  if (powerPulseActive && (uint32_t)(now-powerPulseStarted) >= pwrPulseMilliseconds) {
    setRelay2(false);
    powerPulseActive=false;
  }
  if (timerRunning && remainingSeconds > 0 && !pcExpectedOn &&
      !pcShutdownPending && pulsePowerButton()) pcExpectedOn=true;
  if (pcShutdownPending && (uint32_t)(now-shutdownStarted) >=
      (uint32_t)shutdownGraceSeconds*1000UL && !powerPulseActive) {
    if (pcExpectedOn) {
      if (!pulsePowerButton()) return; // retry only after cooldown
      pcExpectedOn=false;
    }
    pcShutdownPending=false; // never issue multiple shutdown pulses
  }
}

void schedulePcShutdown() {
  if (!pcExpectedOn) return; // Never turn a believed-OFF PC ON at expiry
  pcShutdownPending=true;
  shutdownStarted=millis();
}


void setBuzzer(bool on) {
  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, (on ^ buzzerActiveLow) ? HIGH : LOW);
}

void noBuzzer() {
  noTone(buzzerPin);
  setBuzzer(false);
}

// ------------------------------
// Chime scheduler
// ------------------------------
void stopChime() {
  chimePlaying = false;
  chimePlayedMs = 0;
  chimeIndex = 0;
  chimeSource = ChimeSource::None;
  currentChime = ChimeKind::None;
  progmemChimeFreqs = nullptr;
  progmemChimeDurs = nullptr;
  progmemChimeCount = 0;
  noTone(buzzerPin);
  setBuzzer(false);
}

size_t activeChimeCount() {
  if (chimeSource == ChimeSource::Progmem) return progmemChimeCount;
  if (chimeSource == ChimeSource::Ram) return chimeFreqs.size();
  return 0;
}

uint16_t activeChimeFrequency(size_t index) {
  if (chimeSource == ChimeSource::Progmem) {
    return pgm_read_word(&progmemChimeFreqs[index]);
  }
  return (uint16_t)chimeFreqs[index];
}

uint16_t activeChimeDuration(size_t index) {
  if (chimeSource == ChimeSource::Progmem) {
    return pgm_read_word(&progmemChimeDurs[index]);
  }
  return (uint16_t)chimeDurs[index];
}

void beginCurrentChimeStep() {
  if (!chimePlaying || chimeIndex >= activeChimeCount()) {
    stopChime();
    return;
  }

  uint16_t frequency = activeChimeFrequency(chimeIndex);
  uint32_t maxMs = (uint32_t)chimeDurationSeconds * 1000UL;
  if (chimePlayedMs >= maxMs) { stopChime(); return; }
  chimeStepDurationMs = activeChimeDuration(chimeIndex);
  if (chimeStepDurationMs > maxMs - chimePlayedMs)
    chimeStepDurationMs = maxMs - chimePlayedMs;
  chimeStepStartedAt = millis();

  if (frequency == 0) {
    noTone(buzzerPin);  // A zero-frequency entry is a deliberate rest.
    setBuzzer(false);
  } else {
    tone(buzzerPin, frequency, chimeStepDurationMs + 10UL);
  }
}

void queuePattern(const std::vector<int>& freqs, const std::vector<int>& durs,
                  ChimeKind kind) {
  if (freqs.empty() || durs.empty() || freqs.size() != durs.size()) {
    stopChime();
    return;
  }

  stopChime();
  chimeFreqs.clear();
  chimeDurs.clear();

  // Uploaded/custom patterns retain the configurable safety limit.
  uint32_t maxDurationMs = (uint32_t)chimeDurationSeconds * 1000UL;
  uint32_t totalMs = 0;

  chimeFreqs.reserve(freqs.size());
  chimeDurs.reserve(durs.size());

  for (size_t i = 0; i < freqs.size(); i++) {
    if (totalMs >= maxDurationMs) break;

    int frequency = freqs[i];
    uint32_t duration = durs[i] > 0 ? (uint32_t)durs[i] : 0;
    if (frequency < 0 || frequency > 5000 || duration == 0) continue;
    if (totalMs + duration > maxDurationMs) duration = maxDurationMs - totalMs;
    if (duration == 0) break;

    chimeFreqs.push_back(frequency);
    chimeDurs.push_back((int)duration);
    totalMs += duration;
  }

  if (chimeFreqs.empty()) {
    stopChime();
    return;
  }

  chimeSource = ChimeSource::Ram;
  chimePlayedMs = 0;
  currentChime = kind;
  chimeIndex = 0;
  chimePlaying = true;
  beginCurrentChimeStep();
}

void queueProgmemPattern(const uint16_t* freqs, const uint16_t* durs,
                         size_t count, ChimeKind kind) {
  if (!freqs || !durs || count == 0) {
    stopChime();
    return;
  }

  stopChime();
  progmemChimeFreqs = freqs;
  progmemChimeDurs = durs;
  progmemChimeCount = count;
  chimeSource = ChimeSource::Progmem;
  chimePlayedMs = 0;
  currentChime = kind;
  chimeIndex = 0;
  chimePlaying = true;
  beginCurrentChimeStep();
}

void updateChimePlayer() {
  if (!chimePlaying) return;

  uint32_t now = millis();
  if ((uint32_t)(now - chimeStepStartedAt) < chimeStepDurationMs) return;

  chimePlayedMs += chimeStepDurationMs;
  chimeIndex++;
  if (chimeIndex >= activeChimeCount()) {
    stopChime();
    return;
  }

  beginCurrentChimeStep();
}

// ------------------------------
// Chime parser
// supports:
  // 1) note text format: frequency,duration;frequency,duration;...
  // 2) 8-bit mono WAV files: /welcome.wav, /coin.wav, /warning.wav, /timeup.wav
// ------------------------------
std::vector<int> parsedFreqs;
std::vector<int> parsedDurs;

bool parseNoteListFile(const String& path, std::vector<int>& outFreqs, std::vector<int>& outDurs) {
  outFreqs.clear();
  outDurs.clear();

  if (!LittleFS.exists(path)) return false;

  File f = LittleFS.open(path, "r");
  if (!f) return false;

  String data = f.readString();
  f.close();

  data.trim();
  if (data.length() == 0) return false;

  int start = 0;
  const int dataLength = (int)data.length();
  while (start < dataLength) {
    int end = data.indexOf(';', start);
    if (end < 0) end = dataLength;

    String token = data.substring(start, end);
    token.trim();

    if (token.length() > 0) {
      int comma = token.indexOf(',');
      if (comma > 0) {
        String freqStr = token.substring(0, comma);
        String durStr = token.substring(comma + 1);

        int freq = freqStr.toInt();
        int dur = durStr.toInt();

        if ((freq == 0 || (freq >= 20 && freq <= 5000)) && dur >= 10 && dur <= 10000) {
          outFreqs.push_back(freq);
          outDurs.push_back(dur);
          if (outFreqs.size() >= 300) break;
        }
      }
    }

    if (end >= dataLength) break;
    start = end + 1;
  }

  return outFreqs.size() > 0;
}

bool parseWave8BitMonoFile(const String& path, std::vector<int>& outFreqs, std::vector<int>& outDurs) {
  outFreqs.clear();
  outDurs.clear();

  if (!LittleFS.exists(path)) return false;

  File f = LittleFS.open(path, "r");
  if (!f) return false;

  char id[5] = {0};
  uint8_t tmp[4];

  if (f.readBytes(id, 4) != 4 || strncmp(id, "RIFF", 4) != 0) {
    f.close();
    return false;
  }

  if (f.readBytes((char*)tmp, 4) != 4) {
    f.close();
    return false;
  }

  char wave[5] = {0};
  if (f.readBytes(wave, 4) != 4 || strncmp(wave, "WAVE", 4) != 0) {
    f.close();
    return false;
  }

  uint32_t dataOffset = 0;
  uint32_t dataSize = 0;
  uint32_t sampleRate = 0;
  uint16_t audioFormat = 0;
  uint16_t numChannels = 0;
  uint16_t bitsPerSample = 0;
  bool haveFmt = false;

  while (f.available() >= 8) {
    char chunkId[5] = {0};
    if (f.readBytes(chunkId, 4) != 4) break;
    if (f.readBytes((char*)tmp, 4) != 4) break;

    uint32_t chunkSize = ((uint32_t)tmp[3] << 24) |
                         ((uint32_t)tmp[2] << 16) |
                         ((uint32_t)tmp[1] << 8)  |
                         (uint32_t)tmp[0];

    uint32_t chunkDataStart = f.position();

    if (strncmp(chunkId, "fmt ", 4) == 0) {
      if (chunkSize < 16) {
        f.close();
        return false;
      }

      uint8_t fmtBuf[16];
      if (f.read(fmtBuf, 16) != 16) {
        f.close();
        return false;
      }

      audioFormat = (uint16_t)fmtBuf[0] | ((uint16_t)fmtBuf[1] << 8);
      numChannels = (uint16_t)fmtBuf[2] | ((uint16_t)fmtBuf[3] << 8);
      sampleRate = (uint32_t)fmtBuf[4] |
                   ((uint32_t)fmtBuf[5] << 8) |
                   ((uint32_t)fmtBuf[6] << 16) |
                   ((uint32_t)fmtBuf[7] << 24);
      bitsPerSample = (uint16_t)fmtBuf[14] | ((uint16_t)fmtBuf[15] << 8);
      haveFmt = true;
    } else if (strncmp(chunkId, "data", 4) == 0) {
      dataOffset = chunkDataStart;
      dataSize = chunkSize;
      break;
    }

    // RIFF chunks are padded to an even byte boundary. Seek to the end of
    // this chunk rather than adding chunkSize after already reading data.
    uint32_t nextChunk = chunkDataStart + chunkSize + (chunkSize & 1U);
    if (!f.seek(nextChunk, SeekSet)) {
      f.close();
      return false;
    }
  }

  f.close();

  if (!haveFmt || audioFormat != 1 || numChannels != 1 ||
      bitsPerSample != 8 || sampleRate == 0 || dataSize == 0) {
    return false;
  }

  File wav = LittleFS.open(path, "r");
  if (!wav) return false;

  const uint32_t maxSteps = 300;
  uint32_t step = (dataSize + maxSteps - 1) / maxSteps;
  if (step < 1) step = 1;

  uint32_t durationMs = (step * 1000UL + sampleRate / 2) / sampleRate;
  if (durationMs < 8) durationMs = 8;
  if (durationMs > 100) durationMs = 100;

  outFreqs.reserve(maxSteps);
  outDurs.reserve(maxSteps);

  for (uint32_t i = 0; i < dataSize && outFreqs.size() < maxSteps; i += step) {
    if (!wav.seek(dataOffset + i, SeekSet)) break;

    int sample = wav.read();
    if (sample < 0) break;

    int centered = sample - 128;
    int amplitude = abs(centered);

    // This is intentionally a buzzer-safe approximation, not WAV playback.
    // Stronger sample amplitudes are mapped to higher buzzer frequencies.
    int freq = 220 + amplitude * 12;
    if (freq > 1800) freq = 1800;

    outFreqs.push_back(freq);
    outDurs.push_back((int)durationMs);
  }

  wav.close();
  return !outFreqs.empty();
}

bool loadChimePattern(const String& path, std::vector<int>& outFreqs, std::vector<int>& outDurs) {
  if (path.endsWith(".wav")) {
    return parseWave8BitMonoFile(path, outFreqs, outDurs);
  }
  return parseNoteListFile(path, outFreqs, outDurs);
}

// ------------------------------
// More fun welcome / warning / near-ending tones
// ------------------------------
// Keep insert coin tone as-is (liked already)
bool tryUploadedChime(const char* basename, ChimeKind kind) {
  String txt = String("/")+basename+".txt";
  String wav = String("/")+basename+".wav";
  if (LittleFS.exists(txt) && loadChimePattern(txt,parsedFreqs,parsedDurs)) {
    queuePattern(parsedFreqs,parsedDurs,kind); return true;
  }
  if (LittleFS.exists(wav) && loadChimePattern(wav,parsedFreqs,parsedDurs)) {
    queuePattern(parsedFreqs,parsedDurs,kind); return true;
  }
  return false;
}
void playCoinChime() {
  if (tryUploadedChime("coin",ChimeKind::Coin)) return;
  // Keep the original insert-coin chime exactly as requested.
  std::vector<int> freqs = { 880, 1180, 880, 1180 };
  std::vector<int> durs  = { 110, 150, 110, 180 };
  queuePattern(freqs, durs, ChimeKind::Coin);
}

void playWelcomeChime() {
  if (tryUploadedChime("welcome",ChimeKind::Welcome)) return;
  // Compact GPIO14 buzzer approximation of tacos.mp3, capped at 40 seconds.
  queueProgmemPattern(tacosFreq, tacosDur, tacosCount, ChimeKind::Welcome);
}

void playWarningChime() {
  if (tryUploadedChime("warning",ChimeKind::Manual)) return;
  // Manual warning uses the same supplied faa.mp3-derived pattern.
  queueProgmemPattern(faaFreq, faaDur, faaCount, ChimeKind::Manual);
}

void playNearEndingChime() {
  if (tryUploadedChime("warning",ChimeKind::NearEnd)) { lastNearEndStartedAt=millis(); return; }
  queueProgmemPattern(faaFreq, faaDur, faaCount, ChimeKind::NearEnd);
  lastNearEndStartedAt = millis();
}

void playTimeEndingChime() {
  if (tryUploadedChime("timeup",ChimeKind::Timeout)) return;
  // Plays the complete timeout.mp3-derived sequence. It is interrupted only
  // when another chime is deliberately started, such as inserting a coin.
  queueProgmemPattern(timeoutFreq, timeoutDur, timeoutCount, ChimeKind::Timeout);
}

// ------------------------------
// Timer, sales, and interrupt-assisted coin pulse accounting
// ------------------------------
void startTimerFromSeconds(uint32_t secs) {
  if (secs == 0) { resetTimer(); return; }
  stopChime();
  remainingSeconds = secs;
  remainingMs100 = (uint64_t)secs * 100000ULL;
  timerRunning = true;
  lastCountdownMillis = millis();
  setRelays(true);
  onPaidTimeGranted();
  savePersistentState();
}
void addCoinTime() {
  const uint32_t secs = (uint32_t)addMinutes * 60UL + addSeconds;
  if (secs == 0) return;
  const uint64_t add = (uint64_t)secs * 100000ULL;
  const uint64_t cap = (uint64_t)604800UL * 100000ULL; // 7-day session upper bound
  remainingMs100 = (remainingMs100 + add > cap) ? cap : remainingMs100 + add;
  remainingSeconds = (uint32_t)((remainingMs100 + 99999ULL) / 100000ULL);
  timerRunning = true;
  lastCountdownMillis = millis();
  setRelays(true);
  onPaidTimeGranted();
  lastCoin = millis();
  lastNearEndStartedAt = lastCoin;
  stopChime();
  playCoinChime();
  // Commit AFTER incrementSales() so both paid time and coin count share one write.
}
void updateTimerState() {
  if (!timerRunning) return;
  const uint32_t now = millis();
  const uint32_t elapsed = (uint32_t)(now - lastCountdownMillis);
  if (!elapsed) return;
  lastCountdownMillis = now;
  const uint64_t debit = (uint64_t)elapsed * (100U + countdownSpeedPercent);
  if (debit >= remainingMs100) {
    remainingMs100=0; remainingSeconds=0; timerRunning=false;
    setRelays(false); schedulePcShutdown(); playTimeEndingChime(); savePersistentState();
    return;
  }
  remainingMs100 -= debit;
  remainingSeconds = (uint32_t)((remainingMs100 + 99999ULL) / 100000ULL);
  if (remainingSeconds <= warningSeconds && remainingSeconds > 0) {
    if (!chimePlaying && (uint32_t)(now-lastNearEndStartedAt)>=2000UL) playNearEndingChime();
  }
  // A bounded checkpoint reduces staleness after power loss at a flash-wear cost.
  // 5min checkpoints, in addition to transactional coin writes.
  if ((uint32_t)(now-lastRecoveryCheckpoint)>=300000UL) {
    lastRecoveryCheckpoint=now; savePersistentState();
  }
}
void resetTimer() {
  stopChime(); remainingSeconds=0; remainingMs100=0; timerRunning=false;
  setRelays(false); schedulePcShutdown(); savePersistentState();
}
// Manual admin time adjustment: no coin event, no sale/count increment.
// Called after settling elapsed countdown and pending coins from /api/time.
bool applyManualTime(bool replace, uint32_t inputSeconds) {
  uint64_t targetUnits = 0;
  if (!blazeComputeManualTarget(replace, remainingMs100, inputSeconds, targetUnits)) return false;
  stopChime();
  remainingMs100 = targetUnits;
  remainingSeconds = (uint32_t)((remainingMs100 + 99999ULL) / 100000ULL);
  timerRunning = true;
  const uint32_t now = millis();
  lastCountdownMillis = now;
  lastRecoveryCheckpoint = now;
  lastNearEndStartedAt = now;
  setRelays(true);
  onPaidTimeGranted();
  showRemaining();
  savePersistentState(); // Single commit, also restores the manually granted time after restart.
  Serial.printf("[TIME] Manual %s: +/=%lu s, now %lu s remaining (no sale)\n",
                replace ? "SET" : "ADD", (unsigned long)inputSeconds,
                (unsigned long)remainingSeconds);
  return true;
}

void incrementSales() {
  // No calendar RTC: keep legacy bucket values rather than misreporting uptime
  // as a real day or month. A DS3231 is required for trustworthy date sales.
  if (salesOverall<UINT32_MAX) salesOverall++;
  if (salesToday<UINT32_MAX) salesToday++;
  if (salesMonth<UINT32_MAX) salesMonth++;
  savePersistentState();
}
void clearSales() {
  salesOverall=0; salesToday=0; salesMonth=0;
  salesDayKey=0; salesMonthKey=0;
  savePersistentState();
}

void IRAM_ATTR onCoinEdge() {
  if (!coinInputAllowed) { coinPulseStartUs=0; return; }
  const uint32_t now = micros();
  const bool active = (digitalRead(coinPin) == (coinActiveLow ? LOW : HIGH));
  if (active) {
    coinPulseStartUs=now;
    return;
  }
  const uint32_t started=coinPulseStartUs;
  coinPulseStartUs=0;
  if (!started) return;
  const uint32_t width=(uint32_t)(now-started);
  if (width<COIN_MIN_PULSE_US || width>COIN_MAX_PULSE_US) return;
  if ((uint32_t)(now-lastAcceptedPulseUs)<COIN_REFRACTORY_US) return;
  lastAcceptedPulseUs=now;
  if (coinQueued<250) coinQueued++;
}
void configureCoinInput() {
  pinMode(coinPin,coinActiveLow?INPUT_PULLUP:INPUT);
  coinPulseStartUs=0; coinQueued=0;
  attachInterrupt(digitalPinToInterrupt(coinPin),onCoinEdge,CHANGE);
}
void handleCoinInput() {
  uint8_t count=0;
  noInterrupts(); count=coinQueued; coinQueued=0; interrupts();
  if (!localCoinsAllowed()) return;
  for (uint8_t n=0;n<count;n++) { addCoinTime(); incrementSales(); }
}

// ------------------------------
// Web/API helper functions: UI is a static PROGMEM asset in WebUI.h
// ------------------------------
String jsonQuote(const String& value) {
  String s="\"";
  for (size_t i=0;i<value.length();i++) {
    char c=value[i];
    if (c=='"' || c=='\\') {s+='\\';s+=c;}
    else if ((uint8_t)c<32) s+=' ';
    else s+=c;
  }
  return s+'"';
}
void sendStatus() {
  String s; s.reserve(2100);
  s += F("{\"time\":");s+=jsonQuote(formatTimeMMSS(remainingSeconds));
  s += F(",\"remainingSeconds\":");s+=remainingSeconds;
  s += F(",\"timerRunning\":");s+=(timerRunning?"true":"false");
  s += F(",\"relay1On\":");s+=(relayState?"true":"false");
  s += F(",\"relay2On\":");s+=(relay2State?"true":"false");
  s += F(",\"csEnabled\":");s+=(localCoinsAllowed()?"true":"false");
  s += F(",\"csActiveHigh\":");s+=(csActiveHigh?"true":"false");
  s += F(",\"pcExpectedOn\":");s+=(pcExpectedOn?"true":"false");
  s += F(",\"shutdownPending\":");s+=(pcShutdownPending?"true":"false");
  s += F(",\"shutdownSecondsLeft\":");
  if (pcShutdownPending) {
    uint32_t passed = (uint32_t)(millis()-shutdownStarted)/1000UL;
    s += String(passed < shutdownGraceSeconds ? shutdownGraceSeconds-passed : 0);
  } else s += '0';
  s += F(",\"displayMode\":");s+=jsonQuote(displayUnit.mode());
  s += F(",\"interconRole\":");s+=(unsigned)interconConfig.role;
  s += F(",\"interconStaEnabled\":");s+=(interconConfig.staEnabled?"true":"false");
  s += F(",\"interconStaConnected\":");s+=(WiFi.status()==WL_CONNECTED?"true":"false");
  s += F(",\"interconConfigHealthy\":");s+=(interconConfigHealthy?"true":"false");
  s += F(",\"interconNodeName\":");s+=jsonQuote(String(interconConfig.nodeName));
  s += F(",\"interconStaSsid\":");s+=jsonQuote(String(interconConfig.staSsid));
  s += F(",\"interconStaIp\":");s+=jsonQuote(WiFi.status()==WL_CONNECTED?WiFi.localIP().toString():String("-"));
  s += F(",\"interconNodeId\":");s+=interconConfig.nodeId;
  s += F(",\"interconPeerCount\":");s+=interconPeerCount;
  s += F(",\"interconPeers\":[");
  for(size_t k=0;k<interconPeerCount;k++){
    if(k)s+=',';
    const InterconPeer &peer=interconPeers[k];
    s += F("{\"id\":");s+=peer.hello.nodeId;
    s += F(",\"name\":");s+=jsonQuote(String(peer.hello.name));
    s += F(",\"role\":");s+=peer.hello.role;
    s += F(",\"ip\":");s+=jsonQuote(peer.ip.toString());
    s += F(",\"seenSecondsAgo\":");s+=(uint32_t)(millis()-peer.lastSeen)/1000UL;
    s += '}';
  }
  s += ']';
  s += F(",\"ip\":");s+=jsonQuote(WiFi.softAPIP().toString());
  #define JNUM(KEY,VALUE) s+=F(",\"" KEY "\":");s+=String(VALUE)
  JNUM("uptimeSeconds",millis()/1000UL); JNUM("heap",ESP.getFreeHeap());
  JNUM("displayClk",displayClk);JNUM("displayDio",displayDio);JNUM("brightness",displayBrightness);JNUM("idleTriggerSeconds",idleTriggerSeconds);
  JNUM("coinPin",coinPin);JNUM("relayPin",relayPin);JNUM("relay2Pin",relay2Pin);
  JNUM("shutdownGraceSeconds",shutdownGraceSeconds);JNUM("pwrPulseMilliseconds",pwrPulseMilliseconds);
  JNUM("addMinutes",addMinutes);JNUM("addSeconds",addSeconds);
  JNUM("warningSeconds",warningSeconds);JNUM("speedPct",countdownSpeedPercent);
  JNUM("chimeDurationSeconds",chimeDurationSeconds);
  JNUM("salesOverall",salesOverall);JNUM("salesToday",salesToday);JNUM("salesMonth",salesMonth);
  #undef JNUM
  s += F(",\"apName\":");s+=jsonQuote(String(AP_NAME));
  s += F(",\"coinActiveLow\":");s+=(coinActiveLow?"true":"false");
  s += F(",\"relayActiveLow\":");s+=(relayActiveLow?"true":"false");
  s += F(",\"relay2ActiveLow\":");s+=(relay2ActiveLow?"true":"false");
  s += F(",\"buzzerActiveLow\":");s+=(buzzerActiveLow?"true":"false");
  s += '}';
  server.sendHeader("Cache-Control","no-store");
  server.send(200,"application/json",s);
}
void redirect() { server.sendHeader("Location","/");server.send(303,"text/plain",""); }
void reject(const String& reason,int code=400) { server.send(code,"text/plain",reason); }

// ------------------------------
// LittleFS upload, bounded and validated before replacing existing chimes
// ------------------------------
String uploadDestination;
uint32_t uploadLength=0;
const uint32_t MAX_UPLOAD_BYTES=65536UL;
void handleFileUpload() {
  HTTPUpload& upload = server.upload();
  if (!server.authenticate("admin",adminPassword)) return;
  if (upload.status==UPLOAD_FILE_START) {
    uploadSucceeded=false;uploadMessage="Upload rejected";uploadLength=0;uploadDestination="";
    String which=server.arg("patternName");
    if (which!="welcome" && which!="coin" && which!="warning" && which!="timeup") return;
    String name=String(upload.filename);name.toLowerCase();
    if (!name.endsWith(".txt") && !name.endsWith(".wav")) return;
    uploadDestination="/"+which+(name.endsWith(".wav")?".wav":".txt");
    if (LittleFS.exists("/upload.tmp")) LittleFS.remove("/upload.tmp");
    uploadFile=LittleFS.open("/upload.tmp","w");
    if (!uploadFile) {uploadMessage="Storage unavailable";return;}
    uploadMessage="Uploading";
  } else if (upload.status==UPLOAD_FILE_WRITE) {
    if (uploadFile) {
      if (uploadLength+upload.currentSize>MAX_UPLOAD_BYTES || uploadFile.write(upload.buf,upload.currentSize)!=upload.currentSize) {
        uploadFile.close();LittleFS.remove("/upload.tmp"); uploadMessage="Upload exceeds 64 KB or storage failed";
      } else uploadLength+=upload.currentSize;
    }
  } else if (upload.status==UPLOAD_FILE_END) {
    if (uploadFile) {
      uploadFile.close();
      if (uploadLength==0) {LittleFS.remove("/upload.tmp");uploadMessage="Empty file";return;}
      std::vector<int> freq,dur;
      bool valid=false;
      // The temporary name lacks an extension, so parse using the intended format.
      if (uploadDestination.endsWith(".wav")) valid=parseWave8BitMonoFile("/upload.tmp",freq,dur);
      else valid=parseNoteListFile("/upload.tmp",freq,dur);
      if (!valid) {LittleFS.remove("/upload.tmp"); uploadMessage="File has no valid tones or unsupported WAV format";return;}
      if (LittleFS.exists(uploadDestination)) LittleFS.remove(uploadDestination);
      if (!LittleFS.rename("/upload.tmp",uploadDestination)) {uploadMessage="Unable to commit uploaded file";return;}
      String alt=uploadDestination.substring(0,uploadDestination.lastIndexOf('.'))+(uploadDestination.endsWith(".wav")?".txt":".wav");
      if (LittleFS.exists(alt)) LittleFS.remove(alt);
      uploadSucceeded=true; uploadMessage="Upload saved; selected chime will use this file";
    }
  } else if (upload.status==UPLOAD_FILE_ABORTED) {
    if (uploadFile) uploadFile.close();
    LittleFS.remove("/upload.tmp");
    uploadSucceeded=false;uploadMessage="Upload cancelled";
  }
}

// ------------------------------
// Setup and HTTP endpoints
// ------------------------------
void setup() {
  Serial.begin(115200);Serial.println();
  Serial.println(F("[BLAZE] V1.6 AP+STA read-only INTERCON discovery; peer credit locked"));
  randomSeed(micros());
  bool fsReady=LittleFS.begin();
  loadInterconConfig(fsReady);
  if (!fsReady) Serial.println(F("[FS] LittleFS mount failed; custom chimes unavailable"));
  loadPersistentState();
  loadIdlePreferences();
  loadPowerAndCoinPrefs();
  loadAdminPassword();
  migratePinMapOnce();
  if (!pinsAreValid()) {
    Serial.println(F("[CONFIG] Unsafe/invalid pins; reverting to known default map"));
    revertToDefaults();
  }
  Serial.printf("[GPIO] Display CLK=%u DIO=%u; coin=%u; relays=%u,%u; buzzer=%u\n",
                 displayClk,displayDio,coinPin,relayPin,relay2Pin,buzzerPin);
  // Set OFF level before output direction to avoid relay glitches on initialization.
  digitalWrite(relayPin,relayActiveLow?HIGH:LOW);pinMode(relayPin,OUTPUT);relayState=false;
  digitalWrite(relay2Pin,relay2ActiveLow?HIGH:LOW);pinMode(relay2Pin,OUTPUT);relay2State=false;
  coinInputAllowed = false;
  writeCsEnable(); // Apply persisted night/closed state before coin IRQ attach.
  digitalWrite(buzzerPin,buzzerActiveLow?HIGH:LOW);pinMode(buzzerPin,OUTPUT);
  setupDisplay();
  displayUnit.setIdleDelaySeconds(idleTriggerSeconds);
  configureCoinInput();
  coinInputAllowed = localCoinsAllowed();
  // After any ESP reboot assume PC OFF; retain the last paid balance, PAUSED.
  // Restart countdown and request power-on only when a fresh credit is granted.
  pcExpectedOn = false; pcShutdownPending = false;
  if (remainingSeconds>0) {
    remainingMs100=(uint64_t)remainingSeconds*100000ULL;
    timerRunning=false;
    lastCountdownMillis=millis();
    setRelays(false);
    Serial.println(F("[RECOVERY] Saved time restored, paused. New credit resumes it."));
  } else {remainingSeconds=0;timerRunning=false;remainingMs100=0;setRelays(false);}
  lastRecoveryCheckpoint=millis();

  beginInterconNetwork();
  server.on("/",HTTP_GET,[](){if(!requireAdmin())return;server.send_P(200,PSTR("text/html"),WEB_UI);});
  server.on("/api/status",HTTP_GET,[](){if(!requireAdmin())return;sendStatus();});
  server.on("/display/test",HTTP_POST,[](){
    if(!requireAdmin())return;
    String mode=server.arg("mode");
    if(mode!="normal" && mode!="swapped") {reject("Expected normal or swapped");return;}
    displayUnit.beginTest(mode=="swapped");server.send(200,"text/plain","Display test started");
  });
  server.on("/display/default",HTTP_POST,[](){
    if(!requireAdmin())return;
    if(server.arg("confirm")!="yes") {reject("Confirmation required");return;}
    if(timerRunning) {reject("Finish paid session before changing display pins",409);return;}
    if(!pinSetIsUnique(coinPin,relayPin,relay2Pin,buzzerPin,5,4)) {
      reject("GPIO5/4 overlap another device. Reconfigure pins safely first",409);return;
    }
    displayClk=5;displayDio=4;displayBrightness=7;
    savePersistentState();setupDisplay();
    displayUnit.setIdleDelaySeconds(idleTriggerSeconds);
    server.send(200,"text/plain","Display pin map restored");
  });
  server.on("/api/time",HTTP_POST,[](){
    if(!requireAdmin())return;
    // Drain completed paid coins first and settle elapsed time before changing
    // a live session. A manual credit is not recorded as a purchased coin.
    handleCoinInput();
    updateTimerState();
    if(!server.hasArg("mode") || !server.hasArg("hours") ||
       !server.hasArg("minutes") || !server.hasArg("seconds")) {
      reject("Missing time fields",400);return;
    }
    const String mode = server.arg("mode");
    if(mode != "add" && mode != "set") {reject("Mode must be add or set",400);return;}
    uint32_t duration = 0;
    if(!blazeParseManualDuration(server.arg("hours"),server.arg("minutes"),
                                 server.arg("seconds"),duration)) {
      reject("Use a positive duration: hours 0-168, minutes/seconds 0-59; maximum 7 days",400);return;
    }
    if(!applyManualTime(mode=="set",duration)) {
      reject("Total time would exceed the 7-day limit; no change was made",409);return;
    }
    server.sendHeader("Cache-Control","no-store");
    server.send(200,"text/plain",mode=="set" ? "Remaining time replaced" : "Time added");
  });
  server.on("/action",HTTP_POST,[](){
    if(!requireAdmin())return;
    String a=server.arg("name");
    if(a=="resetTimer") resetTimer();
    else if(a=="clearSales") clearSales();
    else if(a=="warn")playWarningChime();
    else if(a=="relay1") {
      if(timerRunning) {reject("Manual cutoff switching disabled during paid time",409);return;}
      setRelay1(!relayState);
    } else if(a=="pwrPulse") {
      // Manual momentary press changes the estimated state, not actual PC feedback.
      if (!pulsePowerButton()) {reject("PWR_SW busy or 5-second cooldown active",409);return;}
      pcExpectedOn = !pcExpectedOn;
      pcShutdownPending=false;
    } else if(a=="csOn" || a=="csOff") {
      if(a=="csOn" && (!interconConfigHealthy || interconConfig.role!=INTERCON_STANDARD)){
        reject("Remote credit is not enabled in Master/Slave preview; CS is locked OFF",409);return;
      }
      // Honor any completed coins before physically disabling the slot.
      if(a=="csOff") handleCoinInput();
      // CS state is saved across ESP resets, regardless of timer state.
      setCsEnabled(a=="csOn");
      saveCsPref();
    } else {reject("Unknown action",404);return;}
    server.send(200,"text/plain","OK");
  });
  server.on("/settings",HTTP_POST,[](){
    if(!requireAdmin())return;
    if(!server.hasArg("save")) {reject("Save flag missing");return;}
    if(timerRunning) {reject("Do not change settings during paid time",409);return;}
    // Intercon role and Wi-Fi are stored separately from paid balance EEPROM.
    // A network/role save cannot partially overwrite any active coin session.
    const String newRole=server.arg("interconRole");
    if(newRole!="0"&&newRole!="1"&&newRole!="2") {reject("Invalid station role");return;}
    String newNodeId=server.arg("interconNodeId");
    if(newNodeId.length()==0||newNodeId.length()>5){reject("Invalid node ID");return;}
    for(size_t i=0;i<newNodeId.length();i++)if(newNodeId[i]<'0'||newNodeId[i]>'9'){reject("Node ID must be numeric");return;}
    unsigned long nextNodeId=newNodeId.toInt();
    if(nextNodeId<1||nextNodeId>65535){reject("Node ID must be 1-65535");return;}
    String newNodeName=server.arg("interconNodeName");
    if(newNodeName.length()==0||newNodeName.length()>24){reject("Node name must have 1-24 characters");return;}
    for(size_t i=0;i<newNodeName.length();i++){
      char ch=newNodeName[i];
      if(!((ch>='a'&&ch<='z')||(ch>='A'&&ch<='Z')||(ch>='0'&&ch<='9')||ch=='-'||ch=='_')){
        reject("Node name may contain letters, digits, hyphen and underscore");return;
      }
    }
    String newStaName=server.arg("interconStaSsid");
    if(newStaName.length()>32){reject("STA SSID must be at most 32 characters");return;}
    String newStaPass=server.arg("interconStaPass");
    if(newStaPass.length()==0)newStaPass=interconConfig.staPassword;
    bool staOn=server.hasArg("interconStaEnabled");
    if(staOn && (newStaName.length()==0||newStaPass.length()<8||newStaPass.length()>63)){
      reject("STA requires SSID and WPA password (8-63 characters)");return;
    }
    InterconConfig proposed=interconConfig;
    proposed.magic=INTERCON_MAGIC;proposed.version=INTERCON_VERSION;
    proposed.role=(uint8_t)newRole.toInt();proposed.nodeId=(uint16_t)nextNodeId;
    proposed.staEnabled=staOn?1:0;
    newNodeName.toCharArray(proposed.nodeName,sizeof(proposed.nodeName));
    newStaName.toCharArray(proposed.staSsid,sizeof(proposed.staSsid));
    newStaPass.toCharArray(proposed.staPassword,sizeof(proposed.staPassword));
    proposed.checksum=interconChecksum(proposed);
    if(!interconFsReady){reject("LittleFS unavailable; role/network settings cannot be saved",503);return;}
    String newName=server.arg("apName");newName.trim();
    String newPass=server.arg("apPassword");
    if(newPass.length()==0)newPass=String(AP_PASSWORD);
    if(!apConfigIsValid(newName,newPass) || newPass.length()==0) {reject("AP name 1-32; password 8-63 characters");return;}
    String newAdmin=server.arg("adminPassword");
    if(newAdmin.length()!=0 && (newAdmin.length()<10 || newAdmin.length()>32)) {reject("Admin password must be 10-32 characters");return;}
    uint8_t nc=(uint8_t)constrain(server.arg("coinPin").toInt(),0,16);
    uint8_t nr1=(uint8_t)constrain(server.arg("relayPin").toInt(),0,16);
    uint8_t nr2=(uint8_t)constrain(server.arg("relay2Pin").toInt(),0,16);
    uint8_t nclk=(uint8_t)constrain(server.arg("displayClk").toInt(),0,16);
    uint8_t ndio=(uint8_t)constrain(server.arg("displayDio").toInt(),0,16);
    if(!pinSetIsUnique(nc,nr1,nr2,FIXED_BUZZER_PIN,nclk,ndio)) {reject("Unsafe GPIO assignment, duplication, or boot/flash pin conflict");return;}
    int nm=constrain(server.arg("addMinutes").toInt(),0,180);
    int ns=constrain(server.arg("addSeconds").toInt(),0,59);
    if(nm==0 && ns==0) {reject("Coin time cannot be zero");return;}
    int nb=constrain(server.arg("brightness").toInt(),1,7);
    // Strict parsing avoids silently accepting blank/negative/malformed input.
    String idleArg = server.arg("idleTriggerSeconds");
    if (!server.hasArg("idleTriggerSeconds") || idleArg.length() == 0 ||
        idleArg.length() > 4) {
      reject("Idle trigger must be an integer between 0 and 3600 seconds",400);return;
    }
    for (size_t i = 0; i < idleArg.length(); ++i) {
      if (idleArg[i] < '0' || idleArg[i] > '9') {
        reject("Idle trigger must contain digits only",400);return;
      }
    }
    String graceArg=server.arg("shutdownGraceSeconds");
    String pulseArg=server.arg("pwrPulseMilliseconds");
    auto decimalRange = [](const String& val, uint32_t minValue, uint32_t maxValue) -> bool {
      if(val.length()==0 || val.length()>4) return false;
      for(size_t i=0;i<val.length();++i) if(val[i]<'0'||val[i]>'9')return false;
      unsigned long n=val.toInt();return n>=minValue && n<=maxValue;
    };
    if(!decimalRange(graceArg,0,3600) || !decimalRange(pulseArg,100,1000)) {
      reject("Shutdown delay must be 0-3600s, PWR_SW pulse 100-1000ms",400);return;
    }
    const uint16_t newGrace=(uint16_t)graceArg.toInt();
    const uint16_t newPulse=(uint16_t)pulseArg.toInt();
    const bool newCsHigh=server.hasArg("csActiveHigh");
    const uint32_t newIdleTrigger = (uint32_t)idleArg.toInt();
    if (newIdleTrigger > 3600UL) {
      reject("Idle trigger maximum is 3600 seconds",400);return;
    }
    bool newCoinLow=server.hasArg("coinActiveLow");
    bool newR1Low=server.hasArg("relayActiveLow");
    bool newR2Low=server.hasArg("relay2ActiveLow");
    bool newBuzLow=server.hasArg("buzzerActiveLow");
    bool mapChanged=nc!=coinPin || nr1!=relayPin || nr2!=relay2Pin || nclk!=displayClk || ndio!=displayDio;
    bool polarChanged=newCoinLow!=coinActiveLow || newR1Low!=relayActiveLow || newR2Low!=relay2ActiveLow || newBuzLow!=buzzerActiveLow;
    if((mapChanged||polarChanged) && (powerPulseActive||pcShutdownPending)){
      reject("Cannot change power GPIOs while a PWR_SW pulse is active or pending",409);return;
    }
    // Save verified network settings BEFORE touching current relay GPIOs.
    if(!saveInterconConfig(proposed)){
      reject("INTERCON configuration write failed; inspect LittleFS before retrying",503);return;
    }
    if(mapChanged || polarChanged){
      if (powerPulseActive || pcShutdownPending) {reject("Cannot remap power pins while PWR_SW is active/pending",409);return;}
      detachInterrupt(digitalPinToInterrupt(coinPin));
      setRelays(false);stopChime();
      // Disconnect old outputs before configuring new relay pins.
      pinMode(relayPin,INPUT);pinMode(relay2Pin,INPUT);
    }
    newName.toCharArray(AP_NAME,sizeof(AP_NAME));
    newPass.toCharArray(AP_PASSWORD,sizeof(AP_PASSWORD));
    coinPin=nc;relayPin=nr1;relay2Pin=nr2;displayClk=nclk;displayDio=ndio;
    coinActiveLow=newCoinLow;relayActiveLow=newR1Low;relay2ActiveLow=newR2Low;buzzerActiveLow=newBuzLow;
    addMinutes=(uint16_t)nm;addSeconds=(uint16_t)ns;
    warningSeconds=(uint16_t)constrain(server.arg("warningSeconds").toInt(),0,120);
    chimeDurationSeconds=(uint16_t)constrain(server.arg("chimeDurationSeconds").toInt(),1,120);
    countdownSpeedPercent=(uint8_t)constrain(server.arg("speedPct").toInt(),0,50);
    displayBrightness=(uint8_t)nb;
    idleTriggerSeconds=(uint16_t)newIdleTrigger;
    shutdownGraceSeconds=newGrace;
    pwrPulseMilliseconds=newPulse;
    csActiveHigh=newCsHigh;
    writeCsEnable();
    if(mapChanged || polarChanged){
      digitalWrite(relayPin,relayActiveLow?HIGH:LOW);pinMode(relayPin,OUTPUT);
      digitalWrite(relay2Pin,relay2ActiveLow?HIGH:LOW);pinMode(relay2Pin,OUTPUT);
      setBuzzer(false);configureCoinInput();setupDisplay();
    } else displayUnit.setBrightness(displayBrightness);
    displayUnit.setIdleDelaySeconds(idleTriggerSeconds);
    // There is no authenticated remote-credit path in this phase: gate coins.
    noInterrupts();coinInputAllowed=false;coinQueued=0;coinPulseStartUs=0;interrupts();
    writeCsEnable();
    noInterrupts();coinInputAllowed=localCoinsAllowed();interrupts();
    savePersistentState();
    saveIdlePreferences();
    savePowerPref();
    saveCsPref();
    if(newAdmin.length()>0){newAdmin.toCharArray(adminPassword,sizeof(adminPassword));saveAdminPassword();}
    server.send(200,"text/plain","Settings saved");
  });
  server.on("/api/intercon/restart",HTTP_POST,[](){
    if(!requireAdmin())return;
    if(server.arg("confirm")!="yes"){reject("Confirmation required");return;}
    if(timerRunning||powerPulseActive||pcShutdownPending){reject("Restart forbidden during paid session or PWR_SW action",409);return;}
    server.send(200,"text/plain","Restarting controller");
    delay(150);ESP.restart();
  });
  server.on("/upload",HTTP_POST,[](){
    if(!requireAdmin())return;
    server.send(uploadSucceeded?200:400,"text/plain",uploadMessage);
  },handleFileUpload);
  server.onNotFound([](){if(!requireAdmin())return;reject("Not found",404);});
  server.begin();
  lastNearEndStartedAt=millis();
  playWelcomeChime();
  Serial.println(F("[WEB] Ready at 192.168.4.1; user admin; change default password"));
}
void loop() {
  server.handleClient();
  scanInterconPeers();
  handleCoinInput();
  updateTimerState();
  updatePcPowerControl();
  displayUnit.update(remainingSeconds);
  updateBuzzer();
  updateChimePlayer();
  yield();
}

void updateBuzzer() {
  uint32_t now = millis();

  if (buzzerUntil != 0 && (int32_t)(now - buzzerUntil) >= 0) {
    setBuzzer(false);
    buzzerUntil = 0;
  }
}