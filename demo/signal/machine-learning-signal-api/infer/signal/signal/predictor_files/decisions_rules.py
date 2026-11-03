class DecisionsRules:
    CHOICES = {
        "Continue": "Company-data request that Bridge can investigate using permitted sources.",
        "AskIndicator": "Supported task, but the user must choose what to measure.",
        "AskScope": "Supported task, but the user must choose a location, asset or group.",
        "AskPeriod": "Supported task, but the user must choose a time period.",
        "AskComparison": "Supported task, but the user must choose a comparison or ranking direction.",
        "AskOther": "Supported task, but another material choice remains unclear.",
        "Unsupported": "Requested task is outside the permitted capabilities and is unrelated to company data.",
    }
    MISSING = {"AskIndicator": "performance indicator", "AskScope": "location, asset or group",
               "AskPeriod": "time period", "AskComparison": "comparison", "AskOther": "intended meaning"}
