"""
MAVLink Message Logger - Logs all MAVLink messages to CSV.
"""

import os
import csv
import json
import time
from datetime import datetime
from pathlib import Path


class MavlinkLogger:
    """
    Logs all MAVLink messages to a CSV file.
    Handles varying message frequencies by using a generic format.
    """
    
    def __init__(self, message_broker):
        self.message_broker = message_broker
        self._logging = False
        self._file = None
        self._writer = None
        self._start_time = 0.0
        self._msg_count = 0
        self._last_flush_time = 0.0
        self._log_path = None
    
    @property
    def is_logging(self) -> bool:
        return self._logging
    
    @property
    def log_path(self) -> str:
        return self._log_path
    
    def start(self) -> str:
        """
        Start logging. Returns the path to the log file.
        """
        if self._logging:
            return self._log_path
        
        # Create logs directory next to main.py
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._log_path = str(logs_dir / f"mavlink_log_{timestamp}.csv")
        
        # Open file and create CSV writer
        self._file = open(self._log_path, 'w', newline='', encoding='utf-8')
        self._writer = csv.writer(self._file)
        
        # Write header
        self._writer.writerow(['timestamp', 'msg_type', 'fields'])
        
        # Subscribe to all messages
        self._start_time = time.time()
        self._last_flush_time = self._start_time
        self._msg_count = 0
        self.message_broker.subscribe_all(self._on_message)
        
        self._logging = True
        print(f"[Logger] Started logging to: {self._log_path}")
        return self._log_path
    
    def stop(self):
        """
        Stop logging and save the file.
        """
        if not self._logging:
            return
        
        # Unsubscribe
        self.message_broker.unsubscribe_all(self._on_message)
        
        # Close file
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None
            self._writer = None
        
        self._logging = False
        print(f"[Logger] Stopped. {self._msg_count} messages logged to: {self._log_path}")
    
    def _on_message(self, msg):
        """
        Handle incoming MAVLink message.
        """
        if not self._logging or not self._writer:
            return
        
        try:
            # Calculate relative timestamp
            t = time.time() - self._start_time
            
            # Get message type
            msg_type = msg.get_type()
            
            # Convert message to dict and serialize
            msg_dict = msg.to_dict()
            # Remove 'mavpackettype' as it's redundant with msg_type
            msg_dict.pop('mavpackettype', None)
            fields_json = json.dumps(msg_dict)
            
            # Write row
            self._writer.writerow([f"{t:.6f}", msg_type, fields_json])
            self._msg_count += 1
            
            # Periodic flush (every 100 messages or 1 second)
            now = time.time()
            if self._msg_count % 100 == 0 or (now - self._last_flush_time) >= 1.0:
                self._file.flush()
                self._last_flush_time = now
                
        except Exception as e:
            print(f"[Logger] Error writing message: {e}")
