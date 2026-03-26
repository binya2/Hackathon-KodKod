import httpx
import asyncio
import math
import uuid

COMMANDER_URL = "http://localhost:8001"
AGGREGATOR_URL = "http://localhost:8000"


def calculate_distance(pos1, pos2):
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
            print(f" -> Current base status: Recon SLEEP: {sleeping_recon}/1, Attack SLEEP: {sleeping_attack}/2")

            if sleeping_recon >= 1 and sleeping_attack >= 2:
                print(f"✅ המערכת מסונכרנת ומוכנה! (תצפית פנויים: {sleeping_recon}, תקיפה פנויים: {sleeping_attack})")
                return True
            await asyncio.sleep(1)
        return False

    async def test_security_and_validation(self):
        print("\n=== שלב 1: בדיקות אבטחה וולידציה ===")
        resp = await self.client.post(f"{COMMANDER_URL}/new_target", json={"lat": 100.0, "lon": 35.0})
        self.log_result("הגנת קואורדינטות (Pydantic)", resp.status_code == 422)

        fake_id = f"TGT-FAKE-{uuid.uuid4().hex[:6]}"
        resp_deploy = await self.client.post(f"{COMMANDER_URL}/deploy_drone",
                                             json={"role": "attack", "target_id": fake_id})
        resp_engage = await self.client.post(f"{COMMANDER_URL}/engage",
                                             json={"action": "engage", "target_id": fake_id, "drone_id": "DRN-1"})
        self.log_result("הגנה מפני מטרות פיקטיביות", resp_deploy.status_code == 404 and resp_engage.status_code == 404)

    async def test_recon_first_rule(self):
        print("\n=== שלב 2: חוק 'תצפית תחילה' (Recon First) ===")
        # נ"צ קרוב לבסיס אך דורש זמן טיסה קצר
        resp = await self.client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.805, "lon": 35.105})
        if resp.status_code != 200: return None

        target_id = resp.json()["target_id"]
        print(f"🎯 נוצרה מטרה {target_id}. מנסה לתקוף מיידית טרם הגעת תצפית...")

        # ניסיון תקיפה מידי
        state = await self.get_state()
        attack_drone = next((d for d in state.get("attack_data", []) if d.get("assigned_target_id") == target_id), None)

        if attack_drone:
            engage_resp = await self.client.post(f"{COMMANDER_URL}/engage",
                                                 json={"action": "engage", "target_id": target_id,
                                                       "drone_id": attack_drone["drone_id"]})
            self.log_result("בלימת תקיפה עיוורת (מרחק/תצפית)", engage_resp.status_code == 400)

        return target_id

    async def test_full_mission_simulation(self, target_id):
        if not target_id: return
        print(f"\n=== שלב 3: סימולציית משימה מלאה על מטרה {target_id} ===")

        print("ממתין לנעילת תצפית...")
        recon_drone_id = None
        for _ in range(30):
            state = await self.get_state()
            recon = next((d for d in state["recon_data"] if
                          d["assigned_target_id"] == target_id and d["flight_status"] == "ACTIVE"), None)
            if recon:
                recon_drone_id = recon["drone_id"]
                print(f"✅ תצפית {recon_drone_id} בעמדה.")
                break
            await asyncio.sleep(1)

        print("מתחיל סבבי תקיפה...")
        for _ in range(40):
            state = await self.get_state()
            target = next((t for t in state["target_data"] if t["target_id"] == target_id), None)

            if not target or target["health"] <= 0:
                print(f"💀 המטרה חוסלה!")
                # בדיקת ה-Auto Recall החדש
                await asyncio.sleep(2)
                state_after = await self.get_state()
                recon_after = next((d for d in state_after["recon_data"] if d["drone_id"] == recon_drone_id), None)
                self.log_result("סימולציית משימה + חזרה אוטומטית לבסיס",
                                recon_after and recon_after["flight_status"] == "RETURNING")
                return

            attackers = [d for d in state["attack_data"] if
                         d["assigned_target_id"] == target_id and d["weapons_count"] > 0]
            if attackers:
                attacker = attackers[0]
                await self.client.post(f"{COMMANDER_URL}/engage",
                                       json={"action": "engage", "target_id": target_id,
                                             "drone_id": attacker["drone_id"]})
            await asyncio.sleep(1.5)

    async def test_manual_overrides(self):
        print("\n=== שלב 4: קטיעת תקיפה (Manual Overrides) ===")
        resp = await self.client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.81, "lon": 35.11})
        target_id = resp.json()["target_id"]
        await asyncio.sleep(4)

        state = await self.get_state()
        attacker = next((d for d in state['attack_data'] if
                         d['assigned_target_id'] == target_id and d['flight_status'] == "ACTIVE"), None)

        if attacker:
            print(f"קוטע תקיפה של {attacker['drone_id']} ע\"י Manual Move...")
            await self.client.post(f"{COMMANDER_URL}/manual_move",
                                   json={"drone_id": attacker['drone_id'], "lat": 32.0, "lon": 34.0, "alt": 500.0})

            await asyncio.sleep(1.5)  # זמן לסנכרון Redis
            state = await self.get_state()
            drone = next(d for d in state['attack_data'] if d['drone_id'] == attacker['drone_id'])
            self.log_result("מעבר למצב MANUAL (Timestamp Lock)", drone['flight_status'] == "MANUAL")

    async def test_multi_target_stress(self):
        print("\n=== שלב 5: עומס מטרות (Stress Test) ===")
        targets = []
        for i in range(3):
            resp = await self.client.post(f"{COMMANDER_URL}/new_target",
                                          json={"lat": 31.83 + (i * 0.01), "lon": 35.13 + (i * 0.01)})
            if resp.status_code == 200: targets.append(resp.json()["target_id"])
            await asyncio.sleep(0.5)

        print("ממתין לפריסת נחילים...")
        await asyncio.sleep(10)
        state = await self.get_state()

        all_ok = True
        for tgt in targets:
            recons = sum(1 for d in state["recon_data"] if d["assigned_target_id"] == tgt)
            attacks = sum(1 for d in state["attack_data"] if d["assigned_target_id"] == tgt)
            print(f"📊 מטרה {tgt}: תצפית: {recons} | תקיפה: {attacks}")
            if recons < 1 or attacks < 2: all_ok = False

        self.log_result("הקצאת כוחות תחת עומס", all_ok)

        # ניקוי סופי - החזרת כולם הביתה
        print("\n🧹 מנקה את המרחב האווירי...")
        drones_to_recall = [d["drone_id"] for d in state["recon_data"] + state["attack_data"] if
                            d["flight_status"] != "SLEEP"]
        for d_id in drones_to_recall:
            await self.client.post(f"{COMMANDER_URL}/recall_drone", json={"drone_id": d_id})

    async def run(self):
        print("🚀 מתחיל הרצת מאסטר טסט סופי...")
        async with httpx.AsyncClient(timeout=20.0) as client:
            self.client = client
            if await self.wait_for_system_sync():
                await self.test_security_and_validation()
                target_id = await self.test_recon_first_rule()
                await self.test_full_mission_simulation(target_id)
                await self.test_manual_overrides()
                await self.test_multi_target_stress()

        print(f"\n🏁 סיכום סופי: {self.passed_tests} בדיקות עברו, {self.failed_tests} נכשלו.")


if __name__ == "__main__":
    asyncio.run(MasterTester().run())