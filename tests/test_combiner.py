import os
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from combiner import Combine

input = Path(__file__).parent / "input"


class TestCombine(TestCase):
    def test_run(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory / "data").mkdir()
            shutil.copy2(input / "keys.csv", directory /"data/keys.csv")
            shutil.copy2(Path(__file__).parent.parent / "data/touche2020-task2-relevance-withbaseline.qrels",
                         directory / "data/touche2020-task2-relevance-withbaseline.qrels")

            combiner = Combine(input/"topics-task-2.xml",directory)

            self.assertIsInstance(combiner,Combine)

            run = True
            msg = ""

            try:
                combiner.run(
                    score_argumentative=True,
                    score_trustworthiness=True,
                    score_similarity=True,
                    score_bert=False,
                    dry_run=True)
            except Exception as error:
                run = False
                msg = error

            self.assertTrue(expr=run, msg=msg)

            run = True
            msg = ""

            try:
                combiner.run(
                    preprocessing= True,
                    query_expansion= True,
                    weights = {'original': 5,
                                     'annotation': 4,
                                     'sensevec': 3,
                                     'embedded': 3,
                                     'preprocessing': 2,
                                     'syns': 1},
                    method= 'max',
                    score_argumentative = True,
                    underscore = 0.55,
                    score_trustworthiness = True,
                    lemma= True,
                    relation = True,
                    synonyms= True,
                    sensevec= True,
                    embedded= True,
                    score_similarity= True,
                    score_bert= False,
                    dry_run= False,
                    test = True
                )
            except Exception as error:
                msg = error
                run = False

            self.assertTrue(expr=run,msg=msg)

            shutil.rmtree(input.parent / "data",ignore_errors=True)

