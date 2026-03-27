import asyncio
import math

from utils import COMMANDER_URL, get_state, print_result


def calculate_distance(pos1, pos2):
    """מחשב מרחק במטרים בין שתי נקודות גיאוגרפיות."""
    # המרה גסה ממעלות למטרים (1 מעלה ~= 111,139 מטר)
    return math.sqrt((pos1['lat'] - pos2['lat']) ** 2 + (pos1['lon'] - pos2['lon']) ** 2) * 111139


async def run_security_tests(client):
    print("\n=== שלב 1: בדיקות אבטחה וולידציה ===")

    # 1. Pydantic Validation
    resp = await client.post(f"{COMMANDER_URL}/new_target", json={"lat": 100.0, "lon": 35.0})
    print_result("הגנת קואורדינטות (Pydantic)", resp.status_code == 422)

    # 2. Fake Target Protection
    payload = {"action": "engage", "target_id": "TGT-FAKE", "drone_id": "DRN-1"}
    resp_engage = await client.post(f"{COMMANDER_URL}/engage", json=payload)
    print_result("הגנה מפני מטרות פיקטיביות", resp_engage.status_code == 404)


async def run_mission_flow_tests(client):
    print("\n=== שלב 2: סימולציית משימה מלאה ===")

    # 1. יצירת מטרה במרחק של כ-200 מטר מהבסיס (31.800, 35.100)
    target_lat, target_lon = 31.8013, 35.1013
    resp = await client.post(f"{COMMANDER_URL}/new_target", json={"lat": target_lat, "lon": target_lon})

    if resp.status_code != 200:
        print(f"סיבת שגיאה מהשרת: {resp.json()}")
        print_result("יצירת מטרה", False, "ה-API סירב ליצור מטרה")
        return

    target_id = resp.json()["target_id"]
    target_pos = {"lat": target_lat, "lon": target_lon}
    print(f"  🎯 נוצרה מטרה: {target_id} במרחק ~200 מטר מהבסיס.")

    # ... אחרי יצירת המטרה ...
    print(f"  🎯 נוצרה מטרה: {target_id}. מוודא שהיא הופיעה במערכת עם 100% חיים...")

    # וידוא שהמטרה חיה לפני שמתחילים
    target_ready = False
    for _ in range(10):
        state = await get_state(client)
        target = next((t for t in state.get("target_data", []) if t["target_id"] == target_id), None)
        if target and target.get("health", 0) > 0:
            target_ready = True
            break
        await asyncio.sleep(1)

    if not target_ready:
        print_result("סנכרון מטרה", False, "המטרה לא הופיעה או שהיא כבר מתה")
        return

    print("\n  ⚔️ ממתין להגעת הרחפנים (סף אקטיבי: 20 מטר) ושולח פקודות אש...")
    # ... כאן ממשיכה הלולאה שלך ...

    print("\n  ⚔️ ממתין להגעת הרחפנים (סף אקטיבי: 20 מטר) ושולח פקודות אש...")
    target_destroyed = False

    for i in range(40):
        state = await get_state(client)
        target = next((t for t in state.get("target_data", []) if t["target_id"] == target_id), None)

        if not target or target.get("health", 0) <= 0:
            print(f"    [{i}] 💀 המטרה {target_id} חוסלה בהצלחה!")
            target_destroyed = True
            break

        all_drones = state.get("attack_data", []) + state.get("recon_data", [])
        assigned_drones = [d for d in all_drones if d.get("assigned_target_id") == target_id]

        active_attackers = [d for d in assigned_drones if
                            d.get("role") == "attack" and d.get("flight_status") in ["ACTIVE", "ATTACKING"]]

        print(f"    [{i}] בריאות מטרה: {target.get('health', 0)}% | רחפנים משויכים: {len(assigned_drones)}")

        for d in assigned_drones:
            dist = calculate_distance(d['position'], target_pos)
            status_icon = "🟢" if d['flight_status'] in ["ACTIVE", "ATTACKING"] else "🟡"
            role_tag = "🔭" if d['role'] == "recon" else "⚔️"

            # הדפסה מפורטת לזיהוי רגע המעבר ל-ACTIVE ב-20 מטר
            print(f"        {status_icon} {role_tag} {d['drone_id']} | "
                  f"סטטוס: {d['flight_status']:9} | "
                  f"מרחק: {dist:6.1f} מ' | "
                  f"תחמושת: {d.get('weapons_count', 0)}")

        for d in active_attackers:
            if d.get("weapons_count", 0) > 0:
                fire_payload = {"action": "engage", "target_id": target_id, "drone_id": d["drone_id"]}
                fire_resp = await client.post(f"{COMMANDER_URL}/engage", json=fire_payload)
                if fire_resp.status_code < 400:
                    print(f"      -> 🚀 פקודת אש בוצעה ע\"י {d['drone_id']}!")

        await asyncio.sleep(1.5)

    print_result("השמדת מטרה ע\"י הנחיל", target_destroyed)


