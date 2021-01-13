"""Approximately simulates trec_eval using pytrec_eval."""

import argparse
import os
import sys
from statistics import mean 
import pytrec_eval
from plotly import graph_objects as go

import xml.etree.ElementTree as ET
import pandas as pd

n_topics=50

def get_titles(file):
    tree = ET.parse(file)
    root = tree.getroot()
    titles = []
    i=1
    for title in root.iter('title'):
        if i<=int(n_topics):
            title = title.text.strip()
            titles.append(title)
    return titles

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('qrel')
    parser.add_argument('first_approach')
    parser.add_argument('second_approach')
    parser.add_argument('measure')

    args = parser.parse_args()

    assert os.path.exists(args.qrel)
    assert os.path.exists(args.first_approach)
    assert os.path.exists(args.second_approach)

    with open(args.qrel, 'r') as f_qrel:
        qrel = pytrec_eval.parse_qrel(f_qrel)

    with open(args.first_approach, 'r') as f_run:
        first_run = pytrec_eval.parse_run(f_run)
    
    with open(args.second_approach, 'r') as f_run:
        second_run = pytrec_eval.parse_run(f_run)

    evaluator = pytrec_eval.RelevanceEvaluator(
        qrel, {args.measure})

    first_results = evaluator.evaluate(first_run)
    second_results = evaluator.evaluate(second_run)


    def print_line(measure, scope, value):
        #scope = query_id = topic_id
        print('{:25s}{:8s}{:.22f}'.format(measure, scope, value))
    
    first_nDCGs = []
    first_query_value = {}
    for query_id, query_measures in first_results.items():
        for measure, value in sorted(query_measures.items()):
            first_nDCGs.append(value)
            #print_line(measure, query_id, value)
            first_query_value[query_id] = value
    print(' avg of first approach nDCG {:f}'.format(mean(first_nDCGs)))

    second_nDCGs = []
    second_query_value = {}
    for query_id, query_measures in second_results.items():
        for measure, value in sorted(query_measures.items()):
            second_nDCGs.append(value)
            #print_line(measure, query_id, value)
            second_query_value[query_id] = value
    print(' avg of second aprroach nDCG {:f}'.format(mean(second_nDCGs)))
    
    #display comparison plotting between first and second approach
    '''
    fig2 = go.Figure(
        data=[
            go.Bar(
                name="first approach",
                x=list(first_query_value.keys()),
                y=list(first_query_value.values()),
                offsetgroup=0,
            ),
            go.Bar(
                name="second approach",
                x=list(second_query_value.keys()),
                y=list(second_query_value.values()),
                offsetgroup=1,
            ),
        ],
        layout=go.Layout(
            title="comparing first and second approaches",
            yaxis_title="DCG value"
        )
    )
    fig2.show()
'''
    fig3 = go.Figure(
        data=[
            go.Scatter(
                name="first approach",
                x=list(first_query_value.keys()),
                y=list(first_query_value.values()),
                mode='lines+markers',
                #offsetgroup=0,
            ),
            go.Scatter(
                name="second approach",
                x=list(second_query_value.keys()),
                y=list(second_query_value.values()),
                mode='lines+markers',
                #offsetgroup=1,
            ),
        ],
        layout=go.Layout(
            title="comparing first and second approach",
            yaxis_title="DCG value"
        )
    )
    fig3.show()
    
     #print out all queries that model is better then base chatnoir (first)
    better_queries=[]
    for key, value in first_query_value.items():
        if second_query_value[key]>value:
            better_queries.append(key)
    print(better_queries)
    
    titles = get_titles("topics-task-2.xml")
    for query_id in better_queries:
        print(titles[int(query_id)-1])
    
if __name__ == "__main__":
    sys.exit(main())