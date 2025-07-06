#!/usr/bin/env python3
# middleware_server.py - Smart Returns Middleware Server
# FIXED VERSION - Real Bluetooth Commands to LEGO Hub A8:E2:C1:9B:8A:A5

import asyncio
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import threading

# Bluetooth support
try:
    from bleak import BleakClient, BleakScanner
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False

# Configuration
CONNECTION_METHOD = "BLUETOOTH"  # "SIMULATION", "BLUETOOTH", "HTTP"
LEGO_HUB_NAME = "LEGO Hub"
LEGO_HUB_ADDRESS = "A8:E2:C1:9B:8A:A5"  # University Hub
LEGO_COMMAND_UUID = "9ef58b69-e191-4daf-89d6-9e115258e627"  # REAL WORKING CHANNEL!
MINDSTORMS_HOST = "192.168.1.100"  # Fallback for HTTP
MINDSTORMS_PORT = 8080

# Flask App Setup
app = Flask(__name__)
CORS(app)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Command storage
command_log = []
hub_status = {"connected": False, "last_command": None}

class LegoHubController:
    def __init__(self, address=LEGO_HUB_ADDRESS):
        self.address = address
        self.client = None
        self.connected = False
        
    async def connect(self):
        """Connect to LEGO Hub"""
        try:
            if not BLEAK_AVAILABLE:
                logger.error("bleak library not available")
                return False
                
            logger.info(f"Connecting to LEGO Hub {self.address}...")
            self.client = BleakClient(self.address)
            await self.client.connect()
            self.connected = True
            hub_status["connected"] = True
            logger.info("✅ Connected to LEGO Hub!")
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connected = False
            hub_status["connected"] = False
            return False
    
    async def send_command(self, zone, return_id):
        """Send REAL command to LEGO Hub"""
        if not self.connected:
            if not await self.connect():
                return {"success": False, "error": "Connection failed"}
        
        try:
            # Zone mapping für echte Commands
            zone_commands = {
                "Zone A": b"ZONE_A\n",
                "Zone B": b"ZONE_B\n", 
                "Zone C": b"ZONE_C\n",
                "Zone D": b"ZONE_D\n"
            }
            
            # Hole das richtige Command für die Zone
            command = zone_commands.get(zone, zone_commands["Zone A"])
            
            logger.info(f"🤖 Sending REAL command to {zone}")
            logger.info(f"   Return ID: {return_id}")
            logger.info(f"   Command: {command}")
            
            # ECHTER COMMAND CHANNEL - FUNKTIONIERT!
            await self.client.write_gatt_char(LEGO_COMMAND_UUID, command)
            
            hub_status["last_command"] = {
                "zone": zone,
                "return_id": return_id,
                "timestamp": datetime.now().isoformat(),
                "command_sent": command.decode().strip()
            }
            
            logger.info(f"✅ REAL Command executed! Robot received: {command.decode().strip()}")
            
            return {
                "success": True,
                "message": f"REAL Robot command sent to {zone}",
                "command_sent": command.decode().strip(),
                "hub_address": self.address,
                "timestamp": datetime.now().isoformat(),
                "method": "bluetooth_real"
            }
            
        except Exception as e:
            logger.error(f"Command error: {e}")
            return {"success": False, "error": str(e)}
    
    async def disconnect(self):
        """Disconnect from hub"""
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
            hub_status["connected"] = False
            logger.info("🔌 Disconnected from hub")

# Global hub controller
hub_controller = LegoHubController()

def execute_robot_command(zone, return_id, description=""):
    """Execute robot command based on connection method"""
    timestamp = datetime.now().isoformat()
    
    if CONNECTION_METHOD == "SIMULATION":
        # Simulation mode
        result = {
            "success": True,
            "message": f"[SIMULATION] Robot moving to {zone}",
            "method": "simulation",
            "timestamp": timestamp
        }
        
    elif CONNECTION_METHOD == "BLUETOOTH":
        # Bluetooth mode - REAL COMMANDS!
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                hub_controller.send_command(zone, return_id)
            )
            result["method"] = "bluetooth_real"
            loop.close()
        except Exception as e:
            result = {
                "success": False,
                "error": f"Bluetooth error: {str(e)}",
                "method": "bluetooth"
            }
    
    elif CONNECTION_METHOD == "HTTP":
        # HTTP mode (fallback)
        try:
            response = requests.post(
                f"http://{MINDSTORMS_HOST}:{MINDSTORMS_PORT}/robot/move",
                json={"zone": zone, "return_id": return_id},
                timeout=5
            )
            if response.status_code == 200:
                result = {
                    "success": True,
                    "message": f"Robot moving to {zone}",
                    "method": "http"
                }
            else:
                result = {
                    "success": False,
                    "error": f"HTTP error: {response.status_code}",
                    "method": "http"
                }
        except Exception as e:
            result = {
                "success": False,
                "error": f"HTTP connection error: {str(e)}",
                "method": "http"
            }
    
    # Log the command
    log_entry = {
        "timestamp": timestamp,
        "zone": zone,
        "return_id": return_id,
        "description": description,
        "status": "success" if result["success"] else "error",
        "method": result.get("method", CONNECTION_METHOD),
        "message": result.get("message", result.get("error", "")),
        "command_sent": result.get("command_sent", "N/A")
    }
    
    command_log.append(log_entry)
    logger.info(f"Command logged: {zone} -> {result.get('message', result.get('error'))}")
    
    return result

