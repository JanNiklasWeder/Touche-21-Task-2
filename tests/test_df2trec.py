import tempfile
from pathlib import Path
from unittest import TestCase

import pandas

from src.utility.df2trec import write


class Test(TestCase):
    def test_write(self):

        example_df = pandas.DataFrame(
            [["1","clueweb1","4"],
            ["1","clueweb2","2"],
            ["2","clueweb3","1"],
            ["2","clueweb4","2"]]
            ,columns=["TopicID",
                     "TrecID",
                     "final"]
        )

        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory) / "out"

            write(example_df,path=directory)

            self.assertTrue(expr=directory.exists(), msg="write did not create a file")

