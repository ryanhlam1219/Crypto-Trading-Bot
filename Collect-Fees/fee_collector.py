#!/usr/bin/env python3
"""
Fee Data Collection System

Continuously collects trading fee data from multiple exchanges using
exponential transaction sizes (0.001x to 10x coin price).

Implements ratio calculation logic:
- T_ratio = T1 - T2 (transaction difference)
- fee_ratio = fee(T2) - fee(T1) (fee difference) 
- Ratio = T_ratio / fee_ratio
- Average ratios per epoch for fee prediction

Data structure: Map = {Key: [Price Points], Value: [{Fee, Timestamp}]}
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from decouple import config
import os
import glob

# Set up logging with separate files per exchange
from logging_config import setup_logging, get_exchange_logger, get_ratio_logger
setup_logging()
logger = logging.getLogger(__name__)

from ratio_calculator import RatioCalculator, FeePoint

@dataclass
class FeeData:
    fee: float
    timestamp: float
    exchange: str
    transaction_size: float
    coin_price: float

class FeeCollector:
    """Main fee collection orchestrator with ratio calculation"""
    
    def __init__(self):
        self.base_currency = config('BASE_CURRENCY', default='BTC')
        self.quote_currency = config('QUOTE_CURRENCY', default='USD')
        self.collection_interval = int(config('COLLECTION_INTERVAL_SECONDS', default=300))
        
        # Data storage: {transaction_size: [FeeData, ...]}
        self.fee_data: Dict[float, List[FeeData]] = {}
        
        # Ratio calculator
        self.ratio_calculator = RatioCalculator()
        
        # Initialize exchange collectors
        self.exchanges = []
        self._init_exchanges()
        
    def _init_exchanges(self):
        """Initialize available exchange collectors"""
        from exchanges.binance_collector import BinanceCollector
        from exchanges.kraken_collector import KrakenCollector
        from exchanges.gemini_collector import GeminiCollector
        
        # Initialize Binance
        try:
            self.exchanges.append(BinanceCollector(self.base_currency, self.quote_currency))
            logger.info("Binance collector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Binance: {e}")
            
        # Initialize Kraken
        try:
            self.exchanges.append(KrakenCollector(self.base_currency, self.quote_currency))
            logger.info("Kraken collector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Kraken: {e}")
            
        # Initialize Gemini
        try:
            self.exchanges.append(GeminiCollector(self.base_currency, self.quote_currency))
            logger.info("Gemini collector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}")
            
        logger.info(f"Initialized {len(self.exchanges)} exchange collectors")
    
    def generate_transaction_sizes(self, coin_price: float) -> List[float]:
        """
        Generate exponential transaction sizes following README spec:
        Start from $1000, double each time: $1000, $2000, $4000, $8000, $16000...
        until $1 million, ensuring minimum is 0.001x coin price
        """
        # Start from $1000 as specified in README
        base_sizes = []
        current = 1000.0
        
        while current <= 1000000.0:  # Up to $1M as specified
            base_sizes.append(current)
            current *= 2  # Double each time
        
        # Ensure minimum size constraint (0.001x coin price)
        min_allowed = max(0.001 * coin_price, 10.0)  # At least $10 minimum
        
        # Filter sizes that meet minimum requirement
        valid_sizes = [size for size in base_sizes if size >= min_allowed]
        
        # If no sizes meet the minimum, add some smaller sizes
        if not valid_sizes:
            current = min_allowed
            while current <= 1000000.0:
                valid_sizes.append(round(current, 2))
                current *= 2
        
        return sorted(valid_sizes)
    
    def collect_fees_for_exchange(self, exchange) -> List[FeeData]:
        """Collect fee data for all transaction sizes from one exchange"""
        fee_results = []
        
        try:
            # Get current coin price
            coin_price = exchange.get_current_price()
            if not coin_price:
                logger.error(f"Failed to get price from {exchange.name}")
                return fee_results
                
            # Generate transaction sizes
            transaction_sizes = self.generate_transaction_sizes(coin_price)
            logger.info(f"{exchange.name}: Testing {len(transaction_sizes)} sizes from ${min(transaction_sizes):.3f} to ${max(transaction_sizes):.2f}")
            
            # Collect fees for each size
            for size in transaction_sizes:
                try:
                    fee = exchange.get_trading_fee(size)
                    if fee is not None:
                        fee_data = FeeData(
                            fee=fee,
                            timestamp=time.time(),
                            exchange=exchange.name,
                            transaction_size=size,
                            coin_price=coin_price
                        )
                        fee_results.append(fee_data)
                        logger.debug(f"{exchange.name}: ${size:.3f} -> fee: {fee:.2f}")
                    
                    # Rate limiting between requests
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error collecting fee for {exchange.name} size ${size:.3f}: {e}")
                    
        except Exception as e:
            logger.error(f"Error collecting from {exchange.name}: {e}")
            
        return fee_results
    
    def store_fee_data(self, fee_results: List[FeeData]):
        """Store collected fee data and calculate ratios"""
        # Store in hashmap structure
        for fee_data in fee_results:
            size = fee_data.transaction_size
            if size not in self.fee_data:
                self.fee_data[size] = []
            self.fee_data[size].append(fee_data)
        
        # Calculate ratios for each exchange
        exchanges_data = {}
        for fee_data in fee_results:
            exchange = fee_data.exchange
            if exchange not in exchanges_data:
                exchanges_data[exchange] = []
            
            # Convert to FeePoint for ratio calculation
            fee_point = FeePoint(
                transaction_size=fee_data.transaction_size,
                fee=fee_data.fee,
                timestamp=fee_data.timestamp,
                exchange=fee_data.exchange
            )
            exchanges_data[exchange].append(fee_point)
        
        # Calculate and store ratios for each exchange
        for exchange, fee_points in exchanges_data.items():
            if len(fee_points) >= 2:
                ratios = self.ratio_calculator.calculate_ratios_for_fee_points(fee_points, exchange)
                if ratios:
                    self.ratio_calculator.store_ratios(exchange, ratios)
                    avg_ratio, count = self.ratio_calculator.calculate_epoch_ratio_average(ratios)
                    logger.info(f"{exchange} - Calculated {len(ratios)} ratios, average: {avg_ratio:.4f}")
            else:
                logger.debug(f"{exchange} - Need more fee points for ratio calculation")
    
    def save_data_to_disk(self):
        """Save collected data and ratios to JSON files (overall + per exchange)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create data directories
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Create exchange-specific directories
        for exchange_name in [ex.name for ex in self.exchanges]:
            exchange_dir = os.path.join(data_dir, exchange_name.lower())
            os.makedirs(exchange_dir, exist_ok=True)
        
        # Convert fee data to serializable format
        serializable_data = {}
        for size, fee_list in self.fee_data.items():
            serializable_data[str(size)] = [
                {
                    "fee": fd.fee,
                    "timestamp": fd.timestamp,
                    "exchange": fd.exchange,
                    "transaction_size": fd.transaction_size,
                    "coin_price": fd.coin_price,
                    "datetime": datetime.fromtimestamp(fd.timestamp).isoformat()
                }
                for fd in fee_list
            ]
        
        # Prepare exchange-specific data
        exchange_data = {}
        for exchange_name in [ex.name for ex in self.exchanges]:
            exchange_fee_data = {}
            for size, fee_list in self.fee_data.items():
                exchange_fees = [fd for fd in fee_list if fd.exchange == exchange_name]
                if exchange_fees:
                    exchange_fee_data[str(size)] = [
                        {
                            "fee": fd.fee,
                            "timestamp": fd.timestamp,
                            "transaction_size": fd.transaction_size,
                            "coin_price": fd.coin_price,
                            "datetime": datetime.fromtimestamp(fd.timestamp).isoformat()
                        }
                        for fd in exchange_fees
                    ]
            exchange_data[exchange_name] = exchange_fee_data

        # Add ratio analysis data
        ratio_data = {}
        for exchange in self.ratio_calculator.ratio_history:
            recent_avg = self.ratio_calculator.get_recent_ratio_average(exchange)
            ratio_data[exchange] = {
                "recent_ratio_average": recent_avg,
                "total_ratios_calculated": len(self.ratio_calculator.ratio_history[exchange])
            }
        
        # Cross-exchange average
        cross_avg = self.ratio_calculator.get_cross_exchange_ratio_average()
        
        # Save overall combined data
        filename = f"fee_data_combined_{timestamp}.json"
        filepath = os.path.join(data_dir, filename)
        full_data = {
            "timestamp": timestamp,
            "collection_info": {
                "base_currency": self.base_currency,
                "quote_currency": self.quote_currency,
                "exchanges": [ex.name for ex in self.exchanges],
                "total_data_points": sum(len(fee_list) for fee_list in self.fee_data.values())
            },
            "fee_data": serializable_data,
            "ratio_analysis": {
                "exchange_averages": ratio_data,
                "cross_exchange_average": cross_avg,
                "prediction_formula": "fee = transaction_amount / ratio_average"
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(full_data, f, indent=2)
        
        # Clean up old combined data files - keep only 3 most recent
        self._cleanup_combined_files(data_dir)
        
        # Save dedicated ratio analysis file
        self._save_ratio_analysis(data_dir, ratio_data, cross_avg, timestamp)
        
        # Save exchange-specific data files
        for exchange_name, ex_data in exchange_data.items():
            if ex_data:  # Only save if exchange has data
                exchange_dir = os.path.join(data_dir, exchange_name.lower())
                exchange_filename = f"{exchange_name.lower()}_{timestamp}.json"
                exchange_filepath = os.path.join(exchange_dir, exchange_filename)
                
                exchange_file_data = {
                    "timestamp": timestamp,
                    "exchange": exchange_name,
                    "base_currency": self.base_currency,
                    "quote_currency": self.quote_currency,
                    "fee_data": ex_data,
                    "ratio_analysis": {
                        "average": ratio_data.get(exchange_name, {}).get("recent_ratio_average", 0),
                        "total_ratios": ratio_data.get(exchange_name, {}).get("total_ratios_calculated", 0)
                    }
                }
                
                with open(exchange_filepath, 'w') as f:
                    json.dump(exchange_file_data, f, indent=2)
                
                # Clean up old exchange files - keep only 3 most recent per exchange
                self._cleanup_exchange_files(exchange_dir, exchange_name.lower())
                    
        logger.info(f"Saved combined data to {filepath}")
        logger.info(f"Saved {len(exchange_data)} exchange-specific data files")
        
        # Log current ratio averages and cross-exchange data
        logger.info("=== RATIO ANALYSIS ===")
        for exchange, data in ratio_data.items():
            logger.info(f"{exchange:8}: avg={data['recent_ratio_average']:8.4f} | total_ratios={data['total_ratios_calculated']:4d}")
        logger.info(f"Cross-Avg: {cross_avg:8.4f} | prediction: fee = transaction / {cross_avg:.4f}")
        logger.info("=" * 50)
    
    def _cleanup_combined_files(self, data_dir: str):
        """Keep only the 3 most recent combined data files"""
        pattern = os.path.join(data_dir, "fee_data_combined_*.json")
        combined_files = glob.glob(pattern)
        
        if len(combined_files) > 3:
            # Sort by modification time (oldest first)
            combined_files.sort(key=lambda x: os.path.getmtime(x))
            
            # Delete oldest files, keep only 3 most recent
            files_to_delete = combined_files[:-3]
            for old_file in files_to_delete:
                try:
                    os.remove(old_file)
                    logger.debug(f"Deleted old combined file: {os.path.basename(old_file)}")
                except Exception as e:
                    logger.warning(f"Failed to delete {old_file}: {e}")
            
            logger.info(f"Cleaned up {len(files_to_delete)} old combined files, kept 3 most recent")
    
    def _cleanup_exchange_files(self, exchange_dir: str, exchange_name: str):
        """Keep only the 3 most recent files per exchange"""
        pattern = os.path.join(exchange_dir, f"{exchange_name}_*.json")
        exchange_files = glob.glob(pattern)
        
        if len(exchange_files) > 3:
            # Sort by modification time (oldest first)
            exchange_files.sort(key=lambda x: os.path.getmtime(x))
            
            # Delete oldest files, keep only 3 most recent
            files_to_delete = exchange_files[:-3]
            for old_file in files_to_delete:
                try:
                    os.remove(old_file)
                    logger.debug(f"Deleted old {exchange_name} file: {os.path.basename(old_file)}")
                except Exception as e:
                    logger.warning(f"Failed to delete {old_file}: {e}")
            
            logger.info(f"Cleaned up {len(files_to_delete)} old {exchange_name} files, kept 3 most recent")
    
    def _save_ratio_analysis(self, data_dir: str, ratio_data: Dict, cross_avg: float, timestamp: str):
        """Save dedicated ratio analysis file - always overwrites the single file"""
        ratio_filename = "ratio_analysis.json"
        ratio_filepath = os.path.join(data_dir, ratio_filename)
        
        # Prepare detailed ratio analysis
        detailed_ratios = {}
        for exchange in self.ratio_calculator.ratio_history:
            exchange_ratios = self.ratio_calculator.ratio_history[exchange]
            if exchange_ratios:
                # Get recent ratios (last 50)
                recent = exchange_ratios[-50:] if len(exchange_ratios) > 50 else exchange_ratios
                detailed_ratios[exchange] = {
                    "current_average": ratio_data.get(exchange, {}).get("recent_ratio_average", 0),
                    "total_ratios_calculated": len(exchange_ratios),
                    "recent_ratios": [
                        {
                            "ratio": r.ratio,
                            "timestamp": r.timestamp,
                            "t1": r.t1,
                            "t2": r.t2,
                            "fee1": r.fee1,
                            "fee2": r.fee2,
                            "t_ratio": r.t_ratio,
                            "fee_ratio": r.fee_ratio
                        }
                        for r in recent[-10:]  # Last 10 ratios for review
                    ]
                }
        
        ratio_analysis = {
            "last_updated": timestamp,
            "datetime": datetime.fromtimestamp(float(timestamp.replace('_', '.'))).isoformat() if '_' in timestamp else datetime.now().isoformat(),
            "cross_exchange_average": cross_avg,
            "prediction_formula": f"fee = transaction_amount / {cross_avg:.4f}",
            "total_ratios_across_exchanges": sum(len(self.ratio_calculator.ratio_history[ex]) for ex in self.ratio_calculator.ratio_history),
            "exchanges": detailed_ratios,
            "collection_info": {
                "base_currency": self.base_currency,
                "quote_currency": self.quote_currency,
                "active_exchanges": [ex.name for ex in self.exchanges],
                "collection_interval_seconds": self.collection_interval
            }
        }
        
        with open(ratio_filepath, 'w') as f:
            json.dump(ratio_analysis, f, indent=2)
        
        logger.info(f"Updated ratio analysis file: {ratio_filename}")
    
    def run_collection_cycle(self):
        """Run one complete collection cycle across all exchanges"""
        logger.info("Starting fee collection cycle...")
        cycle_start = time.time()
        
        all_fees = []
        
        # Collect from each exchange
        for exchange in self.exchanges:
            logger.info(f"Collecting from {exchange.name}...")
            exchange_fees = self.collect_fees_for_exchange(exchange)
            all_fees.extend(exchange_fees)
            logger.info(f"{exchange.name}: Collected {len(exchange_fees)} fee data points")
        
        # Store all collected data
        self.store_fee_data(all_fees)
        
        cycle_time = time.time() - cycle_start
        logger.info(f"Collection cycle completed in {cycle_time:.1f}s. Total data points: {len(all_fees)}")
        
        # Log current cross-exchange ratio average after each cycle
        if len(self.ratio_calculator.ratio_history) > 0:
            current_cross_avg = self.ratio_calculator.get_cross_exchange_ratio_average()
            logger.info(f"Current cross-exchange ratio average: {current_cross_avg:.4f}")
            
            # Show individual exchange averages
            exchange_avgs = self.ratio_calculator.get_all_exchanges_ratio_average()
            avg_summary = " | ".join([f"{ex}:{avg:.2f}" for ex, avg in exchange_avgs.items() if avg > 0])
            if avg_summary:
                logger.info(f"Exchange ratios: {avg_summary}")
        
        return len(all_fees)
    
    def run_infinite(self):
        """Run the fee collection system indefinitely"""
        logger.info(f"Starting infinite fee collection for {self.base_currency}/{self.quote_currency}")
        logger.info(f"Collection interval: {self.collection_interval} seconds")
        logger.info(f"Active exchanges: {[ex.name for ex in self.exchanges]}")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.info(f"\n=== Cycle {cycle_count} ===")
                
                try:
                    data_points = self.run_collection_cycle()
                    
                    # Save data every 5 cycles or if we collected significant data
                    if cycle_count % 5 == 0 or data_points > 50:
                        self.save_data_to_disk()
                        
                except Exception as e:
                    logger.error(f"Error in collection cycle {cycle_count}: {e}")
                
                # Wait before next cycle
                logger.info(f"Waiting {self.collection_interval}s until next cycle...")
                time.sleep(self.collection_interval)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal. Saving data and shutting down...")
            self.save_data_to_disk()
            
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            self.save_data_to_disk()
            raise

if __name__ == "__main__":
    collector = FeeCollector()
    collector.run_infinite()