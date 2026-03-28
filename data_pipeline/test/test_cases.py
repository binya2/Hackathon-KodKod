import asyncio
import math
from utils import COMMANDER_URL, get_state, print_result


def calculate_distance(pos1, pos2):
    return math.sqrt((pos1['lat'] - pos2['lat']) ** 2 + (pos1['lon'] - pos2['lon']) ** 2) * 111139


async def run_security_tests(client):
    print('\n=== שלב 1: בדיקות אבטחה וולידציה ===')
    resp = await client.post(f'{COMMANDER_URL}/new_target', json={'lat': 100.0, 'lon': 35.0})
    print_result('הגנת קואורדינטות (Pydantic)', resp.status_code == 422)
    payload = {'action': 'engage', 'target_id': 'TGT-FAKE', 'drone_id': 'DRN-1'}
    resp_engage = await client.post(f'{COMMANDER_URL}/engage', json=payload)
    print_result('הגנה מפני מטרות פיקטיביות', resp_engage.status_code == 404)


async def _create_mission_target(client, target_lat, target_lon):
    resp = await client.post(f'{COMMANDER_URL}/new_target', json={'lat': target_lat, 'lon': target_lon})
    if resp.status_code != 200:
        print(f'סיבת שגיאה מהשרת: {resp.json()}')
        print_result('יצירת מטרה', False, 'ה-API סירב ליצור מטרה')
        return None
    target_id = resp.json()['target_id']
    print(f'  🎯 נוצרה מטרה: {target_id} במרחק ~200 מטר מהבסיס.')
    return target_id


async def _wait_for_target_readiness(client, target_id):
    print(f'  🎯 מוודא שהיא הופיעה במערכת עם 100% חיים...')
    for _ in range(10):
        state = await get_state(client)
        target = next((t for t in state.get('target_data', []) if t['target_id'] == target_id), None)
        if target and target.get('health', 0) > 0:
            return True
        await asyncio.sleep(1)
    print_result('סנכרון מטרה', False, 'המטרה לא הופיעה או שהיא כבר מתה')
    return False


async def _monitor_and_execute_strikes(client, target_id, target_pos):
    print('\n  ⚔️ ממתין להגעת הרחפנים (סף אקטיבי: 20 מטר) ושולח פקודות אש...')
    for i in range(40):
        state = await get_state(client)
        target = next((t for t in state.get('target_data', []) if t['target_id'] == target_id), None)
        if not target or target.get('health', 0) <= 0:
            print(f'    [{i}] 💀 המטרה {target_id} חוסלה בהצלחה!')
            return True
        await _print_swarm_status(state, target_id, target_pos, target.get('health', 0), i)
        await _issue_engagement_commands(client, state, target_id)
        await asyncio.sleep(1.5)
    return False


async def _print_swarm_status(state, target_id, target_pos, target_health, iteration):
    all_drones = state.get('attack_data', []) + state.get('recon_data', [])
    assigned_drones = [d for d in all_drones if d.get('assigned_target_id') == target_id]
    print(f"    [{iteration}] בריאות מטרה: {target_health}% | רחפנים משויכים: {len(assigned_drones)}")
    for d in assigned_drones:
        dist = calculate_distance(d['position'], target_pos)
        status_icon = '🟢' if d['flight_status'] in ['ACTIVE', 'ATTACKING'] else '🟡'
        role_tag = '🔭' if d['role'] == 'recon' else '⚔️'
        print(
            f"        {status_icon} {role_tag} {d['drone_id']} | סטטוס: {d['flight_status']:9} | מרחק: {dist:6.1f} מ' | תחמושת: {d.get('weapons_count', 0)}")


async def _issue_engagement_commands(client, state, target_id):
    all_drones = state.get('attack_data', []) + state.get('recon_data', [])
    active_attackers = [d for d in all_drones if
                        d.get('assigned_target_id') == target_id and d.get('role') == 'attack' and d.get(
                            'flight_status') in ['ACTIVE', 'ATTACKING']]
    for d in active_attackers:
        if d.get('weapons_count', 0) > 0:
            fire_payload = {'action': 'engage', 'target_id': target_id, 'drone_id': d['drone_id']}
            fire_resp = await client.post(f'{COMMANDER_URL}/engage', json=fire_payload)
            if fire_resp.status_code < 400:
                print(f"""      -> 🚀 פקודת אש בוצעה ע"י {d['drone_id']}!""")


async def run_mission_flow_tests(client):
    print('\n=== שלב 2: סימולציית משימה מלאה ===')
    target_lat, target_lon = (31.8013, 35.1013)
    target_id = await _create_mission_target(client, target_lat, target_lon)
    if not target_id:
        return
    if not await _wait_for_target_readiness(client, target_id):
        return
    target_destroyed = await _monitor_and_execute_strikes(client, target_id, {'lat': target_lat, 'lon': target_lon})
    print_result('השמדת מטרה ע"י הנחיל', target_destroyed)


