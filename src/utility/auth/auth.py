#!/usr/bin/python
from pathlib import Path

import pandas


class Auth:
    def __init__(self, working_directory: Path):
        self.keyFile = pandas.read_csv(working_directory / "data/keys.csv")

    def get_key(self, name):
        buffer = self.keyFile.loc[self.keyFile["Names"] == name]
        buffer = buffer["Keys"].values[0]
        # print(buffer)
        return buffer
