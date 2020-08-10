import typing

class DirProvider:
    def __init__(self, config, auth_rule_matcher):
        self.config = config
        self.auth_rule_matcher = auth_rule_matcher
    
    def search(self) -> typing.List[typing.AnyStr]:
        raise NotImplementedError()
