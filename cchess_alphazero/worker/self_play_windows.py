import os
import gc 
import numpy as np
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from logging import getLogger
from multiprocessing import Manager
from threading import Thread
from time import time
from collections import defaultdict
from threading import Lock
from time import sleep
from random import random

import cchess_alphazero.environment.static_env as senv
from cchess_alphazero.agent.model import CChessModel
from cchess_alphazero.agent.player import CChessPlayer, VisitState
from cchess_alphazero.agent.api import CChessModelAPI
from cchess_alphazero.config import Config
from cchess_alphazero.environment.env import CChessEnv
from cchess_alphazero.environment.lookup_tables import Winner, ActionLabelsRed, flip_policy, flip_move
from cchess_alphazero.lib.data_helper import get_game_data_filenames, write_game_data_to_file
from cchess_alphazero.lib.model_helper import load_model_weight, save_as_best_model, load_best_model_weight_from_internet
from cchess_alphazero.lib.tf_util import set_session_config
from cchess_alphazero.lib.web_helper import upload_file

logger = getLogger(__name__)

job_done = Lock()
thr_free = Lock()
rst = None
data = None
futures =[]

def start(config: Config):
    set_session_config(per_process_gpu_memory_fraction=1, allow_growth=True, device_list=config.opts.device_list)
    return SelfPlayWorker(config).start()

class SelfPlayWorker:
    def __init__(self, config: Config):
        """
        :param config:
        """
        self.config = config
        self.current_model, self.use_history = self.load_model()
        self.m = Manager()
        self.cur_pipes = self.m.list([self.current_model.get_pipes() for _ in range(self.config.play.max_processes)])

    def start(self):
        global job_done
        global thr_free
        global rst
        global data
        global futures

        self.buffer = []
        need_to_renew_model = True
        job_done.acquire(True)
        logger.info(f"自我博弈开始，请耐心等待....")

        with ProcessPoolExecutor(max_workers=self.config.play.max_processes) as executor:
            game_idx = 0
            while True:
                game_idx += 1
                start_time = time()

                if len(futures) == 0:
                    for i in range(self.config.play.max_processes):
                        ff = executor.submit(self_play_buffer, self.config, self.cur_pipes, self.use_history)
                        ff.add_done_callback(recall_fn)
                        futures.append(ff)

                job_done.acquire(True)

                end_time = time()

                turns = rst[0]
                value = rst[1]
                logger.debug(f"对局完成：对局ID {game_idx} 耗时{(end_time - start_time):.1f} 秒, "
                         f"{turns / 2}回合, 胜者 = {value:.2f} (1 = 红, -1 = 黑, 0 = 和)")
                self.buffer += data

                if (game_idx % self.config.play_data.nb_game_in_file) == 0:
                    self.flush_buffer()
                    self.remove_play_data(all=False) # remove old data
                ff = executor.submit(self_play_buffer, self.config, self.cur_pipes, self.use_history)
                ff.add_done_callback(recall_fn)
                futures.append(ff) # Keep it going
                thr_free.release()

        if len(data) > 0:
            self.flush_buffer()

    def load_model(self, config_file=None):
        use_history = False
        model = CChessModel(self.config)
        weight_path = self.config.resource.model_best_weight_path
        if not config_file:
            config_path = self.config.resource.model_best_config_path
            use_history = False
        else:
            config_path = os.path.join(self.config.resource.model_dir, config_file)
        try:
            if not load_model_weight(model, config_path, weight_path):
                model.build()
                save_as_best_model(model)
                use_history = True
        except Exception as e:
            logger.info(f"Exception {e}, 重新加载权重")
            return self.load_model(config_file='model_192x10_config.json')
        return model, use_history

    def flush_buffer(self):
        rc = self.config.resource
        game_id = datetime.now().strftime("%Y%m%d-%H%M%S.%f")
        filename = rc.play_data_filename_tmpl % game_id
        path = os.path.join(rc.play_data_dir, filename)
        logger.info("保存博弈数据到 %s" % (path))
        write_game_data_to_file(path, self.buffer)
        if self.config.internet.distributed:
            upload_worker = Thread(target=self.upload_play_data, args=(path, filename))
            upload_worker.start()
        self.buffer = []

    def remove_play_data(self,all=False):
        files = get_game_data_filenames(self.config.resource)
        if (all):
            for path in files:
                os.remove(path)
        else:
            while len(files) > self.config.play_data.max_file_num:
                os.remove(files[0])
                del files[0]

    def upload_play_data(self, path, filename):
        digest = CChessModel.fetch_digest(self.config.resource.model_best_weight_path)
        data = {'digest': digest, 'username': self.config.internet.username, 'version': '2.4'}
        response = upload_file(self.config.internet.upload_url, path, filename, data, rm=False)
        if response is not None and response['status'] == 0:
            logger.info(f"上传博弈数据 {filename} 成功.")
        else:
            logger.error(f'上传博弈数据 {filename} 失败. {response.msg if response is not None else None}')

