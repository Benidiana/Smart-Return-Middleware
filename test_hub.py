# test_hub.py - Direkter Test des LEGO Hubs
import asyncio
import requests
from datetime import datetime

try:
    from bleak import BleakClient, BleakScanner
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    print("❌ Installiere bleak: pip install bleak")

HUB_ADDRESS = "A8:E2:C1:9B:8A:A5"

async def quick_hub_test():
    """Schneller Test der Hub Verbindung"""
    print(" LEGO HUB SCHNELLTEST")
    print(f"Hub: {HUB_ADDRESS}")
    print("=" * 40)
    
    if not BLEAK_AVAILABLE:
        print("❌ bleak library fehlt!")
        return False
    
    try:
        # 1. Prüfe ob Hub erreichbar ist
        print("🔍 Suche Hub...")
        devices = await BleakScanner.discover(timeout=5.0)
        
        hub_found = False
        for device in devices:
            if device.address == HUB_ADDRESS:
                print(f"✅ Hub gefunden: {device.name}")
                print(f"   Signal: {device.rssi} dBm")
                hub_found = True
                break
        
        if not hub_found:
            print(f"❌ Hub {HUB_ADDRESS} nicht gefunden")
            print("   Ist der Hub eingeschaltet?")
            return False
        
        # 2. Teste Verbindung
        print("\n🔗 Teste Verbindung...")
        async with BleakClient(HUB_ADDRESS) as client:
            if client.is_connected:
                print("✅ Verbindung erfolgreich!")
                
                # 3. Zeige verfügbare Services
                print("\n📋 Hub Services:")
                services = await client.get_services()
                for service in services:
                    print(f"   🔧 {service.uuid}: {service.description}")
                
                return True
            else:
                print("❌ Verbindung fehlgeschlagen")
                return False
                
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

def test_middleware_with_hub():
    """Teste Middleware mit echtem Hub"""
    print("\n🌐 TESTE MIDDLEWARE MIT HUB")
    print("=" * 40)
    
    # Test ob Middleware läuft
    try:
        response = requests.get('http://localhost:5000/health', timeout=3)
        if response.status_code == 200:
            print("✅ Middleware läuft")
        else:
            print("❌ Middleware antwortet nicht")
            return False
    except:
        print("❌ Middleware nicht erreichbar")
        print("   Starte: python middleware_server.py")
        return False
    
    # Sende Test-Kommando
    test_data = {
        "zone": "Zone A",
        "return_id": f"HUB-TEST-{datetime.now().strftime('%H%M%S')}",
        "item_description": "Hub Connection Test",
        "hub_address": HUB_ADDRESS
    }
    
    try:
        print(f"📤 Sende Test-Kommando...")
        response = requests.post(
            'http://localhost:5000/robot/trigger',
            headers={'Content-Type': 'application/json'},
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Kommando erfolgreich!")
            print(f"   Status: {result.get('message', 'OK')}")
            print(f"   Methode: {result.get('method', 'Unknown')}")
            return True
        else:
            print(f"❌ Kommando fehlgeschlagen: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Verbindungsfehler: {e}")
        return False

async def full_system_test():
    """Vollständiger System Test"""
    print("🏫 VOLLSTÄNDIGER UNI SYSTEM TEST")
    print("=" * 50)
    
    # 1. Hub Test
    hub_ok = await quick_hub_test()
    
    # 2. Middleware Test  
    middleware_ok = test_middleware_with_hub()
    
    # 3. Zusammenfassung
    print("\n📊 TEST ERGEBNISSE:")
    print(f"   🤖 LEGO Hub: {'✅ OK' if hub_ok else '❌ FEHLER'}")
    print(f"   🌐 Middleware: {'✅ OK' if middleware_ok else '❌ FEHLER'}")
    
    if hub_ok and middleware_ok:
        print("\n🎉 SYSTEM BEREIT FÜR DEMO!")
        print("   Du kannst jetzt deine Joget App testen!")
    else:
        print("\n⚠️  System nicht vollständig bereit")
        print("   Behebe die Fehler vor der Demo")
    
    return hub_ok and middleware_ok

if __name__ == "__main__":
    asyncio.run(full_system_test())