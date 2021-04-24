import tempfile
from pathlib import Path
from unittest import TestCase

import numpy
import pandas

from src.utility.df2trec import write


class Test(TestCase):
    def test_write(self):
        example_df = pandas.DataFrame(
            [
                ["1", "clueweb1", numpy.float64(4.0)],
                ["1", "clueweb2", numpy.float64(2.0)],
                ["2", "clueweb3", numpy.float64(1.0)],
                ["2", "clueweb4", numpy.float64(2.0)],
            ],
            columns=["TopicID", "TrecID", "final"],
        )

        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory) / "out"

            write(example_df, path=directory)

            self.assertTrue(expr=directory.exists(), msg="write did not create a file")
