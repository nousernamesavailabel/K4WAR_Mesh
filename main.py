import time
import threading
import meshtastic
import meshtastic.serial_interface
from pubsub import pub

TARGET_NODE_ID = "!b03dca70"  # Change if your target node changes

def handle_packet(packet):
    decoded = packet.get("decoded", {})
    if decoded.get("portnum") == "TEXT_MESSAGE_APP":
        from_id = packet.get("fromId", "unknown")
        text = decoded.get("text", "<no text>")
        snr = packet.get("rxSnr", "?")
        rssi = packet.get("rxRssi", "?")
        print(f"\nText received from {from_id}: {text} (SNR: {snr}, RSSI: {rssi} dBm)")

def send_loop(interface):
    while True:
        try:
            msg = input("Enter message to send (or 'exit' to quit): ")
            if msg.lower() == "exit":
                break
            interface.sendText(msg, destinationId=TARGET_NODE_ID)
        except Exception as e:
            print(f"Error sending message: {e}")

def main():
    try:
        while True:
            com_port = input("What port is your meshtastic connected to (COM1,COM2,COMN...)? ").upper()
            if com_port[:3] == "COM" and len(com_port) == 4:
                interface = meshtastic.serial_interface.SerialInterface(devPath=com_port, connectNow=False)
                break
    except Exception as e:
        print(f"Error opening serial port: {e}")
        return

    time.sleep(2)
    interface.connect()

    # Subscribe to incoming messages
    pub.subscribe(handle_packet, "meshtastic.receive")

    print("Connected to Meshtastic. Receiving messages and ready to send.")
    print("Type your message below and press Enter to send. Type 'exit' to quit.")

    # Run input loop in the main thread
    try:
        send_loop(interface)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nClosing connection...")
        interface.close()

if __name__ == "__main__":
    main()
