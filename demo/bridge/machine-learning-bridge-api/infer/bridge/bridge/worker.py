"""Evaluate one dataframe expression in a separate Python process."""
import ast
import json
import math
from numbers import Real
import sys

import pandas as pd


def calculate(payload):
    df = pd.DataFrame.from_records(payload["records"], columns=payload["columns"])
    tree = ast.parse(payload["expression"], mode="eval")
    nodes = list(ast.walk(tree))
    if not any(isinstance(n,ast.Name) and n.id=="df" for n in nodes):
        raise ValueError("Expected an expression using the supplied dataframe.")
    if any(isinstance(n, ast.Attribute) and n.attr.startswith("_") or
           isinstance(n, ast.Name) and n.id.startswith("_") for n in nodes):
        raise ValueError("Private interpreter access is not available.")
    env = {"__builtins__": {}, "df":df,"pd":pd,"len":len,"abs":abs,"round":round,"sum":sum,"min":min,"max":max}
    value = eval(compile(tree,"<dataframe>","eval"),env)
    if isinstance(value,pd.Series):
        label = value.index.name
        frame = value.rename("value").reset_index()
        if not label and len(value.index.names)==1:
            frame = frame.rename(columns={frame.columns[0]:"label"})
    elif isinstance(value,pd.DataFrame):
        frame = value.reset_index() if any(value.index.names) else value
    elif isinstance(value,(Real,str)):
        frame = pd.DataFrame([{"value":value}])
    else:
        raise ValueError("Return a scalar, Series, or dataframe.")
    if frame.empty or not frame.columns.is_unique:
        raise ValueError("Result empty or ambiguously labelled.")
    for col in frame.select_dtypes("number"):
        if not all(math.isfinite(v) for v in frame[col]):
            raise ValueError("No verified value for the requested read.")
    result=frame.to_json(orient="records",date_format="iso",double_precision=15)
    return result


if __name__ == "__main__":
    try:
        payload=json.load(sys.stdin)
        print(calculate(payload))
    except Exception as error:
        sys.exit(str(error)[:400])
