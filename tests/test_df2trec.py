import tempfile
from pathlib import Path
from unittest import TestCase

import numpy
import pandas

from src.utility.df2trec import write


class Test(TestCase):
    def test_write(self):
        example_df = pandas.DataFrame(
            [["1", "clueweb1", numpy.float64(4)],
             ["1", "clueweb2", numpy.float64(2)],
             ["2", "clueweb3", numpy.float64(1)],
             ["2", "clueweb4", numpy.float64(2)]]
            , columns=["TopicID",
                       "TrecID",
                       "final"]
        )

        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "out.trec"

            write(example_df, path=file)

            self.assertTrue(expr=file.exists(), msg="write did not create a file")

            data = pandas.read_csv(file, delim_whitespace=True,
                                   names=["TopicID", "spacer", "TrecID", "rank", "score", "name"])

            print(numpy.nextafter(2, numpy.NINF))
            self.assertTrue(expr=data["TrecID"].is_unique, msg="Duplicated TrecIDs")
            self.assertTrue(expr=data["score"].is_unique, msg="Identical ranks")
