import subprocess
import threading
from flask import Flask, request, render_template_string

app = Flask(__name__)

ACCESS_POINT_INTERFACE = "wlan0"
WIFI_INTERFACE = "wlan1"
AP_SSID = "MyAccessPoint"
AP_PORT = 8080

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
            if interface in line and "connected" in line:
                return True
        return False
    except subprocess.CalledProcessError:
        return False

def connect_to_wifi(ssid, password):
    """Connect to a Wi-Fi network."""
    try:
        subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, "password", password, "ifname", WIFI_INTERFACE], check=True)
        print(f"Connected to Wi-Fi network '{ssid}'. Stopping access point...")
        stop_access_point(ACCESS_POINT_INTERFACE)
    except subprocess.CalledProcessError:
        print(f"Failed to connect to Wi-Fi network '{ssid}'.")

def start_access_point(interface=ACCESS_POINT_INTERFACE, ssid=AP_SSID):
    """Start an access point using Network Manager."""
    try:
        subprocess.run(["nmcli", "connection", "add", "type", "wifi", "ifname", interface, "con-name", "Hotspot", "ssid", ssid], check=True)
        subprocess.run(["nmcli", "connection", "modify", "Hotspot", "802-11-wireless.mode", "ap", "802-11-wireless.band", "bg", "ipv4.method", "shared"], check=True)
        subprocess.run(["nmcli", "connection", "up", "Hotspot"], check=True)
        print(f"Access point '{ssid}' started on {interface}.")
    except subprocess.CalledProcessError:
        print(f"Failed to start access point on {interface}.")

def stop_access_point(interface=ACCESS_POINT_INTERFACE):
    """Stop the access point."""
    try:
        subprocess.run(["nmcli", "connection", "down", "Hotspot"], check=True)
        print(f"Access point stopped on {interface}.")
    except subprocess.CalledProcessError:
        print(f"Failed to stop access point on {interface}.")

@app.route("/", methods=["GET", "POST"])
def wifi_config():
    """Serve the Wi-Fi configuration page and handle form submission."""
    if request.method == "POST":
        ssid = request.form.get("ssid")
        password = request.form.get("password")

        if ssid and password:
            threading.Thread(target=connect_to_wifi, args=(ssid, password)).start()
            return "<h1>Connecting to Wi-Fi...</h1><p>Please wait and refresh the page.</p>"

        return "<h1>Invalid input</h1><p>Please provide both SSID and password.</p>"

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    if not is_connected(WIFI_INTERFACE):
        print("Wi-Fi not connected. Starting access point...")
        start_access_point(ACCESS_POINT_INTERFACE, AP_SSID)

        # Start the Flask server
        print(f"Starting Flask server on {AP_SSID}:{AP_PORT}")
        app.run(host="0.0.0.0", port=AP_PORT)
    else:
        print("Wi-Fi is already connected. No action needed.")
