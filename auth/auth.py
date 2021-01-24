#!/usr/bin/python
import pandas

keys = pandas.read_csv("../auth/keys.csv")


def get_key(name):
    buffer = keys.loc[keys['Names'] == name]
    buffer = (buffer['Keys'].values[0])
    #print(buffer)
    return buffer
