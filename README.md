# Naim Audio Integration for Unfolded Circle Remote 2/3

Control your Naim audio devices directly from your Unfolded Circle Remote 2 or Remote 3 with comprehensive media player control, **multi-device support**, and **real-time state monitoring**.

![Naim Audio](https://img.shields.io/badge/Naim-Audio-blue)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-naim?style=flat-square)](https://github.com/mase1981/uc-intg-naim/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-naim?style=flat-square)](https://github.com/mase1981/uc-intg-naim/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://community.unfoldedcircle.com/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-naim/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)


## Features

This integration provides comprehensive control of your Naim audio devices directly from your Unfolded Circle Remote, supporting all inputs, volume control, and playback functions across the entire Naim range. **Multi-device support** allows you to control up to 10 Naim devices from a single integration.

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

### 🎵 **Media Player Control**

#### **Playback Control**
- **Play/Pause** - Seamless playback control with visual feedback
- **Stop** - Stop current playback and clear now playing
- **Previous/Next Track** - Navigate through your music collection
- **Volume Control** - Precise volume adjustment with 3% step controls
- **Mute Toggle** - Quick mute/unmute functionality
- **Repeat & Shuffle** - Full repeat (Off/One/All) and shuffle control

#### **Audio Source Management**
- **Comprehensive Input Support** - All Naim inputs: Analog 1-3, Digital 1-3, HDMI, Bluetooth, Internet Radio
- **Streaming Services** - Direct access to Spotify, TIDAL, Qobuz (if supported by device)
- **Network Sources** - UPnP servers, AirPlay, Chromecast built-in
- **Physical Inputs** - USB, Optical, Coaxial connections
- **Real-time Source Display** - Current input always visible on remote

#### **Advanced Features**
- **Power Control** - Device power on/off with standby monitoring
- **Now Playing Display** - Artist, album, track, and artwork display
- **Playback Position** - Real-time position tracking with duration
- **Multi-Device Support** - Control multiple Naim devices independently

### 🎮 **Remote Control Interface**

Comprehensive Naim device control through dedicated remote entity:

#### **Main Controls**
- **Transport Controls** - Play/Pause, Previous, Next, Stop
- **Volume Management** - Volume Up/Down (3% steps), Mute toggle
- **Power Control** - Device power on/off/toggle

#### **Source Selection**
- **Analog Inputs** - Direct access to Analogue 1-3
- **Digital Inputs** - Optical, Coaxial, HDMI connections
- **Streaming Sources** - Spotify, TIDAL, Qobuz, Internet Radio
- **Network Sources** - AirPlay, Chromecast, UPnP servers
- **Audio Controls** - Balance left/right/center adjustment

### 📊 **Visual Status Display**

#### **Dynamic Status Information**
Real-time display of device and playback status:
- **Device State** - Power on/off, standby status
- **Playback State** - Playing, paused, stopped, buffering with visual indicators
- **Current Track** - Title, artist, album information
- **Album Artwork** - High-quality cover art display

#### **Multi-Entity Integration**
- **Media Player Entity** - Primary control interface with full media features (one per device)
- **Remote Entity** - Button-based control for traditional remote experience (one per device)
- **Synchronized State** - All entities reflect real device status
- **Independent Control** - Each device operates independently

### **Multi-Device Support**

The integration now supports **1-10 Naim devices** in a single setup:
- **Device Count Selection** - Choose how many devices to configure during setup
- **Individual Configuration** - Enter IP address and name for each device
- **Concurrent Testing** - All devices tested simultaneously during setup
- **Independent Entities** - Each device gets its own media player and remote entities
- **Centralized Control** - Manage all Naim devices from one integration
- **Room-Based Setup** - Perfect for multi-room audio systems

### **Supported Naim Models**

#### **Tested & Verified**
- **Atom** - Compact all-in-one streaming system
- **Nova** - High-performance streaming amplifier
- **Star** - Premium streaming system
- **Uniti Series** - Core, Atom HE, Nova PE, Star

#### **Expected Compatibility**
This integration should work with **any Naim device supporting HTTP API**, including:
- **Uniti Range** - All current Uniti models with network connectivity
- **Legacy Devices** - Older Naim devices with firmware updates supporting HTTP API
- **Future Models** - New releases following Naim's standard API implementation

### **Protocol Requirements**

- **Protocol**: Naim HTTP API
- **HTTP Port**: 15081 (default)
- **Network Access**: Device must be on same local network
- **Connection**: Periodic polling for state updates
- **Real-time Updates**: Regular polling for instant state changes

### **Network Requirements**

- **Local Network Access** - Integration requires same network as Naim device
- **HTTP Protocol** - HTTP API (port 15081)
- **Static IP Recommended** - Device should have static IP or DHCP reservation
- **Firewall** - Must allow HTTP traffic

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-naim/releases) page
2. Download the latest `uc-intg-naim-<version>.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

**Image**: `ghcr.io/mase1981/uc-intg-naim:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-naim:
    image: ghcr.io/mase1981/uc-intg-naim:latest
    container_name: uc-intg-naim
    network_mode: host
    volumes:
      - </local/path>:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-naim --restart unless-stopped --network host -v naim-config:/app/config -e UC_CONFIG_HOME=/app/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-naim:latest
