import QtQuick
import "root:/services"

Item {
    BatteryMonitor {
        id: batteryMonitor
    }

    Component.onCompleted: {
        console.log("Battery Monitor Started...")
    }
}
