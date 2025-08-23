from typing import Optional

class Trace:
    def __init__(self) -> None:
        self.count = 0

    def begin(self) -> None:
        self.count += 1

    def end(self) -> None:
        pass

class TraceStatus:
    def __init__(self) -> None:
        self.trace: Optional[Trace] = None

    def call_begin(self) -> None:
        if self.trace is not None:
            self.trace.begin()

    def call_end(self) -> None:
        if self.trace is not None:
            self.trace.end()

    def start(self) -> None:
        self.trace = Trace()

    def stop(self) -> Trace:
        trace = self.trace if self.trace is not None else Trace()
        self.trace = None
        return trace
