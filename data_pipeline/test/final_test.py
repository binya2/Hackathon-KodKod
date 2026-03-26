import httpx
import asyncio


async def test_existing_target():
    async with httpx.AsyncClient() as client:
        try:
            state = (await client.get("http://localhost:8000/api/state")).json()
            if not state['target_data']:
                print("אין מטרות באוויר!")
                return

            target_id = state['target_data'][-1]['target_id']
            attacker = next(d for d in state['attack_data'] if d['flight_status'] == 'SLEEP')

            print(f"--- תוקף מטרה קיימת {target_id} עם {attacker['drone_id']} ---")

            # 1. פריסה (התיקון החדש - יעביר ל-ACTIVE)
            await client.post("http://localhost:8001/deploy_drone", json={"role": "attack", "target_id": target_id})
            await asyncio.sleep(3)

            # 2. תקיפה
            for i in range(20):
                state = (await client.get("http://localhost:8000/api/state")).json()
                t = next((t for t in state['target_data'] if t['target_id'] == target_id), None)
                d = next((d for d in state['attack_data'] if d['drone_id'] == attacker['drone_id']), None)

                if not t:
                    print(f"💀 המטרה {target_id} חוסלה בהצלחה!")
                    break

                print(f"זמן {i}: בריאות {t['health']} | מצב רחפן: {d['flight_status']} | טילים: {d['weapons_count']}")

                if d['flight_status'] == "ACTIVE":
                    print("🚀 שולח פקודת אש!")
                    await client.post("http://localhost:8001/engage",
                                      json={"action": "engage", "target_id": target_id, "drone_id": d['drone_id']})

                await asyncio.sleep(2)
        except Exception as e:
            print(f"שגיאה בבדיקה: {e}")


if __name__ == "__main__":
    asyncio.run(test_existing_target())
