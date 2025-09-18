from __future__ import annotations

import ipaddress
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Server
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, ge=1, le=65535, env="APP_PORT")
    
    # Security
    max_request_size: int = Field(default=1048576, ge=1024, env="MAX_REQUEST_SIZE")  # 1MB
    rate_limit_requests: int = Field(default=100, ge=1, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, ge=1, env="RATE_LIMIT_WINDOW")  # 1 hour
    cors_origins: List[str] = Field(default_factory=lambda: ["*"], env="CORS_ORIGINS")
    
    # OAuth 2.0 / OpenID Connect
    oauth_enabled: bool = Field(default=True, env="OAUTH_ENABLED")
    oauth_provider: str = Field(default="google", env="OAUTH_PROVIDER")  # google, microsoft, generic
    oauth_client_id: Optional[str] = Field(default=None, env="OAUTH_CLIENT_ID")
    oauth_client_secret: Optional[str] = Field(default=None, env="OAUTH_CLIENT_SECRET")
    oauth_redirect_uri: str = Field(default="http://localhost:3000/auth/callback", env="OAUTH_REDIRECT_URI")
    oauth_scope: str = Field(default="openid email profile", env="OAUTH_SCOPE")
    oauth_authorization_url: Optional[str] = Field(default=None, env="OAUTH_AUTHORIZATION_URL")
    oauth_token_url: Optional[str] = Field(default=None, env="OAUTH_TOKEN_URL")
    oauth_userinfo_url: Optional[str] = Field(default=None, env="OAUTH_USERINFO_URL")
    
    # JWT Configuration
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, ge=5, le=1440, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1, le=30, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # MFA Configuration
    mfa_enabled: bool = Field(default=True, env="MFA_ENABLED")
    mfa_issuer_name: str = Field(default="SOC Agent", env="MFA_ISSUER_NAME")
    mfa_backup_codes_count: int = Field(default=10, ge=5, le=20, env="MFA_BACKUP_CODES_COUNT")
    
    # RBAC Configuration
    rbac_enabled: bool = Field(default=True, env="RBAC_ENABLED")
    default_user_role: str = Field(default="analyst", env="DEFAULT_USER_ROLE")
    
    # S3-Compatible Storage Configuration
    storage_enabled: bool = Field(default=True, env="STORAGE_ENABLED")
    storage_provider: str = Field(default="s3", env="STORAGE_PROVIDER")  # s3, minio, gcs, azure
    storage_endpoint_url: Optional[str] = Field(default=None, env="STORAGE_ENDPOINT_URL")
    storage_access_key: Optional[str] = Field(default=None, env="STORAGE_ACCESS_KEY")
    storage_secret_key: Optional[str] = Field(default=None, env="STORAGE_SECRET_KEY")
    storage_bucket_name: str = Field(default="soc-agent-storage", env="STORAGE_BUCKET_NAME")
    storage_region: str = Field(default="us-east-1", env="STORAGE_REGION")
    storage_use_ssl: bool = Field(default=True, env="STORAGE_USE_SSL")
    storage_public_url: Optional[str] = Field(default=None, env="STORAGE_PUBLIC_URL")
    
    # Elasticsearch Configuration
    elasticsearch_enabled: bool = Field(default=True, env="ELASTICSEARCH_ENABLED")
    elasticsearch_host: str = Field(default="localhost", env="ELASTICSEARCH_HOST")
    elasticsearch_port: int = Field(default=9200, ge=1, le=65535, env="ELASTICSEARCH_PORT")
    elasticsearch_username: Optional[str] = Field(default=None, env="ELASTICSEARCH_USERNAME")
    elasticsearch_password: Optional[str] = Field(default=None, env="ELASTICSEARCH_PASSWORD")
    elasticsearch_use_ssl: bool = Field(default=False, env="ELASTICSEARCH_USE_SSL")
    elasticsearch_verify_certs: bool = Field(default=True, env="ELASTICSEARCH_VERIFY_CERTS")
    elasticsearch_ca_certs: Optional[str] = Field(default=None, env="ELASTICSEARCH_CA_CERTS")
    elasticsearch_index_prefix: str = Field(default="soc-agent", env="ELASTICSEARCH_INDEX_PREFIX")
    elasticsearch_log_retention_days: int = Field(default=30, ge=1, le=365, env="ELASTICSEARCH_LOG_RETENTION_DAYS")
    
    # Time-Series Database Configuration (InfluxDB)
    timeseries_enabled: bool = Field(default=True, env="TIMESERIES_ENABLED")
    timeseries_provider: str = Field(default="influxdb", env="TIMESERIES_PROVIDER")  # influxdb, timescaledb
    timeseries_url: str = Field(default="http://localhost:8086", env="TIMESERIES_URL")
    timeseries_token: Optional[str] = Field(default=None, env="TIMESERIES_TOKEN")
    timeseries_org: str = Field(default="soc-agent", env="TIMESERIES_ORG")
    timeseries_bucket: str = Field(default="soc-metrics", env="TIMESERIES_BUCKET")
    timeseries_retention_days: int = Field(default=90, ge=1, le=3650, env="TIMESERIES_RETENTION_DAYS")
    timeseries_batch_size: int = Field(default=1000, ge=100, le=10000, env="TIMESERIES_BATCH_SIZE")
    timeseries_flush_interval: int = Field(default=5, ge=1, le=60, env="TIMESERIES_FLUSH_INTERVAL")
    
    # Microservices Configuration
    microservices_enabled: bool = Field(default=True, env="MICROSERVICES_ENABLED")
    api_gateway_enabled: bool = Field(default=True, env="API_GATEWAY_ENABLED")
    api_gateway_port: int = Field(default=8000, ge=1000, le=65535, env="API_GATEWAY_PORT")
    
    # PostgreSQL Clustering
    postgres_clustering_enabled: bool = Field(default=True, env="POSTGRES_CLUSTERING_ENABLED")
    postgres_slave_hosts: Optional[List[str]] = Field(default=None, env="POSTGRES_SLAVE_HOSTS")
    postgres_connection_pool_size: int = Field(default=10, ge=1, le=100, env="POSTGRES_CONNECTION_POOL_SIZE")
    postgres_max_overflow: int = Field(default=20, ge=0, le=200, env="POSTGRES_MAX_OVERFLOW")
    
    # Inter-Service Communication
    messaging_enabled: bool = Field(default=True, env="MESSAGING_ENABLED")
    message_queue_type: str = Field(default="redis", env="MESSAGE_QUEUE_TYPE")  # redis, rabbitmq, kafka
    message_retry_attempts: int = Field(default=3, ge=1, le=10, env="MESSAGE_RETRY_ATTEMPTS")
    message_retry_delay: int = Field(default=5, ge=1, le=60, env="MESSAGE_RETRY_DELAY")
    
    # Advanced Monitoring
    monitoring_enabled: bool = Field(default=True, env="MONITORING_ENABLED")
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(default=8000, ge=1000, le=65535, env="PROMETHEUS_PORT")
    health_check_interval: int = Field(default=30, ge=10, le=300, env="HEALTH_CHECK_INTERVAL")
    metrics_retention_days: int = Field(default=30, ge=1, le=365, env="METRICS_RETENTION_DAYS")
    
    # Feature flags
    enable_email: bool = Field(default=True, env="ENABLE_EMAIL")
    enable_autotask: bool = Field(default=True, env="ENABLE_AUTOTASK")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")

    # Email
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, ge=1, le=65535, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    email_from: Optional[str] = Field(default=None, env="EMAIL_FROM")
    email_to: List[str] = Field(default_factory=list, env="EMAIL_TO")

    # Autotask
    at_base_url: Optional[str] = Field(default=None, env="AT_BASE_URL")
    at_api_integration_code: Optional[str] = Field(default=None, env="AT_API_INTEGRATION_CODE")
    at_username: Optional[str] = Field(default=None, env="AT_USERNAME")
    at_secret: Optional[str] = Field(default=None, env="AT_SECRET")
    at_account_id: Optional[int] = Field(default=None, env="AT_ACCOUNT_ID")
    at_queue_id: Optional[int] = Field(default=None, env="AT_QUEUE_ID")
    at_ticket_priority: int = Field(default=3, ge=1, le=5, env="AT_TICKET_PRIORITY")

    # Threat feeds
    otx_api_key: Optional[str] = Field(default=None, env="OTX_API_KEY")
    vt_api_key: Optional[str] = Field(default=None, env="VT_API_KEY")
    abuseipdb_api_key: Optional[str] = Field(default=None, env="ABUSEIPDB_API_KEY")

    # Scoring
    score_high: int = Field(default=70, ge=0, le=100, env="SCORE_HIGH")
    score_medium: int = Field(default=40, ge=0, le=100, env="SCORE_MEDIUM")

    # HTTP / Cache
    http_timeout: float = Field(default=8.0, ge=1.0, le=60.0, env="HTTP_TIMEOUT")
    ioc_cache_ttl: int = Field(default=1800, ge=60, env="IOC_CACHE_TTL")
    max_retries: int = Field(default=3, ge=0, le=10, env="MAX_RETRIES")
    retry_delay: float = Field(default=1.0, ge=0.1, le=10.0, env="RETRY_DELAY")

    # Webhook auth
    webhook_shared_secret: Optional[str] = Field(default=None, env="WEBHOOK_SHARED_SECRET")
    webhook_hmac_secret: Optional[str] = Field(default=None, env="WEBHOOK_HMAC_SECRET")
    webhook_hmac_header: str = Field(default="X-Signature", env="WEBHOOK_HMAC_HEADER")
    webhook_hmac_prefix: str = Field(default="sha256=", env="WEBHOOK_HMAC_PREFIX")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Monitoring
    metrics_port: int = Field(default=9090, ge=1, le=65535, env="METRICS_PORT")
    health_check_timeout: float = Field(default=5.0, ge=1.0, le=30.0, env="HEALTH_CHECK_TIMEOUT")
    
    # Database
    database_url: str = Field(default="sqlite:///./soc_agent.db", env="DATABASE_URL")
    postgres_host: Optional[str] = Field(default=None, env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, ge=1, le=65535, env="POSTGRES_PORT")
    postgres_user: Optional[str] = Field(default=None, env="POSTGRES_USER")
    postgres_password: Optional[str] = Field(default=None, env="POSTGRES_PASSWORD")
    postgres_db: Optional[str] = Field(default=None, env="POSTGRES_DB")
    
    # Redis
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, ge=1, le=65535, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, ge=0, le=15, env="REDIS_DB")
    
    # AI Integration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=2000, ge=100, le=4000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.1, ge=0.0, le=2.0, env="OPENAI_TEMPERATURE")
    enable_ai_analysis: bool = Field(default=True, env="ENABLE_AI_ANALYSIS")
    
    # ML Model Configuration
    ml_enabled: bool = Field(default=True, env="ML_ENABLED")
    ml_model_storage_path: str = Field(default="./models", env="ML_MODEL_STORAGE_PATH")
    ml_training_data_path: str = Field(default="./data/training", env="ML_TRAINING_DATA_PATH")
    ml_model_retention_days: int = Field(default=90, ge=1, le=365, env="ML_MODEL_RETENTION_DAYS")
    ml_model_update_interval: int = Field(default=24, ge=1, le=168, env="ML_MODEL_UPDATE_INTERVAL")  # hours
    
    # Anomaly Detection
    anomaly_detection_enabled: bool = Field(default=True, env="ANOMALY_DETECTION_ENABLED")
    anomaly_threshold: float = Field(default=0.5, ge=0.0, le=1.0, env="ANOMALY_THRESHOLD")
    anomaly_window_size: int = Field(default=100, ge=10, le=1000, env="ANOMALY_WINDOW_SIZE")
    anomaly_min_samples: int = Field(default=10, ge=5, le=100, env="ANOMALY_MIN_SAMPLES")
    
    # Risk Scoring
    risk_scoring_enabled: bool = Field(default=True, env="RISK_SCORING_ENABLED")
    risk_model_type: str = Field(default="ensemble", env="RISK_MODEL_TYPE")  # ensemble, gradient_boosting, neural_network
    risk_update_frequency: int = Field(default=1, ge=1, le=24, env="RISK_UPDATE_FREQUENCY")  # hours
    
    # Incident Classification
    classification_enabled: bool = Field(default=True, env="CLASSIFICATION_ENABLED")
    classification_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, env="CLASSIFICATION_CONFIDENCE_THRESHOLD")
    auto_classification_enabled: bool = Field(default=True, env="AUTO_CLASSIFICATION_ENABLED")
    
    # False Positive Reduction
    fp_reduction_enabled: bool = Field(default=True, env="FP_REDUCTION_ENABLED")
    fp_model_confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0, env="FP_MODEL_CONFIDENCE_THRESHOLD")
    fp_learning_enabled: bool = Field(default=True, env="FP_LEARNING_ENABLED")
    
    # Attack Pattern Recognition
    pattern_recognition_enabled: bool = Field(default=True, env="PATTERN_RECOGNITION_ENABLED")
    campaign_detection_window: int = Field(default=24, ge=1, le=168, env="CAMPAIGN_DETECTION_WINDOW")  # hours
    pattern_similarity_threshold: float = Field(default=0.6, ge=0.0, le=1.0, env="PATTERN_SIMILARITY_THRESHOLD")
    
    # ML Model Performance
    ml_model_monitoring_enabled: bool = Field(default=True, env="ML_MODEL_MONITORING_ENABLED")
    model_drift_threshold: float = Field(default=0.1, ge=0.0, le=1.0, env="MODEL_DRIFT_THRESHOLD")
    model_performance_threshold: float = Field(default=0.8, ge=0.0, le=1.0, env="MODEL_PERFORMANCE_THRESHOLD")
    auto_retrain_enabled: bool = Field(default=True, env="AUTO_RETRAIN_ENABLED")
    
    # Stream Processing Configuration
    kafka_bootstrap_servers: str = Field(default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic_prefix: str = Field(default="soc-agent", env="KAFKA_TOPIC_PREFIX")
    stream_window_size: int = Field(default=1000, ge=100, le=10000, env="STREAM_WINDOW_SIZE")
    stream_window_duration_minutes: int = Field(default=60, ge=5, le=1440, env="STREAM_WINDOW_DURATION_MINUTES")
    
    # Model Serving Configuration
    tf_serving_port: int = Field(default=8500, ge=1024, le=65535, env="TF_SERVING_PORT")
    tf_serving_grpc_port: int = Field(default=8501, ge=1024, le=65535, env="TF_SERVING_GRPC_PORT")
    tf_serving_model_path: str = Field(default="models/tf_serving", env="TF_SERVING_MODEL_PATH")
    mlflow_tracking_uri: str = Field(default="sqlite:///mlflow.db", env="MLFLOW_TRACKING_URI")
    mlflow_registry_uri: str = Field(default="sqlite:///mlflow.db", env="MLFLOW_REGISTRY_URI")
    mlflow_serving_port: int = Field(default=5000, ge=1024, le=65535, env="MLFLOW_SERVING_PORT")
    
    # A/B Testing Configuration
    ab_testing_enabled: bool = Field(default=True, env="AB_TESTING_ENABLED")
    ab_test_traffic_split: float = Field(default=0.5, ge=0.0, le=1.0, env="AB_TEST_TRAFFIC_SPLIT")
    ab_test_minimum_sample_size: int = Field(default=1000, ge=100, le=100000, env="AB_TEST_MINIMUM_SAMPLE_SIZE")
    ab_test_significance_level: float = Field(default=0.05, ge=0.01, le=0.1, env="AB_TEST_SIGNIFICANCE_LEVEL")
    
    # Auto-Retraining Configuration
    performance_based_retraining: bool = Field(default=True, env="PERFORMANCE_BASED_RETRAINING")
    drift_based_retraining: bool = Field(default=True, env="DRIFT_BASED_RETRAINING")
    feedback_based_retraining: bool = Field(default=True, env="FEEDBACK_BASED_RETRAINING")
    min_feedback_for_retraining: int = Field(default=100, ge=10, le=10000, env="MIN_FEEDBACK_FOR_RETRAINING")
    max_training_data_size: int = Field(default=10000, ge=1000, le=100000, env="MAX_TRAINING_DATA_SIZE")
    min_training_data_size: int = Field(default=100, ge=50, le=10000, env="MIN_TRAINING_DATA_SIZE")
    min_data_completeness: float = Field(default=0.8, ge=0.0, le=1.0, env="MIN_DATA_COMPLETENESS")
    min_data_freshness: float = Field(default=0.7, ge=0.0, le=1.0, env="MIN_DATA_FRESHNESS")
    retrain_interval_hours: int = Field(default=24, ge=1, le=168, env="RETRAIN_INTERVAL_HOURS")
    
    # Advanced Analytics Configuration
    threat_hunting_enabled: bool = Field(default=True, env="THREAT_HUNTING_ENABLED")
    attack_attribution_enabled: bool = Field(default=True, env="ATTACK_ATTRIBUTION_ENABLED")
    vulnerability_correlation_enabled: bool = Field(default=True, env="VULNERABILITY_CORRELATION_ENABLED")
    business_impact_analysis_enabled: bool = Field(default=True, env="BUSINESS_IMPACT_ANALYSIS_ENABLED")
    threat_intelligence_enabled: bool = Field(default=True, env="THREAT_INTELLIGENCE_ENABLED")
    
    # Threat Intelligence Feeds
    virustotal_api_key: Optional[str] = Field(default=None, env="VIRUSTOTAL_API_KEY")
    misp_url: Optional[str] = Field(default=None, env="MISP_URL")
    misp_api_key: Optional[str] = Field(default=None, env="MISP_API_KEY")
    opencti_url: Optional[str] = Field(default=None, env="OPENCTI_URL")
    opencti_api_key: Optional[str] = Field(default=None, env="OPENCTI_API_KEY")
    
    # Analytics Dashboard
    dashboard_cache_ttl: int = Field(default=300, ge=60, le=3600, env="DASHBOARD_CACHE_TTL")
    analytics_time_window_hours: int = Field(default=24, ge=1, le=168, env="ANALYTICS_TIME_WINDOW_HOURS")
    
    # MCP Servers
    kali_mcp_url: str = Field(default="http://localhost:5000", env="KALI_MCP_URL")
    vuln_scanner_url: str = Field(default="http://localhost:5001", env="VULN_SCANNER_URL")
    mcp_timeout: int = Field(default=30, ge=5, le=300, env="MCP_TIMEOUT")
    enable_offensive_testing: bool = Field(default=True, env="ENABLE_OFFENSIVE_TESTING")
    
    # Real-time capabilities
    enable_realtime: bool = Field(default=True, env="ENABLE_REALTIME")
    websocket_ping_interval: int = Field(default=30, ge=5, le=300, env="WEBSOCKET_PING_INTERVAL")
    websocket_ping_timeout: int = Field(default=10, ge=5, le=60, env="WEBSOCKET_PING_TIMEOUT")
    max_websocket_connections: int = Field(default=100, ge=1, le=1000, env="MAX_WEBSOCKET_CONNECTIONS")
    sse_keepalive_interval: int = Field(default=30, ge=5, le=300, env="SSE_KEEPALIVE_INTERVAL")
    alert_stream_buffer_size: int = Field(default=1000, ge=100, le=10000, env="ALERT_STREAM_BUFFER_SIZE")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("email_to", mode="before")
    @classmethod
    def parse_email_to(cls, v):
        if isinstance(v, str):
            return [email.strip() for email in v.split(",")]
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v):
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"log_format must be one of {valid_formats}")
        return v.lower()

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

SETTINGS = Settings()
