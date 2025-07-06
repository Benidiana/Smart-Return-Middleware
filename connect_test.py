# connect_test.py - Einfacher Verbindungstest
import asyncio
from bleak import BleakClient

async def simple_connect():
    print("🔗 Verbinde mit Hub...")
    try:
        client = BleakClient("A8:E2:C1:9B:8A:A5")
        await client.connect()
        
        if client.is_connected:
            print("✅ VERBINDUNG ERFOLGREICH!")
            print("Verbunden für 5 Sekunden...")
            await asyncio.sleep(5)
            await client.disconnect()
            print("🔌 Getrennt")
            return True
        else:
            print("❌ Verbindung fehlgeschlagen")
            return False
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

asyncio.run(simple_connect())