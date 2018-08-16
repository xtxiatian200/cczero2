import os
import sys
import multiprocessing as mp

from logging import getLogger

_PATH_ = os.path.dirname(os.path.dirname(__file__))

if _PATH_ not in sys.path:
    sys.path.append(_PATH_)

from cchess_alphazero.lib.logger import setup_logger
from cchess_alphazero.config import Config
import cchess_alphazero.worker.compute_elo as evaluator

def setup_parameters(config):
    num_cores = mp.cpu_count()
    max_processes = 2
    if len(sys.argv) > 1:
        max_processes = int(sys.argv[1])
    if len(sys.argv) > 2:
        flag = sys.argv[2]
        if flag == 'new':
            config.internet.base_url = 'http://temp.52coding.com.cn'
        elif flag == 'new2':
            config.internet.base_url = 'http://temp3.52coding.com.cn'
        config.internet.upload_url = f'{config.internet.base_url}/api/upload_game_file/192x10'
        config.internet.upload_eval_url = f'{config.internet.base_url}/api/upload_eval_game_file'
        config.internet.get_latest_digest = f'{config.internet.base_url}/api/get_latest_digest/192x10'
        config.internet.get_evaluate_model_url = f'{config.internet.base_url}/api/query_for_evaluate'
        config.internet.update_elo_url = f'{config.internet.base_url}/api/add_eval_result/'
    search_threads = 20
    print(f"max_processes = {max_processes}, search_threads = {search_threads}")
    config.play.max_processes = max_processes
    config.play.search_threads = search_threads

if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    config_type = 'distribute'
    config = Config(config_type=config_type)
    config.opts.device_list = '0'
    config.opts.log_move = True
    config.resource.create_directories()
    setup_logger(config.resource.eval_log_path)
    config.eval.update_play_config(config.play)
    setup_parameters(config)
    # config.internet.download_base_url = 'http://alphazero-1251776088.cossh.myqcloud.com/model/'
    evaluator.start(config)
