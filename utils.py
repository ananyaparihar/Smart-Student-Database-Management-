from datetime import datetime


def log_action(action_name):
    def decorator(function):
        def wrapper(*args, **kwargs):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {action_name}")
            return function(*args, **kwargs)
        return wrapper
    return decorator


GRADE_RANGES = (
    (90, 100, "A+"),
    (80, 89, "A"),
    (70, 79, "B"),
    (60, 69, "C"),
    (50, 59, "D"),
    (0, 49, "F"),
)


def today():
    return datetime.now().strftime("%Y-%m-%d")