```

## Configuration

### Step 1: Prepare Your Naim Device(s)

**IMPORTANT**: Naim device must be powered on and connected to your network before adding the integration.

#### Verify Network Connection:
1. Check that device is connected to network (Ethernet or WiFi)
2. Note the IP address from device's network settings or router
3. Ensure device firmware is up to date
4. Verify HTTP API is accessible (enabled by default on port 15081)

#### Network Setup:
- **Wired Connection**: Recommended for stability
- **Static IP**: Recommended via DHCP reservation
- **Firewall**: Allow HTTP traffic (port 15081)
- **Network Isolation**: Must be on same subnet as Remote

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The Naim Audio integration should appear in **Available Integrations**
3. Click **"Configure"** to begin setup:

#### **Single Device Setup:**
- **Number of Devices**: Select "1"
- **IP Address**: Enter device IP (e.g., 192.168.1.100 or 192.168.1.100:15081)
- **Device Name**: Friendly name (e.g., "Living Room Atom")
- Click **Complete Setup**

#### **Multi-Device Setup:**
- **Number of Devices**: Select 2-10 devices
- **Device Configuration**: For each device, enter:
  - **IP Address**: Device IP address
  - **Device Name**: Friendly name (e.g., "Living Room Atom")
- **Concurrent Testing**: All devices tested simultaneously
- Click **Complete Setup**

#### **Connection Test:**
- Integration verifies device connectivity
- HTTP connection established
- Setup fails if device unreachable

4. Integration will create entities:
   - **Media Player**: `Naim Device Name` (e.g., "Living Room Atom")
   - **Remote Control**: `Naim Device Name Remote` (e.g., "Living Room Atom Remote")

## Using the Integration

### Media Player Entity

The media player entity provides complete control:

- **Power Control**: On/Off with state feedback
- **Volume Control**: Volume slider (0-100)
- **Volume Buttons**: Up/Down (3% steps) with real-time feedback
- **Mute Control**: Toggle, Mute, Unmute
- **Source Selection**: Dropdown with all available inputs
- **Playback Control**: Play/Pause, Next, Previous, Stop
- **Media Info**: Current track, artist, album, duration, position
- **Repeat & Shuffle**: Full control of playback modes

### Remote Control Entity

The remote entity provides traditional button-based control:

- **Transport Controls**: Play/Pause, Previous, Next, Stop buttons
- **Volume Controls**: Volume Up/Down and Mute buttons
- **Power Control**: Device power on/off/toggle
- **Source Selection**: Dedicated button for each available input
- **Audio Controls**: Balance adjustment

### Multi-Device Management

When using multiple devices:
- **Independent Control**: Each device operates completely independently
- **Room-Based Activities**: Create activities for each room/device
- **Centralized Overview**: All devices visible in integration settings
- **Synchronized Status**: Real-time status updates for all devices

## Credits

- **Developer**: Meir Miyara
- **Naim Audio**: HTTP API specification and device support
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Protocol**: Naim HTTP API
- **Community**: Testing and feedback from UC community

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-naim/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **Naim Audio Support**: [Official Naim Support](https://www.naimaudio.com/support)

---

**Made with ❤️ for the Unfolded Circle and Naim Audio Communities**

**Thank You**: Meir Miyara
