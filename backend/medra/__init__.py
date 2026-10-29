"""MeDRA: real-time text mining of a model's chain-of-thought."""

import os

# numpy's OpenBLAS reserves a memory buffer per thread at import. MeDRA only
# does small sparse matrix work (TF-IDF), so threads buy nothing, and with
# many cores the reservation can fail when several layer processes are piped
# together. Must be set before numpy is first imported; an explicit setting wins.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