async def run_manual_override_tests(client):
    print("\n=== שלב 3: שליטה ידנית (Manual Override) ===")

    # יצירת מטרה קרובה לשליטה מהירה
    resp = await client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.8008, "lon": 35.1008})
    target_id = resp.json().get("target_id")

    attacker = None
    for _ in range(15):
        state = await get_state(client)
        attacker = next((d for d in state.get("attack_data", []) if
                         d.get("assigned_target_id") == target_id), None)
        if attacker:
            break
        await asyncio.sleep(1)

    if not attacker:
        print_result("מעבר למצב ידני", False, "לא נמצא רחפן תקיפה")
        return

    drone_id = attacker["drone_id"]
    print(f"  🕹️ משתלט ידנית על רחפן {drone_id}...")

    # פקודת תנועה ידנית
    move_payload = {"drone_id": drone_id, "lat": 32.0, "lon": 34.0, "alt": 100}
    await client.post(f"{COMMANDER_URL}/manual_move", json=move_payload)

    await asyncio.sleep(3.5)

    state_after = await get_state(client)
    drone_manual = next((d for d in state_after.get("attack_data", []) if d.get("drone_id") == drone_id), None)

    success = drone_manual and drone_manual.get("flight_status") == "MANUAL"
    print_result("הגנת סטטוס ידני", success, f"סטטוס: {drone_manual.get('flight_status') if drone_manual else 'N/A'}")

    await client.post(f"{COMMANDER_URL}/recall_drone", json={"drone_id": drone_id})


async def run_edge_cases_tests(client):
    from utils import COMMANDER_URL, get_state, print_result

    print("\n=== שלב 4: בדיקות קצה ועמידות (Edge Cases) ===")

    # מושכים את מצב המערכת כדי למצוא "שחקנים" לניסוי
    state = await get_state(client)
    recon_drone = next((d for d in state.get("recon_data", [])), None)
    sleeping_attack = next((d for d in state.get("attack_data", []) if d.get("flight_status") == "SLEEP"), None)

    # ניצור מטרה פיקטיבית מהירה רק כדי שיהיה על מה לנסות לירות
    resp_tgt = await client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.7, "lon": 35.2})
    target_id = resp_tgt.json().get("target_id") if resp_tgt.status_code == 200 else "TGT-EDGE"

    for _ in range(15):
        current_state = await get_state(client)
        if any(t["target_id"] == target_id for t in current_state.get("target_data", [])):
            break
        await asyncio.sleep(0.5)

    # 1. ניסיון ירי עם רחפן תצפית (מצפים ל-400)
    if recon_drone:
        print("  🧪 בודק חסימת פקודת תקיפה לרחפן תצפית...")
        payload = {"action": "engage", "target_id": target_id, "drone_id": recon_drone["drone_id"]}
        resp = await client.post(f"{COMMANDER_URL}/engage", json=payload)
        print_result("חסימת ירי לרחפן תצפית", resp.status_code == 400, f"קוד שגיאה: {resp.status_code}")

    # 2. ניסיון תנועה ידנית מחוץ לגבולות הפיזיקליים (Pydantic מצפה ל-422)
    if recon_drone:
        print("  🧪 בודק תנועה ידנית אל מחוץ לאטמוספרה/גבולות...")
        # קו רוחב 95 חורג מההגבלות של -90 עד 90
        payload = {"drone_id": recon_drone["drone_id"], "lat": 95.0, "lon": 35.0, "alt": 100.0}
        resp = await client.post(f"{COMMANDER_URL}/manual_move", json=payload)
        print_result("חסימת נ\"צ שגוי בהשתלטות ידנית", resp.status_code == 422, f"קוד שגיאה: {resp.status_code}")

    # 3. פקודה לרחפן פנטום שלא קיים במערכת (מצפים ל-404)
    print("  🧪 בודק פקודת חזרה לבסיס לרחפן לא קיים...")
    resp = await client.post(f"{COMMANDER_URL}/recall_drone", json={"drone_id": "DRN-GHOST-99"})
    print_result("טיפול ברחפן לא קיים (Recall)", resp.status_code == 404, f"קוד שגיאה: {resp.status_code}")

    # 4. ניסיון תקיפה עם רחפן שישן בבסיס (מצפים ל-400)
    if sleeping_attack:
        print("  🧪 בודק חסימת תקיפה לרחפן בסטטוס SLEEP...")
        payload = {"action": "engage", "target_id": target_id, "drone_id": sleeping_attack["drone_id"]}
        resp = await client.post(f"{COMMANDER_URL}/engage", json=payload)
        print_result("חסימת ירי לרחפן ישן", resp.status_code == 400, f"קוד שגיאה: {resp.status_code}")
