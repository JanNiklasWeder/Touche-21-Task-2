[![Tests](https://github.com/JanNiklasWeder/Touche-21-Task-2/actions/workflows/main.yml/badge.svg)](https://github.com/JanNiklasWeder/Touche-21-Task-2/actions/workflows/main.yml)
[![linter](https://github.com/JanNiklasWeder/Touche-21-Task-2/actions/workflows/linter.yml/badge.svg)](https://github.com/JanNiklasWeder/Touche-21-Task-2/actions/workflows/linter.yml)

# ...
A ranking pipeline for the shared touch Task 2: Argument Retrieval for Comparative Questions. 

The goal of the second task was to rank documents of the CLueWeb12 corpus to support an imaginary user in decision making.ChatNoir was used as a baseline and ... was built around this search engine.


## Usage
We provide two enviremonts.yml one for use with GPUs and one for use without GPUs. To use them Conda must be installed. Then the following command can be used to create the enviremont and to activate it.
```
conda env create -f environment.yml
conda activate touche
```
To return to the default environment
```
conda activate base
```
can be used.

The pipeline reloads all necessary and not locally available data. This may take some time depending on the available download rate.
To use the pipeline, combiner.py must first be called with the flag -d to learn the parameters necessary for the SVM using a qrels file.
All parts of the pipeline that are to be used later must be activated. It is possible to train several combinations one after the other and to use them later. All necessary data are stored locally under data.
```
python combiner.py [...] -d
```
After this, the pipeline can be used without the -d flag to generate a ranking. 

```
usage: combiner.py [-h] [-p] [-e] [-w] [-m] [-a] [-b] [-u] [-t] [-v] [-d] [-o] [-s] Topics

positional arguments:
  Topics                File path to 'topics-task-2.xml'

optional arguments:
  -h, --help            show this help message and exit
  -p, --Preprocessing   Activate the Preprocessing (default: False)
  -e, --QueryExpansion  Activate the QueryExpansion (default: False)
  -w , --WeightsMerging 
                        Adding weights for merging responses
  -m , --MergeMethod    Method for merging responses (default: max)
  -a, --Argumentative   Activate the argumentative score (default: False)
  -b, --Bert            Activate the computation of a score via Bert (default: False)
  -u , --Underscore     Underscore for argument score (default: 0.55)
  -t, --Trustworthiness
                        Activate the Trustworthiness score (default: False)
  -v , --loglevel       Set the detail of the log events (default: WARNING)
  -d, --DryRun          Start dry run to train the svm (default: False)
  -o , --output         File path where the output should be stored (default: ./out.trec)
  -s , --size           Size of the requested reply from ChatNoir (default: 100)
```
