class Config:
    def __init__(self, include, exclude, use_only, forks, bootstrap) -> None:
        self.include = include
        self.exclude = exclude
        self.use_only = use_only
        self.forks = forks
        self.bootstrap = bootstrap
