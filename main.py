import time
import threading
import meshtastic
import meshtastic.serial_interface
from pubsub import pub
import tkinter as tk
from tkinter import messagebox

TARGET_NODE_ID = "!b03dca70"
log_file = "log.txt"
received_ids = []
interface = None  # Define globally so other threads can use it

def handle_packet(packet):
    decoded = packet.get("decoded", {})
    if decoded.get("portnum") == "TEXT_MESSAGE_APP":
        from_id = packet.get("fromId", "unknown")
        text = decoded.get("text", "<no text>")
        snr = packet.get("rxSnr", "?")
        rssi = packet.get("rxRssi", "?")
        print(f"\nText received from {from_id}: {text} (SNR: {snr}, RSSI: {rssi} dBm)")
        update_rx_ids(from_id)
        update_message_dict(from_id, text, snr, rssi)

def update_rx_ids(from_id):
    if from_id not in received_ids:
        received_ids.append(from_id)
    print(f"Received ID List: {received_ids}")

def update_message_dict(from_id, text, snr, rssi):
    with open(log_file, 'a') as lf:
        lf.write(f"{from_id}, {text}, {snr}, {rssi}\n")

def send_loop():
    while True:
        try:
            msg = input("Enter message to send (or 'exit' to quit): ")
            if msg.lower() == "exit":
                break
            interface.sendText(msg, destinationId=TARGET_NODE_ID)
            print(f"Sent {msg} to {TARGET_NODE_ID}")
        except Exception as e:
            print(f"Error sending message: {e}")

def send_text():
    global message_entry
    try:
        msg = message_entry.get()
        interface.sendText(msg, destinationId=TARGET_NODE_ID)
        print(f"Sent {msg} to {TARGET_NODE_ID}")
    except:
        print("Unable to send message.")

def com_connect():
    global interface
    com_port = com_port_entry.get().upper()
    if not com_port.startswith("COM") or len(com_port) < 4:
        messagebox.showerror("Invalid Port", "Please enter a valid COM port (e.g., COM5)")
        return

    try:
        print(f"Attempting to connect to {com_port}...")
        interface = meshtastic.serial_interface.SerialInterface(devPath=com_port, connectNow=False)
        time.sleep(2)
        interface.connect()
        pub.subscribe(handle_packet, "meshtastic.receive")
        interface.sendText("I'm up!", destinationId=TARGET_NODE_ID)
        messagebox.showinfo("Connected", f"Connected to {com_port}")
        com_window.destroy()

        # Start text input loop in background thread
        threading.Thread(target=send_loop, daemon=True).start()

    except Exception as e:
        print(f"Connection failed: {e}")
        messagebox.showerror("Connection Error", f"Failed to connect: {e}")

def main():
    global com_window
    global com_port_entry
    global message_entry

    com_window = tk.Tk()
    com_window.title("Meshtastic COM Connector")

    tk.Label(com_window, text="Enter COM Port (e.g., COM5):").grid(row=0, column=0)
    com_port_entry = tk.Entry(com_window)
    com_port_entry.grid(row=0, column=1)

    tk.Button(com_window, text="Connect", command=com_connect).grid(row=1, column=0, columnspan=2)
    com_window.mainloop()

    main_window = tk.Tk()
    #head_label = tk.Label(text="It works")
    #head_label.grid(row=0, column=0)

    message_entry_label = tk.Label(main_window, text="Message to send: ")
    message_entry_label.grid(row=1, column=0)


    message_entry = tk.Entry(main_window, textvariable="Test")
    message_entry.grid(row=1, column=1)

    send_button = tk.Button(main_window, text="Send", command = send_text)
    send_button.grid(row=2, column=0, columnspan=2)
    main_window.mainloop()

if __name__ == "__main__":
    main()
