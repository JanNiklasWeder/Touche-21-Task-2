"""Approximately simulates trec_eval using pytrec_eval."""

import argparse
import os
import sys
from statistics import mean 
import pytrec_eval
from plotly import graph_objects as go
from collections import Counter
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('qrel')
    #parser.add_argument('chatnoir')
    #parser.add_argument('new')
    parser.add_argument('measure')

    args = parser.parse_args()

    assert os.path.exists(args.qrel)
    #assert os.path.exists(args.chatnoir)
    #assert os.path.exists(args.new)

    with open(args.qrel, 'r') as f_qrel:
        qrel = pytrec_eval.parse_qrel(f_qrel)
    #print(qrel)
    for topic_id, result in qrel.items():
        print(topic_id)
        print(Counter(list(result.keys())))
        
    '''
    with open(args.chatnoir, 'r') as f_run:
        base_run = pytrec_eval.parse_run(f_run)
    
    with open(args.new, 'r') as f_run:
        new_run = pytrec_eval.parse_run(f_run)
    
    evaluator = pytrec_eval.RelevanceEvaluator(
        qrel, {args.measure})

    base_results = evaluator.evaluate(base_run)
    new_results = evaluator.evaluate(new_run)


    def print_line(measure, scope, value):
        #scope = query_id = topic_id
        print('{:25s}{:8s}{:.22f}'.format(measure, scope, value))
    
    base_nDCGs = []
    base_query_value = {}
    for query_id, query_measures in base_results.items():
        for measure, value in sorted(query_measures.items()):
            base_nDCGs.append(value)
            #print_line(measure, query_id, value)
            base_query_value[query_id] = value
    print(' avg of chatnoir nDCG {:f}'.format(mean(base_nDCGs)))

    new_nDCGs = []
    new_query_value = {}
    for query_id, query_measures in new_results.items():
        for measure, value in sorted(query_measures.items()):
            new_nDCGs.append(value)
            #print_line(measure, query_id, value)
            new_query_value[query_id] = value
    print(' avg of new aprroach nDCG {:f}'.format(mean(new_nDCGs)))

    #display comparison plotting between base and new approach
    fig2 = go.Figure(
        data=[
            go.Bar(
                name="chatnoir",
                x=list(base_query_value.keys()),
                y=list(base_query_value.values()),
                offsetgroup=0,
            ),
            go.Bar(
                name="new approach",
                x=list(new_query_value.keys()),
                y=list(new_query_value.values()),
                offsetgroup=1,
            ),
        ],
        layout=go.Layout(
            title="comparing base chatnoir and approach with classifyWD_dep",
            yaxis_title="DCG value"
        )
    )
    fig2.show()

    fig3 = go.Figure(
        data=[
            go.Scatter(
                name="chatnoir",
                x=list(base_query_value.keys()),
                y=list(base_query_value.values()),
                mode='lines+markers',
                #offsetgroup=0,
            ),
            go.Scatter(
                name="new approach",
                x=list(new_query_value.keys()),
                y=list(new_query_value.values()),
                mode='lines+markers',
                #offsetgroup=1,
            ),
        ],
        layout=go.Layout(
            title="comparing base chatnoir and approach with classifyWD_dep",
            yaxis_title="DCG value"
        )
    )
    fig3.show()
    '''
if __name__ == "__main__":
    sys.exit(main())