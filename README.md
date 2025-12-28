# Volume Control control driver using I2C for ES9018K2M DAC with Volumio 4
adapted from https://github.com/DedeHai/Volumio

Python daemon for hardware volume and mute control of ES9018K2M DAC via I²C, driven by Volumio playback events over WebSocket (Socket.IO).
The script listens to Volumio state changes in real time and synchronizes:
- volume
- mute state
directly with ES9018K2M registers.

Install instructions https://github.com/DanyHovard/es9018k2m_volumio_I2C_control/wiki/Install-instructions

> [!NOTE]
> This controller does NOT change DAC bit depth (16 / 24 / 32 bit).
> Changing bit depth dynamically based on Volumio WebSocket (Socket.IO) events causes unstable behavior, including: audible clicks and pops, playback stalls, DAC desynchronization, random playback errors when switching between 16-bit, 24-bit, 32-bit streams.
These issues were observed when attempting to react to bit-depth changes reported via WebSocket state updates.

## How It Works
1. Script connects to Volumio WebSocket (socket.io)
2. Listens for pushState events
3. Extracts:
- playback status
- volume (0–100)
- mute state
4. Converts Volumio volume → ES9018K2M attenuation
5. Writes values directly to DAC via I²C
