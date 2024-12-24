#!/bin/bash

# Get the installed version of the package (if it exists)
INSTALLED_VERSION=$(dpkg-query -W -f='${Version}' thermal-monitoring 2>/dev/null)

# If the package is not installed, set INSTALLED_VERSION to "none"
if [ -z "$INSTALLED_VERSION" ]; then
    INSTALLED_VERSION="none"
fi

echo "Installed version: $INSTALLED_VERSION"
echo "Getting latest version..."
LATEST_RELEASE=$(curl -s https://api.github.com/repos/Elgemp4/pi_thermal_monitoring/releases/latest)

LATEST_VERSION=$(echo $LATEST_RELEASE | jq -r '.tag_name' | sed 's/^[vV]//')
echo "Latest version: $LATEST_VERSION"

if [ "$INSTALLED_VERSION" = "$LATEST_VERSION" ]; then
    echo "The installed version ($INSTALLED_VERSION) is the latest version ($LATEST_VERSION). No update needed."
    exit 0
fi

echo "New version available. Downloading..."

DEB_URL=$(echo $LATEST_RELEASE | jq -r '.assets[] | select(.name == "pi-therm-monitoring.deb") | .browser_download_url')

if [ -n "$DEB_URL" ]; then
    echo "Downloading new version: $LATEST_VERSION"
    curl -L -o install.deb $DEB_URL
    echo "Downloaded install.deb"
    echo "Installing..."
    sudo apt install ./install.deb
    echo "Installed new version: $LATEST_VERSION"
else
    echo "Couldn't find deb file"
fi
