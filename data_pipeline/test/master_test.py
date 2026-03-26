import httpx
import asyncio
import math
import uuid

COMMANDER_URL = "http://localhost:8001"
AGGREGATOR_URL = "http://localhost:8000"


def calculate_distance(pos1, pos2):
    # חישוב מרחק מקורב במטרים
    lat_diff = pos1["lat"] - pos2["lat"]
    lon_diff = pos1["lon"] - pos2["lon"]
    return math.sqrt(lat_diff ** 2 + lon_diff ** 2) * 111139


class MasterTester:
    def __init__(self):
        self.client = None
        self.passed_tests = 0
        self.failed_tests = 0

    async def get_state(self):
        resp = await self.client.get(f"{AGGREGATOR_URL}/api/state")
        return resp.json()

    def log_result(self, test_name, success, reason=""):
        if success:
            print(f"✅ עבר: {test_name}")
            self.passed_tests += 1
        else:
            print(f"❌ נכשל: {test_name} - {reason}")
            self.failed_tests += 1

    async def wait_for_system_sync(self):
        print("\n[0] ⏳ ממתין לסנכרון טלמטריה ראשוני וטעינת רחפנים בבסיס...")
        for _ in range(20):
            state = await self.get_state()
            sleeping_recon = sum(1 for d in state.get("recon_data", []) if d.get("flight_status") == "SLEEP")
            sleeping_attack = sum(1 for d in state.get("attack_data", []) if d.get("flight_status") == "SLEEP")

            if sleeping_recon >= 1 and sleeping_attack >= 2:
                print(f"✅ המערכת מסונכרנת ומוכנה! (תצפית פנויים: {sleeping_recon}, תקיפה פנויים: {sleeping_attack})")
                return True
            await asyncio.sleep(1)
        print("⚠️ אזהרה: אין מספיק רחפנים בבסיס. ייתכן והבדיקות ייכשלו.")
        return False

    async def test_security_and_validation(self):
        print("\n=== שלב 1: בדיקות אבטחה וולידציה ===")

        # בדיקת קואורדינטות מחוץ לטווח
        resp = await self.client.post(f"{COMMANDER_URL}/new_target", json={"lat": 100.0, "lon": 35.0})
        self.log_result("הגנת קואורדינטות (Pydantic)", resp.status_code == 422)

        # בדיקת פעולות על מטרה לא קיימת
        fake_id = f"TGT-FAKE-{uuid.uuid4().hex[:6]}"
        resp_deploy = await self.client.post(f"{COMMANDER_URL}/deploy_drone",
                                             json={"role": "attack", "target_id": fake_id})
        resp_engage = await self.client.post(f"{COMMANDER_URL}/engage",
                                             json={"action": "engage", "target_id": fake_id, "drone_id": "DRN-1"})
        self.log_result("הגנה מפני מטרות פיקטיביות (Ghost Targets)",
                        resp_deploy.status_code == 404 and resp_engage.status_code == 404)

    async def test_recon_first_rule(self):
        print("\n=== שלב 2: חוק 'תצפית תחילה' (Recon First) ===")

        resp = await self.client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.85, "lon": 35.15})
        if resp.status_code != 200:
            self.log_result("חוק תצפית תחילה", False, "לא הצליח ליצור מטרה")
            return None

        target_id = resp.json()["target_id"]
        print(f"🎯 נוצרה מטרה רחוקה {target_id}. מנסה לתקוף מיידית טרם הגעת תצפית...")
        await asyncio.sleep(1.5)

        state = await self.get_state()
        attack_drone = next((d for d in state.get("attack_data", []) if d.get("assigned_target_id") == target_id), None)

        if attack_drone:
            engage_resp = await self.client.post(
                f"{COMMANDER_URL}/engage",
                json={"action": "engage", "target_id": target_id, "drone_id": attack_drone["drone_id"]}
            )
            self.log_result("בלימת תקיפה עיוורת", engage_resp.status_code == 400 and "Recon" in engage_resp.text)
        else:
            self.log_result("בלימת תקיפה עיוורת", False, "לא שובץ רחפן תקיפה למטרה החדשה")

        return target_id  # נחזיר את המטרה לשלב הבא

    async def test_full_mission_simulation(self, target_id):
        if not target_id:
            print("\n=== שלב 3: סימולציית משימה - מדלג (לא נוצרה מטרה בשלב קודם) ===")
            return

        print(f"\n=== שלב 3: סימולציית משימה מלאה על מטרה {target_id} ===")

        # המתנה לרחפן תצפית
        print("ממתין שרחפן תצפית יגיע ויינעל על המטרה...")
        recon_locked = False
        for _ in range(20):
            state = await self.get_state()
            recon = next((d for d in state["recon_data"] if
                          d["assigned_target_id"] == target_id and d["flight_status"] == "ACTIVE"), None)
            if recon:
                recon_locked = True
                print(f"✅ רחפן תצפית {recon['drone_id']} בעמדה.")
                break
            await asyncio.sleep(1)

        if not recon_locked:
            self.log_result("סימולציית משימה: נעילת תצפית", False)
            return

        print("מתחיל תקיפה ולולאת חימוש...")
        current_attacker = None
        mission_success = False

        for _ in range(30):  # הגבלת זמן לסימולציה
            state = await self.get_state()
            target = next((t for t in state["target_data"] if t["target_id"] == target_id), None)

            if not target or target["health"] <= 0:
                print(f"💀 המטרה חוסלה בהצלחה!")
                mission_success = True
                break

            active_attackers = [d for d in state["attack_data"] if
                                d["assigned_target_id"] == target_id and d["weapons_count"] > 0 and d[
                                    "flight_status"] in ["ACTIVE", "ATTACKING"]]

            if not active_attackers:
                print("⏳ ממתין לחילופי רחפנים (תחמושת התרוקנה)...")
                await asyncio.sleep(2)
                continue

            attacker = active_attackers[0]
            if current_attacker != attacker["drone_id"]:
                print(f"🔄 רחפן תקיפה {attacker['drone_id']} נכנס לפעולה (טילים: {attacker['weapons_count']}).")
                current_attacker = attacker["drone_id"]

            dist = calculate_distance(attacker["position"], target["position"])
            print(f"🚀 שולח פקודת אש ל-{current_attacker} | מרחק: {dist:.1f} מ' | חיים: {target['health']}%")

            await self.client.post(f"{COMMANDER_URL}/engage",
                                   json={"action": "engage", "target_id": target_id, "drone_id": current_attacker})
            await asyncio.sleep(1.5)

        self.log_result("סימולציית משימה מלאה", mission_success)

    async def test_manual_overrides(self):
        print("\n=== שלב 4: קטיעת תקיפה (Manual Overrides) ===")

        # יצירת מטרה קרובה במיוחד לצורך הטסט
        resp = await self.client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.81, "lon": 35.11})
        target_id = resp.json()["target_id"]

        await asyncio.sleep(3)  # ממתין שרחפנים יגיעו למצב פעיל
        state = await self.get_state()
        attacker = next((d for d in state['attack_data'] if
                         d['assigned_target_id'] == target_id and d['flight_status'] == "ACTIVE"), None)

        if not attacker:
            self.log_result("עקיפה ידנית", False, "לא נמצא רחפן תקיפה זמין לניסוי")
            return

        print(f"שולח פקודת אש לרחפן {attacker['drone_id']}...")
        await self.client.post(f"{COMMANDER_URL}/engage",
                               json={"action": "engage", "target_id": target_id, "drone_id": attacker['drone_id']})

        print("שולח פקודת תנועה ידנית לקטיעת התקיפה באמצע צלילה...")
        await self.client.post(f"{COMMANDER_URL}/manual_move",
                               json={"drone_id": attacker['drone_id'], "lat": 32.0, "lon": 34.0, "alt": 500.0})

        await asyncio.sleep(1)
        state = await self.get_state()
        final_drone = next(d for d in state['attack_data'] if d['drone_id'] == attacker['drone_id'])

        self.log_result("מעבר מיידי למצב תנועה ידנית (Manual)",
                        final_drone['flight_status'] == "MANUAL" and final_drone['assigned_target_id'] is None)

        print("שולח פקודת חזרה לבסיס (Recall)...")
        await self.client.post(f"{COMMANDER_URL}/recall_drone", json={"drone_id": attacker['drone_id']})
        await asyncio.sleep(1)

        state = await self.get_state()
        returning_drone = next(d for d in state['attack_data'] if d['drone_id'] == attacker['drone_id'])
        self.log_result("פקודת ריקול מיידית (Optimistic Update)", returning_drone['flight_status'] == "RETURNING")

    async def test_multi_target_stress(self):
        print("\n=== שלב 5: עומס מטרות (Stress Test) ===")
        targets = []
        for i in range(3):
            resp = await self.client.post(f"{COMMANDER_URL}/new_target",
                                          json={"lat": 31.83 + (i * 0.01), "lon": 35.13 + (i * 0.01)})
            if resp.status_code == 200:
                targets.append(resp.json()["target_id"])
            await asyncio.sleep(0.5)

        print("ממתין 8 שניות לפריסת כלל הנחילים...")
        await asyncio.sleep(8)

        state = await self.get_state()
        stress_success = True

        for tgt in targets:
            recon_count = sum(1 for d in state.get("recon_data", []) if
                              d.get("assigned_target_id") == tgt and d.get("flight_status") == "ACTIVE")
            attack_count = sum(1 for d in state.get("attack_data", []) if
                               d.get("assigned_target_id") == tgt and d.get("flight_status") in ["ACTIVE", "ATTACKING"])

            print(f"📊 מטרה {tgt}: תצפית: {recon_count} | תקיפה: {attack_count}")
            if recon_count < 1 or attack_count < 2:
                stress_success = False

        self.log_result("הקצאת כוחות במקביל תחת עומס", stress_success)

    async def run(self):
        print("🚀 מתחיל הרצת מאסטר טסט...")
        async with httpx.AsyncClient(timeout=15.0) as client:
            self.client = client
            is_ready = await self.wait_for_system_sync()

            if is_ready:
                await self.test_security_and_validation()
                target_id = await self.test_recon_first_rule()
                await self.test_full_mission_simulation(target_id)
                await self.test_manual_overrides()
                await self.test_multi_target_stress()

        print(f"\n🏁 סיכום: {self.passed_tests} בדיקות עברו בהצלחה, {self.failed_tests} נכשלו.")


if __name__ == "__main__":
    asyncio.run(MasterTester().run())
