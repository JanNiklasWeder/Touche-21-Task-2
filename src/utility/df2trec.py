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
    df["order"] = (
        df.sort_values(["final"], ascending=False)
        .groupby("TopicID")
        .final.transform(lambda x: pandas.factorize(x)[0] + 1)
    )

    while any(ties):
        df.loc[ties, "final"] = numpy.nextafter(df.loc[ties, "final"], numpy.NINF)
        ties = df.duplicated(subset=["final"])

    df.sort_values(["TopicID", "order"], ascending=True)

    with open(path, "w") as filehandle:
        for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Write to file:"):
            line = (
                str(row["TopicID"])
                + " Q0 "
                + str(row["TrecID"])
                + " "
                + str(row["order"])
                + " "
                + str(row["final"])
                + " "
                + team
                + "_"
                + tag
                + "\n"
            )
            filehandle.write(line)
