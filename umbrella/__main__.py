import logging
from .logger_config import init_logging
import yaml
import sys
from .git_mirror import GitMirroredRepo

logger = logging.getLogger(__name__)


def main() -> int:
    logger.info("Starting")

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

    repo = GitMirroredRepo(r"A:\Umbrella_test\systemd-named-netns", "https://github.com/Jamesits/systemd-named-netns.git")
    repo.update()
    repo.snapshot()


if __name__ == "__main__":
    init_logging()
    sys.exit(main())