async def run_manual_override_tests(client):
    print('\n=== שלב 3: שליטה ידנית (Manual Override) ===')
    resp = await client.post(f'{COMMANDER_URL}/new_target', json={'lat': 31.8008, 'lon': 35.1008})
    target_id = resp.json().get('target_id')
    attacker = None
    for _ in range(15):
        state = await get_state(client)
        attacker = next((d for d in state.get('attack_data', []) if d.get('assigned_target_id') == target_id), None)
        if attacker:
            break
        await asyncio.sleep(1)
    if not attacker:
        print_result('מעבר למצב ידני', False, 'לא נמצא רחפן תקיפה')
        return
    drone_id = attacker['drone_id']
    print(f'  🕹️ משתלט ידנית על רחפן {drone_id}...')
    move_payload = {'drone_id': drone_id, 'lat': 32.0, 'lon': 34.0, 'alt': 100}
    await client.post(f'{COMMANDER_URL}/manual_move', json=move_payload)
    await asyncio.sleep(3.5)
    state_after = await get_state(client)
    drone_manual = next((d for d in state_after.get('attack_data', []) if d.get('drone_id') == drone_id), None)
    success = drone_manual and drone_manual.get('flight_status') == 'MANUAL'
    print_result('הגנת סטטוס ידני', success, f"סטטוס: {(drone_manual.get('flight_status') if drone_manual else 'N/A')}")
    
    print(f'  🤖 מחזיר רחפן {drone_id} למצב אוטונומי...')
    await client.post(f'{COMMANDER_URL}/resume_auto', json={'drone_id': drone_id})
    await asyncio.sleep(1.5)
    state_final = await get_state(client)
    drone_auto = next((d for d in state_final.get('attack_data', []) if d.get('drone_id') == drone_id), None)
    auto_success = drone_auto and drone_auto.get('flight_status') in ['ACTIVE', 'EN_ROUTE']
    print_result('חזרה למצב אוטונומי', auto_success, f"סטטוס: {(drone_auto.get('flight_status') if drone_auto else 'N/A')}")

    await client.post(f'{COMMANDER_URL}/recall_drone', json={'drone_id': drone_id})


async def run_edge_cases_tests(client):
    print('\n=== שלב 4: בדיקות קצה ועמידות (Edge Cases) ===')
    state = await get_state(client)
    recon_drone = next((d for d in state.get('recon_data', [])), None)
    sleeping_attack = next((d for d in state.get('attack_data', []) if d.get('flight_status') == 'SLEEP'), None)
    resp_tgt = await client.post(f'{COMMANDER_URL}/new_target', json={'lat': 31.7, 'lon': 35.2})
    target_id = resp_tgt.json().get('target_id') if resp_tgt.status_code == 200 else 'TGT-EDGE'
    for _ in range(15):
        current_state = await get_state(client)
        if any((t['target_id'] == target_id for t in current_state.get('target_data', []))):
            break
        await asyncio.sleep(0.5)
    if recon_drone:
        print('  🧪 בודק חסימת פקודת תקיפה לרחפן תצפית...')
        payload = {'action': 'engage', 'target_id': target_id, 'drone_id': recon_drone['drone_id']}
        resp = await client.post(f'{COMMANDER_URL}/engage', json=payload)
        print_result('חסימת ירי לרחפן תצפית', resp.status_code == 400, f'קוד שגיאה: {resp.status_code}')
    if recon_drone:
        print('  🧪 בודק תנועה ידנית אל מחוץ לאטמוספרה/גבולות...')
        payload = {'drone_id': recon_drone['drone_id'], 'lat': 95.0, 'lon': 35.0, 'alt': 100.0}
        resp = await client.post(f'{COMMANDER_URL}/manual_move', json=payload)
        print_result('חסימת נ"צ שגוי בהשתלטות ידנית', resp.status_code == 422, f'קוד שגיאה: {resp.status_code}')
    print('  🧪 בודק פקודת חזרה לבסיס לרחפן לא קיים...')
    resp = await client.post(f'{COMMANDER_URL}/recall_drone', json={'drone_id': 'DRN-GHOST-99'})
    print_result('טיפול ברחפן לא קיים (Recall)', resp.status_code == 404, f'קוד שגיאה: {resp.status_code}')
    if sleeping_attack:
        print('  🧪 בודק חסימת תקיפה לרחפן בסטטוס SLEEP...')
        payload = {'action': 'engage', 'target_id': target_id, 'drone_id': sleeping_attack['drone_id']}
        resp = await client.post(f'{COMMANDER_URL}/engage', json=payload)
        print_result('חסימת ירי לרחפן ישן', resp.status_code == 400, f'קוד שגיאה: {resp.status_code}')


