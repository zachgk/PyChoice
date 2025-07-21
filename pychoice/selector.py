import inspect

def selector_matches(selector: str) -> bool:
    stack_info = inspect.stack()
    for frame_info in stack_info:
        if frame_info.function == selector:
            return True

    return False