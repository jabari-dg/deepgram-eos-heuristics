class Heuristic:
    def __init__(self, pause_threshold: float = 0.5):
        self.pause_threshold = pause_threshold
        self.audio_cursor = 0
        self.vad_speech_detected = False
        self.vad_speech_end_at = None
        self.current_result = None
        self.last_transcript_result = None
        self.current_utterance = ""
        self.current_utterance_start = None
        self.current_utterance_end = None
        self.last_word_end = 0
        self.completed_utterances = []
        self.events = []
        self._event_handlers = {}
        self._event_handlers = self.__class__._event_handlers.copy()
    
    @classmethod
    def event_handler(cls, event_type):
        def decorator(f):
            if not hasattr(cls, '_class_event_handlers'):
                cls._class_event_handlers = {}
            cls._class_event_handlers[event_type] = f
            return f
        return decorator
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, '_class_event_handlers'):
            cls._event_handlers = cls._class_event_handlers.copy()
        else:
            cls._event_handlers = {}

    def process(self, event: dict) -> dict:
        event_type = event.get("event_type")
        handler = self._event_handlers.get(event_type)
        if handler:
            return handler(self, event)
        return {}