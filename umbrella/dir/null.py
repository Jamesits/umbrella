from . import DirProvider

class NullDirProvider(DirProvider):
    def search(self):
        return self.config['repos']
