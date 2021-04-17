from pathlib import Path
from unittest import TestCase

import pandas

from src.utility.ChatNoir import querys
from src.utility.auth.auth import Auth

path = Path(__file__).parent.parent
print(path)


class Test(TestCase):
    def test_get_titles(self):
        input = path / "data/topics-task-2.xml"
        out = querys.get_titles(input)

        expected_column_names = ['TopicID', 'topic']

        self.assertEqual(out.columns.tolist(),
                         expected_column_names,
                         msg="get_titles does not provide the correct Columns"
                         )


class TestChatNoir(TestCase):
    def test_api(self):
        auth = Auth(path)

        chatnoir = querys.ChatNoir(auth.get_key("ChatNoir"), path)

        expected_response = [{'score': 1057.6371,
                              'uuid': '81ae4041-65e3-5e39-8c31-0ca03d250fa2',
                              'index': 'cw12',
                              'trec_id': 'clueweb12-1903wb-07-16216',
                              'target_hostname': 'www.techday.co.nz',
                              'target_uri': 'http://www.techday.co.nz/netguide/news/google-liberates-google/21089/1/',
                              'page_rank': 1.1814474e-09,
                              'spam_rank': 75,
                              'title': '<em>Google</em> liberates <em>Google</em>+ - TechDay',
                              'snippet': 'The two are now in true competition, though, and <em>Google</em> looks '
                                         'committed to a fight to the finish. May the best network win. What do you '
                                         'think of the looming <em>Google</em>+&#x2F;Facebook battle?',
                              'explanation': None}]

        self.assertIsInstance(chatnoir, querys.ChatNoir)

        response = chatnoir.api("google", 1)
        self.assertEqual(response, expected_response, msg="chatnoir.api doesn't provide expected response")

    def test_get_response(self):
        query = pandas.DataFrame(['google'], columns=["query"])
        expected_df = pandas.DataFrame(
            [["google",
              "clueweb12-1903wb-07-16216",
              "81ae4041-65e3-5e39-8c31-0ca03d250fa2",
              "Google liberates Google+ - TechDay",
              "The two are now in true competition, though, and Google looks committed to a fight to the finish. May "
              "the best network win. What do you think of the looming Google+&#x2F;Facebook battle?",
              "www.techday.co.nz",
              1057.6371]],

            columns=["query",
                     "TrecID",
                     "uuid",
                     "title",
                     "snippet",
                     "target_hostname",
                     "Score_ChatNoir"]
        )

        auth = Auth(path)
        chatnoir = querys.ChatNoir(auth.get_key("ChatNoir"), path)

        response = chatnoir.get_response(query, 1)
        pandas.testing.assert_frame_equal(response, expected_df)
