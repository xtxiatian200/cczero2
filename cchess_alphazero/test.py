import os
import sys
import multiprocessing as mp

_PATH_ = os.path.dirname(os.path.dirname(__file__))


if _PATH_ not in sys.path:
    sys.path.append(_PATH_)

def test_env():
    from cchess_alphazero.environment.env import CChessEnv
    env = CChessEnv()
    env.reset()
    print(env.observation)
    env.step('0001')
    print(env.observation)
    env.step('7770')
    print(env.observation)
    env.render()
    print(env.input_planes()[0+7:3+7])

def test_player():
    from cchess_alphazero.agent.player import CChessPlayer

def test_config():
    from cchess_alphazero.config import Config
    c = Config('mini')
    c.resource.create_directories()
    print(c.resource.project_dir, c.resource.data_dir)

def test_self_play():
    from cchess_alphazero.config import Config
    from cchess_alphazero.worker.self_play import start
    from cchess_alphazero.lib.logger import setup_logger
    c = Config('mini')
    c.resource.create_directories()
    setup_logger(c.resource.main_log_path)
    start(c)

def test_cli_play():
    from cchess_alphazero.play_games.test_cli_game import main
    main()

def test_gui_play():
    from cchess_alphazero.play_games.test_window_game import main
    main()

def test_optimise():
    from cchess_alphazero.worker.optimize import start
    from cchess_alphazero.config import Config
    from cchess_alphazero.lib.logger import setup_logger
    c = Config('mini')
    c.resource.create_directories()
    setup_logger(c.resource.main_log_path)
    start(c)

def test_light():
    from cchess_alphazero.environment.light_env.chessboard import L_Chessboard
    from cchess_alphazero.environment.chessboard import Chessboard
    lboard = L_Chessboard()
    while not lboard.is_end():
        for i in range(lboard.height):
            print(lboard.screen[i])
        print(f"legal_moves = {lboard.legal_moves()}")
        action = input(f'Enter move for {lboard.is_red_turn} r/b: ')
        lboard.move_action_str(action)
    for i in range(lboard.height):
        print(lboard.screen[i])
    print(lboard.winner)
    print(f"Turns = {lboard.steps / 2}")

def test_light_env():
    from cchess_alphazero.environment.env import CChessEnv
    from cchess_alphazero.config import Config
    c = Config('mini')
    env = CChessEnv(c)
    env.reset()
    print(env.observation)
    env.step('0001')
    print(env.observation)
    env.step('7770')
    print(env.observation)
    env.render()
    print(env.input_planes()[0+7:3+7])

def test_wxf():
    from cchess_alphazero.environment.light_env.chessboard import L_Chessboard
    lboard = L_Chessboard()
    while not lboard.is_end():
        for i in range(lboard.height):
            print(lboard.screen[i])
        print(f"legal_moves = {lboard.legal_moves()}")
        wxf = input(f'Enter WXF move for {lboard.is_red_turn} r/b: ')
        action = lboard.parse_WXF_move(wxf)
        print(action)
        lboard.move_action_str(action)

def test_sl():
    from cchess_alphazero.worker import sl
    from cchess_alphazero.config import Config
    from cchess_alphazero.environment.lookup_tables import ActionLabelsRed, flip_policy, flip_move
    c = Config('mini')
    labels_n = len(ActionLabelsRed)
    move_lookup = {move: i for move, i in zip(ActionLabelsRed, range(labels_n))}
    slworker = sl.SupervisedWorker(c)
    p1 = slworker.build_policy('0001', False)
    print(p1[move_lookup['0001']])
    p2 = slworker.build_policy('0001', True)
    print(p2[move_lookup[flip_move('0001')]])

def test_static_env():
    from cchess_alphazero.environment.env import CChessEnv
    import cchess_alphazero.environment.static_env as senv
    from cchess_alphazero.environment.static_env import INIT_STATE
    from cchess_alphazero.environment.lookup_tables import flip_move
    env = CChessEnv()
    env.reset()
    print("env:  " + env.observation)
    print("senv: " + INIT_STATE)
    state = INIT_STATE
    env.step('0001')
    state = senv.step(state, '0001')
    print(senv.evaluate(state))
    print("env:  " + env.observation)
    print("senv: " + state)
    env.step('7770')
    state = senv.step(state, flip_move('7770'))
    print(senv.evaluate(state))
    print("env:  " + env.observation)
    print("senv: " + state)
    env.render()
    board = senv.state_to_board(state)
    for i in range(9, -1, -1):
        print(board[i])
    print("env: ")
    print(env.input_planes()[0+7:3+7])
    print("senv: ")
    print(senv.state_to_planes(state)[0+7:3+7])
    print(f"env:  {env.board.legal_moves()}" )
    print(f"senv: {senv.get_legal_moves(state)}")
    print(set(env.board.legal_moves()) == set(senv.get_legal_moves(state)))

def test_onegreen():
    import cchess_alphazero.environment.static_env as senv
    from cchess_alphazero.environment.lookup_tables import flip_move
    init = '9999299949999999249999869999999958999999519999999999999999997699'
    state = senv.init(init)
    print(state)
    senv.render(state)
    move = senv.parse_onegreen_move('8685')
    state = senv.step(state, move)
    print(state)
    senv.render(state)
    move = senv.parse_onegreen_move('7666')
    state = senv.step(state, flip_move(move))
    print(state)
    senv.render(state)

