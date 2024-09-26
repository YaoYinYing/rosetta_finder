import contextlib
import time


@contextlib.contextmanager
def timing(msg: str):
    print(f"Started {msg}")
    tic = time.time()
    yield
    toc = time.time()
    print(f"Finished {msg} in {toc - tic:.3f} seconds")