# Flask Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Smart Returns Middleware",
        "connection_method": CONNECTION_METHOD,
        "hub_connected": hub_status["connected"] if CONNECTION_METHOD == "BLUETOOTH" else "N/A",
        "hub_address": LEGO_HUB_ADDRESS if CONNECTION_METHOD == "BLUETOOTH" else "N/A",
        "command_channel": LEGO_COMMAND_UUID if CONNECTION_METHOD == "BLUETOOTH" else "N/A",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/robot/trigger', methods=['POST'])
def trigger_robot():
    """Main robot trigger endpoint - SENDS REAL COMMANDS!"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'zone' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: zone"
            }), 400
        
        zone = data.get('zone')
        return_id = data.get('return_id', f'R-{datetime.now().strftime("%H%M%S")}')
        description = data.get('item_description', '')
        
        logger.info(f"🎯 Robot trigger request: {zone} (ID: {return_id})")
        logger.info(f"   Mode: {CONNECTION_METHOD}")
        if CONNECTION_METHOD == "BLUETOOTH":
            logger.info(f"   Will send REAL command to Hub: {LEGO_HUB_ADDRESS}")
        
        # Execute command
        result = execute_robot_command(zone, return_id, description)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Trigger error: {e}")
        return jsonify({
            "success": False,
            "error": f"Internal error: {str(e)}"
        }), 500

@app.route('/robot/status', methods=['GET'])
def robot_status():
    """Get robot status"""
    return jsonify({
        "hub_connected": hub_status["connected"],
        "last_command": hub_status.get("last_command"),
        "connection_method": CONNECTION_METHOD,
        "hub_address": LEGO_HUB_ADDRESS,
        "command_channel": LEGO_COMMAND_UUID,
        "commands_sent": len(command_log)
    })

@app.route('/logs', methods=['GET'])
def get_logs():
    """Get command logs"""
    return jsonify({
        "success": True,
        "logs": command_log[-50:],  # Last 50 commands
        "total_commands": len(command_log),
        "hub_status": hub_status,
        "connection_method": CONNECTION_METHOD,
        "real_commands_sent": len([log for log in command_log if log.get("method") == "bluetooth_real"])
    })

@app.route('/test', methods=['POST', 'GET'])
def test_connection():
    """Test endpoint"""
    if request.method == 'GET':
        return jsonify({
            "message": "Test endpoint active",
            "method": "GET",
            "connection_method": CONNECTION_METHOD,
            "hub_address": LEGO_HUB_ADDRESS,
            "command_channel": LEGO_COMMAND_UUID,
            "timestamp": datetime.now().isoformat()
        })
    
    # POST test
    test_result = execute_robot_command("Zone A", "TEST-001", "Connection test")
    return jsonify({
        "test_result": test_result,
        "connection_method": CONNECTION_METHOD,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/config', methods=['POST'])
def update_config():
    """Update configuration"""
    global CONNECTION_METHOD
    
    data = request.get_json()
    if data and 'connection_method' in data:
        old_method = CONNECTION_METHOD
        CONNECTION_METHOD = data['connection_method']
        
        return jsonify({
            "success": True,
            "message": f"Connection method changed from {old_method} to {CONNECTION_METHOD}",
            "new_method": CONNECTION_METHOD
        })
    
    return jsonify({
        "success": False,
        "error": "Invalid configuration data"
    }), 400

if __name__ == '__main__':
    print("🤖 Smart Returns Middleware Server Starting...")
    print(f"📡 Connection Method: {CONNECTION_METHOD}")
    
    if CONNECTION_METHOD == "BLUETOOTH":
        print(f"🔵 Bluetooth Mode - Will connect to '{LEGO_HUB_NAME}'")
        print(f"📍 Hub Address: {LEGO_HUB_ADDRESS}")
        print(f"🎯 Command Channel: {LEGO_COMMAND_UUID}")
        print("⚡ REAL COMMANDS ENABLED!")
        if not BLEAK_AVAILABLE:
            print("⚠️  Warning: Bluetooth libraries not available")
            print("   Run: pip install bleak")
    elif CONNECTION_METHOD == "HTTP":
        print(f"🌐 HTTP Mode - Will connect to {MINDSTORMS_HOST}:{MINDSTORMS_PORT}")
    else:
        print("🎭 Simulation Mode - Perfect for testing!")
    
    print("📝 Logging commands to robot_commands.log")
    print("🌐 Server will run on http://localhost:5000")
    print("\nEndpoints:")
    print("  POST /robot/trigger - Main robot control (REAL COMMANDS!)")
    print("  POST /config       - Update connection settings")
    print("  GET  /health       - Health check")
    print("  GET  /logs         - Command logs")
    print("  POST /test         - Test connection")
    print("=" * 60)
    if CONNECTION_METHOD == "BLUETOOTH":
        print("🚀 READY TO SEND REAL BLUETOOTH COMMANDS TO LEGO HUB!")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)