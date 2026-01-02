from enum import Enum, auto
import threading
import logging

logger = logging.getLogger(__name__)

class AppState(Enum):
    IDLE = auto()
    RECORDING = auto()
    PROCESSING = auto()
    SUCCESS = auto()
    ERROR = auto()

class StateMachine:
    """
    Singleton State Machine using the Observer pattern.
    Thread-safe state transitions and event broadcasting.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StateMachine, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self._state = AppState.IDLE
        self._observers = []
        self._audio_level_observers = []  # Separate observers for audio levels
        self._state_lock = threading.Lock()
        self._data = {} # Optional payload for state (e.g., error message)

    def add_observer(self, observer_func):
        """
        Register a callback function to be called on state changes.
        Callback signature: observer_func(state: AppState, data: dict)
        """
        with self._state_lock:
            if observer_func not in self._observers:
                self._observers.append(observer_func)

    def remove_observer(self, observer_func):
        with self._state_lock:
            if observer_func in self._observers:
                self._observers.remove(observer_func)

    @property
    def current_state(self):
        with self._state_lock:
            return self._state

    def set_state(self, new_state: AppState, **kwargs):
        """
        Transition to a new state and notify observers.
        kwargs can be used to pass data (e.g. error_message="...", text="...")
        """
        with self._state_lock:
            if self._state == new_state and not kwargs:
                return # No change
            
            self._state = new_state
            self._data = kwargs
            logger.info(f"State Transition: {new_state.name} | Data: {kwargs}")
            
            # Notify observers
            observers_copy = list(self._observers)  # Copy to avoid modification during iteration
        
        # Notify outside the lock to prevent deadlocks
        for observer in observers_copy:
            try:
                observer(new_state, kwargs)
            except Exception as e:
                logger.error(f"Error in observer {observer}: {e}", exc_info=True)
                # If critical observer fails during RECORDING, trigger ERROR state
                if new_state == AppState.RECORDING:
                    # Schedule error state to avoid recursion
                    import threading
                    threading.Timer(0.1, lambda: self.set_state(AppState.ERROR, error="Recording failed to start")).start()

    def add_audio_level_observer(self, observer_func):
        """Register a callback for audio level updates. Signature: observer_func(level: float)"""
        with self._state_lock:
            if observer_func not in self._audio_level_observers:
                self._audio_level_observers.append(observer_func)

    def remove_audio_level_observer(self, observer_func):
        with self._state_lock:
            if observer_func in self._audio_level_observers:
                self._audio_level_observers.remove(observer_func)

    def broadcast_audio_level(self, level: float):
        """Broadcast audio level (0.0-1.0) to all audio level observers."""
        # logger.debug(f"Broadcasting audio level: {level:.4f} to {len(self._audio_level_observers)} observers")
        if level > 0.01:
             # Only log significant levels to avoid spam
             pass 

        with self._state_lock:
            observers_copy = list(self._audio_level_observers)
        
        for observer in observers_copy:
            try:
                observer(level)
            except Exception as e:
                logger.error(f"Error in audio level observer {observer}: {e}")

# Global instance accessor
state_machine = StateMachine()
