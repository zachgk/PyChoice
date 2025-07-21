import inspect


def selector_matches(selectors: list[str]) -> list[bool]:
    if not selectors:
        return []
    res = []
    stack_info = inspect.stack()
    for selector in selectors:
        for frame_info in stack_info:
            if frame_info.function == selector:
                res.append(True)
                break

        res.append(False)

    return res
