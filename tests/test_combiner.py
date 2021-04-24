import os
import shutil
import tempfile
import traceback
from pathlib import Path
from unittest import TestCase

import pandas

from combiner import Combine

input = Path(__file__).parent / "input"


class TestCombine(TestCase):
    def test_run(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "data").mkdir()
            shutil.copy2(input / "keys.csv", directory / "data/keys.csv")
            shutil.copy2(Path(__file__).parent.parent / "data/touche2020-task2-relevance-withbaseline.qrels",
                         directory / "data/touche2020-task2-relevance-withbaseline.qrels")

            combiner = Combine(input / "topics-task-2.xml", directory)

            self.assertIsInstance(combiner, Combine)

            run = True
            msg = ""

            try:
                combiner.run(
                    score_argumentative=True,
                    score_trustworthiness=True,
                    score_similarity=True,
                    score_bert=True,
                    dry_run=True)
            except Exception as error:
                run = False
                msg = str(error) + "\n" + str(traceback.format_exc())

            self.assertTrue(expr=run, msg=msg)

            run = True
            msg = ""

            try:
                combiner.run(
                    preprocessing=True,
                    query_expansion=True,
                    weights={'original': 5,
                             'annotation': 4,
                             'sensevec': 3,
                             'embedded': 3,
                             'preprocessing': 2,
                             'syns': 1},
                    method='max',
                    score_argumentative=True,
                    underscore=0.55,
                    score_trustworthiness=True,
                    lemma=True,
                    relation=True,
                    synonyms=True,
                    sensevec=True,
                    embedded=True,
                    score_similarity=True,
                    score_bert=True,
                    dry_run=False,
                    test=True
                )

            except Exception as error:
                msg = str(error) + "\n" + str(traceback.format_exc())
                run = False

            self.assertTrue(expr=run, msg=msg)

            data = pandas.read_csv(directory / "out.trec", delim_whitespace=True,
                                   names=["TopicID", "spacer", "TrecID", "rank", "score", "name"])
            
            self.assertTrue(expr=data["TrecID"].is_unique, msg="Duplicated TrecIDs")
            self.assertTrue(expr=data["score"].is_unique, msg="Identical ranks")

            shutil.rmtree(input.parent / "data", ignore_errors=True)
