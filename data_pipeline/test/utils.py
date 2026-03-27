import asyncio
import httpx
COMMANDER_URL = 'http://localhost:8001'
AGGREGATOR_URL = 'http://localhost:8000'

async def get_state(client: httpx.AsyncClient):
    resp = await client.get(f'{AGGREGATOR_URL}/api/state')
    return resp.json()

async def wait_for_system_sync(client: httpx.AsyncClient) -> bool:
    print('\n[⏳] ממתין לסנכרון ראשוני של הרחפנים מול ה-Redis...')
    for _ in range(40):
        try:
            state = await get_state(client)
            sleeping_recon = sum((1 for d in state.get('recon_data', []) if d.get('flight_status') == 'SLEEP'))
            sleeping_attack = sum((1 for d in state.get('attack_data', []) if d.get('flight_status') == 'SLEEP'))
            if sleeping_recon > 0 and sleeping_attack > 0:
                print(f'[✅] המערכת מוכנה! (תצפית: {sleeping_recon}, תקיפה: {sleeping_attack})')
                return True
        except Exception:
            pass
        await asyncio.sleep(1)
    return False

def print_result(test_name: str, success: bool, reason: str=''):
    if success:
        print(f'  ✅ עבר: {test_name}')
    else:
        print(f'  ❌ נכשל: {test_name} - {reason}')