#!/usr/bin/python3
# coding: utf-8

import json
import time
import smbus2
import logging
import signal
import sys
import os
from websocket import WebSocketApp

# =========================
# CONFIG
# =========================

I2C_BUS = 1
DAC_ADDR = 0x48

REG_MUTE = 0x07
REG_VOL_L = 0x0F
REG_VOL_R = 0x10

WS_URL = "ws://localhost:3000/socket.io/?EIO=3&transport=websocket"
LOG_FILE = os.path.join(os.path.dirname(__file__), "es9018k2m_ws.log")

# =========================
# LOGGING
# =========================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logging.getLogger().addHandler(logging.StreamHandler())

# =========================
# DAC CONTROLLER
# =========================

class ES9018K2M:
    def __init__(self):
        self.bus = smbus2.SMBus(I2C_BUS)
        self.volume = None
        self.mute = None
        self.last_write = 0

    def _write(self, reg, val):
        now = time.time()
        if now - self.last_write < 0.03:
            time.sleep(0.03)
        self.bus.write_byte_data(DAC_ADDR, reg, val)
        self.last_write = time.time()

    def set_volume(self, vol):
        if vol == self.volume:
            return
        att = 100 - max(0, min(100, vol))
        self._write(REG_VOL_L, att)
        self._write(REG_VOL_R, att)
        self.volume = vol
        logging.info(f"Volume  ^f^r {vol}%")

    def set_mute(self, mute):
        if mute == self.mute:
            return
        self._write(REG_MUTE, 0x83 if mute else 0x80)
        self.mute = mute
        logging.info(f"Mute  ^f^r {mute}")

# =========================
# WEBSOCKET HANDLERS
# =========================

dac = ES9018K2M()

def on_message(ws, message):
    # socket.io framing
    if not message.startswith("42"):
        return

    payload = json.loads(message[2:])
    if payload[0] != "pushState":
        return

    state = payload[1]
    status = state.get("status")
    volume = state.get("volume")
    mute = state.get("mute")

    if status != "play":
        dac.set_volume(0)
        return

    if isinstance(volume, int):
        dac.set_volume(volume)

    if isinstance(mute, bool):
        dac.set_mute(mute)

def on_open(ws):
    logging.info("WebSocket connected to Volumio")

def on_close(ws, *_):
    logging.warning("WebSocket closed, reconnecting...")
    time.sleep(2)
    start_ws()

def on_error(ws, error):
    logging.error(f"WebSocket error: {error}")

# =========================
# MAIN
# =========================

def start_ws():
    ws = WebSocketApp(
        WS_URL,
        on_message=on_message,
        on_open=on_open,
        on_close=on_close,
        on_error=on_error
    )
    ws.run_forever(ping_interval=10, ping_timeout=5)

def stop(sig, frame):
    logging.info("Stopping ES9018K2M controller")
    sys.exit(0)

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

if __name__ == "__main__":
    logging.info("ES9018K2M WebSocket controller started")
    start_ws()
