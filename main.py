import time
import threading
import meshtastic
import meshtastic.serial_interface
from pubsub import pub
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
import json

TARGET_NODE_ID = "!b03dca70"
LOG_FILE = "log.txt"
IDENTITY_FILE = "ident.txt"

class MeshtasticGUI:
    def __init__(self):
        self.interface = None
        self.received_ids = []

        self.com_window = None
        self.com_port_entry = None

        self.main_window = None
        self.message_entry = None

        self.build_com_window()

    def handle_packet(self, packet):
        decoded = packet.get("decoded", {})
        #print(f"Raw Decode: {decoded}")
        if decoded.get("portnum") == "TEXT_MESSAGE_APP":
            from_id = packet.get("fromId", "unknown")
            text = decoded.get("text", "<no text>")
            snr = packet.get("rxSnr", "?")
            rssi = packet.get("rxRssi", "?")
            print(f"\nText received from {from_id}: {text} (SNR: {snr}, RSSI: {rssi} dBm)")
            self.update_rx_ids(from_id)
            self.update_message_dict(from_id, text, snr, rssi)
            self.update_scrolled_text(from_id, text, snr, rssi, 'RX')
        elif decoded.get("portnum") == "TELEMETRY_APP":
            from_id = packet.get("fromId", "unknown")
            telemetry = decoded.get("telemetry", {})
            device_metrics = telemetry.get("deviceMetrics", {})
            voltage = device_metrics.get("voltage", "?")
            battery = device_metrics.get("batteryLevel", "?")
            print(f"{self.lookup_identity(from_id)} -- Voltage: {voltage}\tBat Level: {battery}")


    def update_rx_ids(self, from_id):
        if from_id not in self.received_ids:
            self.received_ids.append(from_id)
        print(f"Received ID List: {self.received_ids}")

    def update_message_dict(self, from_id, text, snr, rssi):
        with open(LOG_FILE, 'a') as lf:
            lf.write(f"{from_id}, {text}, {snr}, {rssi}\n")

    import json

    def lookup_identity(self, from_id):
        try:
            with open(IDENTITY_FILE, 'r') as IDF:
                identities = json.load(IDF)
                return identities.get(from_id, f"No Identity, {from_id}")
        except Exception as e:
            print(f"Error loading identity file: {e}")
            return from_id

    def update_scrolled_text(self, from_id, text, snr, rssi, rxtx):
        id = self.lookup_identity(from_id)
        string = (f"{rxtx}: {id}: {text}")
        self.message_log.config(state='normal')
        self.message_log.insert(tk.END, string + '\n')
        self.message_log.see(tk.END)
        self.message_log.config(state='disabled')

    def send_loop(self):
        while True:
            try:
                msg = input("Enter message to send (or 'exit' to quit): ")
                if msg.lower() == "exit":
                    break
                self.interface.sendText(msg, destinationId=TARGET_NODE_ID)
                print(f"Sent {msg} to {TARGET_NODE_ID}")
            except Exception as e:
                print(f"Error sending message: {e}")

    def send_text(self):
        try:
            msg = self.message_entry.get()
            self.interface.sendText(msg, destinationId=TARGET_NODE_ID)
            self.update_scrolled_text('Me', msg, 'NA', 'NA', 'TX')
            print(f"Sent {msg} to {TARGET_NODE_ID}")
        except:
            print("Unable to send message.")

    def com_connect(self):
        com_port = self.com_port_entry.get().upper()
        if not com_port.startswith("COM") or len(com_port) < 4:
            messagebox.showerror("Invalid Port", "Please enter a valid COM port (e.g., COM5)")
            return

        try:
            print(f"Attempting to connect to {com_port}...")
            self.interface = meshtastic.serial_interface.SerialInterface(devPath=com_port, connectNow=False)
            time.sleep(2)
            self.interface.connect()
            pub.subscribe(self.handle_packet, "meshtastic.receive")
            self.interface.sendText("I'm up!", destinationId=TARGET_NODE_ID)
            messagebox.showinfo("Connected", f"Connected to {com_port}")
            self.com_window.destroy()

            # Start input thread
            #threading.Thread(target=self.send_loop, daemon=True).start()

            self.build_main_window()

        except Exception as e:
            print(f"Connection failed: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")

    def build_com_window(self):
        self.com_window = tk.Tk()
        self.com_window.title("Meshtastic COM Connector")

        tk.Label(self.com_window, text="Enter COM Port (e.g., COM5):").grid(row=0, column=0)
        self.com_port_entry = tk.Entry(self.com_window)
        self.com_port_entry.grid(row=0, column=1)

        tk.Button(self.com_window, text="Connect", command=self.com_connect).grid(row=1, column=0, columnspan=2)
        self.com_window.mainloop()

    import tkinter.scrolledtext as scrolledtext  # ensure this is imported

    def build_main_window(self):
        self.main_window = tk.Tk()
        self.main_window.title("Meshtastic Messenger")

        # Message log (ScrolledText)
        self.message_log = scrolledtext.ScrolledText(self.main_window, state='disabled', wrap=tk.WORD, height=20,
                                                     width=60)
        self.message_log.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        # Message input
        tk.Label(self.main_window, text="Message to send:").grid(row=1, column=0)
        self.message_entry = tk.Entry(self.main_window)
        self.message_entry.grid(row=1, column=1)

        # Send button
        tk.Button(self.main_window, text="Send", command=self.send_text).grid(row=2, column=0, columnspan=2)

        self.main_window.mainloop()


if __name__ == "__main__":
    MeshtasticGUI()
