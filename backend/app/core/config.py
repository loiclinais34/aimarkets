from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
import os
from urllib.parse import quote_plus


class Settings(BaseSettings):
    # Configuration de l'application
    app_name: str = "AIMarkets API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Configuration de la base de données
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "aimarkets"
    db_user: str = "loiclinais"
    db_password: str = ""
    db_ssl_mode: str = "prefer"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    # URL de connexion complète (générée automatiquement)
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{quote_plus(self.db_password)}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # Configuration Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_ssl: bool = False
    
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{quote_plus(self.redis_password)}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # Configuration de l'API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    api_reload: bool = True
    
    # Configuration de sécurité
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Configuration CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Configuration des modèles ML
    ml_models_path: str = "./models"
    ml_max_features: int = 1000
    ml_training_batch_size: int = 32
    ml_prediction_batch_size: int = 100
    
    # Configuration des corrélations
    correlation_window_sizes: List[int] = [5, 20, 60]
    correlation_methods: List[str] = ["pearson", "spearman", "kendall"]
    
    # Configuration des indicateurs techniques
    technical_sma_periods: List[int] = [5, 10, 20, 50, 200]
    technical_ema_periods: List[int] = [5, 10, 20, 50, 200]
    technical_rsi_period: int = 14
    technical_macd_fast: int = 12
    technical_macd_slow: int = 26
    technical_macd_signal: int = 9
    technical_bollinger_period: int = 20
    technical_bollinger_std: float = 2.0
    technical_atr_period: int = 14
    technical_stochastic_k: int = 14
    technical_stochastic_d: int = 3
    technical_stochastic_smooth: int = 3
    technical_williams_r_period: int = 14
    technical_roc_period: int = 10
    technical_cci_period: int = 20
    technical_volume_roc_period: int = 10
    technical_volume_sma_period: int = 20
    
    # Configuration des alertes
    alert_correlation_break: float = 0.7
    alert_sentiment_extreme: float = 0.8
    alert_volume_spike: float = 2.0
    alert_price_volatility: float = 0.05
    
    # Configuration des notifications
    notification_email_enabled: bool = False
    notification_email_smtp_host: str = ""
    notification_email_smtp_port: int = 587
    notification_email_smtp_user: str = ""
    notification_email_smtp_password: str = ""
    notification_email_from: str = ""
    
    # Configuration des fichiers de données
    data_historical_path: str = "/app/data/historical_data.csv"
    data_sentiment_path: str = "/app/data/historical_sentiment.csv"
    data_backup_path: str = "/app/backups"
    data_export_path: str = "/app/exports"
    
    # Configuration des logs
    log_file_path: str = "/app/logs"
    log_max_size: str = "10MB"
    log_backup_count: int = 5
    log_format: str = "json"
    log_level: str = "INFO"
    
    # Configuration du monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    
    # Configuration pour le développement
    dev_auto_reload: bool = True
    dev_debug_toolbar: bool = True
    dev_profiling: bool = False
    
    # Configuration pour les tests
    test_database_url: str = "postgresql://test_user:test_password@localhost:5432/aimarkets_test"
    test_redis_url: str = "redis://localhost:6379/1"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = ""
        extra = "ignore"


# Instance globale des paramètres
settings = Settings()