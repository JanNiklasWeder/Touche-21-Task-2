#!/usr/bin/python

import jsonlines

buffer = ""

with jsonlines.open("../res/touche20-task2-docs-with-judgments.jsonl") as f:
    for line in f.iter():
        buffer += line["uuid"] + "," + line["id"] + "\n"

with open("../res/touche20-task2-docs-ID-UUID", "w+") as file:
    file.write(buffer)
