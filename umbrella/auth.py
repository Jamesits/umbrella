import logging
import re
import sys
import copy
import typing

logger = logging.getLogger(__name__)

class AuthRuleMatcher:
    def __init__(self, authentication_config_block: typing.List[typing.Dict[typing.AnyStr, typing.AnyStr]]):
        self.rules = []
        if authentication_config_block:
            for rule in authentication_config_block:
                d = {
                    "regex": None,
                }
                if "password" in rule:
                    d["type"] = "username_password"
                    d["username"] = rule["username"]
                    d["password"] = rule["password"]
                elif "ssh_key" in rule:
                    d["type"] = "ssh_key"
                    d["ssh_key"] = rule["ssh-key"]
                else:
                    logger.error("Unknown authentication method")
                    sys.exit(-1)

                for m in rule["matches"]:
                    d1 = copy.deepcopy(d)
                    d1['regex'] = re.compile(m)
                    self.rules.append(d1)

    def add_authentication_username_password(self, regex: typing.AnyStr, username: typing.AnyStr, password: typing.AnyStr) -> None:
        self.rules.append({
            "regex": re.compile(regex),
            "type": "username_password",
            "username": username,
            "password": password,
        })

    def add_authentication_ssh_key(self, regex: typing.AnyStr, ssh_key: typing.AnyStr) -> None:
        self.rules.append({
            "regex": re.compile(regex),
            "type": "ssh_key",
            "ssh_key": ssh_key,
        })

    def match(self, url) -> typing.Dict[typing.AnyStr, typing.Any]:
        for r in self.rules:
            if r["regex"].match(url) is not None:
                return r
        return {
            "regex": ".*",
            "type": "null",
        }