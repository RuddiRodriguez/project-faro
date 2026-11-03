"""Evaluate one dataframe expression after removing host access from the worker."""
import ast
import ctypes
import json
import math
from numbers import Real
from pathlib import Path
import resource
import sys

import pandas as pd


def isolate():
    # Apply the OS boundary after pandas is imported. No file writes, network, child
    # processes, other projects, or application credentials are available to the expression.
    library = ctypes.CDLL("/usr/lib/libsandbox.dylib")
    roots = [str(Path(sys.prefix)/"lib"), "/System/Library", "/usr/lib"]
    profile = "(version 1)(deny default)(allow sysctl-read)(allow file-read* " + " ".join(
        "(subpath " + json.dumps(p) + ")" for p in roots) + ")"
    err = ctypes.c_char_p()
    if library.sandbox_init(profile.encode(), 0, ctypes.byref(err)):
        raise ValueError("Could not isolate the dataframe worker.")
    resource.setrlimit(resource.RLIMIT_CPU, (5,5))


def calculate(payload):
    df = pd.DataFrame.from_records(payload["records"], columns=payload["columns"])
    tree = ast.parse(payload["expression"], mode="eval")
    nodes = list(ast.walk(tree))
    if len(nodes)>400 or not any(isinstance(n,ast.Name) and n.id=="df" for n in nodes):
        raise ValueError("Expected a bounded expression using the supplied dataframe.")
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
    if frame.empty or frame.size>5000 or not frame.columns.is_unique:
        raise ValueError("Result empty, too large, or ambiguously labelled.")
    for col in frame.select_dtypes("number"):
        if not all(math.isfinite(v) for v in frame[col]):
            raise ValueError("No verified value for the requested read.")
    result=frame.to_json(orient="records",date_format="iso",double_precision=15)
    if len(result)>250000:
        raise ValueError("Result too large.")
    return result


if __name__ == "__main__":
    try:
        payload=json.load(sys.stdin)
        isolate()
        print(calculate(payload))
    except Exception as error:
        sys.exit(str(error)[:400])
