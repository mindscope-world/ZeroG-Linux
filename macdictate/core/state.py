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
            for observer in self._observers:
                try:
                    observer(new_state, kwargs)
                except Exception as e:
                    logger.error(f"Error in observer {observer}: {e}")

# Global instance accessor
state_machine = StateMachine()
