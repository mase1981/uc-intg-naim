# Naim Audio Integration for Unfolded Circle Remote 2/3

Control your Naim audio devices directly from your Unfolded Circle Remote 2 or Remote 3. **Now supports multiple devices!**

![Naim Audio](https://img.shields.io/badge/Naim-Audio-blue)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-naim)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-tnaimya/total)
![License](https://img.shields.io/badge/license-MPL--2.0-blue)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/mase1981/button)


## Features

This integration provides comprehensive control of your Naim audio devices directly from your Unfolded Circle Remote, supporting all inputs, volume control, and playback functions across the entire Naim range. **Multi-device support** allows you to control up to 10 Naim devices from a single integration.

### 🎵 **Media Player Control**

Transform your remote into a powerful Naim controller with full device management:

#### **Playback Control**
- **Play/Pause** - Seamless playback control with visual feedback
- **Stop** - Stop current playback and clear now playing
- **Previous/Next Track** - Navigate through your music collection (enhanced with working API)
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
- **Transport Controls** - Play/Pause, Previous, Next, Stop (all working)
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
- **Device State**: Power on/off, standby status
- **Playback State**: Playing, paused, stopped, buffering with visual indicators
- **Current Track**: Title, artist, album information
- **Album Artwork**: High-quality cover art display

#### **Multi-Entity Integration**
- **Media Player Entity**: Primary control interface with full media features (one per device)
- **Remote Entity**: Button-based control for traditional remote experience (one per device)
- **Synchronized State**: All entities reflect real device status
- **Independent Control**: Each device operates independently

#### **Smart State Management**
- **Playing State**: Device on and actively playing content
- **Paused State**: Device on but playback paused
- **Standby State**: Device in standby/off mode
- **Source Indication**: Current input source clearly displayed

## Multi-Device Support

### **Setup Multiple Devices**
The integration now supports **1-10 Naim devices** in a single setup:

1. **Device Count Selection**: Choose how many devices to configure during setup
2. **Individual Configuration**: Enter IP address and name for each device
3. **Concurrent Testing**: All devices tested simultaneously during setup
4. **Independent Entities**: Each device gets its own media player and remote entities

### **Entity Naming**
Each device creates two entities:
- **Media Player**: `Naim Device Name` (e.g., "Living Room Atom")
- **Remote Control**: `Naim Device Name Remote` (e.g., "Living Room Atom Remote")

### **Benefits**
- **Centralized Control**: Manage all Naim devices from one integration
- **Room-Based Setup**: Perfect for multi-room audio systems
- **Individual Control**: Each device operates independently
- **Simplified Management**: Single integration for your entire Naim ecosystem

## Supported Naim Models

### **Tested & Verified**
- **Atom** - Compact all-in-one streaming system (Development & Testing Platform)
- **Nova** - High-performance streaming amplifier
- **Star** - Premium streaming system
- **Uniti Series** - Core, Atom HE, Nova PE, Star

### **Expected Compatibility**
This integration should work with **any Naim device supporting HTTP API**, including:
- **Uniti Range** - All current Uniti models with network connectivity
- **Legacy Devices** - Older Naim devices with firmware updates supporting HTTP API
- **Future Models** - New releases following Naim's standard API implementation

### **Requirements**
- **HTTP API Support** - Device must support Naim's HTTP control interface
- **Network Connection** - Wired or wireless network connectivity
- **Local Network Access** - Integration requires same network as device
- **Modern Firmware** - Keep device firmware updated for best compatibility

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-naim/releases) page
2. Download the latest `uc-intg-naim-<version>.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** â†' **Integrations** â†' **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

**Image**: `ghcr.io/mase1981/uc-intg-naim:latest`

**Docker Compose:**
```yaml
version: '3.8'

services:
  naim-integration:
    image: ghcr.io/mase1981/uc-intg-naim:latest
    container_name: uc-intg-naim
    restart: unless-stopped
    network_mode: host  # Required for device discovery
    volumes:
      - ./data:/data  # Persistent configuration storage
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_DISABLE_MDNS_PUBLISH=false
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9090/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    labels:
      - "com.unfoldedcircle.integration=naim-audio"
      - "com.unfoldedcircle.version=1.0.0"
```

### Option 3: Development Simulator
For testing without physical hardware, including multi-device testing:

**Single Device:**
```bash
python naim_simulator.py --single --port 8080
# Use 'localhost:8080' as device IP during setup
```

**Multi-Device Testing:**
```bash
python naim_simulator.py --count 3
# Creates 3 simulated devices on ports 8080, 8081, 8082
# Use 'localhost:8080', 'localhost:8081', 'localhost:8082' during setup
```

## Configuration

### Step 1: Prepare Your Naim Device(s)

1. **Network Setup:**
   - Connect each device to your local network (WiFi or Ethernet)
   - Note each device's IP address from your router or device display
   - Ensure all devices are powered on and network connected

2. **Naim App Verification:**
   - Download Naim app to verify device connectivity
   - Confirm each device appears and is controllable in the app
   - Test basic functions like play/pause and volume

3. **Network Requirements:**
   - All devices and Remote must be on same local network
   - HTTP communication on port 15081 (standard Naim port)
   - No firewall blocking required

### Step 2: Setup Integration

1. After installation, go to **Settings** â†' **Integrations**
2. The Naim Audio integration should appear in **Available Integrations**
3. Click **"Configure"** and follow the setup wizard:

#### **Single Device Setup**
   - **Number of Devices**: Select "1"
   - **IP Address**: Enter device IP (e.g., 192.168.1.100 or 192.168.1.100:15081)
   - **Test Connection**: Verify device communication
   - **Complete Setup**: Creates 2 entities (Media Player + Remote)

#### **Multi-Device Setup**
   - **Number of Devices**: Select 2-10 devices
   - **Device Configuration**: For each device, enter:
     - **IP Address**: Device IP address
     - **Device Name**: Friendly name (e.g., "Living Room Atom")
   - **Concurrent Testing**: All devices tested simultaneously
   - **Complete Setup**: Creates 2 entities per device

4. Integration will detect available input sources automatically for each device
5. Entities will be created and available immediately

### Step 3: Add Entities to Activities

1. Go to **Activities** in your remote interface
2. Edit or create an activity
3. Add Naim entities from the **Available Entities** list:
   - **Device Name** (Media Player) - Primary control interface
   - **Device Name Remote** (Remote) - Button-based control
4. Configure button mappings and UI layout as desired
5. Save your activity

## Usage

### Media Player Control

Use the **Naim Device** media player entity for each device:

1. **Playback Control**:
   - **Play/Pause**: Toggle playback state
   - **Stop**: Stop playback and clear now playing
   - **Previous/Next**: Navigate tracks (now working with real API)
   - **Repeat**: Cycle through Off/One/All modes
   - **Shuffle**: Toggle shuffle on/off

2. **Volume Control**:
   - **Volume Slider**: Precise volume adjustment (0-100)
   - **Volume +/-**: 3% step volume control (improved from 5%)
   - **Mute Toggle**: Quick mute/unmute

3. **Source Selection**:
   - Click **Sources** button to view available inputs
   - Select from Analog, Digital, HDMI, Bluetooth, Streaming services
   - Current source displayed in media player

4. **Power Control**:
   - **Power On/Off**: Control device power state
   - **Toggle**: Switch between on and standby

### Remote Control

Use the **Naim Device Remote** remote entity for traditional control:

1. **Main Controls**:
   - Transport controls for playback management (all working)
   - Volume up/down (3% steps) and mute buttons
   - Power control for device on/off

2. **Source Selection**:
   - Dedicated button for each available input source
   - Quick switching between favorite sources
   - Audio balance controls

### Multi-Device Management

When using multiple devices:

1. **Independent Control**: Each device operates completely independently
2. **Room-Based Activities**: Create activities for each room/device
3. **Centralized Overview**: All devices visible in integration settings
4. **Synchronized Status**: Real-time status updates for all devices

## Performance & Optimization

### **Intelligent Polling System**
- **Dynamic Updates**: Real-time status monitoring every 5 seconds per device
- **Resource Efficient**: Minimal network traffic and device load
- **Multi-Device Optimization**: Concurrent status updates for all devices
- **Error Recovery**: Automatic reconnection after network interruptions

### **Network Requirements**
- **Local Network**: Integration requires same network as Naim devices
- **Bandwidth**: Minimal (~500 bytes per device per update cycle)
- **Port**: Standard HTTP port 15081 for Naim devices
- **Reliability**: Graceful handling of temporary network issues

### **Entity Persistence**
- **Post-Reboot Stability**: All entities remain available after system restarts
- **State Synchronization**: Real-time sync between remote and devices
- **Configuration Persistence**: Settings survive system reboots

## Troubleshooting

### Common Issues

#### **"Device Not Found" (Multi-Device)**
- Verify all device IP addresses are correct
- Ensure all devices and Remote are on same network
- Check each device is powered on and network connected
- Try using Naim app to verify each device connectivity
- Verify devices don't conflict on same IP address

#### **"Partial Device Setup"**
- Some devices may connect while others fail
- Check failed device IP addresses and network connectivity
- Successfully connected devices will still work
- Re-run setup to add failed devices

#### **"Commands Not Working"**
- Repeat/Shuffle/Next/Prev commands now use working API endpoints
- Ensure device is powered on (not in deep standby)
- Try controlling device directly via Naim app to confirm functionality

#### **"Integration Offline"**
- Check Remote's network connectivity
- Verify each Naim device is still accessible on network
- Restart integration from Remote settings
- Check devices haven't changed IP addresses

### Debug Information

Enable detailed logging for troubleshooting:

**Docker Environment:**
```bash
# Add to docker-compose.yml environment section
- LOG_LEVEL=DEBUG

# View logs
docker logs uc-intg-naim
```

**Multi-Device Verification:**
- **Naim App**: Verify each device appears and responds
- **Network Ping**: Confirm each device IP is reachable
- **Browser Test**: Visit `http://device-ip:15081/nowplaying` for each device

## Limitations

### **Naim API Limitations**
- **Local Network Only**: No remote/internet control of devices
- **Device Dependent**: Feature availability varies by device model and firmware
- **Source Limitations**: Some sources may not support all commands
- **Network Dependency**: Requires continuous network connectivity

### **Integration Limitations**  
- **Maximum Devices**: Up to 10 devices per integration instance
- **Main Zone Only**: Multi-room features not implemented
- **Limited Playlist Support**: Basic playback control, no playlist management
- **No DSP Control**: Room correction and DSP settings not accessible

### **Compatibility Notes**
- **Newer Models**: Latest Naim devices fully supported
- **Older Models**: Basic functionality on devices with HTTP API support
- **Firmware Updates**: Keep device firmware updated for best compatibility

## For Developers

### Local Development

1. **Clone and setup:**
   ```bash
   git clone https://github.com/mase1981/uc-intg-naim.git
   cd uc-intg-naim
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuration:**
   Integration uses environment variables and config files:
   ```bash
   export UC_CONFIG_HOME=./config
   # Config automatically created during setup
   ```

3. **Run development simulator:**
   ```bash
   # Terminal 1: Start multi-device simulator
   python naim_simulator.py --count 3
   
   # Terminal 2: Run integration
   python uc_intg_naim/driver.py
   ```

4. **VS Code debugging:**
   - Open project in VS Code
   - Use F5 to start debugging session
   - Integration runs on `localhost:9090`
   - Use simulator addresses for device IPs

### Testing Multi-Device Setup

```bash
# Test with 3 simulated devices
python naim_simulator.py --count 3

# In integration setup:
# Device count: 3
# Device 1: localhost:8080 (name: Living Room)
# Device 2: localhost:8081 (name: Kitchen) 
# Device 3: localhost:8082 (name: Bedroom)
```

### Project Structure

```
uc-intg-naim/
â"œâ"€â"€ uc_intg_naim/               # Main package
â"‚   â"œâ"€â"€ __init__.py             # Package info  
â"‚   â"œâ"€â"€ client.py               # Naim HTTP API client (enhanced)
â"‚   â"œâ"€â"€ config.py               # Configuration management
â"‚   â"œâ"€â"€ driver.py               # Main integration driver (multi-device)
â"‚   â"œâ"€â"€ media_player.py         # Media player entity (enhanced)
â"‚   â""â"€â"€ remote.py               # Remote control entity (enhanced)
â"œâ"€â"€ .github/workflows/          # GitHub Actions CI/CD
â"‚   â""â"€â"€ build.yml               # Automated build pipeline
â"œâ"€â"€ naim_simulator.py           # Multi-device development simulator
â"œâ"€â"€ docker-compose.yml          # Docker deployment
â"œâ"€â"€ Dockerfile                  # Container build instructions
â"œâ"€â"€ driver.json                 # Integration metadata (enhanced)
â"œâ"€â"€ requirements.txt            # Dependencies
â"œâ"€â"€ pyproject.toml              # Python project config
â""â"€â"€ README.md                   # This file
```

### Development Features

#### **Multi-Device Naim Simulator**
Complete Naim HTTP API simulator for development without hardware:
- **Multiple Device Support**: Simulate 1-10 devices simultaneously
- **Full API Coverage**: All endpoints implemented with working commands
- **Realistic Responses**: Matches real device behavior
- **Unique Device States**: Each simulated device has different content
- **Concurrent Testing**: Perfect for multi-device development

#### **CI/CD Pipeline**
Automated building and deployment:
- **Multi-Architecture**: Builds for amd64 and arm64
- **Docker Images**: Automated GitHub Container Registry publishing
- **Release Artifacts**: Automatic tar.gz generation
- **Version Management**: Semantic versioning with git tags

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test with multi-device simulator
4. Test with real Naim hardware if available
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request


## Advanced Features

### **Entity Persistence Management**
Advanced race condition prevention ensures entities remain available after system reboots:
- **Pre-initialization**: Entities created before UC Remote connection
- **Atomic Creation**: All entities created atomically to prevent timing issues
- **Multi-Device Coordination**: Proper entity management across multiple devices

### **Dynamic Source Detection**
Intelligent input source management:
- **Model-Specific Sources**: Automatic detection based on device capabilities
- **Per-Device Configuration**: Each device maintains its own source list
- **Real-time Updates**: Source list updated when device configuration changes

### **State Synchronization**
Advanced state management between entities:
- **Dual Entity Support**: Media player and remote entities stay synchronized per device
- **Immediate Updates**: WiiM-pattern implementation for instant state display
- **Multi-Device Independence**: Each device operates independently

## Security Considerations

### **Network Security**
- **Local Network Only**: Communication limited to local network
- **No Authentication**: Naim devices typically don't require authentication
- **HTTP Protocol**: Standard HTTP communication on port 15081

### **Privacy**
- **No Data Collection**: Integration doesn't collect or transmit personal data
- **Local Processing**: All processing happens locally on Remote device
- **No Cloud Dependency**: No external services or cloud connectivity required

## Compatibility Matrix

| Device Type | Example Models | Status | Features |
|-------------|----------------|---------|-----------|
| Uniti Atom | All Atom variants | âœ… Tested | Full control, all inputs, streaming, multi-device |
| Uniti Nova | All Nova variants | âœ… Compatible | Full control, preamp functions, multi-device |
| Uniti Star | All Star variants | âœ… Compatible | Full control, CD ripping, streaming, multi-device |
| Uniti Core | Core, Core 2 | âœ… Compatible | Server functions, limited playback, multi-device |
| Legacy Uniti | Original Uniti range | âš ï¸ Limited | Basic control if HTTP API available |

## License

This project is licensed under the Mozilla Public License 2.0 - see the [LICENSE](LICENSE) file for details.

## Credits

- **Developer**: Meir Miyara
- **Naim Audio**: HTTP API specification and device support
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Community**: Testing and feedback from UC community

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-naim/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)

---

**Made with ❤️ for the Unfolded Circle Community** 

**Thank You**: Meir Miyara