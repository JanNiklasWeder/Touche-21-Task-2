import os
import tempfile
from pathlib import Path
from unittest import TestCase, mock

import pandas

from src.postprocessing.SVM import svm


class TestCompound(TestCase):
    def test_from_file(self):
        SVM = svm.Compound.new()
        df = pandas.DataFrame([[5, 5], [4, 4], [3, 3]], columns=["Score_Test", "qrel"])
        SVM.train(df)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            SVM.save("test", directory)
            SVM = svm.Compound.from_file("test", directory)

        self.assertIsInstance(SVM, svm.Compound)

    def test_new(self):
        SVM = svm.Compound.new()

        self.assertIsInstance(SVM, svm.Compound)

    def test_save(self):
        SVM = svm.Compound.new()
        df = pandas.DataFrame([[5, 5], [4, 4], [3, 3]], columns=["Score_Test", "qrel"])
        SVM.train(df)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            SVM.save("test", directory)
            filename = directory / "test"

            self.assertTrue(expr=filename.exists(), msg="svm was not saved")

    def test_train(self):
        SVM = svm.Compound.new()

        df = pandas.DataFrame([[5, 5], [4, 4], [3, 3]], columns=["Score_Test", "qrel"])

        SVM.train(df)

        self.assertIsInstance(SVM, svm.Compound)

    def test_predict(self):
        SVM = svm.Compound.new()

        df = pandas.DataFrame([[5, 5], [4, 4], [3, 3]], columns=["Score_Test", "qrel"])
        expected = pandas.DataFrame([[1.224745, 5, 4.9],
                                     [0, 4, 4],
                                     [-1.224745, 3, 3.1]],
                                    columns=["Score_Test", "qrel", "final"])

        SVM.train(df)

        pandas.testing.assert_frame_equal(SVM.predict(df), expected)


class Test(TestCase):
    def test_train(self):
        df = pandas.DataFrame([[5, 5], [4, 4], [3, 3]], columns=["Score_Test", "qrel"])

        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)

            svm.train(df, "test", directory)
            filename = directory / "test"

            self.assertTrue(expr=(filename / "svm.joblib").exists(), msg="svm was not saved")
            self.assertTrue(expr=(filename / "mean_sd.csv").exists(), msg="svm was not saved")
            self.assertTrue(expr=(filename / "scores.pickle").exists(), msg="svm was not saved")

    def test_df_add_score(self):
        df = pandas.DataFrame([[5, 5], [4, 4], [3, 3]], columns=["Score_Test", "qrel"])
        expected = pandas.DataFrame([[1.224745, 5, 4.9],
                                     [0, 4, 4],
                                     [-1.224745, 3, 3.1]],
                                    columns=["Score_Test", "qrel", "final"])

        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)

            svm.train(df, "test", directory)
            df = svm.df_add_score(df, "test", directory)

        pandas.testing.assert_frame_equal(df, expected)
