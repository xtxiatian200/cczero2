import argparse
import multiprocessing as mp

from logging import getLogger

from cchess_alphazero.lib.logger import setup_logger
from cchess_alphazero.config import Config, PlayWithHumanConfig

logger = getLogger(__name__)

CMD_LIST = ['self', 'opt', 'eval', 'play', 'eval', 'sl', 'ob']
PIECE_STYLE_LIST = ['WOOD', 'POLISH', 'DELICATE']
BG_STYLE_LIST = ['CANVAS', 'DROPS', 'GREEN', 'QIANHONG', 'SHEET', 'SKELETON', 'WHITE', 'WOOD']
RANDOM_LIST = ['none', 'small', 'medium', 'large']

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", help="what to do", choices=CMD_LIST)
    parser.add_argument("--new", help="run from new best model", action="store_true")
    parser.add_argument("--type", help="use normal setting", default="mini")
    parser.add_argument("--total-step", help="set TrainerConfig.start_total_steps", type=int)
    parser.add_argument("--ai-move-first", help="set human or AI move first", action="store_true")
    parser.add_argument("--cli", help="play with AI with CLI, default with GUI", action="store_true")
    parser.add_argument("--gpu", help="device list", default="0")
    parser.add_argument("--onegreen", help="train sl work with onegreen data", action="store_true")
    parser.add_argument("--skip", help="skip games", default=0, type=int)
    parser.add_argument("--ucci", help="play with ucci engine instead of self play", action="store_true")
    parser.add_argument("--piece-style", help="choose a style of piece", choices=PIECE_STYLE_LIST, default="WOOD")
    parser.add_argument("--bg-style", help="choose a style of board", choices=BG_STYLE_LIST, default="WOOD")
    parser.add_argument("--random", help="choose a style of randomness", choices=RANDOM_LIST, default="none")
    parser.add_argument("--distributed", help="whether upload/download file from remote server", action="store_true")
    parser.add_argument("--elo", help="whether to compute elo score", action="store_true")
    return parser

def setup(config: Config, args):
    config.opts.new = args.new
    if args.total_step is not None:
        config.trainer.start_total_steps = args.total_step
    config.opts.device_list = args.gpu
    config.resource.create_directories()
    if args.cmd == 'self':
        setup_logger(config.resource.main_log_path)
    elif args.cmd == 'opt':
        setup_logger(config.resource.opt_log_path)
    elif args.cmd == 'play' or args.cmd == 'ob':
        setup_logger(config.resource.play_log_path)
    elif args.cmd == 'eval':
        setup_logger(config.resource.eval_log_path)
    elif args.cmd == 'sl':
        setup_logger(config.resource.sl_log_path)

def start():
    parser = create_parser()
    args = parser.parse_args()
    config_type = args.type

    config = Config(config_type=config_type)
    setup(config, args)

    logger.info('Config type: %s' % (config_type))
    config.opts.piece_style = args.piece_style
    config.opts.bg_style = args.bg_style
    config.internet.distributed = args.distributed

    # use multiple GPU
    gpus = config.opts.device_list.split(',')
    if len(gpus) > 1:
        config.opts.use_multiple_gpus = True
        config.opts.gpu_num = len(gpus)
        logger.info(f"User GPU {config.opts.device_list}")

    if args.cmd == 'self':
        if args.ucci:
            import cchess_alphazero.worker.play_with_ucci_engine as self_play
        else:
            if mp.get_start_method() == 'spawn':
                import cchess_alphazero.worker.self_play_windows as self_play
            else:
                from cchess_alphazero.worker import self_play
        return self_play.start(config)
    elif args.cmd == 'opt':
        from cchess_alphazero.worker import optimize
        return optimize.start(config)
    elif args.cmd == 'play':
        if args.cli:
            import cchess_alphazero.play_games.play_cli as play
        else:
            from cchess_alphazero.play_games import play
        config.opts.light = False
        pwhc = PlayWithHumanConfig()
        pwhc.update_play_config(config.play)
        logger.info(f"AI move first : {args.ai_move_first}")
        play.start(config, not args.ai_move_first)
    elif args.cmd == 'eval':
        if args.elo == False:
            from cchess_alphazero.worker import evaluator
        else:
            if mp.get_start_method() == 'spawn':
                import cchess_alphazero.worker.compute_elo_windows as evaluator
            else:
                import cchess_alphazero.worker.compute_elo as evaluator
        config.eval.update_play_config(config.play)
        evaluator.start(config)
    elif args.cmd == 'sl':
        if args.onegreen:
            import cchess_alphazero.worker.sl_onegreen as sl
            sl.start(config, args.skip)
        else:
            from cchess_alphazero.worker import sl
            sl.start(config)
        
    elif args.cmd == 'ob':
        from cchess_alphazero.play_games import ob_self_play
        pwhc = PlayWithHumanConfig()
        pwhc.update_play_config(config.play)
        ob_self_play.start(config, args.ucci, args.ai_move_first)
        
