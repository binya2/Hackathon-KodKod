from service_manager import run_service


def main():
    print("[Main] Launching History & Archive Service...")
    run_service()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[Main] Fatal error: {exc}")
