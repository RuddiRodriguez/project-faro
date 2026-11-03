from knowledge_search.common.error_messages import SearchErrorMessages
from knowledge_search.retrieval.inputs.search_input import SearchFilter, SearchFilterOperator, SearchInput

MINIMUM_TOP_K = 1
MAXIMUM_BEDROCK_KNOWLEDGE_BASE_TOP_K = 100
MINIMUM_RELEVANCE_SCORE = 0.0
MAXIMUM_RELEVANCE_SCORE = 1.0
LIST_VALUE_OPERATORS = {SearchFilterOperator.IN, SearchFilterOperator.NOT_IN}
NUMBER_VALUE_OPERATORS = {SearchFilterOperator.GREATER_THAN,
                          SearchFilterOperator.GREATER_THAN_OR_EQUALS,
                          SearchFilterOperator.LESS_THAN,
                          SearchFilterOperator.LESS_THAN_OR_EQUALS}
STRING_VALUE_OPERATORS = {SearchFilterOperator.LIST_CONTAINS,
                          SearchFilterOperator.STARTS_WITH,
                          SearchFilterOperator.STRING_CONTAINS}


class Validator:
    @staticmethod
    def validate(search_input: SearchInput) -> str | None:
        if not search_input.knowledge_base_id.strip():
            return SearchErrorMessages.Retrieval.KNOWLEDGE_BASE_ID_REQUIRED
        if not search_input.query.strip():
            return SearchErrorMessages.Retrieval.QUERY_EMPTY
        if search_input.top_k < MINIMUM_TOP_K:
            return SearchErrorMessages.Retrieval.TOP_K_TOO_LOW.format(search_input.top_k, MINIMUM_TOP_K)
        if search_input.top_k > MAXIMUM_BEDROCK_KNOWLEDGE_BASE_TOP_K:
            return SearchErrorMessages.Retrieval.TOP_K_TOO_HIGH.format(search_input.top_k,
                                                                     MAXIMUM_BEDROCK_KNOWLEDGE_BASE_TOP_K)
        if search_input.minimum_relevance_score is not None and not (
            MINIMUM_RELEVANCE_SCORE <= search_input.minimum_relevance_score <= MAXIMUM_RELEVANCE_SCORE
        ):
            return SearchErrorMessages.Retrieval.MINIMUM_RELEVANCE_SCORE_OUT_OF_RANGE.format(search_input.minimum_relevance_score,
                                                                                           MINIMUM_RELEVANCE_SCORE,
                                                                                           MAXIMUM_RELEVANCE_SCORE)

        return Validator._validate_filters(search_input)

    @staticmethod
    def _validate_filters(search_input: SearchInput) -> str | None:
        undefined_filter_keys = set()
        for search_filter in search_input.filters:
            try:
                operator = SearchFilterOperator(search_filter.operator)
            except ValueError:
                supported_operator_values = sorted(supported_operator.value
                                                   for supported_operator in SearchFilterOperator)
                return SearchErrorMessages.Retrieval.FILTER_OPERATOR_UNSUPPORTED.format(search_filter.operator,
                                                                                      supported_operator_values)
            if not search_filter.key.strip():
                return SearchErrorMessages.Retrieval.FILTER_KEY_EMPTY
            if search_filter.key not in search_input.scope_filterable_keys:
                undefined_filter_keys.add(search_filter.key)
            value_error_message = Validator._validate_filter_value(search_filter, operator)
            if value_error_message is not None:
                return value_error_message

        if undefined_filter_keys:
            return SearchErrorMessages.Retrieval.FILTER_KEY_NOT_ALLOWED.format(sorted(undefined_filter_keys))
        return None

    @staticmethod
    def _validate_filter_value(search_filter: SearchFilter, operator: SearchFilterOperator) -> str | None:
        if operator in LIST_VALUE_OPERATORS:
            return Validator._validate_string_list_value(search_filter, operator)
        if operator in NUMBER_VALUE_OPERATORS:
            return Validator._validate_number_value(search_filter, operator)
        if operator in STRING_VALUE_OPERATORS:
            return Validator._validate_string_value(search_filter, operator)
        return Validator._validate_scalar_value(search_filter, operator)

    @staticmethod
    def _validate_string_list_value(search_filter: SearchFilter, operator: SearchFilterOperator) -> str | None:
        value = search_filter.value
        if not isinstance(value, list) or not value:
            return SearchErrorMessages.Retrieval.FILTER_VALUE_LIST_REQUIRED.format(search_filter.key, operator.value)
        if not all(isinstance(item, str) and item.strip() for item in value):
            return SearchErrorMessages.Retrieval.FILTER_VALUE_STRING_LIST_REQUIRED.format(search_filter.key,
                                                                                        operator.value)
        return None

    @staticmethod
    def _validate_number_value(search_filter: SearchFilter, operator: SearchFilterOperator) -> str | None:
        value = search_filter.value
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return SearchErrorMessages.Retrieval.FILTER_VALUE_NUMBER_REQUIRED.format(search_filter.key, operator.value)
        return None

    @staticmethod
    def _validate_string_value(search_filter: SearchFilter, operator: SearchFilterOperator) -> str | None:
        value = search_filter.value
        if not isinstance(value, str) or not value.strip():
            return SearchErrorMessages.Retrieval.FILTER_VALUE_STRING_REQUIRED.format(search_filter.key, operator.value)
        return None

    @staticmethod
    def _validate_scalar_value(search_filter: SearchFilter, operator: SearchFilterOperator) -> str | None:
        value = search_filter.value
        if value is None or (isinstance(value, str) and not value.strip()):
            return SearchErrorMessages.Retrieval.FILTER_VALUE_EMPTY.format(search_filter.key)
        if not isinstance(value, (str, int, float, bool)):
            return SearchErrorMessages.Retrieval.FILTER_VALUE_SCALAR_REQUIRED.format(search_filter.key, operator.value)
        return None
