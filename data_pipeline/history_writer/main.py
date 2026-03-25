from service_manager import run_history_service

if __name__ == "__main__":
    try:
        run_history_service()
    except Exception as e:
        print(f"[Fatal] History service failed: {e}")
