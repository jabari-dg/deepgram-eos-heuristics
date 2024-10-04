from common.base_heuristic import Heuristic

class VADHeuristic(Heuristic):
    def __init__(self, pause_threshold: float = 1.2):
        super().__init__(pause_threshold)
        self.current_interim_utterance = ""
        self.current_interim_utterance_start = 0
        self.interim_endpointed = False
        self.spot_interim_latency = 0
        self.spot_endpoint_latency = 0

    @Heuristic.event_handler("vad_event")
    def handle_vad_event(self, event):
        speech_dict = event["data"]
        event_audio_cursor = event["audio_cursor"]
        if "start" in speech_dict:
            self.vad_speech_detected = True
            self.vad_speech_end_at = None
            
            speech_start_time = speech_dict['start']
            latency = int((event_audio_cursor - speech_start_time) * 1000)
            self.events.append({
                "audio_cursor": f"{event_audio_cursor:.2f}",
                "transcript_cursor": "-",
                "event_type": "vad_event_start",
                "latency": latency,
                "speech_start_time": speech_start_time,
                "speech_end_time": "-",
                "content": f"[Speech Started at {speech_start_time:.2f}s]"
            })
        elif "end" in speech_dict:
            speech_end_time = speech_dict['end']
            self.vad_speech_detected = False
            self.vad_speech_end_at = speech_end_time
        
            latency = int((event_audio_cursor - speech_end_time) * 1000)
            self.events.append({
                "audio_cursor": f"{event_audio_cursor:.2f}",
                "transcript_cursor": "-",
                "event_type": "vad_event_end",
                "latency": latency,
                "speech_start_time": "-",
                "speech_end_time": speech_end_time,
                "content": f"[Speech Ended at {speech_end_time:.2f}s]"
            })
    
     # TODO: Experiment with also checking for punctuation and/or capitalization on joining ends of transcripts)
     # TODO: May be an edge case where an interim utterance is endpointed and then new words are uttered before is_final 
    @Heuristic.event_handler("transcript")
    def handle_transcript(self, event):
        result = event["data"]
        self.current_result = result
        transcript_cursor = result.start + result.duration
        transcript = result.channel.alternatives[0].transcript
        words = result.channel.alternatives[0].words
        event_audio_cursor = event["audio_cursor"]
        first_word_start = None
        last_word_end = None
        latency = None
        
        
        if words:
            first_word_start = words[0].start
            last_word_end = words[-1].end
        
        # TODO: Consolidate all of this. Being redundant at first.
        if result.speech_final:
            event_type = "speech_final_transcript"
            if words and not self.interim_endpointed:
                latency = int((event_audio_cursor - last_word_end) * 1000)
                self.spot_endpoint_latency = latency
                if self.current_utterance:
                    self.current_utterance += " " + transcript
                else:
                    self.current_utterance = transcript
                    self.current_utterance_start = first_word_start

                if self.first_or_distinct_utterance():
                    self._add_completed_utterance(first_word_start, last_word_end, latency, "speech_final", self.current_utterance)
            self.current_interim_utterance = ""
            self.current_interim_utterance_start = None
            self.interim_endpointed = False
                
        elif result.is_final:
            event_type = "final_transcript"
            latency = "-"
            if words and not self.interim_endpointed:
                if self.current_utterance:
                    self.current_utterance += " " + transcript
                else:
                    self.current_utterance = transcript
                    self.current_utterance_start = first_word_start
            self.current_interim_utterance = ""
            self.current_interim_utterance_start = None
            self.interim_endpointed = False
        else:
            event_type = "interim_transcript"
            latency = int((event_audio_cursor - transcript_cursor) * 1000)
            self.spot_interim_latency = latency
            
            if words and not self.interim_endpointed:
                self.current_interim_utterance = transcript
                self.current_interim_utterance_start = first_word_start

        if self.vad_endpoint_needed():
            self.endpoint_current_utterance(
                event_type,
                event_audio_cursor, 
                transcript_cursor, 
                transcript, 
                first_word_start, 
                last_word_end
                )
            
        elif self.utterance_endpoint_needed():
            self.endpoint_current_utterance(
                    "local_utt_end",
                    event_audio_cursor, 
                    transcript_cursor, 
                    transcript, 
                    first_word_start, 
                    last_word_end
                    )
                
        self.events.append({
            "audio_cursor": f"{event_audio_cursor:.2f}",
            "transcript_cursor": f"{transcript_cursor:.2f}",
            "event_type": event_type,
            "latency": latency or '-',
            "speech_start_time": f"{first_word_start:.2f}" if first_word_start else '-',
            "speech_end_time": f"{last_word_end:.2f}" if last_word_end else '-',
            "content": transcript
        })
        
        self.last_word_end = last_word_end or self.last_word_end

        

    @Heuristic.event_handler("utterance_end")
    def handle_utterance_end(self, event):
        result = event["data"]
        last_word_end = result.last_word_end
        event_audio_cursor = event["audio_cursor"]

        content = f"Utterance end for word at {last_word_end:.2f} s"

        latency = int((event_audio_cursor - last_word_end) * 1000)
        
        self.events.append({
            "audio_cursor": f"{event_audio_cursor:.2f}",
            "transcript_cursor": "-",
            "event_type": "utterance_end",
            "latency": latency,
            "speech_start_time": "-",
            "speech_end_time": f"{last_word_end:.2f}",
            "content": content
        })
    
    def first_or_distinct_utterance(self):
        return (
            not self.completed_utterances or
            float(self.completed_utterances[-1]["end_time"]) < (self.current_utterance_start or 0)
        )
    
    def vad_endpoint_needed(self):
        return (
            not self.vad_speech_detected and
            not self.interim_endpointed and
            (self.current_utterance or self.current_interim_utterance) and
            self.events and
            self.events[-1]["event_type"] == "vad_event_end"
        )
    
    def utterance_endpoint_needed(self):
        return (
            not self.vad_speech_detected and 
            not self.interim_endpointed and
            self.current_utterance and
            self.audio_cursor - self.last_word_end > self.pause_threshold
        )

    # TODO: This function should be for pre-speech_final endpointing? Maybe not because empty speech_final possibility?
    def endpoint_current_utterance(self, event_type, event_audio_cursor, transcript_cursor, transcript, first_word_start, last_word_end):
        latency = int((event_audio_cursor - self.last_word_end) * 1000)
        
        reason = event_type
        match event_type:
            case "speech_final_transcript": 
                reason = "empty_speech_final"
            case "final_transcript":
                reason = "vad_is_final"
            case "interim_transcript":
                reason = "vad_interim"
        
        if not self.current_result.is_final:
            if self.current_utterance:
                self.current_utterance += " " + self.current_interim_utterance
            else:
                self.current_utterance = self.current_interim_utterance
            self.current_interim_utterance = ""
            self.current_interim_utterance_start = None
            self.interim_endpointed = True
            
        self.events.append({
            "audio_cursor": f"{event_audio_cursor:.2f}",
            "transcript_cursor": f"{transcript_cursor:.2f}",
            "event_type": reason,
            "latency": latency,
            "speech_start_time": f"{first_word_start:.2f}" if first_word_start else "-",
            "speech_end_time": f"{last_word_end:.2f}" if last_word_end else "-",
            "content": transcript
        })
            
        self._add_completed_utterance(first_word_start, last_word_end, latency, reason, self.current_utterance)

    def _add_completed_utterance(self, start_time, end_time, latency, completed_by, transcript):
        self.completed_utterances.append({
            "start_time": f"{start_time:.2f}" if start_time else "-",
            "end_time": f"{end_time:.2f}" if end_time else "-",
            "latency": latency,
            "completed_by": completed_by,
            "transcript": transcript
        })
        self.current_utterance = ""
        self.current_utterance_start = None

    def get_display_data(self):
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