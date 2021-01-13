"""Approximately simulates trec_eval using pytrec_eval."""

import argparse
import os
import sys
from statistics import mean 
import pytrec_eval


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('qrel')
    parser.add_argument('run')
    parser.add_argument('measure')

    args = parser.parse_args()

    assert os.path.exists(args.qrel)
    assert os.path.exists(args.run)

    with open(args.qrel, 'r') as f_qrel:
        qrel = pytrec_eval.parse_qrel(f_qrel)

    with open(args.run, 'r') as f_run:
        run = pytrec_eval.parse_run(f_run)
    
    evaluator = pytrec_eval.RelevanceEvaluator(
        qrel, {args.measure})

    results = evaluator.evaluate(run)
    
    def print_line(measure, scope, value):
        #scope = query_id = topic_id
        print('{:25s}{:8s}{:.22f}'.format(measure, scope, value))
    avg_DCG = []
    for query_id, query_measures in results.items():
   
        for measure, value in sorted(query_measures.items()):
            avg_DCG.append(value)
            #print_line(measure, query_id, value)
    #print(avg_DCG)
    #print(mean(avg_DCG))
    print(mean(avg_DCG))

if __name__ == "__main__":
    sys.exit(main())