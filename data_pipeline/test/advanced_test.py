import httpx
import asyncio

COMMANDER_URL = "http://localhost:8001"
AGGREGATOR_URL = "http://localhost:8000"


async def test_recon_first_rule(client):
    print("\n--- בדיקה 1: חוק 'תצפית תחילה' (Recon First) ---")

    # 1. יצירת מטרה
    resp = await client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.8, "lon": 35.1})
    target_id = resp.json()["target_id"]
    print(f"🎯 נוצרה מטרה {target_id}. מנסה לתקוף מיידית (לפני הגעת תצפית)...")

    # 2. ניסיון תקיפה מיידי (אמור להיכשל!)
    state = (await client.get(f"{AGGREGATOR_URL}/api/state")).json()
    attack_drone = next((d for d in state.get("attack_data", []) if d["assigned_target_id"] == target_id), None)

    if attack_drone:
        engage_resp = await client.post(
            f"{COMMANDER_URL}/engage",
            json={"action": "engage", "target_id": target_id, "drone_id": attack_drone["drone_id"]}
        )
        if engage_resp.status_code == 400 and "Recon" in engage_resp.text:
            print("✅ המערכת חסמה את התקיפה בהצלחה! (אין תצפית מאשרת)")
        else:
            print(f"❌ שגיאה: המערכת אישרה תקיפה עיוורת! קוד: {engage_resp.status_code}")


async def test_multi_target_stress(client):
    print("\n--- בדיקה 2: עומס מטרות (Multi-Target Stress Test) ---")

    targets = []
    # יוצרים 3 מטרות במקביל
    for i in range(3):
        resp = await client.post(f"{COMMANDER_URL}/new_target",
                                 json={"lat": 31.8 + (i * 0.01), "lon": 35.1 + (i * 0.01)})
        targets.append(resp.json()["target_id"])
        print(f"🎯 נוצרה מטרה {i + 1}: {targets[-1]}")
        await asyncio.sleep(1)

    print("⏳ ממתין 10 שניות לפריסת הנחיל (Recon + Attack) לכל המטרות...")
    await asyncio.sleep(10)

    state = (await client.get(f"{AGGREGATOR_URL}/api/state")).json()

    for tgt in targets:
        recon_count = sum(
            1 for d in state.get("recon_data", []) if d["assigned_target_id"] == tgt and d["flight_status"] == "ACTIVE")
        attack_count = sum(1 for d in state.get("attack_data", []) if
                           d["assigned_target_id"] == tgt and d["flight_status"] == "ACTIVE")

        print(f"📊 מטרה {tgt}: רחפני תצפית: {recon_count} | רחפני תקיפה: {attack_count}")
        if recon_count >= 1 and attack_count >= 2:
            print(f"✅ הקצאת כוחות מושלמת למטרה {tgt}")
        else:
            print(f"⚠️ חוסר כוחות במטרה {tgt} (ייתכן ונגמרו הרחפנים בבסיס)")


async def run_all_tests():
    async with httpx.AsyncClient() as client:
        await test_recon_first_rule(client)
        await test_multi_target_stress(client)


if __name__ == "__main__":
    asyncio.run(run_all_tests())