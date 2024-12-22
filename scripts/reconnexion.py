import subprocess
import threading
import time
from flask import Flask, request, render_template_string

app = Flask(__name__)

ACCESS_POINT_INTERFACE = "wlan0"
WIFI_INTERFACE = "wlan1"
AP_PORT = 80

# Minimalist HTML template for the web page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Wi-Fi Configuration</title>
</head>
<body>
    <h1>Connect to Wi-Fi</h1>
    <form method="POST" action="/">
        <label for="ssid">SSID:</label>
        <input type="text" id="ssid" name="ssid" required><br><br>
        <label for="password">Password:</label>
        <input type="password" id="password" name="password" required><br><br>
        <button type="submit">Connect</button>
    </form>
</body>
</html>
"""

def is_connected(interface=WIFI_INTERFACE):
    """Check if the specified interface is connected to a network."""
    try:
        output = subprocess.check_output(["nmcli", "-t", "-f", "DEVICE,STATE", "device"])
        for line in output.decode().splitlines():
            if interface in line and f"{interface}:connected" in line:
                return True
        return False
    except subprocess.CalledProcessError:
        return False

def connect_to_wifi(ssid, password):
    """Connect to a Wi-Fi network."""
    try:
        subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, "password", password, "ifname", WIFI_INTERFACE], check=True)
        print(f"Connected to Wi-Fi network '{ssid}'. Stopping access point...")
        stop_access_point()
    except subprocess.CalledProcessError:
        print(f"Failed to connect to Wi-Fi network '{ssid}'.")

def start_access_point():
    try:
        subprocess.run(["nmcli", "con", "up", "AP"], check=True)
        print(f"Access point started on {ACCESS_POINT_INTERFACE}.")
    except subprocess.CalledProcessError:
        print(f"Failed to start access point on {ACCESS_POINT_INTERFACE}.")

def stop_access_point():
    try:
        subprocess.run(["nmcli", "connection", "down", "AP"], check=True)
        print(f"Access point stopped on {ACCESS_POINT_INTERFACE}.")
    except subprocess.CalledProcessError:
        print(f"Failed to stop access point on {ACCESS_POINT_INTERFACE}.")

def monitor_wifi_connection():
    while True:
        if not is_connected(WIFI_INTERFACE) and not is_connected(ACCESS_POINT_INTERFACE):
            print("Wi-Fi disconnected. Starting access point...")
            start_access_point()
        time.sleep(10)  # Check every 10 seconds

@app.route("/", methods=["GET", "POST"])
def wifi_config():
    if request.method == "POST":
        ssid = request.form.get("ssid")
        password = request.form.get("password")

        if ssid and password:
            threading.Thread(target=connect_to_wifi, args=(ssid, password)).start()
            return "<h1>Connecting to Wi-Fi...</h1><p>Please wait and refresh the page.</p>"

        return "<h1>Invalid input</h1><p>Please provide both SSID and password.</p>"

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    time.sleep(60) #Sleep for 60 seconds to give time to the network manager to start and connect to the network
    # Start the Flask server
    print(f"Starting Flask server")
    threading.Thread(target=lambda: app.run(host="10.42.0.1", port=AP_PORT)).start()
    monitor_wifi_connection()
