import httpx
import asyncio
import time
import math

COMMANDER_URL = "http://localhost:8001"
AGGREGATOR_URL = "http://localhost:8000"


def calculate_distance(pos1, pos2):
    # Rough estimation: 1 degree approx 111,139 meters
    lat_diff = pos1["lat"] - pos2["lat"]
    lon_diff = pos1["lon"] - pos2["lon"]
    return math.sqrt(lat_diff**2 + lon_diff**2) * 111139


async def get_state():
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{AGGREGATOR_URL}/api/state")
        return resp.json()


async def run_transparent_mission():
    print("=== מתחיל תהליך בדיקה שקוף ומפורט ===")

    async with httpx.AsyncClient() as client:
        # 0. המתנה לזמינות רחפנים
        print("\n[0] ממתין לזמינות רחפנים בבסיס...")
        for i in range(20):
            state = await get_state()
            sleeping_recon = sum(1 for d in state.get("recon_data", []) if d.get("flight_status") == "SLEEP")
            sleeping_attack = sum(1 for d in state.get("attack_data", []) if d.get("flight_status") == "SLEEP")
            if sleeping_recon >= 1 and sleeping_attack >= 2:
                print(f" -> ✅ רחפנים מוכנים! (Recon: {sleeping_recon}, Attack: {sleeping_attack})")
                break
            print(f" -> ⏳ ממתין... (Recon: {sleeping_recon}/1, Attack: {sleeping_attack}/2)")
            await asyncio.sleep(2)
        else:
            print(" -> ❌ שגיאה: לא נמצאו מספיק רחפנים פנויים בבסיס. עוצר בדיקה.")
            return

        # 1. בדיקת מצב התחלתי
        print("\n[1] בודק מצב מערכת נוכחי...")
        state = await get_state()
        print(f" -> מטרות באוויר: {len(state['target_data'])}")
        print(f" -> רחפני תצפית באוויר: {len([d for d in state['recon_data'] if d['flight_status'] == 'ACTIVE'])}")

        # 2. יצירת מטרה
        print("\n[2] שולח פקודה ליצירת מטרה חדשה...")
        resp = await client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.8009, "lon": 35.1000})
        target_id = resp.json().get("target_id")
        print(f" -> המפקד אישר יצירת מטרה: {target_id}")
        await asyncio.sleep(2) # המתנה להתפשטות המטרה

        # 3. המתנה להגעת רחפן תצפית
        print("\n[3] ממתין שרחפן תצפית יינעל על המטרה...")
        recon_drone_id = None
        for i in range(15):
            state = await get_state()
            recon = next((d for d in state["recon_data"] if
                          d["assigned_target_id"] == target_id and d["flight_status"] == "ACTIVE"), None)
            if recon:
                recon_drone_id = recon["drone_id"]
                print(f" -> ✅ רחפן תצפית {recon_drone_id} ננעל על המטרה! (גובה: {recon['position']['alt']:.1f})")
                break
            await asyncio.sleep(1)

        if not recon_drone_id:
            print(" -> ❌ שגיאה: אף רחפן תצפית לא יצא למטרה. עוצר בדיקה.")
            return

        # 4. תהליך התקיפה והחילופים
        print("\n[4] מתחיל תהליך תקיפה (לולאה מפורטת)...")
        current_attacker = None

        while True:
            state = await get_state()
            target = next((t for t in state["target_data"] if t["target_id"] == target_id), None)

            # התיקון כאן: החלפתי ל'רדאר'
            if not target:
                print(f" -> ⚠️ המטרה {target_id} נעלמה מהרדאר!")
                break

            if target["health"] <= 0:
                print(f" -> 💀 המטרה {target_id} חוסלה בהצלחה (Health: 0)!")
                break

            # מחפשים מי הרחפן שתוקף עכשיו
            active_attackers = [d for d in state["attack_data"] if
                                d["assigned_target_id"] == target_id and d["weapons_count"] > 0 and d[
                                    "flight_status"] in ["ACTIVE", "ATTACKING"]]

            if not active_attackers:
                print(f" -> ⏳ אין רחפני תקיפה זמינים למטרה {target_id}. ממתין להגעת כוחות...")
                await asyncio.sleep(2)
                continue

            attacker = active_attackers[0]
            dist = calculate_distance(attacker["position"], target["position"])

            if current_attacker != attacker["drone_id"]:
                print(
                    f"\n -> 🔄 חילוף! רחפן תקיפה {attacker['drone_id']} נכנס לפעולה (טילים: {attacker['weapons_count']}).")
                current_attacker = attacker["drone_id"]

            print(
                f" -> 🚀 שולח פקודת אש ל-{current_attacker} | מרחק: {dist:.1f} מ' | בריאות מטרה: {target['health']}% | טילים נותרים: {attacker['weapons_count']}")

            # שליחת פקודת התקיפה
            engage_resp = await client.post(f"{COMMANDER_URL}/engage", json={"action": "engage", "target_id": target_id,
                                                                             "drone_id": current_attacker})
            if engage_resp.status_code >= 400:
                print(f" -> ❌ שגיאה בשיגור: {engage_resp.json()}")

            await asyncio.sleep(1.5)  # המתנה כדי לראות את ההשפעה באגרגטור

        # 5. ניקוי המרחב (ריקול לרחפנים)
        print("\n[5] שולח פקודת חזרה לבסיס לרחפן התצפית...")
        await client.post(f"{COMMANDER_URL}/recall_drone", json={"drone_id": recon_drone_id})
        print(f" -> נשלחה פקודת RECALL ל-{recon_drone_id}. הבדיקה הסתיימה.")


if __name__ == "__main__":
    asyncio.run(run_transparent_mission())
