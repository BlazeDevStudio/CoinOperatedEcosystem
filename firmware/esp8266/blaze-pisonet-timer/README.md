# BLAZE PISONET — ESP8266 timer firmware (V1.2)

**Status:** source review / physical validation pending. This is a separate ESP8266 coin-operated timer controller, **not** the Windows `Pisonet/` SoftTimer project in this repository.

## Source

- [BLAZE_PISONET_WELCOME_V1_2/BLAZE_PISONET_WELCOME_V1_2.ino](BLAZE_PISONET_WELCOME_V1_2/BLAZE_PISONET_WELCOME_V1_2.ino) — complete single-file Arduino sketch, based on the owner-tested V1.1 repair build and updated with the V1.2 display animation.
- SHA-256 of the original local V1.2 single-file source artifact: `3ad2bf2b702b67ac6d2a9f94dd4fa113cf54629ff5f53e55881964a97f84fff4`. GitHub's text transport may normalize a newline; verify the uploaded version independently before using this checksum as a binary identity assertion.

## What it does

ESP8266 Wi-Fi access point with browser controls, a coin-credit countdown, two relay outputs, TM1637 four-digit display, audible alerts, saved settings, and admin-protected manual **Add Time** / **Set Time** controls. The V1.2 boot display shows the TM1637 brightness sweep followed by `8888`, `1234`, `bLAZ`, `LAZE`, `AZE`, `ZE`, `E` with trailing digits unlit. The seven-segment module approximates Z using 2-shaped segments.

## Default NodeMCU / ESP-12E-F connections

| Signal | NodeMCU label | GPIO |
| --- | --- | --- |
| Display CLK | D6 | 12 |
| Display DIO | D7 | 13 |
| Buzzer | D5 | 14 |
| Coin input | D3 | 0 |
| Relay 1 driver IN | D1 | 5 |
| Relay 2 driver IN | D2 | 4 |

Settings saved in EEPROM can override some assignments. **GPIO0 is boot-sensitive**: a LOW signal at power-up can prevent the ESP8266 booting the application. Do not directly drive relay coils from GPIO pins. Test with mains loads disconnected and a properly isolated relay driver.

## Build and run

1. Install the ESP8266 Arduino board core and **TM1637Display** by Avishay Orpaz.
2. Put `BLAZE_PISONET_WELCOME_V1_2.ino` in a folder with the same name and open it in Arduino IDE.
3. Select the correct ESP8266 board and flash size. Preserve flash/EEPROM contents when upgrading from a known-good image.
4. Check relay polarity, coin input electrical levels, and the initial display sequence before attaching powered equipment.
5. Join the configured ESP8266 AP and visit `http://192.168.4.1` for management.

**Security:** The sketch contains factory/demo AP and administrator passwords. Change them on first use. An AP password is not a substitute for access control.

## Release limitations

- Prior validation used offline Arduino-compatible stubs and behavior tests; a real ESP8266-core compile and physical end-to-end test were **not** completed as part of this GitHub import.
- Commercial coin acceptor reliability, sales accuracy with calendar dates, persistence under power loss, relay electrical safety, and security require independent validation.
- Do **not** treat this branch as a certified production release or merge it into a commercial product without hardware and payment-path testing.
- The firmware is deliberately isolated from `Pisonet/` (Windows SoftTimer), preserving that directory's independent product boundary.
