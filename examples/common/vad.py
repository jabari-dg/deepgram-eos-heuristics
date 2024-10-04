import queue
from typing import Callable
import threading
import numpy as np
import librosa
import torch


# Constants
VAD_SAMPLE_RATE = 16000
VAD_CHUNK = 512
VAD_CHUNK_DURATION = VAD_CHUNK / VAD_SAMPLE_RATE

# Load Silero VAD model
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=True)

(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

# vad_iterator = VADIterator(
#     model,
#     threshold=0.4,
#     sampling_rate=VAD_SAMPLE_RATE,
#     min_silence_duration_ms=10 * VAD_CHUNK_DURATION * 1000,
#     speech_pad_ms=0
# )

def create_vad_iterator(min_silence_duration_ms):
    return VADIterator(
        model,
        threshold=0.4,
        sampling_rate=VAD_SAMPLE_RATE,
        min_silence_duration_ms=min_silence_duration_ms,
        speech_pad_ms=0
    )

def vad_worker(vad_queue: queue.Queue, process_vad_event: Callable, stop_event: threading.Event, input_sample_rate: int, vad_iterator):
    while not stop_event.is_set():
        try:
            data = vad_queue.get(timeout=2*VAD_CHUNK_DURATION)
        except queue.Empty:
            continue

        audio_int16 = np.frombuffer(data, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        audio_resampled = librosa.resample(audio_float32, orig_sr=input_sample_rate, target_sr=VAD_SAMPLE_RATE)
        
        for i in range(0, len(audio_resampled), VAD_CHUNK):
            chunk = audio_resampled[i:i+VAD_CHUNK]
            if len(chunk) == VAD_CHUNK:
                speech_dict = vad_iterator(chunk, return_seconds=True)
                if speech_dict:
                    process_vad_event(speech_dict)