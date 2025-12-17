"""
Docker Container Stats Collector
Collects performance metrics from Docker containers during operations
"""
import docker
import time
import threading
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class DockerStatsCollector:
    """Collects Docker container statistics during operations"""
    
    def __init__(self, container_names: List[str], sample_interval: float = 0.5):
        """
        Initialize Docker stats collector
        
        Args:
            container_names: List of container names to monitor (e.g., ['postgres', 'elasticsearch'])
            sample_interval: Interval in seconds between stat samples
        """
        self.container_names = container_names
        self.sample_interval = sample_interval
        self.client = None
        self.containers = {}
        self._monitoring = False
        self._monitor_threads = {}
        self.stats_data = {}  # {container_name: [stats_dict, ...]}
        
        try:
            self.client = docker.from_env()
            self._initialize_containers()
        except Exception as e:
            logger.warning(f"Failed to initialize Docker client: {e}. Docker stats will not be available.")
            self.client = None
    
    def _initialize_containers(self):
        """Initialize container objects"""
        if not self.client:
            logger.warning("Docker client is None, cannot initialize containers")
            return
        
        try:
            all_containers = self.client.containers.list()
            logger.info(f"Found {len(all_containers)} containers: {[c.name for c in all_containers]}")
            for container_name in self.container_names:
                container = next(
                    (c for c in all_containers if c.name == container_name),
                    None
                )
                if container:
                    self.containers[container_name] = container
                    self.stats_data[container_name] = []
                    logger.info(f"Successfully initialized container '{container_name}'")
                else:
                    logger.warning(f"Container '{container_name}' not found. Available containers: {[c.name for c in all_containers]}")
        except Exception as e:
            logger.error(f"Error initializing containers: {e}", exc_info=True)
    
    def _parse_stats(self, stats: Dict) -> Dict:
        """Parse Docker stats into useful metrics"""
        try:
            # CPU calculation - handle cases where system_cpu_usage might be missing
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            cpu_usage = cpu_stats.get('cpu_usage', {})
            precpu_usage = precpu_stats.get('cpu_usage', {})
            
            cpu_delta = cpu_usage.get('total_usage', 0) - precpu_usage.get('total_usage', 0)
            system_cpu_usage = cpu_stats.get('system_cpu_usage', 0)
            precpu_system_cpu_usage = precpu_stats.get('system_cpu_usage', 0)
            
            system_delta = system_cpu_usage - precpu_system_cpu_usage
            num_cpus = cpu_stats.get('online_cpus', 1)
            
            if system_delta > 0 and num_cpus > 0:
                cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0
                # Clamp to reasonable range (0-1000% to handle multi-core)
                cpu_percent = max(0.0, min(cpu_percent, 1000.0))
            else:
                # Fallback: if system_cpu_usage is missing, try to estimate from throttling
                # or return 0 if we can't calculate
                throttled_data = cpu_stats.get('throttling_data', {})
                if throttled_data:
                    cpu_percent = 0.0  # Can't calculate without system_cpu_usage
                else:
                    cpu_percent = 0.0
            
            # Memory - handle missing fields
            memory_stats = stats.get('memory_stats', {})
            memory_usage = memory_stats.get('usage', 0)
            memory_limit = memory_stats.get('limit', 0)
            memory_percent = (memory_usage / memory_limit * 100.0) if memory_limit > 0 else 0.0
            
            # Block I/O - handle missing fields
            # Docker block I/O stats are cumulative (total since container start)
            # We need to track the cumulative values and calculate deltas later
            blkio_stats = stats.get('blkio_stats', {})
            read_bytes = 0
            write_bytes = 0
            
            # Try different possible field names for block I/O stats
            io_service_bytes = blkio_stats.get('io_service_bytes_recursive', [])
            if not io_service_bytes:
                io_service_bytes = blkio_stats.get('io_service_bytes', [])
            
            if isinstance(io_service_bytes, list) and len(io_service_bytes) > 0:
                for entry in io_service_bytes:
                    if isinstance(entry, dict):
                        op = entry.get('op', '')
                        value = entry.get('value', 0)
                        major = entry.get('major', 0)
                        minor = entry.get('minor', 0)
                        # Docker uses 'Read' and 'Write' operations
                        if op == 'Read' or op == 'read':
                            read_bytes += value
                        elif op == 'Write' or op == 'write':
                            write_bytes += value
            elif not blkio_stats:
                # Log once if blkio_stats is empty (might be normal for some containers)
                logger.debug("No blkio_stats found in Docker stats")
            else:
                # Log the structure to help debug
                logger.debug(f"blkio_stats structure: {list(blkio_stats.keys())}")
            
            # Network I/O - handle missing fields
            networks = stats.get('networks', {})
            rx_bytes = 0
            tx_bytes = 0
            if isinstance(networks, dict):
                for net in networks.values():
                    if isinstance(net, dict):
                        rx_bytes += net.get('rx_bytes', 0)
                        tx_bytes += net.get('tx_bytes', 0)
            
            # PIDs
            pids_stats = stats.get('pids_stats', {})
            pids = pids_stats.get('current', 0) if isinstance(pids_stats, dict) else 0
            
            return {
                'timestamp': time.time(),
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage_mb': round(memory_usage / 1024 / 1024, 2) if memory_usage else 0.0,
                'memory_limit_mb': round(memory_limit / 1024 / 1024, 2) if memory_limit else 0.0,
                'memory_percent': round(memory_percent, 2),
                'block_read_mb': round(read_bytes / 1024 / 1024, 2),
                'block_write_mb': round(write_bytes / 1024 / 1024, 2),
                'network_rx_mb': round(rx_bytes / 1024 / 1024, 2),
                'network_tx_mb': round(tx_bytes / 1024 / 1024, 2),
                'pids': pids
            }
        except Exception as e:
            logger.error(f"Error parsing stats: {e}")
            logger.debug(f"Stats structure: {stats.keys() if isinstance(stats, dict) else 'Not a dict'}")
            return None
    
    def _monitor_container(self, container_name: str):
        """Monitor a single container in a separate thread"""
        container = self.containers.get(container_name)
        if not container:
            logger.warning(f"Container '{container_name}' not found in containers dict")
            return
        
        logger.info(f"Starting stats stream for container '{container_name}'")
        try:
            # Start streaming stats - this ensures we get at least one sample
            # The first stat from the stream will be collected immediately
            # Note: Docker's stats stream provides stats at its own rate (typically ~1 per second)
            # We can't force it to provide stats faster, but we can collect them as they arrive
            stats_stream = container.stats(stream=True, decode=True)
            first_stat_collected = False
            stat_count = 0
            last_stat_time = None
            
            for stats in stats_stream:
                if not self._monitoring:
                    logger.info(f"Monitoring stopped for container '{container_name}', collected {stat_count} stats")
                    break
                
                current_time = time.time()
                if last_stat_time:
                    time_since_last = current_time - last_stat_time
                    logger.debug(f"Time since last stat: {time_since_last:.3f}s")
                last_stat_time = current_time
                
                parsed_stats = self._parse_stats(stats)
                if parsed_stats:
                    self.stats_data[container_name].append(parsed_stats)
                    stat_count += 1
                    if not first_stat_collected:
                        logger.info(f"Collected first stat for container '{container_name}'")
                        first_stat_collected = True
                    else:
                        # Log subsequent samples for debugging
                        logger.info(f"Collected stat #{stat_count} for container '{container_name}' (CPU: {parsed_stats.get('cpu_percent', 0):.2f}%)")
                
                # Don't sleep - Docker's stats stream provides stats at its own rate
                # Sleeping here would just delay collection of the next stat
        except Exception as e:
            logger.error(f"Error monitoring container {container_name}: {e}", exc_info=True)
    
    def start(self):
        """Start monitoring all containers"""
        if not self.client:
            logger.warning("Docker client not available, cannot start monitoring")
            return
        
        if not self.containers:
            logger.warning("No containers found to monitor")
            return
        
        logger.info(f"Starting Docker stats collection for containers: {list(self.containers.keys())}")
        self._monitoring = True
        self.stats_data = {name: [] for name in self.containers.keys()}
        
        for container_name in self.containers.keys():
            thread = threading.Thread(
                target=self._monitor_container,
                args=(container_name,),
                daemon=True
            )
            thread.start()
            self._monitor_threads[container_name] = thread
            logger.info(f"Started monitoring thread for container '{container_name}'")
        
        # Wait for at least one stat to be collected for each container
        # This ensures we have data even for very fast operations
        max_wait_time = 2.0  # Maximum time to wait
        wait_interval = 0.1  # Check every 100ms
        elapsed = 0.0
        
        while elapsed < max_wait_time:
            all_have_stats = all(
                len(self.stats_data.get(name, [])) > 0 
                for name in self.containers.keys()
            )
            if all_have_stats:
                logger.info(f"All containers have at least one stat collected (waited {elapsed:.2f}s)")
                break
            time.sleep(wait_interval)
            elapsed += wait_interval
        
        if elapsed >= max_wait_time:
            missing = [name for name in self.containers.keys() if len(self.stats_data.get(name, [])) == 0]
            if missing:
                logger.warning(f"Timeout waiting for stats from containers: {missing}")
    
    def stop(self):
        """Stop monitoring all containers"""
        if not self._monitoring:
            return
        
        logger.info(f"Stopping Docker stats collection for containers: {list(self.containers.keys())}")
        
        # Before stopping, check if we have enough samples for delta calculations
        # If we only have 1-2 samples, wait a bit longer to collect more
        # CRITICAL: Keep _monitoring = True while waiting so the thread continues collecting
        # NOTE: Docker's stats stream provides stats at ~1 per second, so we need to wait at least 1-2 seconds
        max_wait_iterations = 3  # Try up to 3 times to collect more samples
        for iteration in range(max_wait_iterations):
            all_have_enough_samples = True
            for container_name in self.containers.keys():
                stats_list = self.stats_data.get(container_name, [])
                if len(stats_list) <= 2:  # If we have 1 or 2 samples, wait for more
                    all_have_enough_samples = False
                    logger.info(f"Iteration {iteration + 1}: Only {len(stats_list)} sample(s) for '{container_name}', waiting for more...")
                    # Wait for Docker to provide more stats
                    # Docker's stats stream provides stats at ~1 per second, so we need to wait at least 1.5 seconds
                    # to get a reasonable chance of collecting another stat
                    wait_time = max(1.5, self.sample_interval * 10)  # Wait at least 1.5 seconds
                    logger.info(f"Waiting {wait_time:.2f}s for Docker to provide more stats (Docker rate: ~1 per second)...")
                    time.sleep(wait_time)
                    stats_after_wait = self.stats_data.get(container_name, [])
                    logger.info(f"After waiting, collected {len(stats_after_wait)} samples for '{container_name}' (was {len(stats_list)})")
            
            if all_have_enough_samples:
                logger.info(f"All containers have enough samples after {iteration + 1} iteration(s)")
                break
        
        # Now stop monitoring
        self._monitoring = False
        
        # Wait a bit more to ensure final stats are collected
        # Give enough time for at least one more sample
        wait_time = max(self.sample_interval * 2, 0.3)
        time.sleep(wait_time)
        
        for container_name, thread in self._monitor_threads.items():
            thread.join(timeout=2.0)
            stats_count = len(self.stats_data.get(container_name, []))
            logger.info(f"Stopped monitoring container '{container_name}', collected {stats_count} stats")
        
        self._monitor_threads.clear()
    
    def get_summary(self) -> Dict[str, Dict]:
        """
        Get summary statistics for all monitored containers
        
        Returns:
            Dictionary with container names as keys and summary stats as values
        """
        summary = {}
        
        logger.info(f"Getting summary for containers: {list(self.stats_data.keys())}")
        
        # Wait a bit more if we don't have stats yet (for very fast operations)
        # Also wait if we only have 1 sample to try to get at least 2 for delta calculation
        for container_name in self.stats_data.keys():
            stats_list = self.stats_data.get(container_name, [])
            if len(stats_list) == 0:
                logger.warning(f"No stats yet for '{container_name}', waiting a bit more...")
                # Give it a bit more time
                time.sleep(0.3)
            elif len(stats_list) == 1:
                # Only 1 sample - this shouldn't happen if stop() was called properly
                # But if it does, log a warning
                logger.warning(f"Only 1 sample for '{container_name}' in get_summary() - monitoring may have stopped too early")
        
        for container_name, stats_list in self.stats_data.items():
            if not stats_list:
                logger.warning(f"No stats collected for container '{container_name}' after waiting. Stats data keys: {list(self.stats_data.keys())}")
                continue
            
            logger.info(f"Processing {len(stats_list)} stats for container '{container_name}'")
            
            # Calculate peak and average values
            cpu_values = [s['cpu_percent'] for s in stats_list if s]
            memory_values = [s['memory_usage_mb'] for s in stats_list if s]
            
            # Log CPU values for debugging - especially if all values are the same
            if cpu_values:
                unique_cpu_values = set(cpu_values)
                if len(unique_cpu_values) == 1 and len(cpu_values) > 1:
                    logger.warning(f"All {len(cpu_values)} CPU samples for '{container_name}' are identical: {cpu_values[0]}% - PostgreSQL may be idle")
                elif len(cpu_values) == 1:
                    logger.warning(f"Only 1 CPU sample collected for '{container_name}': {cpu_values[0]}% - operation may be too fast")
                else:
                    logger.info(f"CPU values for '{container_name}': min={min(cpu_values):.2f}%, max={max(cpu_values):.2f}%, avg={sum(cpu_values)/len(cpu_values):.2f}% (samples: {len(cpu_values)})")
            block_read_values = [s['block_read_mb'] for s in stats_list if s]
            block_write_values = [s['block_write_mb'] for s in stats_list if s]
            network_rx_values = [s['network_rx_mb'] for s in stats_list if s]
            network_tx_values = [s['network_tx_mb'] for s in stats_list if s]
            
            # Block I/O and Network stats are cumulative (total since container start)
            # Calculate the delta (actual I/O during monitoring period)
            # This is the difference between the last and first sample
            # NOTE: We need at least 2 samples to calculate a meaningful delta
            # With only 1 sample, we can't determine the I/O during the operation
            if len(block_read_values) > 1:
                total_block_read = max(0, block_read_values[-1] - block_read_values[0])
            elif len(block_read_values) == 1:
                # Can't calculate delta with only one sample - return 0
                # The single value is cumulative since container start, not operation-specific
                total_block_read = 0
            else:
                total_block_read = 0
                
            if len(block_write_values) > 1:
                total_block_write = max(0, block_write_values[-1] - block_write_values[0])
            elif len(block_write_values) == 1:
                # Can't calculate delta with only one sample - return 0
                # The single value is cumulative since container start, not operation-specific
                total_block_write = 0
            else:
                total_block_write = 0
            
            # Network stats are also cumulative, calculate delta
            # We need at least 2 samples to calculate a meaningful delta
            if len(network_rx_values) > 1:
                total_network_rx = max(0, network_rx_values[-1] - network_rx_values[0])
            elif len(network_rx_values) == 1:
                # Can't calculate delta with only one sample - return 0
                total_network_rx = 0
            else:
                total_network_rx = 0
                
            if len(network_tx_values) > 1:
                total_network_tx = max(0, network_tx_values[-1] - network_tx_values[0])
            elif len(network_tx_values) == 1:
                # Can't calculate delta with only one sample - return 0
                total_network_tx = 0
            else:
                total_network_tx = 0
            
            summary[container_name] = {
                'cpu_percent_peak': round(max(cpu_values), 2) if cpu_values else 0.0,
                'cpu_percent_avg': round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else 0.0,
                'memory_usage_mb_peak': round(max(memory_values), 2) if memory_values else 0.0,
                'memory_usage_mb_avg': round(sum(memory_values) / len(memory_values), 2) if memory_values else 0.0,
                'memory_usage_mb_start': round(memory_values[0], 2) if memory_values else 0.0,
                'memory_usage_mb_end': round(memory_values[-1], 2) if memory_values else 0.0,
                'memory_delta_mb': round(memory_values[-1] - memory_values[0], 2) if len(memory_values) > 1 else 0.0,
                'block_read_total_mb': round(total_block_read, 2),
                'block_write_total_mb': round(total_block_write, 2),
                'network_rx_total_mb': round(total_network_rx, 2),
                'network_tx_total_mb': round(total_network_tx, 2),
                'sample_count': len(stats_list)
            }
        
        return summary
    
    def clear(self):
        """Clear collected stats"""
        self.stats_data = {name: [] for name in self.containers.keys()}

