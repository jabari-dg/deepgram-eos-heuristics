from common.base_heuristic import Heuristic

class VADHeuristic(Heuristic):
    """
    VADHeuristic processes Voice Activity Detection (VAD) events and transcription results
    to manage speech utterances, handle endpointing, and maintain event logs for display.
    """

    def __init__(self, pause_threshold: float = 1.2):
        """
        Initializes the VADHeuristic with default parameters and state variables.

        Args:
            pause_threshold (float): Allowed pause between words in seconds for utterance end detection.
        """
        super().__init__(pause_threshold)
        self.current_interim_utterance = ""
        self.current_interim_utterance_start = 0.0
        self.interim_endpointed = False
        self.spot_interim_latency = 0
        self.spot_endpoint_latency = 0
        self.vad_speech_detected = False
        self.vad_speech_end_at = None
        self.completed_utterances = []
        self.events = []
        self.last_word_end = 0.0
        self.current_utterance = ""
        self.current_utterance_start = None
        self.current_result = None
        self.audio_cursor = 0.0

    @Heuristic.event_handler("vad_event")
    def handle_vad_event(self, event):
        """
        Handles VAD events indicating the start or end of speech.

        Args:
            event (dict): The VAD event containing speech data and audio cursor position.
        """
        speech_dict = event.get("data", {})
        event_audio_cursor = event.get("audio_cursor", 0.0)

        if "start" in speech_dict:
            self._handle_vad_start(speech_dict["start"], event_audio_cursor)
        elif "end" in speech_dict:
            self._handle_vad_end(speech_dict["end"], event_audio_cursor)

    def _handle_vad_start(self, start_time: float, audio_cursor: float):
        """
        Processes the start of a speech segment detected by VAD.

        Args:
            start_time (float): The timestamp when speech starts.
            audio_cursor (float): The current position of the audio cursor.
        """
        self.vad_speech_detected = True
        self.vad_speech_end_at = None

        transcription_latency = int((audio_cursor - start_time) * 1000)
        vad_start_event = {
            "audio_cursor": f"{audio_cursor:.2f}",
            "transcript_cursor": "-",
            "event_type": "vad_event_start",
            "latency": f"{max(transcription_latency, 0)}",
            "speech_start_time": start_time,
            "speech_end_time": "-",
            "content": f"[Speech Started at {start_time:.2f}s]"
        }
        self.events.append(vad_start_event)

    def _handle_vad_end(self, end_time: float, audio_cursor: float):
        """
        Processes the end of a speech segment detected by VAD.

        Args:
            end_time (float): The timestamp when speech ends.
            audio_cursor (float): The current position of the audio cursor.
        """
        self.vad_speech_detected = False
        self.vad_speech_end_at = end_time

        endpoint_latency = int((audio_cursor - end_time) * 1000)
        vad_end_event = {
            "audio_cursor": f"{audio_cursor:.2f}",
            "transcript_cursor": "-",
            "event_type": "vad_event_end",
            "latency": f"{endpoint_latency}",
            "speech_start_time": "-",
            "speech_end_time": end_time,
            "content": f"[Speech Ended at {end_time:.2f}s]"
        }
        self.events.append(vad_end_event)

    @Heuristic.event_handler("transcript")
    def handle_transcript(self, event):
        """
        Handles transcription events, updating the current utterance based on transcription results.

        Args:
            event (dict): The transcription event containing transcription data and audio cursor position.
        """
        result = event.get("data", {})
        self.current_result = result
        transcript_cursor = result.start + result.duration
        transcript = result.channel.alternatives[0].transcript
        words = result.channel.alternatives[0].words
        event_audio_cursor = event.get("audio_cursor", 0.0)

        first_word_start, last_word_end = self._extract_word_times(words)
        # Update the last_word_end before processing to ensure accurate latency
        self.last_word_end = last_word_end if last_word_end else self.last_word_end
        transcription_latency = self._calculate_transcription_latency(result, transcript_cursor)
        endpoint_latency = self._calculate_endpoint_latency(result, event_audio_cursor, last_word_end)

        # Update current utterance based on transcription result type
        if result.speech_final:
            event_type = "speech_final_transcript"
            self._process_speech_final(transcript, first_word_start, last_word_end, transcription_latency)
        elif result.is_final:
            event_type = "final_transcript"
            transcription_latency = None
            self._process_final_transcript(transcript, first_word_start)
        else:
            event_type = "interim_transcript"
            self._process_interim_transcript(transcript, first_word_start, transcription_latency)

        # Determine if endpointing is needed and handle utterance accordingly
        if self.vad_endpoint_needed():
            self.endpoint_current_utterance(
                event_type,
                event_audio_cursor, 
                transcript_cursor, 
                transcript, 
                first_word_start, 
                last_word_end,
                endpoint_latency
            )
        elif self.utterance_endpoint_needed():
            self.endpoint_current_utterance(
                "local_utt_end",
                event_audio_cursor, 
                transcript_cursor, 
                transcript, 
                first_word_start, 
                last_word_end,
                endpoint_latency
            )

        # Log the current transcription event
        should_log_endpoint_latency = (
            event_type in ["speech_final_transcript", "vad_interim", "vad_is_final", "empty_speech_final"] and
            bool(transcript.strip())
        )
        self._log_transcription_event(
            transcript, 
            transcript_cursor, 
            event_audio_cursor, 
            event_type, 
            first_word_start, 
            last_word_end, 
            transcription_latency, 
            endpoint_latency if should_log_endpoint_latency else None
        )

        # Update the last word end time
        self.last_word_end = last_word_end or self.last_word_end

    def _extract_word_times(self, words):
        """
        Extracts the start and end times of the first and last words in the transcription.

        Args:
            words (list): List of word objects from the transcription result.

        Returns:
            tuple: (first_word_start, last_word_end)
        """
        if words:
            first_word_start = words[0].start
            last_word_end = words[-1].end
            return first_word_start, last_word_end
        return None, None

    def _calculate_transcription_latency(self, result, transcript_cursor):
        """
        Calculates the transcription latency.

        Args:
            result (object): The transcription result object.
            transcript_cursor (float): The position of the transcript cursor.

        Returns:
            int: Calculated transcription latency in milliseconds.
        """
        return int((self.audio_cursor - transcript_cursor) * 1000)

    def _calculate_endpoint_latency(self, result, audio_cursor, last_word_end):
        """
        Calculates the endpoint latency.

        Args:
            result (object): The transcription result object.
            audio_cursor (float): The current position of the audio cursor.
            last_word_end (float): The end time of the last word.

        Returns:
            int: Calculated endpoint latency in milliseconds.
        """
        if last_word_end:
            return int((audio_cursor - last_word_end) * 1000)
        return 0

    def _process_speech_final(self, transcript, first_word_start, last_word_end, transcription_latency):
        """
        Processes a speech_final transcription result, updating the current utterance.

        Args:
            transcript (str): The transcribed text.
            first_word_start (float): Start time of the first word.
            last_word_end (float): End time of the last word.
            transcription_latency (int): Transcription latency in milliseconds.
        """
        if first_word_start and not self.interim_endpointed:
            self.spot_endpoint_latency = transcription_latency
            if self.current_utterance:
                self.current_utterance += " " + transcript
            else:
                self.current_utterance = transcript
                self.current_utterance_start = first_word_start

            if self.first_or_distinct_utterance():
                self._add_completed_utterance(first_word_start, last_word_end, transcription_latency, "speech_final", self.current_utterance)

        # Reset interim utterance state
        self.current_interim_utterance = ""
        self.current_interim_utterance_start = None
        self.interim_endpointed = False

    def _process_final_transcript(self, transcript, first_word_start):
        """
        Processes a final_transcript result, updating the current utterance.

        Args:
            transcript (str): The transcribed text.
            first_word_start (float): Start time of the first word.
        """
        if first_word_start and not self.interim_endpointed:
            if self.current_utterance:
                self.current_utterance += " " + transcript
            else:
                self.current_utterance = transcript
                self.current_utterance_start = first_word_start

        # Reset interim utterance state
        self.current_interim_utterance = ""
        self.current_interim_utterance_start = None
        self.interim_endpointed = False

    def _process_interim_transcript(self, transcript, first_word_start, transcription_latency):
        """
        Processes an interim_transcript result, updating the current interim utterance.

        Args:
            transcript (str): The transcribed text.
            first_word_start (float): Start time of the first word.
            transcription_latency (int): Transcription latency in milliseconds.
        """
        self.spot_interim_latency = transcription_latency
        if first_word_start and not self.interim_endpointed:
            self.current_interim_utterance = transcript
            self.current_interim_utterance_start = first_word_start

    def _log_transcription_event(self, transcript, transcript_cursor, audio_cursor, event_type, first_word_start, last_word_end, transcription_latency, endpoint_latency=None):
        """
        Logs a transcription event to the events list.

        Args:
            transcript (str): The transcribed text.
            transcript_cursor (float): The position of the transcript cursor.
            audio_cursor (float): The current position of the audio cursor.
            event_type (str): The type of event.
            first_word_start (float): Start time of the first word.
            last_word_end (float): End time of the last word.
            transcription_latency (int): Transcription latency in milliseconds.
            endpoint_latency (int, optional): Endpoint latency in milliseconds. Defaults to None.
        """
        if endpoint_latency is not None:
            latency_str = f"{transcription_latency} ({endpoint_latency})"
        else:
            latency_str = f"{transcription_latency}" if isinstance(transcription_latency, int) else '-'

        event_log = {
            "audio_cursor": f"{audio_cursor:.2f}",
            "transcript_cursor": f"{transcript_cursor:.2f}" if isinstance(transcript_cursor, float) else "-",
            "event_type": event_type,
            "latency": latency_str,
            "speech_start_time": f"{first_word_start:.2f}" if first_word_start else '-',
            "speech_end_time": f"{last_word_end:.2f}" if last_word_end else '-',
            "content": transcript
        }
        self.events.append(event_log)

    @Heuristic.event_handler("utterance_end")
    def handle_utterance_end(self, event):
        """
        Handles utterance_end events, logging the end of an utterance.

        Args:
            event (dict): The utterance_end event containing data (UtteranceEndResponse) and audio cursor position.
        """
        result = event.get("data", {})
        last_word_end = result.last_word_end
        event_audio_cursor = event.get("audio_cursor", 0.0)

        content = f"Utterance end for word at {last_word_end:.2f} s"
        endpoint_latency = int((event_audio_cursor - last_word_end) * 1000)

        utterance_end_event = {
            "audio_cursor": f"{event_audio_cursor:.2f}",
            "transcript_cursor": "-",
            "event_type": "utterance_end",
            "latency": f"{endpoint_latency}",
            "speech_start_time": "-",
            "speech_end_time": f"{last_word_end:.2f}",
            "content": content
        }
        self.events.append(utterance_end_event)

    def first_or_distinct_utterance(self) -> bool:
        """
        Determines if the current utterance is the first or distinct from previous utterances.

        Returns:
            bool: True if it's the first or distinct utterance, False otherwise.
        """
        return (
            not self.completed_utterances or
            float(self.completed_utterances[-1]["end_time"]) < (self.current_utterance_start or 0)
        )
    
    def vad_endpoint_needed(self) -> bool:
        """
        Determines if endpointing is needed based on VAD events and current utterance state.

        Returns:
            bool: True if endpointing is needed via VAD, False otherwise.
        """
        return (
            not self.vad_speech_detected and
            not self.interim_endpointed and
            (self.current_utterance or self.current_interim_utterance) and
            self.events and
            self.events[-1]["event_type"] == "vad_event_end"
        )
    
    def utterance_endpoint_needed(self) -> bool:
        """
        Determines if endpointing is needed based on pause thresholds and current utterance state.

        Returns:
            bool: True if endpointing is needed due to pause threshold, False otherwise.
        """
        return (
            not self.vad_speech_detected and 
            not self.interim_endpointed and
            self.current_utterance and
            (self.audio_cursor - self.last_word_end) > self.pause_threshold
        )

    def endpoint_current_utterance(self, event_type, audio_cursor, transcript_cursor, transcript, first_word_start, last_word_end, endpoint_latency):
        """
        Finalizes the current utterance and logs the endpoint event.

        Args:
            event_type (str): The type of event triggering endpointing.
            audio_cursor (float): The current position of the audio cursor.
            transcript_cursor (float): The position of the transcript cursor.
            transcript (str): The transcribed text.
            first_word_start (float): Start time of the first word.
            last_word_end (float): End time of the last word.
            endpoint_latency (int): Endpoint latency in milliseconds.
        """
        reason = self._determine_endpoint_reason(event_type)

        if not self.current_result.is_final:
            self._merge_interim_utterance()

        # Calculate transcription latency for endpointing events
        transcription_latency = self._calculate_transcription_latency(self.current_result, transcript_cursor)

        # Format latency as "transcription_latency (endpoint_latency)"
        latency_str = f"{transcription_latency} ({endpoint_latency})"

        endpoint_event = {
            "audio_cursor": f"{audio_cursor:.2f}",
            "transcript_cursor": f"{transcript_cursor:.2f}",
            "event_type": reason,
            "latency": latency_str,
            "speech_start_time": f"{first_word_start:.2f}" if first_word_start else "-",
            "speech_end_time": f"{last_word_end:.2f}" if last_word_end else "-",
            "content": transcript
        }
        self.events.append(endpoint_event)

        self._add_completed_utterance(
            first_word_start, 
            last_word_end, 
            endpoint_latency, 
            reason, 
            self.current_utterance
        )

    def _determine_endpoint_reason(self, event_type: str) -> str:
        """
        Determines the reason for endpointing based on the event type.

        Args:
            event_type (str): The original event type.

        Returns:
            str: The mapped reason for endpointing.
        """
        reason_mapping = {
            "speech_final_transcript": "empty_speech_final",
            "final_transcript": "vad_is_final",
            "interim_transcript": "vad_interim"
        }
        return reason_mapping.get(event_type, event_type)

    def _merge_interim_utterance(self):
        """
        Merges the current interim utterance into the main utterance if the result is not final.
        """
        if self.current_utterance:
            self.current_utterance += " " + self.current_interim_utterance
        else:
            self.current_utterance = self.current_interim_utterance
        self.current_interim_utterance = ""
        self.current_interim_utterance_start = None
        self.interim_endpointed = True

    def _add_completed_utterance(self, start_time, end_time, latency, completed_by, transcript):
        """
        Adds a completed utterance to the list of completed utterances.

        Args:
            start_time (float): Start time of the utterance.
            end_time (float): End time of the utterance.
            latency (int): Latency in milliseconds.
            completed_by (str): Reason for completion.
            transcript (str): The transcribed text.
        """
        completed_utterance = {
            "start_time": f"{start_time:.2f}" if start_time else "-",
            "end_time": f"{end_time:.2f}" if end_time else "-",
            "latency": latency,
            "completed_by": completed_by,
            "transcript": transcript
        }
        self.completed_utterances.append(completed_utterance)
        self.current_utterance = ""
        self.current_utterance_start = None

    def get_display_data(self) -> dict:
        """
        Retrieves the current state data for display purposes.

        Returns:
            dict: Contains completed utterances, events, current utterance states, and metrics.
        """
        return {
            'completed_utterances': self.completed_utterances,
            'events': self.events,
            'current_utterance': self.current_utterance,
            'current_utterance_start': self.current_utterance_start or "",
            'current_interim_utterance': self.current_interim_utterance,
            'current_interim_utterance_start': self.current_interim_utterance_start or "",
            'metrics': {
                'spot_interim_latency': self.spot_interim_latency,
                'spot_endpoint_latency': self.spot_endpoint_latency,
                'vad_speech_detected': self.vad_speech_detected
            }
        }