import threading
from concurrent.futures import ThreadPoolExecutor


# ThreadPool for parallel jobs (max 5 threads)
MAX_THREADS = 5
parallel_executor = ThreadPoolExecutor(max_workers=MAX_THREADS)

# Lock to control access to the database when marking a job as processing
db_lock = threading.Lock()