def test_onegreen2():
    from cchess_alphazero.environment.env import CChessEnv
    import cchess_alphazero.environment.static_env as senv
    from cchess_alphazero.config import Config
    c = Config('mini')
    init = '9999299949999999249999869999999958999999519999999999999999997699'
    env = CChessEnv(c)
    env.reset(init)
    print(env.observation)
    env.render()
    move = senv.parse_onegreen_move('8685')
    env.step(move)
    print(env.observation)
    env.render()
    move = senv.parse_onegreen_move('7666')
    env.step(move)
    print(env.observation)
    env.render()

def test_ucci():
    import cchess_alphazero.environment.static_env as senv
    from cchess_alphazero.environment.lookup_tables import flip_move
    state = senv.INIT_STATE
    state = senv.step(state, '0001')
    fen = senv.state_to_fen(state, 1)
    print(fen)
    senv.render(state)
    move = 'b7b0'
    move = senv.parse_ucci_move(move)
    print(f'Parsed move {move}')
    move = flip_move(move)
    print(f'fliped move {move}')
    state = senv.step(state, move)
    senv.render(state)
    fen = senv.state_to_fen(state, 2)
    print(fen)

def test_done():
    import cchess_alphazero.environment.static_env as senv
    state = '4s4/9/4e4/p8/2e2R2p/P5E2/8P/9/9/4S1E2'
    board = senv.state_to_board(state)
    for i in range(9, -1, -1):
        print(board[i])
    print(senv.done(state))

def test_upload():
    from cchess_alphazero.lib.web_helper import upload_file
    from cchess_alphazero.config import Config
    c = Config('mini')
    url = 'http://alphazero.52coding.com.cn/api/upload_game_file'
    path = '/Users/liuhe/Documents/Graduation Project/ChineseChess-AlphaZero/data/play_data/test.json'
    filename = 'test.json'
    data = {'digest': 'test', 'username': 'test'}
    res = upload_file(url, path, filename=filename, data=data)
    print(res)

def test_download():
    from cchess_alphazero.lib.web_helper import download_file
    from cchess_alphazero.config import Config
    c = Config('mini')
    url = 'http://alphazero.52coding.com.cn/model_best_weight.h5'
    path = '/Users/liuhe/Downloads/model_best_weight.h5'
    res = download_file(url, path)
    print(res)

def test_request():
    from cchess_alphazero.lib.web_helper import http_request
    from cchess_alphazero.config import Config
    c = Config('mini')
    url = 'http://alphazero.52coding.com.cn/api/add_model'
    digest = 'd6fce85e040a63966fa7651d4a08a7cdba2ef0e5975fc16a6d178c96345547b3'
    elo = 0
    data = {'digest': digest, 'elo': elo}
    res = http_request(url, post=True, data=data)
    print(res)

def fixbug():
    from cchess_alphazero.config import Config
    from cchess_alphazero.lib.data_helper import get_game_data_filenames, read_game_data_from_file, write_game_data_to_file
    import cchess_alphazero.environment.static_env as senv
    c = Config('distribute')
    files = get_game_data_filenames(c.resource)
    cnt = 0
    fix = 0
    draw_cnt = 0
    for filename in files:
        try:
            data = read_game_data_from_file(filename)
        except:
            print(f"error: {filename}")
            os.remove(filename)
            continue
        state = data[0]
        real_data = [state]
        need_fix = True
        draw = False
        action = None
        value = None
        is_red_turn = True
        for item in data[1:]:
            action = item[0]
            value = -item[1]
            if value == 0:
                need_fix = False
                draw = True
                draw_cnt += 1
                break
            state = senv.step(state, action)
            is_red_turn = not is_red_turn
            real_data.append([action, value])
        if not draw:
            game_over, v, final_move = senv.done(state)
            if final_move:
                v = -v
                is_red_turn = not is_red_turn
            if not is_red_turn:
                v = -v
            if not game_over:
                v = 1
            # print(game_over, v, final_move, state)
            if v == data[1][1]:
                need_fix = False
            else:
                need_fix = True
        if need_fix:
            write_game_data_to_file(filename, real_data)
            # print(filename)
            fix += 1
        cnt += 1
        if cnt % 1000 == 0:
            print(cnt, fix, draw_cnt)
    print(f"all {cnt}, fix {fix}, draw {draw_cnt}")


def plot_model():
    from keras.utils import plot_model
    from cchess_alphazero.agent.model import CChessModel
    from cchess_alphazero.config import Config
    from cchess_alphazero.lib.model_helper import save_as_best_model
    config = Config('distribute')
    model = CChessModel(config)
    model.build()
    save_as_best_model(model)
    plot_model(model.model, to_file='model.png', show_shapes=True, show_layer_names=True)

def test_check_and_catch():
    import cchess_alphazero.environment.static_env as senv
    state = senv.fen_to_state('rnba1cbnr/1a7/1c7/p1p3p1p/2p5k/2P1R4/P1P3P1P/1C5C1/9/RNBAKABN1 r')
    # state = senv.fliped_state(state)
    ori_state = state
    senv.render(state)
    print()
    action = '4454'
    state = senv.step(state, action)
    senv.render(state)
    state = senv.fliped_state(state)
    print()
    senv.render(state)
    print(senv.will_check_or_catch(ori_state, action))

def test_be_catched():
    import cchess_alphazero.environment.static_env as senv
    state = senv.fen_to_state('rnbakab1r/9/1c3c2n/p1p5p/7p1/3PR4/P1P3P1P/C7C/9/RNBAKABN1 b')
    # state = senv.fliped_state(state)
    ori_state = state
    senv.render(state)
    print()
    action = '4454'
    print(senv.be_catched(ori_state, action))
    

if __name__ == "__main__":
    test_be_catched()
    
