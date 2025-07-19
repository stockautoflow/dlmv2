import time
import sys
import logging

logger = logging.getLogger(__name__)

def start_countdown(duration_sec: int):
    if duration_sec <= 0: return
        
    logger.info(f"{duration_sec}秒間の待機を開始します。")
    
    sys.stdout.write("Waiting...")
    sys.stdout.flush()

    for i in range(duration_sec, 0, -1):
        sys.stdout.write(f"{i}")
        if i > 1: sys.stdout.write("...")
        sys.stdout.flush()
        time.sleep(1)
    
    sys.stdout.write("\n")