import time
import sys
import logging

logger = logging.getLogger(__name__)

def start_countdown(duration_sec: int):
    """
    指定された秒数だけ待機し、コンソールに "Waiting...60...59..." のようにカウントダウンを表示する

    Args:
        duration_sec (int): 待機する秒数
    """
    if duration_sec <= 0:
        return
        
    logger.info(f"{duration_sec}秒間の待機を開始します。")
    
    # "Waiting..." を最初に表示
    sys.stdout.write("Waiting...")
    sys.stdout.flush()

    # 残り秒数を "..." 区切りで表示
    for i in range(duration_sec, 0, -1):
        sys.stdout.write(f"{i}")
        if i > 1:
            sys.stdout.write("...")
        sys.stdout.flush()
        time.sleep(1)
    
    # カウントダウン終了後に改行
    sys.stdout.write("\n")