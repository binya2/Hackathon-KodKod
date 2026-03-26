import httpx
import asyncio
import time
import sys

COMMANDER_URL = "http://localhost:8001"
AGGREGATOR_URL = "http://localhost:8000"


async def test_workflow():
    async with httpx.AsyncClient() as client:
        print("\n--- 1. Testing Coordinate Validation ---")
        try:
            # Pydantic validation should trigger before even reaching the service logic
            resp = await client.post(f"{COMMANDER_URL}/new_target", json={"lat": 100.0, "lon": 35.0})
            print(f"Spawn with lat=100 (invalid): {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Error testing validation: {e}")

        print("\n--- 2. Spawning a valid target ---")
        resp = await client.post(f"{COMMANDER_URL}/new_target", json={"lat": 31.7, "lon": 35.2})
        if resp.status_code != 200:
            print(f"Failed to spawn target: {resp.status_code} - {resp.text}")
            return
        target_id = resp.json().get('target_id')
        print(f"Target spawned: {target_id}")

        # Wait for state to update
        print("Waiting for state to synchronize...")
        await asyncio.sleep(5)
        state_resp = await client.get(f"{AGGREGATOR_URL}/api/state")
        state = state_resp.json()

        # Find an attack drone assigned to our target
        attack_drones = state.get('attack_data', [])
        drone = next((d for d in attack_drones if d['assigned_target_id'] == target_id), None)

        if not drone:
            print(f"No drone assigned to {target_id} yet, picking first available...")
            drone = attack_drones[0]

        drone_id = drone['drone_id']
        print(f"Using drone: {drone_id}")

        print("\n--- 3. Testing Optimistic Update on Engage ---")
        if not drone.get('assigned_target_id') or drone.get('assigned_target_id') != target_id:
            print(f"Drone {drone_id} not assigned to {target_id}, deploying manually...")
            await client.post(f"{COMMANDER_URL}/deploy_drone", json={"role": "attack", "target_id": target_id})
            await asyncio.sleep(2)
            state = (await client.get(f"{AGGREGATOR_URL}/api/state")).json()
            drone = next((d for d in state.get('attack_data', []) if d['drone_id'] == drone_id), None)
            target_id = drone['assigned_target_id'] if drone else target_id

        if drone and drone.get('assigned_target_id'):
            t_id = drone['assigned_target_id']
            print(f"Drone {drone_id} assigned to {t_id}. Engaging...")
            # We need to make sure a RECON drone is documenting this target for the test to pass
            # spawn_target_with_swarm already deploys a recon drone.
            resp = await client.post(f"{COMMANDER_URL}/engage",
                                     json={"action": "engage", "target_id": t_id, "drone_id": drone_id})
            if resp.status_code == 200:
                payload = resp.json().get('payload', {})
                # Note: our optimistic update in services.py actually modifies the 'drone' object in local_world_state
                # The response from /engage currently returns the 'payload' dict which doesn't have the optimistic state.
                # But we can check the state aggregator immediately after.
                print(f"Engage command sent.")

                # Check state immediately for optimistic change (if possible, though network delay might exist)
                state_now = (await client.get(f"{AGGREGATOR_URL}/api/state")).json()
                drone_now = next((d for d in state_now.get('attack_data', []) if d['drone_id'] == drone_id), None)
                print(f"Immediate state check: flight_status={drone_now['flight_status']}")
            else:
                print(f"Engage failed: {resp.status_code} - {resp.text}")

        print("\n--- 4. Testing Recall and Release ---")
        resp = await client.post(f"{COMMANDER_URL}/recall_drone", json={"drone_id": drone_id})
        if resp.status_code == 200:
            print(f"Recall sent for {drone_id}.")

        await asyncio.sleep(2)
        state = (await client.get(f"{AGGREGATOR_URL}/api/state")).json()
        drone_after = next((d for d in state.get('attack_data', []) if d['drone_id'] == drone_id), None)
        if drone_after:
            print(
                f"State after 2s: flight_status={drone_after['flight_status']}, assigned_target_id={drone_after['assigned_target_id']}")

        print("\n--- 5. Testing Manual Move and Release ---")
        if len(attack_drones) > 1:
            other_drone_id = attack_drones[1]['drone_id']
            print(f"Deploying {other_drone_id} to {target_id}...")
            await client.post(f"{COMMANDER_URL}/deploy_drone", json={"role": "attack", "target_id": target_id})
            await asyncio.sleep(2)

            resp = await client.post(f"{COMMANDER_URL}/manual_move",
                                     json={"drone_id": other_drone_id, "lat": 32.0, "lon": 34.0, "alt": 100.0})
            if resp.status_code == 200:
                print(f"Manual move sent for {other_drone_id}.")

            await asyncio.sleep(2)
            state = (await client.get(f"{AGGREGATOR_URL}/api/state")).json()
            drone_after = next((d for d in state.get('attack_data', []) if d['drone_id'] == other_drone_id), None)
            if drone_after:
                print(
                    f"State after 2s: flight_status={drone_after['flight_status']}, assigned_target_id={drone_after['assigned_target_id']}")


if __name__ == "__main__":
    asyncio.run(test_workflow())
