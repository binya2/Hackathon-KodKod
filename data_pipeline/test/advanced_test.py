import httpx
import asyncio

COMMANDER_URL = "http://localhost:8001"
AGGREGATOR_URL = "http://localhost:8000"


async def wait_for_system_sync(client):
    print("⏳ ממתין לסנכרון טלמטריה ראשוני מול הרחפנים...")
    for _ in range(20):
        state = (await client.get(f"{AGGREGATOR_URL}/api/state")).json()
        sleeping_recon = sum(1 for d in state.get("recon_data", []) if d.get("flight_status") == "SLEEP")
        sleeping_attack = sum(1 for d in state.get("attack_data", []) if d.get("flight_status") == "SLEEP")

        if sleeping_recon >= 1 and sleeping_attack >= 2:
            print(f"✅ המערכת מסונכרנת ומוכנה! (תצפית: {sleeping_recon}, תקיפה: {sleeping_attack})")
            return
        await asyncio.sleep(1)
    print("⚠️ אזהרה: לא כל הרחפנים הסתנכרנו. ממשיך בכל זאת...")


async def test_recon_first_rule(client):
    print("\n--- בדיקה 1: חוק 'תצפית תחילה' (Recon First) ---")

    # ניצור מטרה *רחוקה* מהבסיס כדי שלתצפית ייקח זמן להגיע
    resp = await client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.85, "lon": 35.15})
    if resp.status_code != 200:
        print(f"❌ שגיאה ביצירת מטרה: {resp.text}")
        return

    target_id = resp.json()["target_id"]
    print(f"🎯 נוצרה מטרה רחוקה {target_id}. מנסה לתקוף מיידית...")

    # ממתין שנייה שהמוח יקצה רחפנים
    await asyncio.sleep(1)

    state = (await client.get(f"{AGGREGATOR_URL}/api/state")).json()
    attack_drone = next((d for d in state.get("attack_data", []) if d.get("assigned_target_id") == target_id), None)

    if attack_drone:
        # התקיפה צריכה להיכשל כי התצפית עוד בדרך!
        engage_resp = await client.post(
            f"{COMMANDER_URL}/engage",
            json={"action": "engage", "target_id": target_id, "drone_id": attack_drone["drone_id"]}
        )
        if engage_resp.status_code == 400 and "Recon" in engage_resp.text:
            print("✅ המערכת חסמה את התקיפה בהצלחה! (התצפית טרם הגיעה ליעד)")
        else:
            print(f"❌ שגיאה: המערכת לא חסמה כראוי. קוד: {engage_resp.status_code}, תשובה: {engage_resp.text}")


async def test_multi_target_stress(client):
    print("\n--- בדיקה 2: עומס מטרות (Multi-Target Stress Test) ---")

    targets = []
    for i in range(3):
        resp = await client.post(f"{COMMANDER_URL}/new_target",
                                 json={"lat": 31.82 + (i * 0.01), "lon": 35.12 + (i * 0.01)})
        if resp.status_code == 200:
            targets.append(resp.json()["target_id"])
            print(f"🎯 נוצרה מטרה {i + 1}: {targets[-1]}")
        else:
            print(f"❌ שגיאה ביצירת מטרה {i + 1}: {resp.text}")
        await asyncio.sleep(1)

    print("⏳ ממתין 10 שניות לפריסת הנחיל (Recon + Attack) לכל המטרות...")
    await asyncio.sleep(10)

    state = (await client.get(f"{AGGREGATOR_URL}/api/state")).json()

    for tgt in targets:
        recon_count = sum(1 for d in state.get("recon_data", []) if
                          d.get("assigned_target_id") == tgt and d.get("flight_status") == "ACTIVE")
        attack_count = sum(1 for d in state.get("attack_data", []) if
                           d.get("assigned_target_id") == tgt and d.get("flight_status") in ["ACTIVE", "ATTACKING"])

        print(f"📊 מטרה {tgt}: רחפני תצפית: {recon_count} | רחפני תקיפה: {attack_count}")
        if recon_count >= 1 and attack_count >= 2:
            print(f"✅ הקצאת כוחות מושלמת למטרה {tgt}")
        else:
            print(f"⚠️ חוסר כוחות במטרה {tgt}")


async def run_all_tests():
    async with httpx.AsyncClient() as client:
        await wait_for_system_sync(client)
        await test_recon_first_rule(client)
        await test_multi_target_stress(client)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
