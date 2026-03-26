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
        resp_deploy = await self.client.post(f"{COMMANDER_URL}/deploy_drone", json={"role": "attack", "target_id": fake_id})
        print(f"Deploy Response: {resp_deploy.status_code} | Body: {resp_deploy.text}")
        
        # ניסיון תקיפה
        resp_engage = await self.client.post(f"{COMMANDER_URL}/engage", json={"action": "engage", "target_id": fake_id, "drone_id": "DRN-8"})
        print(f"Engage Response: {resp_engage.status_code} | Body: {resp_engage.text}")
        
        deploy_ok = resp_deploy.status_code == 404
        engage_ok = resp_engage.status_code == 404
        
        self.log_result("Target Validation", deploy_ok and engage_ok)

    async def test_manual_override(self):
        print("\n--- בדיקה 2: קטיעת תקיפה ע\"י תנועה ידנית ---")
        state = await self.get_state()
        if not state['target_data']:
            print("יוצר מטרה לבדיקה...")
            await self.client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.8, "lon": 35.1})
            await asyncio.sleep(2)
            state = await self.get_state()

        target_id = state['target_data'][0]['target_id']
        attacker = next((d for d in state['attack_data'] if d['flight_status'] == "ACTIVE"), None)
        if not attacker:
            print("אין רחפן פעיל. מדלג.")
            return

        print(f"שולח פקודת אש ל-{attacker['drone_id']}...")
        await self.client.post(f"{COMMANDER_URL}/engage", json={"action": "engage", "target_id": target_id, "drone_id": attacker['drone_id']})
        
        print("שולח פקודת תנועה ידנית לקטיעה...")
        resp = await self.client.post(f"{COMMANDER_URL}/manual_move", json={"drone_id": attacker['drone_id'], "lat": 32.0, "lon": 34.0, "alt": 500})
        
        await asyncio.sleep(1)
        state = await self.get_state()
        final_drone = next(d for d in state['attack_data'] if d['drone_id'] == attacker['drone_id'])
        self.log_result("Manual Override", final_drone['flight_status'] == "MANUAL", f"Status: {final_drone['flight_status']}")

    async def run_all(self):
        print("=== התחלת סדרת בדיקות חוסן מלאה ===")
        await self.test_target_validation()
        await self.test_manual_override()
        
        print(f"\nסיכום: {self.passed_tests} הצלחות, {self.failed_tests} כשלים.")

if __name__ == "__main__":
    asyncio.run(SecurityTester().run_all())