async def cleanup_all_drones(client):
    print('\n  🧹 מחזיר רחפנים לבסיס וממתין לנחיתה (SLEEP)...')
    state = await get_state(client)
    all_drones = state.get('attack_data', []) + state.get('recon_data', [])
    for d in all_drones:
        if d.get('flight_status') != 'SLEEP':
            await client.post(f'{COMMANDER_URL}/recall_drone', json={'drone_id': d['drone_id']})
    
    for _ in range(25):
        state = await get_state(client)
        recon_data = state.get('recon_data', [])
        attack_data = state.get('attack_data', [])
        sleeping_recon = sum(1 for d in recon_data if d.get('flight_status') == 'SLEEP')
        sleeping_attack = sum(1 for d in attack_data if d.get('flight_status') == 'SLEEP')
        if sleeping_recon >= 4 and sleeping_attack >= 12:
            break
        await asyncio.sleep(1)


async def run_recon_first_test(client):
    print('\n=== שלב 5: חוק תצפית תחילה (Recon First) ===')
    target_id = await _create_mission_target(client, 31.805, 35.105)
    if not target_id:
        return
    
    attacker = None
    for _ in range(8):
        await asyncio.sleep(1)
        state = await get_state(client)
        attacker = next((d for d in state.get('attack_data', []) if d.get('assigned_target_id') == target_id), None)
        if attacker:
            break

    if not attacker:
        print_result('חסימת תקיפה ללא תצפית', False, 'לא נמצא רחפן תקיפה משויך בזמן')
        return
    payload = {'action': 'engage', 'target_id': target_id, 'drone_id': attacker['drone_id']}
    resp = await client.post(f'{COMMANDER_URL}/engage', json=payload)
    print_result('חסימת תקיפה ללא תצפית (400)', resp.status_code == 400, f'קוד שגיאה: {resp.status_code}')


async def run_multi_target_stress_test(client):
    print('\n=== שלב 6: עומס מטרות (Stress Test) ===')
    targets = []
    for i in range(1, 4):
        t_id = await _create_mission_target(client, 31.81 + (i * 0.01), 35.11 + (i * 0.01))
        if t_id:
            targets.append(t_id)
    print(f'  ⏳ ממתין 12 שניות להקצאת נחיל עבור {len(targets)} מטרות...')
    await asyncio.sleep(12)
    state = await get_state(client)
    all_success = True
    for t_id in targets:
        all_drones = state.get('attack_data', []) + state.get('recon_data', [])
        assigned = [d for d in all_drones if d.get('assigned_target_id') == t_id]
        recons = [d for d in assigned if d.get('role') == 'recon']
        attacks = [d for d in assigned if d.get('role') == 'attack']
        success = len(recons) == 1 and len(attacks) >= 2
        print(f"  🎯 מטרה {t_id}: {len(recons)} תצפית, {len(attacks)} תקיפה | {'✅' if success else '❌'}")
        if not success:
            all_success = False
    print_result('עמידות בעומס והקצאה תקינה', all_success)
    print('  🧹 מנקה את השטח (Recall All)...')
    state = await get_state(client)
    all_active = state.get('attack_data', []) + state.get('recon_data', [])
    for d in all_active:
        if d.get('flight_status') != 'SLEEP':
            await client.post(f'{COMMANDER_URL}/recall_drone', json={'drone_id': d['drone_id']})


async def run_abort_mission_test(client):
    print('\n=== שלב 7: ביטול משימה (Abort Mission) ===')
    target_id = await _create_mission_target(client, 31.82, 35.12)
    if not target_id:
        return
    
    print('  ⏳ ממתין להקצאת כוחות והזנקת רחפנים...')
    await asyncio.sleep(5)
    
    state = await get_state(client)
    assigned_attackers = [d for d in state.get('attack_data', []) if d.get('assigned_target_id') == target_id]
    if not assigned_attackers:
        print('❌ שגיאה: לא הוקצו רחפני תקיפה למטרה.')
        return
    
    print('  🛑 שולח פקודת ביטול משימה (CANCEL_TARGET)...')
    resp = await client.post(f'{COMMANDER_URL}/cancel_target', json={'target_id': target_id})
    print(f'  📡 תגובת השרת: {resp.status_code} - {resp.json().get("status")}')
    
    print('  ⏳ ממתין לתגובת הנחיל (U-Turn)...')
    await asyncio.sleep(4)
    
    state_after = await get_state(client)
    target_after = next((t for t in state_after.get('target_data', []) if t['target_id'] == target_id), None)
    target_dead = not target_after or target_after.get('health', 0) <= 0
    print_result('מחיקת המטרה מהמערכת', target_dead)
    
    assigned_ids = [d['drone_id'] for d in assigned_attackers]
    all_drones_after = state_after.get('attack_data', []) + state_after.get('recon_data', [])
    returning_count = 0
    for d_id in assigned_ids:
        drone_now = next((d for d in all_drones_after if d['drone_id'] == d_id), None)
        if drone_now and drone_now.get('flight_status') in ['RETURNING', 'SLEEP']:
            returning_count += 1
            
    is_returning = returning_count == len(assigned_ids)
    print_result('חזרת הנחיל לבסיס (Auto-Recall)', is_returning, f'{returning_count}/{len(assigned_ids)} רחפנים בדרך חזרה')
