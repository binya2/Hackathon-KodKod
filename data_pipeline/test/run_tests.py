import asyncio
import sys
import httpx
from test_cases import run_security_tests, run_mission_flow_tests, run_manual_override_tests, run_edge_cases_tests
from utils import wait_for_system_sync

async def main():
    print('🚀 מתחיל הרצת חבילת בדיקות מקיפה...')
    timeout = httpx.Timeout(20.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        is_ready = await wait_for_system_sync(client)
        if not is_ready:
            print('❌ המערכת לא מסונכרנת. הבדיקה מבוטלת.')
            return
        await run_security_tests(client)
        await run_mission_flow_tests(client)
        await run_manual_override_tests(client)
        await run_edge_cases_tests(client)
    print('\n🏁 הבדיקות הסתיימו. אם הכל ירוק, אפשר להמשיך לניקוי קוד הסרוויסים!')
if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())