import httpx
import asyncio
import uuid

COMMANDER_URL = "http://localhost:8001"
AGGREGATOR_URL = "http://localhost:8000"


class SecurityTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.passed_tests = 0
        self.failed_tests = 0

    async def get_state(self):
        resp = await self.client.get(f"{AGGREGATOR_URL}/api/state")
        return resp.json()

    def log_result(self, test_name, success, reason=""):
        if success:
            print(f"✅ PASSED: {test_name}")
            self.passed_tests += 1
        else:
            print(f"❌ FAILED: {test_name} - {reason}")
            self.failed_tests += 1

    async def test_target_validation(self):
        print("\n--- בדיקה 1: מניעת פעולות על מטרה לא קיימת ---")
        fake_id = f"TGT-FAKE-{uuid.uuid4().hex[:6]}"

        print(f"בודק מטרה פיקטיבית: {fake_id}")

        # ניסיון פריסה
        resp_deploy = await self.client.post(f"{COMMANDER_URL}/deploy_drone",
                                             json={"role": "attack", "target_id": fake_id})
        print(f"Deploy Response: {resp_deploy.status_code} | Body: {resp_deploy.text}")

        # ניסיון תקיפה
        resp_engage = await self.client.post(f"{COMMANDER_URL}/engage",
                                             json={"action": "engage", "target_id": fake_id, "drone_id": "DRN-8"})
        print(f"Engage Response: {resp_engage.status_code} | Body: {resp_engage.text}")

        deploy_ok = resp_deploy.status_code == 404
        engage_ok = resp_engage.status_code == 404

        self.log_result("Target Validation", deploy_ok and engage_ok)

    async def test_manual_override(self):
        print("\n--- בדיקה 2: קטיעת תקיפה ע\"י תנועה ידנית ---")

        # 1. יצירת מטרה חדשה בצורה מבוקרת
        print("יוצר מטרה לבדיקה...")
        resp = await self.client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.8, "lon": 35.1})
        if resp.status_code != 200:
            print(f"❌ שגיאה ביצירת מטרה: {resp.text}")
            return

        target_id = resp.json()["target_id"]

        # 2. לולאת המתנה לסנכרון המטרה באגרגטור
        print(f"ממתין לסנכרון המטרה {target_id} במערכת...")
        target_found = False
        for _ in range(10):
            state = await self.get_state()
            if any(t['target_id'] == target_id for t in state.get('target_data', [])):
                target_found = True
                break
            await asyncio.sleep(1)

        if not target_found:
            self.log_result("Manual Override", False, "המטרה לא הופיעה באגרגטור בזמן")
            return

        # 3. המתנה לרחפן תקיפה שיוקצה ויהיה פעיל
        print(f"ממתין לרחפן תקיפה שיגיע למטרה...")
        attacker = None
        for _ in range(15):
            state = await self.get_state()
            attacker = next((d for d in state['attack_data']
                             if d['assigned_target_id'] == target_id and d['flight_status'] == "ACTIVE"), None)
            if attacker:
                break
            await asyncio.sleep(1)

        if not attacker:
            print("⚠️ לא נמצא רחפן תקיפה פעיל למטרה. מדלג.")
            return

        # 4. ביצוע פקודת אש וקטיעה מיידית
        drone_id = attacker['drone_id']
        print(f"שולח פקודת אש ל-{drone_id}...")
        await self.client.post(f"{COMMANDER_URL}/engage",
                               json={"action": "engage", "target_id": target_id, "drone_id": drone_id})

        print(f"שולח פקודת תנועה ידנית לקטיעת התקיפה של {drone_id}...")
        await self.client.post(f"{COMMANDER_URL}/manual_move",
                               json={"drone_id": drone_id, "lat": 32.0, "lon": 34.0, "alt": 500})

        # 5. בדיקת הסטטוס הסופי (בזכות ה-Timestamp Lock, ה-MANUAL אמור להישמר)
        await asyncio.sleep(1.5)
        state = await self.get_state()
        final_drone = next((d for d in state['attack_data'] if d['drone_id'] == drone_id), None)

        success = final_drone and final_drone['flight_status'] == "MANUAL"
        reason = f"Status: {final_drone['flight_status']}" if final_drone else "Drone lost"
        self.log_result("Manual Override", success, reason)

    async def run_all(self):
        print("=== התחלת סדרת בדיקות חוסן מלאה ===")
        await self.test_target_validation()
        await self.test_manual_override()

        print(f"\nסיכום: {self.passed_tests} הצלחות, {self.failed_tests} כשלים.")


if __name__ == "__main__":
    asyncio.run(SecurityTester().run_all())
