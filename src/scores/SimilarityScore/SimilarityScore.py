# -*- coding: utf-8 -*-

import requests
import xml.etree.ElementTree as ET
import time
from collections import Counter
from itertools import chain
import pandas as pd
from pathlib import Path
from tqdm import tqdm


# install packages
from simpletransformers.language_representation import RepresentationModel
from scipy.spatial import distance


class SimilarityScore:
    def __init__(
        self, all_topics: [str], data: pd.DataFrame, transform_model_name: str = "gpt"
    ):

        self.data = data.reset_index(drop=True)
        self.n_samples = 5
        self.topics = all_topics
        # self.transform_model
        if transform_model_name == "gpt":
            gpt2_model = RepresentationModel(
                model_type="gpt2",
                model_name="gpt2-medium",
                args={"manual_seed": 42},
                use_cuda=False,
            )
            self.transform_model = gpt2_model
        if transform_model_name == "bert":
            bert_model = RepresentationModel(
                model_type="bert",
                model_name="bert-base-uncased",
                args={"manual_seed": 42},
                use_cuda=False,
            )
            self.transform_model = bert_model

        # import in advance automated generated texts for each topic with GPT2-Medium model
        start_TopicID = min(list(self.data["TopicID"].unique()))
        if start_TopicID == 1:
            # generated texts for topics from task 20
            path = Path(__file__).parent.joinpath("text_task20/generated_texts.txt")

        else:
            # generated texts for topics from task 21
            path = Path(__file__).parent.joinpath("text_task21/generated_texts.txt")

        filename = path
        with open(filename) as f:
            lines = f.read()
        local_generated_texts = []
        for line in lines.split("=" * 40 + "\n"):
            if len(line.replace("\n", "")) != 0:
                local_generated_texts.append(
                    [e.replace("\n", "") for e in line.split("\n\n\n")]
                )

        self.generated_texts = {
            (start_TopicID + i): local_generated_texts[i]
            for i in range(0, len(local_generated_texts))
        }
        self.topicid_topic = {
            self.data.iloc[i]["TopicID"]: self.data.iloc[i]["topic"]
            for i in range(0, len(self.data.index))
        }

    def get_similarity_scores(self):

        similarity_scores = []

        for i in tqdm(
            range(0, len(self.data.index)), desc="Similarity score progress:"
        ):
            topic_id = self.data.iloc[i]["TopicID"]
            doc = self.data.iloc[i]["title"] + self.data.iloc[i]["snippet"]
            similarity_score = self.calculate_similarity_for_doc(topic_id, doc)
            similarity_scores.append(similarity_score)

        self.data["Score_Similarity"] = similarity_scores

        return self.data

    def calculate_similarity_for_doc(self, topic_id, doc):

        generated_texts = self.load_generated_text_for_topic(topic_id)

        # add query and generted_texts in a list
        tmp = []
        tmp.append(doc)
        for text in generated_texts:
            tmp.append(text)

        # transformation to vectors
        vectors = self.transform_model.encode_sentences(tmp, combine_strategy="mean")
        # similarity
        scores = []
        doc_vector = vectors[0]
        generated_texts_vectors = vectors[1:]

        for vector in generated_texts_vectors:
            scores.append(1 - distance.cosine(doc_vector, vector))

        similarity_score = sum(scores) / len(scores)
        return similarity_score

    def load_generated_text_for_topic(self, required_topic_id):
        # adding original topic to its generated texts
        combined_data = []
        try:
            origin = self.topicid_topic[required_topic_id]
            generated = self.generated_texts[required_topic_id]
            combined_data = [origin + ". " + e for e in generated]
        except:
            print("error")
        return combined_data


if __name__ == "__main__":

    # READ RESULTS FROM CHATNOIR UND MERGED DF
    merged_resp = pd.read_csv("merged_results.csv", sep=";")
    print(merged_resp)

    print("\n" + "=====================GET ALL TOPICS=================")
    n_topics = 50

    def get_titles(filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        buffer = []
        i = 1
        for title in root.iter("title"):
            if i <= int(n_topics):
                buffer.append(title.text.strip())
            i = i + 1
        return buffer

    filename = "topics-task-2.xml"
    topics = get_titles(filename)

    print("\n" + "===================DF WITH SIMILARITY SCORE==============")
    df_with_similarity_score = SimilarityScore(
        topics, merged_resp, "gpt"
    ).get_similarity_scores()
    print(df_with_similarity_score)
