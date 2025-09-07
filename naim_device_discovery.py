#!/usr/bin/env python3
"""
Naim Audio Device Discovery Script

This script connects to your Naim device and exports comprehensive
API data to help improve the integration. No external dependencies required.

Usage:
    python naim_device_discovery.py

The script will:
1. Ask for your Naim device IP address and port
2. Connect and query all available API endpoints
3. Generate a detailed report file
4. Create an export file you can share with the developer

:copyright: (c) 2025 by Meir Miyara
:license: MPL-2.0, see LICENSE for more details.
"""

import json
import socket
import sys
import time
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode


class NaimDiscovery:
    """Comprehensive Naim device API discovery."""
    
    def __init__(self):
        self.device_ip = None
        self.device_port = None
        self.base_url = None
        self.api_base = None
        self.device_info = {}
        self.discovery_data = {
            "timestamp": datetime.now().isoformat(),
            "script_version": "1.1.0",
            "device_info": {},
            "api_responses": {},
            "errors": [],
            "warnings": [],
            "summary": {}
        }
        
    def print_header(self):
        """Print script header."""
        print("=" * 70)
        print("🎵 Naim Audio Device Discovery Script v1.1")
        print("=" * 70)
        print("This script will connect to your Naim device and")
        print("export comprehensive API data to help improve the integration.")
        print()
        print("What this script does:")
        print("• Connects to your Naim device")
        print("• Queries all available API endpoints")
        print("• Tests device capabilities and features")
        print("• Generates a detailed report for developers")
        print("• Creates an export file you can share")
        print()
        print("Requirements:")
        print("• Python 3.6+ (already installed)")
        print("• Naim device on same network")
        print("• Device IP address and port (usually 80)")
        print("=" * 70)
        print()
    
    def get_device_details(self):
        """Get device IP and port from user input."""
        while True:
            try:
                ip_input = input("Enter your Naim device IP address (optionally with :port): ").strip()
                if not ip_input:
                    print("❌ Please enter an IP address")
                    continue
                
                # Check if IP:port format is used
                if ':' in ip_input:
                    try:
                        ip, port_str = ip_input.split(':', 1)
                        port = int(port_str)
                    except ValueError:
                        print("❌ Invalid IP:port format. Use format: 192.168.1.100:15081")
                        continue
                else:
                    ip = ip_input
                    # Get port separately
                    port_input = input("Enter device port (press Enter for default 80): ").strip()
                    if not port_input:
                        port = 80
                    else:
                        port = int(port_input)
                
                # Basic IP validation
                parts = ip.split('.')
                if len(parts) != 4:
                    print("❌ Invalid IP format. Use format: 192.168.1.100")
                    continue
                
                for part in parts:
                    if not (0 <= int(part) <= 255):
                        raise ValueError("Invalid IP range")
                
                # Validate port
                if not (1 <= port <= 65535):
                    raise ValueError("Port must be between 1 and 65535")
                
                self.device_ip = ip
                self.device_port = port
                self.base_url = f"http://{ip}:{port}"
                self.api_base = f"{self.base_url}"
                print(f"✅ Using device: {ip}:{port}")
                return True
                
            except ValueError as e:
                print(f"❌ Invalid input: {e}")
            except KeyboardInterrupt:
                print("\n🛑 Discovery cancelled by user")
                return False
    
    def test_connection(self):
        """Test basic connection to device."""
        print("\n🔍 Testing connection to device...")
        
        try:
            # Test basic HTTP connectivity - try various endpoint patterns
            test_endpoints = [
                "/",
                "/naim/",
                "/naim/index.fcgi",
                "/nowplaying",
                "/naim/nowplaying",
                "/system",
                "/naim/system",
                "/status",
                "/naim/status"
            ]
            
            connection_found = False
            api_prefix = ""
            
            for endpoint in test_endpoints:
                response = self.make_request("GET", endpoint)
                if response:
                    print(f"✅ Connected to Naim device via {endpoint}")
                    self.device_info = response
                    connection_found = True
                    
                    # Determine API prefix based on successful endpoint
                    if endpoint.startswith("/naim/"):
                        api_prefix = "/naim"
                        self.api_base = f"{self.base_url}/naim"
                        print(f"🔧 Detected API prefix: {api_prefix}")
                    
                    break
            
            if not connection_found:
                print("❌ No valid endpoints found")
                return False
                
            return True
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def make_request(self, method, endpoint, params=None, data=None, timeout=10):
        """Make HTTP request to device API."""
        # Handle both absolute URLs and relative paths
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.base_url}{endpoint}"
            
        if params:
            url += "?" + urlencode(params)
        
        try:
            if method.upper() == "PUT" and data:
                request = Request(url, data=json.dumps(data).encode('utf-8'), method="PUT")
                request.add_header('Content-Type', 'application/json')
            else:
                request = Request(url)
            
            request.add_header('User-Agent', 'Naim-Discovery/1.1')
            
            with urlopen(request, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                try:
                    return json.loads(response_data)
                except json.JSONDecodeError:
                    # Return raw text for non-JSON responses
                    return {"raw_response": response_data, "status_code": response.status}
                
        except HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.reason}"
            self.discovery_data["errors"].append({
                "endpoint": endpoint,
                "method": method,
                "error": error_msg,
                "type": "http_error"
            })
            return None
            
        except URLError as e:
            error_msg = f"URL Error: {e.reason}"
            self.discovery_data["errors"].append({
                "endpoint": endpoint,
                "method": method,
                "error": error_msg,
                "type": "url_error"
            })
            return None
            
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.discovery_data["errors"].append({
                "endpoint": endpoint,
                "method": method,
                "error": error_msg,
                "type": "unknown_error"
            })
            return None
    
    def discover_core_endpoints(self):
        """Discover core Naim API endpoints."""
        print("\n🔍 Discovering core endpoints...")
        
        # Test both with and without /naim prefix
        api_prefixes = ["", "/naim"]
        
        core_endpoints = [
            # Status and info endpoints
            "/",
            "/index.fcgi",
            "/nowplaying",
            "/system",
            "/status",
            "/info",
            "/deviceinfo",
            "/device",
            "/version",
            "/capabilities",
            
            # Playback control endpoints
            "/playback",
            "/player",
            "/transport",
            "/play",
            "/pause",
            "/stop",
            "/next",
            "/previous",
            "/skip",
            "/back",
            
            # Volume endpoints
            "/volume",
            "/levels",
            "/levels/room",
            "/levels/main",
            "/audio",
            "/mute",
            
            # Input/source endpoints
            "/inputs",
            "/sources",
            "/input",
            "/source",
            
            # Network and system endpoints
            "/network",
            "/settings",
            "/config",
            "/upnp",
            "/streaming",
            "/services",
            
            # WebSocket endpoint
            "/websocket",
            "/ws",
            "/events",
            "/notifications"
        ]
        
        for prefix in api_prefixes:
            print(f"  🔍 Testing API prefix: '{prefix if prefix else '(root)'}'")
            for endpoint in core_endpoints:
                full_endpoint = f"{prefix}{endpoint}"
                short_name = endpoint.split('/')[-1] or "root"
                print(f"    📡 Testing GET {short_name}...", end="")
                
                response = self.make_request("GET", full_endpoint)
                if response:
                    self.discovery_data["api_responses"][f"GET_{full_endpoint}"] = response
                    print(" ✅")
                else:
                    print(" ❌")
    
    def discover_playback_endpoints(self):
        """Discover playback control endpoints."""
        print("\n🔍 Discovering playback endpoints...")
        
        playback_commands = [
            "play", "pause", "stop", "skip", "back", "next", "previous",
            "seek", "shuffle", "repeat", "volume", "mute"
        ]
        
        # Test both with and without /naim prefix
        api_prefixes = ["", "/naim"]
        playback_endpoints = [
            "/playback?cmd={cmd}",
            "/transport?cmd={cmd}",
            "/player?cmd={cmd}",
            "/control?cmd={cmd}",
            "/{cmd}"
        ]
        
        working_endpoints = 0
        for prefix in api_prefixes:
            for cmd in playback_commands:
                print(f"  🎮 Testing command: {cmd} (prefix: {prefix if prefix else 'root'})")
                for endpoint_template in playback_endpoints:
                    full_endpoint = f"{prefix}{endpoint_template.format(cmd=cmd)}"
                    response = self.make_request("GET", full_endpoint)
                    if response:
                        self.discovery_data["api_responses"][f"GET_{full_endpoint}"] = response
                        working_endpoints += 1
                        print(f"    ✅ {full_endpoint}")
                        break  # Found working endpoint for this command
        
        print(f"  📊 Playback endpoints: {working_endpoints} working")
    
    def discover_input_endpoints(self):
        """Discover input/source selection endpoints."""
        print("\n🔍 Discovering input/source endpoints...")
        
        # Common Naim inputs
        inputs = [
            "analog", "ana", "analog1", "analog:1",
            "digital", "dig", "digital1", "digital:1", "digital2", "digital:2", "digital3", "digital:3",
            "bluetooth", "bt",
            "spotify", "spot",
            "tidal",
            "qobuz",
            "usb",
            "airplay",
            "chromecast",
            "upnp",
            "radio", "webradio", "iradio", "internetradio"
        ]
        
        # Test both with and without /naim prefix
        api_prefixes = ["", "/naim"]
        input_endpoints = [
            "/inputs/{input}?cmd=select",
            "/inputs/{input}",
            "/source/{input}",
            "/select/{input}",
            "/input?source={input}",
            "/source?input={input}"
        ]
        
        working_inputs = []
        for prefix in api_prefixes:
            for input_name in inputs:
                print(f"  📻 Testing input: {input_name} (prefix: {prefix if prefix else 'root'})")
                for endpoint_template in input_endpoints:
                    full_endpoint = f"{prefix}{endpoint_template.format(input=input_name)}"
                    response = self.make_request("GET", full_endpoint)
                    if response:
                        self.discovery_data["api_responses"][f"GET_{full_endpoint}"] = response
                        working_inputs.append(input_name)
                        print(f"    ✅ {full_endpoint}")
                        break
        
        print(f"  📊 Working inputs: {len(set(working_inputs))}")
        self.discovery_data["discovered_inputs"] = list(set(working_inputs))
    
    def discover_volume_endpoints(self):
        """Discover volume control endpoints."""
        print("\n🔍 Discovering volume endpoints...")
        
        # Test both with and without /naim prefix
        api_prefixes = ["", "/naim"]
        
        volume_endpoints = [
            # GET endpoints
            ("GET", "/volume"),
            ("GET", "/levels"),
            ("GET", "/levels/room"),
            ("GET", "/levels/main"),
            ("GET", "/audio"),
            ("GET", "/audio/volume"),
            
            # PUT endpoints for setting volume
            ("PUT", "/volume?level=50"),
            ("PUT", "/levels/room?volume=50"),
            ("PUT", "/levels/room?level=50"),
            ("PUT", "/audio?volume=50"),
            ("PUT", "/volume"),  # with JSON data
            
            # Mute endpoints
            ("GET", "/mute"),
            ("PUT", "/mute?state=on"),
            ("PUT", "/mute?state=off"),
            ("PUT", "/levels/room?mute=on"),
            ("PUT", "/levels/room?mute=off"),
        ]
        
        working_endpoints = 0
        for prefix in api_prefixes:
            for method, endpoint in volume_endpoints:
                full_endpoint = f"{prefix}{endpoint}"
                print(f"  🔊 Testing {method} {full_endpoint}...", end="")
                
                if method == "PUT" and "volume" in endpoint and "?" not in endpoint:
                    # Test with JSON data
                    response = self.make_request(method, full_endpoint, data={"volume": 50})
                else:
                    response = self.make_request(method, full_endpoint)
                    
                if response:
                    self.discovery_data["api_responses"][f"{method}_{full_endpoint}"] = response
                    working_endpoints += 1
                    print(" ✅")
                else:
                    print(" ❌")
        
        print(f"  📊 Volume endpoints: {working_endpoints} working")
    
    def discover_power_endpoints(self):
        """Discover power control endpoints."""
        print("\n🔍 Discovering power endpoints...")
        
        # Test both with and without /naim prefix
        api_prefixes = ["", "/naim"]
        
        power_endpoints = [
            # GET endpoints
            ("GET", "/power", None),
            ("GET", "/system", None),
            ("GET", "/power/status", None),
            ("GET", "/system/power", None),
            
            # PUT endpoints for power control (testing with safe values)
            ("PUT", "/power", {"system": "on"}),
            ("PUT", "/power", {"system": "standby"}),
            ("PUT", "/system", {"power": "on"}),
            ("PUT", "/system/power", {"state": "on"}),
        ]
        
        working_endpoints = 0
        for prefix in api_prefixes:
            for method, endpoint, data in power_endpoints:
                full_endpoint = f"{prefix}{endpoint}"
                print(f"  ⚡ Testing {method} {full_endpoint}...", end="")
                
                response = self.make_request(method, full_endpoint, data=data)
                if response:
                    self.discovery_data["api_responses"][f"{method}_{full_endpoint}"] = response
                    working_endpoints += 1
                    print(" ✅")
                else:
                    print(" ❌")
        
        print(f"  📊 Power endpoints: {working_endpoints} working")
    
    def test_websocket_endpoint(self):
        """Test WebSocket endpoint availability."""
        print("\n🔍 Testing WebSocket endpoint...")
        
        # Test both with and without /naim prefix
        api_prefixes = ["", "/naim"]
        websocket_paths = [
            "/websocket",
            "/ws",
            "/events",
            "/notifications",
            "/stream",
            "/live"
        ]
        
        for prefix in api_prefixes:
            for path in websocket_paths:
                full_path = f"{prefix}{path}"
                try:
                    # Test if WebSocket endpoint responds to HTTP request
                    response = self.make_request("GET", full_path)
                    if response:
                        print(f"  ✅ WebSocket endpoint found: {full_path}")
                        self.discovery_data["websocket_endpoint"] = full_path
                        return
                except Exception:
                    continue
        
        print("  ❌ No WebSocket endpoint found")
    
    def discover_streaming_services(self):
        """Discover available streaming services."""
        print("\n🔍 Testing streaming services...")
        
        streaming_services = [
            "spotify", "tidal", "qobuz", "deezer", "amazon", "apple",
            "pandora", "sirius", "lastfm", "soundcloud", "bandcamp"
        ]
        
        # Test both with and without /naim prefix
        api_prefixes = ["", "/naim"]
        service_endpoints = [
            "/services/{service}",
            "/streaming/{service}",
            "/{service}",
            "/inputs/{service}",
            "/sources/{service}"
        ]
        
        detected_services = []
        for prefix in api_prefixes:
            for service in streaming_services:
                print(f"  🌍 Testing service: {service} (prefix: {prefix if prefix else 'root'})")
                for endpoint_template in service_endpoints:
                    full_endpoint = f"{prefix}{endpoint_template.format(service=service)}"
                    response = self.make_request("GET", full_endpoint)
                    if response:
                        detected_services.append(service)
                        self.discovery_data["api_responses"][f"GET_{full_endpoint}"] = response
                        print(f"    ✅ {full_endpoint}")
                        break
        
        if detected_services:
            self.discovery_data["streaming_services"] = list(set(detected_services))
            print(f"    ✅ Detected services: {', '.join(set(detected_services))}")
        else:
            print("    ❌ No streaming services detected")
    
    def test_special_features(self):
        """Test device-specific special features."""
        print("\n🔍 Testing special device features...")
        
        # Test both with and without /naim prefix
        api_prefixes = ["", "/naim"]
        
        # Test advanced features
        special_endpoints = [
            ("/presets", "Presets"),
            ("/playlist", "Playlists"),
            ("/queue", "Play Queue"),
            ("/favorites", "Favorites"),
            ("/equalizer", "Equalizer"),
            ("/eq", "EQ Settings"),
            ("/dsp", "DSP Settings"),
            ("/balance", "Balance Control"),
            ("/crossover", "Crossover"),
            ("/room", "Room Correction"),
            ("/upnp/browse", "UPnP Browse"),
            ("/metadata", "Metadata"),
            ("/artwork", "Artwork"),
            ("/search", "Search"),
            ("/browse", "Browse")
        ]
        
        detected_features = []
        for prefix in api_prefixes:
            for endpoint, feature_name in special_endpoints:
                full_endpoint = f"{prefix}{endpoint}"
                print(f"  🛠️  Testing {feature_name} ({full_endpoint})...")
                response = self.make_request("GET", full_endpoint)
                if response:
                    detected_features.append(feature_name)
                    self.discovery_data["api_responses"][f"GET_{full_endpoint}"] = response
                    print(f"    ✅ {feature_name} supported")
                else:
                    print(f"    ❌ {feature_name} not available")
        
        if detected_features:
            self.discovery_data["special_features"] = list(set(detected_features))
            print(f"  📊 Special features: {len(set(detected_features))} detected")
        else:
            print("  📊 No special features detected")
    
    def analyze_capabilities(self):
        """Analyze device capabilities based on discovered data."""
        print("\n📊 Analyzing device capabilities...")
        
        capabilities = {
            "inputs": [],
            "streaming_services": [],
            "special_features": [],
            "api_coverage": {},
            "power_control": False,
            "volume_control": False,
            "playback_control": False,
            "websocket_support": False
        }
        
        # Analyze discovered inputs
        capabilities["inputs"] = self.discovery_data.get("discovered_inputs", [])
        
        # Analyze streaming services
        capabilities["streaming_services"] = self.discovery_data.get("streaming_services", [])
        
        # Analyze special features
        capabilities["special_features"] = self.discovery_data.get("special_features", [])
        
        # Check for control capabilities
        for key in self.discovery_data["api_responses"]:
            if "power" in key or "system" in key:
                capabilities["power_control"] = True
            if "volume" in key or "levels" in key or "mute" in key:
                capabilities["volume_control"] = True
            if "playback" in key or "play" in key or "transport" in key:
                capabilities["playback_control"] = True
        
        # Check WebSocket support
        capabilities["websocket_support"] = "websocket_endpoint" in self.discovery_data
        
        # Count API coverage
        total_endpoints = len(self.discovery_data["api_responses"])
        total_errors = len(self.discovery_data["errors"])
        
        capabilities["api_coverage"] = {
            "working_endpoints": total_endpoints,
            "failed_endpoints": total_errors,
            "success_rate": f"{(total_endpoints / (total_endpoints + total_errors) * 100):.1f}%" if (total_endpoints + total_errors) > 0 else "0%"
        }
        
        self.discovery_data["capabilities"] = capabilities
        
        print(f"  📻 Inputs detected: {len(capabilities['inputs'])}")
        print(f"  🌍 Streaming services: {len(capabilities['streaming_services'])}")
        print(f"  🛠️  Special features: {len(capabilities['special_features'])}")
        print(f"  📡 API coverage: {capabilities['api_coverage']['success_rate']}")
        print(f"  ⚡ Power control: {'Yes' if capabilities['power_control'] else 'No'}")
        print(f"  🔊 Volume control: {'Yes' if capabilities['volume_control'] else 'No'}")
        print(f"  🎮 Playback control: {'Yes' if capabilities['playback_control'] else 'No'}")
        print(f"  🔌 WebSocket support: {'Yes' if capabilities['websocket_support'] else 'No'}")
    
    def generate_summary(self):
        """Generate discovery summary."""
        # Extract device info from successful responses
        device_info = {}
        for key, response in self.discovery_data["api_responses"].items():
            if isinstance(response, dict):
                if "model" in response or "device" in response or "name" in response:
                    device_info = response
                    break
        
        summary = {
            "device_model": device_info.get("model", device_info.get("model_name", "Unknown")),
            "device_id": device_info.get("device_id", device_info.get("id", "Unknown")),
            "device_name": device_info.get("device_name", device_info.get("name", "Unknown")),
            "system_version": device_info.get("system_version", device_info.get("version", "Unknown")),
            "api_version": device_info.get("api_version", "Unknown"),
            "device_ip": self.device_ip,
            "device_port": self.device_port,
            "discovery_timestamp": self.discovery_data["timestamp"],
            "total_endpoints_tested": len(self.discovery_data["api_responses"]) + len(self.discovery_data["errors"]),
            "successful_endpoints": len(self.discovery_data["api_responses"]),
            "failed_endpoints": len(self.discovery_data["errors"]),
            "capabilities_found": len(self.discovery_data.get("capabilities", {})),
            "inputs_detected": len(self.discovery_data.get("discovered_inputs", [])),
            "streaming_services": len(self.discovery_data.get("streaming_services", [])),
        }
        
        self.discovery_data["summary"] = summary
    
    def save_results(self):
        """Save discovery results to files."""
        print("\n💾 Saving discovery results...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        device_model = self.discovery_data["summary"].get("device_model", "Unknown").replace(" ", "_")
        
        # Create detailed report filename
        report_filename = f"naim_discovery_{device_model}_{self.device_ip}_{timestamp}.json"
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(self.discovery_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Detailed report saved: {report_filename}")
            
            # Create user-friendly summary
            summary_filename = f"naim_summary_{device_model}_{self.device_ip}_{timestamp}.txt"
            with open(summary_filename, 'w', encoding='utf-8') as f:
                f.write("🎵 Naim Audio Device Discovery Summary\n")
                f.write("=" * 50 + "\n\n")
                
                summary = self.discovery_data["summary"]
                f.write(f"Device Model: {summary['device_model']}\n")
                f.write(f"Device ID: {summary['device_id']}\n")
                f.write(f"Device Name: {summary['device_name']}\n")
                f.write(f"Device IP: {summary['device_ip']}:{summary['device_port']}\n")
                f.write(f"System Version: {summary['system_version']}\n")
                f.write(f"API Version: {summary['api_version']}\n")
                f.write(f"Discovery Date: {summary['discovery_timestamp']}\n\n")
                
                f.write("📊 API Discovery Results:\n")
                f.write(f"• Total endpoints tested: {summary['total_endpoints_tested']}\n")
                f.write(f"• Successful endpoints: {summary['successful_endpoints']}\n")
                f.write(f"• Failed endpoints: {summary['failed_endpoints']}\n")
                f.write(f"• Success rate: {(summary['successful_endpoints']/summary['total_endpoints_tested']*100):.1f}%\n\n")
                
                capabilities = self.discovery_data.get("capabilities", {})
                if capabilities:
                    f.write("🎛️  Device Capabilities:\n")
                    f.write(f"• Power control: {'Yes' if capabilities.get('power_control') else 'No'}\n")
                    f.write(f"• Volume control: {'Yes' if capabilities.get('volume_control') else 'No'}\n")
                    f.write(f"• Playback control: {'Yes' if capabilities.get('playback_control') else 'No'}\n")
                    f.write(f"• WebSocket support: {'Yes' if capabilities.get('websocket_support') else 'No'}\n")
                    f.write(f"• Inputs: {', '.join(capabilities.get('inputs', []))}\n")
                    if capabilities.get('special_features'):
                        f.write(f"• Special Features: {', '.join(capabilities['special_features'])}\n")
                    f.write("\n")
                
                if self.discovery_data.get("streaming_services"):
                    f.write(f"🌍 Streaming Services: {', '.join(self.discovery_data['streaming_services'])}\n\n")
                
                f.write("📁 Files Generated:\n")
                f.write(f"• Detailed report: {report_filename}\n")
                f.write(f"• This summary: {summary_filename}\n\n")
                
                f.write("📤 Next Steps:\n")
                f.write("1. Send the detailed report file to the developer\n")
                f.write("2. Include your device model and any special features\n")
                f.write("3. Mention any functions you'd like to see added\n\n")
                
                f.write("Thank you for helping improve the Naim integration!\n")
            
            print(f"✅ Summary report saved: {summary_filename}")
            
            return report_filename, summary_filename
            
        except Exception as e:
            print(f"❌ Error saving files: {e}")
            return None, None
    
    def run_discovery(self):
        """Run complete discovery process."""
        self.print_header()
        
        # Get device details
        if not self.get_device_details():
            return False
        
        # Test connection
        if not self.test_connection():
            print("\n❌ Cannot connect to device. Please check:")
            print("• Device IP address and port are correct")
            print("• Device is powered on and connected to network")
            print("• Device and computer are on same network")
            print("• No firewall blocking the connection")
            print("• Try port 80 if using a different port")
            return False
        
        # Store device info
        self.discovery_data["device_info"] = self.device_info
        
        # Run discovery
        print("\n🚀 Starting comprehensive API discovery...")
        print("This may take a few minutes...")
        
        self.discover_core_endpoints()
        self.discover_playback_endpoints()
        self.discover_input_endpoints()
        self.discover_volume_endpoints()
        self.discover_power_endpoints()
        self.test_websocket_endpoint()
        self.discover_streaming_services()
        self.test_special_features()
        self.analyze_capabilities()
        self.generate_summary()
        
        # Save results
        report_file, summary_file = self.save_results()
        
        if report_file and summary_file:
            print("\n🎉 Discovery completed successfully!")
            print("\n📋 Summary:")
            summary = self.discovery_data["summary"]
            print(f"• Device: {summary['device_model']} ({summary['device_id']})")
            print(f"• Location: {summary['device_ip']}:{summary['device_port']}")
            print(f"• API endpoints found: {summary['successful_endpoints']}")
            print(f"• Input sources: {summary['inputs_detected']}")
            print(f"• Streaming services: {summary['streaming_services']}")
            
            capabilities = self.discovery_data.get("capabilities", {})
            print(f"• Power control: {'Yes' if capabilities.get('power_control') else 'No'}")
            print(f"• Volume control: {'Yes' if capabilities.get('volume_control') else 'No'}")
            print(f"• Playback control: {'Yes' if capabilities.get('playback_control') else 'No'}")
            print(f"• WebSocket support: {'Yes' if capabilities.get('websocket_support') else 'No'}")
            
            print(f"\n📁 Files created:")
            print(f"• {report_file} (send this to developer)")
            print(f"• {summary_file} (human-readable summary)")
            
            print(f"\n📤 Next steps:")
            print(f"1. Send '{report_file}' to the developer")
            print(f"2. Include device model and any special requests")
            print(f"3. The developer will use this to enhance the integration")
            
            print(f"\nThank you for helping improve the Naim integration!")
            return True
        else:
            print("\n❌ Discovery completed but failed to save results")
            return False


def main():
    """Main entry point."""
    try:
        discovery = NaimDiscovery()
        success = discovery.run_discovery()
        
        if success:
            input("\nPress Enter to exit...")
        else:
            input("\nPress Enter to exit...")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Discovery cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please report this error to the developer")
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()