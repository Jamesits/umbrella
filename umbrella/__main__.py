import logging
from .logger_config import init_logging
#import yaml
import sys
from .git_mirror import GitMirroredRepo
import argparse

logger = logging.getLogger(__name__)


def main() -> int:
    logger.info("Starting")
    
    parser = argparse.ArgumentParser(description="Backup your Git repo.")
    parser.add_argument('git_repo', type=str, help="URL to the source Git repo that you want to archive")
    parser.add_argument('destination', type=str, nargs='?', default=".", help="Backup target directory")
    args = parser.parse_args()

    # logger.debug("Reading config file")
    # try:
    #     with open("dev_assets/test_config_1.yaml", encoding="utf-8") as f:
    #         a = yaml.safe_load(f)
    # except FileNotFoundError:
    #     logger.exception("Config file not found")
    #     return 1
    # except yaml.parser.ParserError:
    #     logger.exception("Config file have format problem")
    #     return 1
    #
    # print(a)

    repo = GitMirroredRepo(args.destination, args.git_repo)
    repo.update()
    repo.snapshot()


if __name__ == "__main__":
    init_logging()
    sys.exit(main())
