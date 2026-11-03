class NemoErrorMessages:
    class Retrieval:
        KNOWLEDGE_BASE_ID_REQUIRED = "knowledge_base_id is required."
        QUERY_EMPTY = "Search query must be a non-empty string."
        TOP_K_TOO_LOW = "top_k value {} must be at least {}."
        TOP_K_TOO_HIGH = "top_k value {} must not exceed the Bedrock Knowledge Bases limit of {}."
        MINIMUM_RELEVANCE_SCORE_OUT_OF_RANGE = "minimum_relevance_score value {} is out of range [{}, {}]."
        FILTER_KEY_EMPTY = "Search filters must not contain empty keys."
        FILTER_VALUE_EMPTY = "Search filter '{}' must not have an empty value."
        FILTER_KEY_NOT_ALLOWED = "Search filters contain non-filterable or unknown keys: {}."
        FILTER_OPERATOR_UNSUPPORTED = "Unsupported search filter operator '{}'. Supported operators: {}."
        FILTER_VALUE_LIST_REQUIRED = "Search filter '{}' must use a non-empty list value for operator '{}'."
        FILTER_VALUE_STRING_LIST_REQUIRED = "Search filter '{}' must use a non-empty list of strings for operator '{}'."
        FILTER_VALUE_NUMBER_REQUIRED = "Search filter '{}' must use a number value for operator '{}'."
        FILTER_VALUE_STRING_REQUIRED = "Search filter '{}' must use a non-empty string value for operator '{}'."
        FILTER_VALUE_SCALAR_REQUIRED = "Search filter '{}' must use a string, number, or boolean value for operator '{}'."

    class Metadata:
        KEY_NOT_ALLOWED = "Metadata contains non-filterable or unknown keys: {}."
        FILTERABLE_KEY_COUNT_EXCEEDED = "Too many filterable keys."
        FILTERABLE_BYTES_EXCEEDED = "Filterable metadata exceeds 1KB limit."

    class SourceAsset:
        DOCUMENT_EMPTY = "Document '{}' is empty"
        DOCUMENT_TOO_LARGE = "Document '{}' exceeds the Bedrock document size limit. Size: {} bytes, Max: {} bytes."
        IMAGE_TOO_LARGE = "Image '{}' exceeds the Bedrock multimodal size limit. Size: {} bytes, Max: {} bytes (3.75 MB)."
        S3_NOT_READABLE = (
            "Source object '{}' is not readable by Nemo. "
            "For S3 sources, use a bucket and prefix the asset workflow role can read."
        )
        UNSUPPORTED_SCHEME = "Unsupported asset URL scheme: {}"
        TEXT_DECODE_FAILED = "MediaType '{}' could not be decoded as UTF-8 text."
        SIZE_LIMIT_EXCEEDED = "Source '{}' exceeds the configured size limit. Size: {} bytes, Max: {} bytes."
        HTTP_CREDENTIALS_FORBIDDEN = "HTTP source URLs must not include credentials."
        HTTP_UNSUPPORTED_SCHEME = "Unsupported HTTP source URL scheme: {}"
        HTTP_HOST_MISSING = "HTTP source URL is missing a host: {}"
        UNEXPECTED_LOAD_ERROR = "Unexpected source loading error for '{}'."

    class ShadowAsset:
        SHADOW_STORE_REF_S3_REQUIRED = "shadow_store_ref must be an s3:// URI, got: {}"
        DELETE_FAILED = "Failed to delete staged shadow asset '{}'."

    class Media:
        TYPE_REQUIRED = "MediaType is required."
        UNSUPPORTED_SUPPORTED = "Unsupported MediaType '{}'. Nemo v1 supports only: {}."
        AUDIO_VIDEO_UNSUPPORTED = (
            "Unsupported MediaType '{}'. Nemo v1 supports text and image assets only; audio and video are not supported yet."
        )
        UNSUPPORTED_TEXT_IMAGE = "Unsupported MediaType '{}'. Nemo currently supports text and image assets only."
        IMAGE_SOURCE_EXTENSION_REQUIRED = "Image source URL must end with .png, .jpg, or .jpeg."

    class Indexing:
        BEDROCK_S3_DATA_SOURCE_REQUIRES_SHADOW_STORE_REF = "S3-backed Bedrock data source requires an S3 shadow_store_ref."
        KB_IDS_DESCRIPTOR_KNOWLEDGE_BASE_ID_REQUIRED = "knowledge_base_id is required for KB ID descriptors."
        KB_IDS_DESCRIPTOR_DATA_SOURCE_ID_REQUIRED = "data_source_id is required for KB ID descriptors."
        KB_IDS_DESCRIPTOR_SHADOW_STORE_REF_REQUIRED = "shadow_store_ref is required for KB ID descriptors."
        INGESTION_ASSETS_REQUIRED = "At least one ingestion asset is required."
        INGESTION_ASSET_ID_REQUIRED = "asset_id is required for ingestion assets."
        INGESTION_ASSET_ID_DUPLICATED = "Duplicate ingestion asset_id values are not allowed: {}."
        INGESTION_ASSET_URL_REQUIRED = "asset_url is required for ingestion assets."
        ASSET_CONTENT_URIS_REQUIRED = "At least one asset content URI is required."
        ASSET_ID_REQUIRED = "asset_id is required."
        ASSET_CONTENT_URI_REQUIRED = "content_uri is required for asset '{}'."

    class Bedrock:
        DOCUMENT_STATUS_DETAILS_MISSING = "Bedrock returned no document status details."
        DOCUMENT_DETAILS_IDENTITY_MISSING = "Bedrock documentDetails could not be mapped back to requested assets."
        STATUS_REASON_MISSING = "Bedrock returned status {} without a statusReason."
        DOCUMENT_STATUS_MISSING = "Document is missing from Bedrock status lookup."
        STATUS_UNSUPPORTED = "Bedrock returned an unsupported status without a statusReason."
        CLIENT_UNEXPECTED = "Unexpected Bedrock client error during {}: {}: {}"
        UNEXPECTED_ERROR = "Unexpected Bedrock error during {}."

    class Provisioning:
        MULTIMODAL_STORAGE_BUCKET_REQUIRED = "MULTIMODAL_STORAGE_BUCKET_NAME is required for multimodal scopes."
        KB_UNSUPPORTED_CHUNKING_CONFIG = "Unsupported chunking config: {}"
        KB_LOG_DELIVERY_DESTINATION_ARN_MISSING = (
            "CloudWatch Logs delivery did not return ARN for Firehose destination {}."
        )
        S3_VECTORS_BUCKET_ARN_MISSING = "S3 Vectors did not return vectorBucketArn for bucket '{}'."
        S3_VECTORS_INDEX_NOT_CREATED = "S3 Vectors index could not be created or read back."

    class IndexDefinition:
        CONFIG_RECORD_REQUIRED = "{} record is required."
        CONFIG_STRATEGY_REQUIRED = "{} strategy is required."
        CONFIG_STRATEGY_UNSUPPORTED = "Unsupported {} strategy: {}"
        CONFIG_FIELD_REQUIRED = "{} field '{}' is required for strategy '{}'."
        CONFIG_FIELD_MUST_BE_INT = "{} field '{}' must be an integer for strategy '{}'."
        PROCESSING_CONFIG_REQUIRES_EMBEDDING_MODEL = "ProcessingConfig Strategy {} requires EmbeddingModel {}."
        NON_FILTERABLE_KEYS_MUST_BE_ADDITIONAL_INFO = 'non_filterable_keys must be exactly ["AdditionalInfo"].'
        EMBEDDING_DIMENSION_FIXED_MISMATCH = (
            "EmbeddingDimension {} does not match the fixed dimension {} for this model."
        )
        EMBEDDING_DIMENSION_UNSUPPORTED = "EmbeddingDimension {} is unsupported for this model. Supported dimensions: {}."
        EMBEDDING_DIMENSION_REQUIRED_FOR_UNKNOWN_MODEL = "EmbeddingDimension is required for unsupported embedding model: {}."
        VECTOR_INDEX_EMBEDDING_MODEL_UNSUPPORTED = (
            "Unsupported embedding model for vector index provisioning: {}. Provide EmbeddingDimension or add a known model spec."
        )
