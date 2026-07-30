NTI IoT Parking System Project
This is the Graduation Project for the NTI Summer Internship (IoT)


Features :

-ESP32 Edge Device: Manages parking entry/exit gates, physical slot detection, and LCD status displays.
-MQTT Communication: Sends real-time parking slot telemetry via broker.hivemq.com .
-Node RED Middleware: Offloads time tracking, slot ticket management, and system analytics.
-Node RED UI Dashboard: Displays real-time occupied slot gauges and active capacity.
-Telegram Bot Billing: Automatically generates a unique Ticket ID on entry and calculates a 1 EGP/second receipt upon exit sent directly to the driver's Telegram.


System Architecture :

ESP32 Microcontroller ──> (MQTT)──> HiveMQ Broker ──> Node-RED Engine ──> (HTTPS API) ──> Telegram Bot & Web Dashboard


Interactive Simulation :

Project Repository Structure
main.py — MicroPython source code for the ESP32.
diagram.json — Circuit schematic and pin wiring for Wokwi.
flows.json — Exported Node-RED flow configuration.


You can test and run the full ESP32 circuit simulation live on Wokwi:

[Open Wokwi Simulation] : (https://wokwi.com/projects/470918554597260289)


***Exit Logic: LIFO (Last-In, First-Out)  -  Slot-based stack management.
