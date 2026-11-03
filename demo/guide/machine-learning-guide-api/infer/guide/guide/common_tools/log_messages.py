class ErrorMessages:

    ASSISTANT_FUNCTION_NOT_EXISTS = "Could not find assistant function in predict output"
    ERROR_PREDICTING_SUFFICIENCY_LEVEL = "Error in predicting the sufficiency level the received error: {}"
    ERROR_PREDICTING_SENSITIVITY_LEVEL = "Error in predicting the sensitivity level the received error: {}"
    ERROR_GENERATING_FOLLOWUP = "Error in predicting the followup the received error: {}"
    ERROR_BUILDING_CONVERSATION = "Error in building the conversation the received error: {}"
    EXECUTOR_ERROR = "Error during task execution in asynchronous execution: {}"
    GENERAL_ERROR = "A general error occurred. Error: {}"
    INPUT_ERROR = "Error in input: {}"
    KEY_MISSING_FROM_ASSISTANT_TOOLS = "Assistant tools missed a required key: {}"
    OPENAI_ERROR_MESSAGE = "OpenAI call failed with error: {}"
    OPENAI_PREDICTED_WRONG_KEY = "Unexpected key predicted by the LLM: {}"
    OPENAI_PARSED_ARGUMENTS_NULL =  "OpenAI call contains a null parsed arguments"
    PREDICT_OUTPUT_PARSE_FAILED = "Could not parse the required information from the predict output. Error received: {}"
    UNEXPECTED_ERROR_MESSAGE = "Unexpected error occurred. Error received: {}"
    ERROR_INCORRECT_TYPE = "Incorrect type of the generated follow-wp text: {} of type {}"
    ERROR_LANGUAGE_NOT_SUPPORTED = "{} LANGUAGE IS NOT SUPPORTED:"
    
   
    
    
