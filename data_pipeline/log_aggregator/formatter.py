def format_log(log_data: dict) -> str:
    timestamp = log_data.get("timestamp", "N/A")
    level = log_data.get("level", "INFO")
    service = log_data.get("service", "unknown")
    message = log_data.get("message", "")

    return f"[{timestamp}] [{level:5}] [{service:16}] {message}"


def print_log(log_data: dict):
    print(format_log(log_data))
