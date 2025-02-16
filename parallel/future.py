import typing as T


class Future:
    def __init__(self, fn, *args, **kwargs) -> None:
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

        self._cancelled = False
        self._completed = False
        self._result: T.Any = None
        self._exception: T.Optional[BaseException] = None

    def __repr__(self) -> str:
        return f"Future(CANC={int(self._cancelled)}|COMP={int(self._completed)})"

    @property
    def state(self):
        return self._cancelled, self._completed, self._result, self._exception

    @state.setter
    def state(self, new):
        self._cancelled, self._completed, self._result, self._exception = new

    def cancel(self):
        if not self._completed:
            self._cancelled = True

    def run(self):
        if self._cancelled or self._completed:
            raise Exception("Can't run a cancelled or already completed future")

        try:
            self._result = self._fn(*self._args, **self._kwargs)
        except Exception as e:
            self._exception = e

        self._completed = True

    def result(self):
        if self._cancelled or not self._completed:
            raise Exception("Can't get result of a incomplete or cancelled future")

        if self._exception is None:
            return self._result
        else:
            raise self._exception

    @staticmethod
    def eval_future(future: "Future"):
        future.run()
        return future.state