def recall_fn(future):
    global thr_free
    global job_done
    global rst
    global data
    global futures

    thr_free.acquire(True)
    rst, data = future.result()
    futures.remove(future)
    job_done.release()

def self_play_buffer(config, cur, use_history=False) -> (tuple, list):
    pipe = cur.pop() # borrow

    if random() > config.play.enable_resign_rate:
        enable_resign = True
    else:
        enable_resign = False

    player = CChessPlayer(config, search_tree=defaultdict(VisitState), pipes=pipe, 
                            enable_resign=enable_resign, debugging=False, use_history=use_history)

    state = senv.INIT_STATE
    history = [state]
    # policys = [] 
    value = 0
    turns = 0
    game_over = False
    final_move = None
    no_eat_count = 0
    check = False
    no_act = None
    increase_temp = False

    while not game_over:
        start_time = time()
        action, policy = player.action(state, turns, no_act, increase_temp=increase_temp)
        end_time = time()
        if action is None:
            print(f"{turns % 2} (0 = 红; 1 = 黑) 投降了!")
            value = -1
            break
        print(f"博弈中: 回合{turns / 2 + 1} {'红方走棋' if turns % 2 == 0 else '黑方走棋'}, 着法: {action}, 用时: {(end_time - start_time):.1f}s")
        # policys.append(policy)
        history.append(action)
        try:
            state, no_eat = senv.new_step(state, action)
        except Exception as e:
            logger.error(f"{e}, no_act = {no_act}, policy = {policy}")
            game_over = True
            value = 0
            break
        turns += 1
        if no_eat:
            no_eat_count += 1
        else:
            no_eat_count = 0
        history.append(state)

        if no_eat_count >= 120 or turns / 2 >= config.play.max_game_length:
            game_over = True
            value = 0
        else:
            game_over, value, final_move, check = senv.done(state, need_check=True)
            no_act = []
            increase_temp = False
            if not game_over:
                if not senv.has_attack_chessman(state):
                    logger.info(f"双方无进攻子力，作和。state = {state}")
                    game_over = True
                    value = 0
            if not game_over and not check and state in history[:-1]:
                free_move = defaultdict(int)
                for i in range(len(history) - 1):
                    if history[i] == state:
                        if senv.will_check_or_catch(state, history[i+1]):
                            no_act.append(history[i + 1])
                        elif not senv.be_catched(state, history[i+1]):
                            increase_temp = True
                            free_move[state] += 1
                            if free_move[state] >= 3:
                                # 作和棋处理
                                game_over = True
                                value = 0
                                logger.info("闲着循环三次，作和棋处理")
                                break

    if final_move:
        # policy = build_policy(final_move, False)
        history.append(final_move)
        # policys.append(policy)
        state = senv.step(state, final_move)
        turns += 1
        value = -value
        history.append(state)

    player.close()
    del player
    gc.collect()

    if turns % 2 == 1:  # balck turn
        value = -value
    
    v = value
    data = [history[0]]
    for i in range(turns):
        k = i * 2
        data.append([history[k + 1], value])
        value = -value

    cur.append(pipe)
    return (turns, v), data

def build_policy(action, flip):
    labels_n = len(ActionLabelsRed)
    move_lookup = {move: i for move, i in zip(ActionLabelsRed, range(labels_n))}
    policy = np.zeros(labels_n)

    policy[move_lookup[action]] = 1

    if flip:
        policy = flip_policy(policy)
    return list(policy)
