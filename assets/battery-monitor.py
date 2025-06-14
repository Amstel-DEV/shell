#!/usr/bin/env python3
import asyncio
import os
from dbus_next.aio import MessageBus
from dbus_next.constants import BusType

# === ICON CONFIGURATION ===
low_bat_icon = "battery-caution-symbolic"
critical_bat_icon = "battery-empty-symbolic"
full_bat_icon = "battery-full-charged-symbolic"
plugged_icon = "battery-good-charging-symbolic"
unplugged_icon = "battery-good-symbolic"
# ===========================

NOTIFY_SEND = "/sbin/notify-send"

last_state = {
    "percentage": None,
    "state": None,
    "plugged_in": None
}

def send_notification(summary, body="", urgency="normal", icon="battery"):
    os.system(f'{NOTIFY_SEND} --urgency={urgency} -i "{icon}" "{summary}" "{body}"')

async def monitor_battery():
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    battery_path = "/org/freedesktop/UPower/devices/battery_BAT0"
    proxy = await bus.introspect("org.freedesktop.UPower", battery_path)
    obj = bus.get_proxy_object("org.freedesktop.UPower", battery_path, proxy)
    props_iface = obj.get_interface("org.freedesktop.DBus.Properties")

    async def get(key):
        val = await props_iface.call_get("org.freedesktop.UPower.Device", key)
        return val.value

    while True:
        percent = int(await get("Percentage"))
        state = await get("State")
        plugged_in = state in (1, 4)

        # Plug/unplug
        if last_state["plugged_in"] is not None and plugged_in != last_state["plugged_in"]:
            if plugged_in:
                send_notification("Charger plugged in", f"{percent}% remaining", "low", plugged_icon)
            else:
                send_notification("Charger unplugged", f"{percent}% remaining", "low", unplugged_icon)

        # Battery full
        if plugged_in and percent == 100 and last_state["percentage"] != 100:
            send_notification("Battery full", "You can unplug the charger", "normal", full_bat_icon)

        # Low battery alerts
        if not plugged_in:
            if percent <= 5 and (last_state["percentage"] is None or last_state["percentage"] > 5):
                send_notification("Battery critically low", f"{percent}% remaining", "critical", critical_bat_icon)
            elif percent <= 15 and (last_state["percentage"] is None or last_state["percentage"] > 15):
                send_notification("Battery low", f"{percent}% remaining", "normal", low_bat_icon)

        # Save state
        last_state.update({
            "percentage": percent,
            "state": state,
            "plugged_in": plugged_in
        })

        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_battery())
    except KeyboardInterrupt:
        print("Battery monitor stopped.")
