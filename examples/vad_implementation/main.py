import os
import threading
import queue
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents, Microphone
from common.vad import vad_worker, create_vad_iterator, VAD_SAMPLE_RATE, VAD_CHUNK_DURATION # 32 ms
from heuristic import VADHeuristic
from terminal_renderer import TerminalRenderer

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# These three can be changed
INPUT_SAMPLE_RATE = 48000 # Microphone sample rate Note: Must manually provide this
# Silence required for endpointing for both Deepgram API VAD (speech_final) and local VAD (silero-VAD)
# TODO: Make it easier to just pass in ms, handle the math in code
MIN_SILENCE_DURATION_MULTIPLIER = 10 # Multiples of 32 ms
PAUSE_THRESHOLD = 1.0 # Allowed pause between words in seconds, for local utterance_end

# Avoid changing these directly
MIN_SILENCE_DURATION_MS = MIN_SILENCE_DURATION_MULTIPLIER * VAD_CHUNK_DURATION * 1000 # Defaulting to 320 ms, change the multiplier
INPUT_CHUNK_DURATION = int(INPUT_SAMPLE_RATE / VAD_SAMPLE_RATE) * VAD_CHUNK_DURATION # Defaulting to quotient of input sample rate / VAD sample rate
INPUT_CHUNK_SIZE = int(INPUT_SAMPLE_RATE * INPUT_CHUNK_DURATION) # samples at INPUT_SAMPLE_RATE


def main():
    deepgram = DeepgramClient(DEEPGRAM_API_KEY)
    dg_connection = deepgram.listen.websocket.v("1")

    heuristic = VADHeuristic(pause_threshold=PAUSE_THRESHOLD)
    terminal_renderer = TerminalRenderer()
    
    stop_event = threading.Event()
    vad_queue = queue.Queue()

    def process_vad_event(speech_dict):
        heuristic.process({
            "event_type": "vad_event", 
            "audio_cursor": heuristic.audio_cursor, 
            "data": speech_dict
        })
        display_data = heuristic.get_display_data()
        terminal_renderer.update(**display_data)
        terminal_renderer.render()

    vad_iterator = create_vad_iterator(MIN_SILENCE_DURATION_MS)
    vad_thread = threading.Thread(
        target=vad_worker, 
        args=(vad_queue, process_vad_event, stop_event, INPUT_SAMPLE_RATE, vad_iterator)
    )
    vad_thread.start()
    
    def on_message(self, result, **kwargs):
        audio_cursor = heuristic.audio_cursor
        heuristic.process({
            "event_type": "transcript", 
            "audio_cursor": audio_cursor, 
            "data": result
        })
        display_data = heuristic.get_display_data()
        terminal_renderer.update(**display_data)
        terminal_renderer.render()
        
    def on_utterance_end(self, utterance_end, **kwargs):
        audio_cursor = heuristic.audio_cursor
        heuristic.process({
            "event_type": "utterance_end", 
            "audio_cursor": audio_cursor, 
            "data": utterance_end
        })
        display_data = heuristic.get_display_data()
        terminal_renderer.update(**display_data)
        terminal_renderer.render()
        
    def on_error(_, error, **__):
        print(f"Error: {error}")

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)

    options = LiveOptions(
        model="nova-2",
        language="en",
        smart_format=True,
        interim_results=True,
        utterance_end_ms=max(1000, int(PAUSE_THRESHOLD * 1000)),
        endpointing=int(MIN_SILENCE_DURATION_MS),
        encoding="linear16",
        channels=1,
        sample_rate=INPUT_SAMPLE_RATE
    )

    if dg_connection.start(options) is False:
        print("Failed to connect to Deepgram")
        return
    
    def process_mic_data(data):
        if not stop_event.is_set():
            heuristic.audio_cursor += INPUT_CHUNK_DURATION
            dg_connection.send(data)
            vad_queue.put(data)
            
    microphone = Microphone(
        process_mic_data, 
        rate=INPUT_SAMPLE_RATE,
        chunk=INPUT_CHUNK_SIZE,
    )
    
    microphone.start()

    print("\nPress Enter to stop streaming...\n")
    input("")
    stop_event.set()

    microphone.finish()
    dg_connection.finish()
    vad_thread.join()
    print("Finished")

if __name__ == "__main__":
    main()