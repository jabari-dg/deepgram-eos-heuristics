import sys
import os

class TerminalRenderer:
    def __init__(self):
        self.completed_utterances = []
        self.events = []
        self.prev_buffer_size = 0
        self.spot_interim_latency = 0
        self.spot_endpoint_latency = 0
        self.vad_speech_detected = False

    def update(self, completed_utterances, events, current_utterance, current_utterance_start, current_interim_utterance, current_interim_utterance_start, metrics):
        self.completed_utterances = completed_utterances
        self.events = events
        self.current_utterance = current_utterance
        self.current_utterance_start = current_utterance_start
        self.current_interim_utterance = current_interim_utterance
        self.current_interim_utterance_start = current_interim_utterance_start
        self.spot_interim_latency = metrics.get('spot_interim_latency', 0)
        self.spot_endpoint_latency = metrics.get('spot_endpoint_latency', 0)
        self.vad_speech_detected = metrics.get('vad_speech_detected', False)

    def render(self):
        line_length = 150
        terminal_output = "\n"
        terminal_output += "=" * line_length + "\n"
        terminal_output += "Completed Utterances:\n"
        terminal_output += "=" * line_length + "\n"
        
        for utterance in self.completed_utterances[-10:]:  # Display last 10 utterances
            transcript = utterance.get('transcript', 'N/A')  # Safeguard against missing key
            latency = utterance.get('latency', '0')
            terminal_output += f"[{utterance.get('start_time', '-')}"
            terminal_output += f" - {utterance.get('end_time', '-')}"
            terminal_output += f" ({latency} ms - {utterance.get('completed_by', 'Unknown')})]  {transcript}\n"
        
        terminal_output += "\n" + "=" * line_length + "\n\n"
        terminal_output += f"Current utterance ({self.current_utterance_start} - ): " + self.current_utterance + "\n"
        terminal_output += f"Current interim utterance ({self.current_interim_utterance_start} - ): " + self.current_interim_utterance + "\n"
        terminal_output += "Real-time Events Log:\n"
        terminal_output += "-" * line_length + "\n"
        metrics_row = f"Spot Interim Latency: {self.spot_interim_latency} ms | Spot Endpoint Latency: {self.spot_endpoint_latency} ms | VAD Speech detected: {self.vad_speech_detected}"
        terminal_output += f"{metrics_row:^150}\n"
        terminal_output += "-" * line_length + "\n"
        terminal_output += f"{'Audio Cursor':^15}|{'Transcript Cursor':^20}| {'Event Type':<30}|{'Latency':^20}|{'Words Start':^15}|{'Words End':^15}| {'Content':<60}\n"
        terminal_output += "-" * line_length + "\n"

        num_rows = os.get_terminal_size().lines - terminal_output.count("\n") - 1  # -1 to account for input
        for event in self.events[-num_rows:]:
            audio_cursor = event.get('audio_cursor', '-')
            transcript_cursor = event.get('transcript_cursor', '-')
            event_type = event.get('event_type', '-')
            latency = event.get('latency', '-')
            speech_start_time = event.get('speech_start_time', '-')
            speech_end_time = event.get('speech_end_time', '-')
            content = event.get('content', '-')
            terminal_output += f"{audio_cursor:^15}|{transcript_cursor:^20}| {event_type:<30}|{latency:^20}|{speech_start_time:^15}|{speech_end_time:^15}| {content:<60}\n"
        
        sys.stdout.write("\x1b[1A" * self.prev_buffer_size)
        sys.stdout.write("\x1b[0J")
        sys.stdout.write(terminal_output)
        sys.stdout.flush()

        self.prev_buffer_size = terminal_output.count("\n")