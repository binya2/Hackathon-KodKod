import httpx
import asyncio

COMMANDER_URL = "http://localhost:8001"
AGGREGATOR_URL = "http://localhost:8000"

async def run():
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.85, "lon": 35.15})
        target_id = resp.json()["target_id"]
        print(f"Target spawned: {target_id}")
        await asyncio.sleep(3)
        state = (await client.get(f"{AGGREGATOR_URL}/api/state")).json()
        attack_drone = next((d for d in state.get("attack_data", []) if d.get("assigned_target_id") == target_id), None)
        if attack_drone:
            engage_resp = await client.post(f"{COMMANDER_URL}/engage",
                                                 json={"action": "engage", "target_id": target_id,
                                                       "drone_id": attack_drone["drone_id"]})
            print(f"Status code: {engage_resp.status_code}")
            print(f"Response: {engage_resp.text}")

        else:
            print("No attack drone found.")

if __name__ == "__main__":
    asyncio.run(run())
