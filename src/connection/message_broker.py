"""
Message Broker for MAVLink data distribution.
Allows widgets to subscribe to specific message types.
"""

from typing import Dict, Set, Callable
from PyQt5.QtCore import QObject, pyqtSignal


class MessageBroker(QObject):
    """
    Pub/Sub message broker for distributing MAVLink messages to subscribers.
    Thread-safe for use with background receive thread.
    """
    
    def __init__(self):
        super().__init__()
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._all_subscribers: Set[Callable] = set()
    
    def subscribe(self, message_type: str, callback: Callable):
        """
        Subscribe to a specific message type.
        
        Args:
            message_type: MAVLink message type (e.g., 'HEARTBEAT', 'ATTITUDE')
            callback: Function to call when message is received
        """
        if message_type not in self._subscribers:
            self._subscribers[message_type] = set()
        self._subscribers[message_type].add(callback)
    
    def subscribe_all(self, callback: Callable):
        """Subscribe to all message types."""
        self._all_subscribers.add(callback)
    
    def unsubscribe(self, message_type: str, callback: Callable):
        """Unsubscribe from a specific message type."""
        if message_type in self._subscribers:
            self._subscribers[message_type].discard(callback)
    
    def unsubscribe_all(self, callback: Callable):
        """Unsubscribe from all messages."""
        self._all_subscribers.discard(callback)
        for subscribers in self._subscribers.values():
            subscribers.discard(callback)
    
    def publish(self, message):
        """
        Publish a message to all relevant subscribers.
        
        Args:
            message: MAVLink message object
        """
        msg_type = message.get_type()
        
        # Notify type-specific subscribers
        if msg_type in self._subscribers:
            for callback in self._subscribers[msg_type]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"Subscriber error for {msg_type}: {e}")
        
        # Notify all-message subscribers
        for callback in self._all_subscribers:
            try:
                callback(message)
            except Exception as e:
                print(f"All-subscriber error: {e}")
    
    def get_subscribed_types(self) -> list:
        """Get list of message types that have subscribers."""
        return list(self._subscribers.keys())
