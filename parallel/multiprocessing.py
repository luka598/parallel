import typing as T
from multiprocessing import SimpleQueue, Process
from .future import Future


def worker(work_queue: SimpleQueue, result_queue: SimpleQueue):
    try:
        while True:
            message = work_queue.get()
            if message[0] == "STOP":
                work_queue.put(message)
                break

            elif message[0] == "FUTURE":
                future_idx = message[1]

                try:
                    future_state = Future.eval_future(message[2])
                except BaseException as e:
                    future_state = (True, False, None, e)

                result_queue.put((future_idx, future_state))
    except KeyboardInterrupt:
        print("Got SIGINT")


def eval_futures(
    futures: T.List[Future],
    workers: int,
    progress_callback: T.Callable[[int, int, int], T.Any] = lambda a, b, c: None,
):
    workers = min(len(futures), workers)
    work_queue = SimpleQueue()
    result_queue = SimpleQueue()
    processes = [
        Process(
            target=worker,
            args=(work_queue, result_queue),
        )
        for _ in range(workers)
    ]

    for process in processes:
        process.start()

    # ---

    try:
        future_idx = 0
        results = 0
        total = len(futures)

        for _ in range(workers):
            work_queue.put(("FUTURE", future_idx, futures[future_idx]))
            future_idx += 1
            progress_callback(future_idx, results, total)

        while future_idx < total:
            _future_idx, state = result_queue.get()
            futures[_future_idx].state = state
            results += 1

            work_queue.put(("FUTURE", future_idx, futures[future_idx]))
            future_idx += 1

            progress_callback(future_idx, results, total)

        while results < total:
            _future_idx, state = result_queue.get()
            futures[_future_idx].state = state
            results += 1

            progress_callback(future_idx, results, total)

    except KeyboardInterrupt as e:
        for future in futures:
            future.cancel()
            future._exception = e

    work_queue.put(("STOP",))

    # ---

    for process in processes:
        process.join()

    work_queue.close()
    result_queue.close()
