import logging
from .logger_config import init_logging
import yaml
import sys
from .git_mirror import GitMirroredRepo
import argparse
from .utils import dict_search
import os
from .auth import AuthRuleMatcher
from .dir.null import NullDirProvider
from .dir.github import GitHubDirProvider
import re

logger = logging.getLogger(__name__)

provider_mapping = {
    "null": NullDirProvider,
    "github": GitHubDirProvider,
}

def main() -> int:
    # logger.info("Starting")
    
    parser = argparse.ArgumentParser(description="Backup your Git repo.")
    parser.add_argument('git_repo', type=str, nargs='?', help="URL to the source Git repo that you want to archive")
    parser.add_argument('destination', type=str, nargs='?', default=".", help="Backup target directory")
    parser.add_argument('--config', type=str, nargs='?', default=None, help="Config file (YAML) path")
    parser.add_argument('--username', type=str, nargs='?', default=None, help="Git username")
    parser.add_argument('--password', type=str, nargs='?', default=None, help="Git password")
    parser.add_argument('--key', type=str, nargs='?', default=None, help="SSH private key file")
    parser.add_argument('--recursive', type=bool, nargs='?', default=True, help='Backup submodules')
    args = parser.parse_args()

    config_content = None
    if args.config is not None:
        logger.debug("Reading config file")
        try:
            with open(args.config, encoding="utf-8") as f:
                config_content = yaml.safe_load(f)
        except FileNotFoundError:
            logger.exception("Config file not found")
            return -1
        except yaml.parser.ParserError:
            logger.exception("Config file parsing failed")
            return -1

    root_dir = dict_search(config_content, 'global', 'backup_destination_root')
    if root_dir:
        logging.debug(f"Backup root dir: {root_dir}")
        os.makedirs(root_dir, exist_ok=True)
        os.chdir(root_dir)

    # create authentication rules
    a = AuthRuleMatcher(dict_search(config_content, 'authentication'))
    if args.username and args.password:
        a.add_authentication_username_password(r"^https://", args.username, args.password)
    if args.key:
        a.add_authentication_ssh_key(r"^git@", args.key)

    # read directories
    repos = []
    config_directories = dict_search(config_content, "directories")
    if config_directories:
        for d in config_directories:
            provider = dict_search(d, "provider")
            if not provider: provider = "null"
            provider = provider.lower()
            for key, value in provider_mapping.items():
                if key.lower() == provider:
                    repos.extend(value(d, a).search())
                    continue
    if args.git_repo:
        repos.append(args.git_repo)

    repos = list(set(repos))
    for r in repos:
        logging.debug(f"Backup: {r}")

    logging.info(f"{len(repos)} repos collected")

    finished_repos = []
    while len(repos) > 0:
        r = repos.pop(0)
        logger.info(f"{len(finished_repos) + 1}/{len(finished_repos) + len(repos) + 1} backing up {r}...")

        kwargs = {
            "storage_directory": args.destination if r == args.git_repo else re.subn(r"[/:\\]", "_", r)[0],
            "upstream_url": r,
        }
        auth_strategy = a.match(r)
        if auth_strategy["type"] == "null":
            pass
        elif auth_strategy["type"] == "username_password":
            kwargs['git_username'] = auth_strategy['username']
            kwargs['git_password'] = auth_strategy['password']
        elif auth_strategy["type"] == "ssh_key":
            kwargs['git_ssh_key_path'] = auth_strategy['ssh_key']
        else:
            logger.error(f"Unsupported auth strategy type {auth_strategy['type']}")

        m = GitMirroredRepo(**kwargs)
        m.update()
        m.snapshot()

        finished_repos.append(r)

        # search for submodules
        if args.recursive:
            for sm in m.submodules():
                if sm in repos:
                    logger.debug(f"Submodule {sm} already in queue")
                elif sm in finished_repos:
                    logger.debug(f"Submodule {sm} already backed up")
                else:
                    repos.append(sm)
                    logger.info(f"Submodule {sm} appended to the queue")


if __name__ == "__main__":
    init_logging()
    sys.exit(main())
