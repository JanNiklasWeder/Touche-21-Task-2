#!/usr/bin/python
from pathlib import Path

import numpy
import pandas
from tqdm import tqdm


def write(
    df: pandas.DataFrame,
    tag: str = "NotDefined",
    team: str = "JackSparrow",
    path: Path = Path.cwd() / "out.trec",
) -> None:

    ties = df.duplicated(subset=["final"])
    eps = numpy.finfo(numpy.float64).eps * 100
    last = len(df.index)

    df["order"] = (
        df.sort_values(["final"], ascending=False)
        .groupby("TopicID")
        .final.transform(lambda x: pandas.factorize(x)[0] + 1)
    )

    while any(ties):
        first = ties.idxmax()
        df.loc[first:last, "final"] = df.loc[first:last, "final"] - eps
        ties = df.duplicated(subset=["final"])

    df.sort_values(["TopicID", "order"], ascending=True)

    with open(path, "w") as filehandle:
        for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Write to file:"):
            line = (
                str(row["TopicID"]) + " Q0 "
                + str(row["TrecID"]) + " "
                + str(row["order"]) + " "
                + str(numpy.format_float_positional(row["final"])) + " "
                + team + "_" + tag + "\n"
            )
            filehandle.write(line)
