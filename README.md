# Naim Audio Integration for Unfolded Circle Remote 2/3

Control your Naim audio devices directly from your Unfolded Circle Remote 2 or Remote 3.

![Naim Audio](https://img.shields.io/badge/Naim-Audio-blue)
![Version](https://img.shields.io/badge/version-1.0.0-green)
![License](https://img.shields.io/badge/license-MPL--2.0-blue)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)

## Features

This integration provides comprehensive control of your Naim audio devices directly from your Unfolded Circle Remote, supporting all inputs, volume control, and playback functions across the entire Naim range.

### 🎵 **Media Player Control**

Transform your remote into a powerful Naim controller with full device management:

#### **Playback Control**
- **Play/Pause** - Seamless playback control with visual feedback
- **Stop** - Stop current playback and clear now playing
- **Previous/Next Track** - Navigate through your music collection
- **Volume Control** - Precise volume adjustment with 5% step controls
- **Mute Toggle** - Quick mute/unmute functionality

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
- **Balance Control** - Audio balance adjustment

### 🎮 **Remote Control Interface**

Comprehensive Naim device control through dedicated remote entity:

#### **Main Controls**
- **Transport Controls** - Play/Pause, Previous, Next, Stop
- **Volume Management** - Volume Up/Down, Mute toggle
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

#### **Two-Entity Integration**
- **Media Player Entity**: Primary control interface with full media features
- **Remote Entity**: Button-based control for traditional remote experience
- **Synchronized State**: Both entities reflect real device status

#### **Smart State Management**
- **Playing State**: Device on and actively playing content
- **Paused State**: Device on but playback paused
- **Standby State**: Device in standby/off mode
- **Source Indication**: Current input source clearly displayed

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
4. Go to **Settings** → **Integrations** → **Add Integration**
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

**Docker Run:**
```bash
docker run -d --restart=unless-stopped --net=host \
  -v $(pwd)/data:/data \
  -e UC_CONFIG_HOME=/data \
  -e UC_INTEGRATION_INTERFACE=0.0.0.0 \
  -e UC_INTEGRATION_HTTP_PORT=9090 \
  -e UC_DISABLE_MDNS_PUBLISH=false \
  --name uc-intg-naim \
  ghcr.io/mase1981/uc-intg-naim:latest
```

**Specific Version:**
```bash
# Replace v1.0.1 with desired version
docker pull ghcr.io/mase1981/uc-intg-naim:v1.0.1
docker run -d --restart=unless-stopped --net=host \
  -v $(pwd)/data:/data \
  -e UC_CONFIG_HOME=/data \
  --name uc-intg-naim \
  ghcr.io/mase1981/uc-intg-naim:v1.0.1
```

### Option 3: Development Simulator
For testing without physical hardware:

**Run Simulator:**
```bash
# In separate terminal
python naim_simulator.py

# Simulator runs on http://localhost:8080
# Use 'localhost:8080' as device IP during setup
```

## Configuration

### Step 1: Prepare Your Naim Device

1. **Network Setup:**
   - Connect device to your local network (WiFi or Ethernet)
   - Note the device's IP address from your router or device display
   - Ensure device is powered on and network connected

2. **Naim App Verification:**
   - Download Naim app to verify device connectivity
   - Confirm device appears and is controllable in the app
   - Test basic functions like play/pause and volume

3. **Network Requirements:**
   - Device and Remote must be on same local network
   - HTTP communication on port 15081 (standard Naim port)
   - No firewall blocking required

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The Naim Audio integration should appear in **Available Integrations**
3. Click **"Configure"** and follow the setup wizard:

   **Device Connection:**
   - **IP Address**: Your Naim device IP address (e.g., 192.168.1.100 or 192.168.1.100:15081)
   - **Auto-Discovery**: Integration attempts to find devices automatically
   - **Manual Entry**: Enter IP address if auto-discovery fails

4. Click **"Test Connection"** to verify device communication
5. Integration will detect available input sources automatically
6. Click **"Complete Setup"** when connection is successful
7. Two entities will be created:
   - **[Device Name]** (Media Player)
   - **[Device Name] Remote** (Remote Control)

### Step 3: Add Entities to Activities

1. Go to **Activities** in your remote interface
2. Edit or create an activity
3. Add Naim entities from the **Available Entities** list:
   - **Naim Device** (Media Player) - Primary control interface
   - **Naim Device Remote** (Remote) - Button-based control
4. Configure button mappings and UI layout as desired
5. Save your activity

## Usage

### Media Player Control

Use the **Naim Device** media player entity:

1. **Playback Control**:
   - **Play/Pause**: Toggle playback state
   - **Stop**: Stop playback and clear now playing
   - **Previous/Next**: Navigate tracks in current playlist/source

2. **Volume Control**:
   - **Volume Slider**: Precise volume adjustment (0-100)
   - **Volume +/-**: 5% step volume control
   - **Mute Toggle**: Quick mute/unmute

3. **Source Selection**:
   - Click **Sources** button to view available inputs
   - Select from Analog, Digital, HDMI, Bluetooth, Streaming services
   - Current source displayed in media player

4. **Power Control**:
   - **Power On/Off**: Control device power state
   - **Toggle**: Switch between on and standby
   - **Standby Monitoring**: Optional monitoring when device is off

### Remote Control

Use the **Naim Device Remote** remote entity:

1. **Main Controls**:
   - Transport controls for playback management
   - Volume up/down and mute buttons
   - Power control for device on/off

2. **Source Selection**:
   - Dedicated button for each available input source
   - Quick switching between favorite sources
   - Audio balance controls

### Status Monitoring

#### **Media Player States**
- **Playing**: Device on and actively playing content with transport controls
- **Paused**: Device on but playback paused, ready to resume
- **Stopped**: Device on but no active playback
- **Standby**: Device in standby/off mode

#### **Source Information**
- Current input source always displayed
- Automatic detection of available sources based on device model
- Real-time source switching feedback

#### **Now Playing Display**
- Track title, artist, and album information
- Album artwork when available from streaming services
- Playback position and total duration for supported sources

## Performance & Optimization

### **Intelligent Polling System**
- **Dynamic Updates**: Real-time status monitoring every 5 seconds
- **Resource Efficient**: Minimal network traffic and device load
- **Race Condition Prevention**: Advanced entity persistence management
- **Error Recovery**: Automatic reconnection after network interruptions

### **Network Requirements**
- **Local Network**: Integration requires same network as Naim device
- **Bandwidth**: Minimal (~500 bytes per update cycle)
- **Port**: Standard HTTP port 15081 for Naim devices
- **Reliability**: Graceful handling of temporary network issues

### **Entity Persistence**
- **Post-Reboot Stability**: Entities remain available after system restarts
- **State Synchronization**: Real-time sync between remote and device
- **Configuration Persistence**: Settings survive system reboots

## Troubleshooting

### Common Issues

#### **"Device Not Found"**
- Verify Naim device IP address is correct
- Ensure device and Remote are on same network
- Check device is powered on and network connected
- Try using Naim app to verify device connectivity
- Check if device uses custom port (default is 15081)

#### **"Connection Failed"**
- Confirm device IP address in integration settings
- Check network connectivity between Remote and device
- Verify no firewall blocking communication on port 15081
- Ensure device supports HTTP API (most modern Naim devices do)
- Try connecting from Naim mobile app first

#### **"Sources Not Available"**
- Verify device inputs are properly connected
- Check device input configuration in Naim settings
- Restart integration to refresh source list
- Some sources may require firmware updates to appear

#### **"Commands Not Working"**
- Ensure device is powered on (not in deep standby)
- Verify current source supports the requested command
- Check device isn't in a restricted mode
- Try controlling device directly via Naim app to confirm functionality

#### **"Integration Offline"**
- Check Remote's network connectivity
- Verify Naim device is still accessible on network
- Restart integration from Remote settings
- Check device hasn't changed IP address

### Debug Information

Enable detailed logging for troubleshooting:

**Docker Environment:**
```bash
# Add to docker-compose.yml environment section
- LOG_LEVEL=DEBUG

# View logs
docker logs uc-intg-naim
```

**Integration Logs:**
- **Remote Interface**: Settings → Integrations → Naim Audio → View Logs
- **Common Errors**: Connection timeouts, API response errors, source detection issues

**Device Verification:**
- **Naim App**: Verify device appears and responds
- **Network Ping**: Confirm device IP is reachable
- **Browser Test**: Visit `http://device-ip:15081/nowplaying` (should return JSON)

## Limitations

### **Naim API Limitations**
- **Local Network Only**: No remote/internet control of devices
- **Device Dependent**: Feature availability varies by device model and firmware
- **Source Limitations**: Some sources may not support all commands
- **Network Dependency**: Requires continuous network connectivity

### **Integration Limitations**  
- **Single Device**: Currently supports one Naim device per integration instance
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
   # Terminal 1: Start simulator
   python naim_simulator.py
   
   # Terminal 2: Run integration
   python uc_intg_naim/driver.py
   ```

4. **VS Code debugging:**
   - Open project in VS Code
   - Use F5 to start debugging session
   - Integration runs on `localhost:9090`
   - Use `localhost:8080` as device IP to connect to simulator

### Project Structure

```
uc-intg-naim/
├── uc_intg_naim/               # Main package
│   ├── __init__.py             # Package info  
│   ├── client.py               # Naim HTTP API client
│   ├── config.py               # Configuration management
│   ├── driver.py               # Main integration driver
│   ├── media_player.py         # Media player entity
│   └── remote.py               # Remote control entity
├── .github/workflows/          # GitHub Actions CI/CD
│   └── build.yml               # Automated build pipeline
├── naim_simulator.py           # Development simulator
├── docker-compose.yml          # Docker deployment
├── Dockerfile                  # Container build instructions
├── driver.json                 # Integration metadata
├── requirements.txt            # Dependencies
├── pyproject.toml              # Python project config
└── README.md                   # This file
```

### Testing

```bash
# Install test dependencies
pip install -r requirements.txt

# Run with simulator
python naim_simulator.py  # Terminal 1
python uc_intg_naim/driver.py  # Terminal 2

# Test with real hardware
# Configure integration with actual Naim device IP
```

### Development Features

#### **Naim Simulator**
Complete Naim HTTP API simulator for development without hardware:
- **Full API Coverage**: All endpoints implemented
- **Realistic Responses**: Matches real device behavior
- **State Management**: Persistent state across requests
- **Multiple Device Models**: Simulates different Naim models

#### **CI/CD Pipeline**
Automated building and deployment:
- **Multi-Architecture**: Builds for amd64 and arm64
- **Docker Images**: Automated GitHub Container Registry publishing
- **Release Artifacts**: Automatic tar.gz generation
- **Version Management**: Semantic versioning with git tags

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test with simulator
4. Test with real Naim hardware if available
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## Advanced Features

### **Entity Persistence Management**
Advanced race condition prevention ensures entities remain available after system reboots:
- **Pre-initialization**: Entities created before UC Remote connection
- **Atomic Creation**: All entities created atomically to prevent timing issues
- **State Guards**: Protection against subscription before entity readiness

### **Dynamic Source Detection**
Intelligent input source management:
- **Model-Specific Sources**: Automatic detection based on device capabilities
- **Friendly Names**: Technical input IDs mapped to user-friendly names
- **Real-time Updates**: Source list updated when device configuration changes

### **State Synchronization**
Advanced state management between entities:
- **Dual Entity Support**: Media player and remote entities stay synchronized
- **Immediate Updates**: WiiM-pattern implementation for instant state display
- **Attribute Persistence**: State maintained across connection interruptions

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
| Uniti Atom | All Atom variants | ✅ Tested | Full control, all inputs, streaming |
| Uniti Nova | All Nova variants | ✅ Compatible | Full control, preamp functions |
| Uniti Star | All Star variants | ✅ Compatible | Full control, CD ripping, streaming |
| Uniti Core | Core, Core 2 | ✅ Compatible | Server functions, limited playback |
| Legacy Uniti | Original Uniti range | ⚠️ Limited | Basic control if HTTP API available |

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