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
        line_length = 134
        terminal_output = "\n"
        terminal_output += "=" * line_length + "\n"
        terminal_output += "Completed Utterances:\n"
        terminal_output += "=" * line_length + "\n"
        
        for utterance in self.completed_utterances[-10:]:  # Display last 10 utterances
            terminal_output += f"[{utterance['start_time']} - {utterance['end_time']} ({utterance['latency']} ms - {utterance['completed_by']})]  {utterance['transcript']}\n"
        
        terminal_output += "\n" + "=" * line_length + "\n\n"
        terminal_output += f"Current utterance ({self.current_utterance_start} - ): " + self.current_utterance + "\n"
        terminal_output += f"Current interim utterance ({self.current_interim_utterance_start} - ): " + self.current_interim_utterance + "\n"
        terminal_output += "Real-time Events Log:\n"
        terminal_output += "-" * line_length + "\n"
        metrics_row = f"Spot Interim Latency: {self.spot_interim_latency} ms | Spot Endpoint Latency: {self.spot_endpoint_latency} ms | VAD Speech detected: {self.vad_speech_detected}"
        terminal_output += f"{metrics_row:^134}\n"
        terminal_output += "-" * line_length + "\n"
        terminal_output += f"{'Audio Cursor':^15}|{'Transcript Cursor':^20}| {'Event Type':<25}|{'Latency':^10}|{'Words Start':^13}|{'Words End':^13}| {'Content':<50}\n"
        terminal_output += "-" * line_length + "\n"

        num_rows = os.get_terminal_size().lines - terminal_output.count("\n") - 1  # -1 to account for input
        for event in self.events[-num_rows:]:
            terminal_output += f"{event['audio_cursor']:^15}|{event['transcript_cursor']:^20}| {event['event_type']:<25}|{event['latency']:^10}|{event['speech_start_time']:^13}|{event['speech_end_time']:^13}| {event['content']:<50}\n"
        
        # for event in self.events[-num_rows:]:
        #     terminal_output += f"{self.safe_format(event['audio_cursor']):^15}|{self.safe_format(event['transcript_cursor']):^20}| {event['event_type']:<25}|{self.safe_format(event['latency']):^10}|{self.safe_format(event['speech_start_time']):^13}|{self.safe_format(event['speech_end_time']):^13}| {event['content']:<50}\n"
        
        sys.stdout.write("\x1b[1A" * self.prev_buffer_size)
        sys.stdout.write("\x1b[0J")
        sys.stdout.write(terminal_output)
        sys.stdout.flush()

        self.prev_buffer_size = terminal_output.count("\n")
        
    # @staticmethod
    # def safe_format(value):
    #     if value is None or value == '-':
    #         return '-'
    #     try:
    #         return f"{float(value):.1f}"
    #     except (ValueError, TypeError):
    #         return str(value)