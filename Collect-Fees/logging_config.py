#!/usr/bin/env python3
"""
Logging Configuration

Sets up separate log files for each exchange and main collector
"""

import logging
import logging.handlers
import os
from datetime import datetime
from decouple import config

def setup_logging():
    """Set up logging configuration with separate files per exchange"""
    
    # Create logs directory
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Get log level from config
    log_level = getattr(logging, config('LOG_LEVEL', default='INFO').upper())
    
    # Create timestamp for log files
    timestamp = datetime.now().strftime("%Y%m%d")
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.handlers.RotatingFileHandler(
                os.path.join(logs_dir, f"fee_collector_{timestamp}.log"),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # Set up exchange-specific loggers
    exchanges = ['binance', 'kraken', 'gemini']
    
    for exchange in exchanges:
        logger = logging.getLogger(f"exchange.{exchange}")
        logger.setLevel(log_level)
        
        # Add file handler for this exchange
        handler = logging.handlers.RotatingFileHandler(
            os.path.join(logs_dir, f"{exchange}_{timestamp}.log"),
            maxBytes=5*1024*1024,  # 5MB per exchange
            backupCount=3
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Prevent duplicate messages in root logger
        logger.propagate = False
        
        # Also add console output for exchange loggers
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Set up ratio calculator logger
    ratio_logger = logging.getLogger("ratio_calculator")
    ratio_logger.setLevel(log_level)
    
    ratio_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, f"ratios_{timestamp}.log"),
        maxBytes=5*1024*1024,
        backupCount=3
    )
    
    ratio_formatter = logging.Formatter(
        '%(asctime)s - RATIO - %(levelname)s - %(message)s'
    )
    ratio_handler.setFormatter(ratio_formatter)
    ratio_logger.addHandler(ratio_handler)
    ratio_logger.propagate = False
    
    # Add console output for ratio logger
    ratio_console = logging.StreamHandler()
    ratio_console.setFormatter(ratio_formatter)
    ratio_logger.addHandler(ratio_console)
    
    return logging.getLogger(__name__)

def get_exchange_logger(exchange_name: str) -> logging.Logger:
    """Get logger for specific exchange"""
    return logging.getLogger(f"exchange.{exchange_name.lower()}")

def get_ratio_logger() -> logging.Logger:
    """Get ratio calculator logger"""
    return logging.getLogger("ratio_calculator")