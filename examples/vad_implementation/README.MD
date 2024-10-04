# VAD Implementation Example

This example demonstrates a proof-of-concept approach to low-latency end-of-speech detection using the Deepgram API and local Voice Activity Detection (VAD).

## Installation

Clone the repository and navigate to the `examples/vad_implementation` directory.


```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

1. Set your Deepgram API key as an environment variable:
   ```bash
   export DEEPGRAM_API_KEY=your_api_key_here
   ```

2. Configure key parameters in `main.py` (optional):
   - `INPUT_SAMPLE_RATE`: Set this to match your microphone's capture sample rate.
   - `MIN_SILENCE_DURATION_MULTIPLIER`: Controls the silence threshold for both API and local VAD. Higher values require longer silences for end-of-speech detection. Default is 10 (320ms).
   - `PAUSE_THRESHOLD`: Sets the allowed pause between words in seconds, affecting both API and local utterance end detection. Default is 1.0 second.

3. Run the script:
   ```bash
   python main.py
   ```

4. Speak into your microphone. The script will display real-time transcription results and VAD events.

5. Press Enter to stop the script.

Note: The script uses sane defaults for most parameters, but you can adjust them in `main.py` if needed.

## Example Output

[Placeholder for GIF or text description of output]

## Explanation of the Code

This implementation combines the Deepgram API for real-time transcription with local Voice Activity Detection (VAD) using silero-VAD. Here's a high-level overview of how it works:

1. Audio Input: The script captures audio from your computer's microphone.

2. Dual Processing:
   - The audio is streamed to the Deepgram API for transcription.
   - Simultaneously, the audio is processed by the local VAD to obtain start and end speech timestamps.

3. Audio Processing:
   - For the VAD, the audio is downsampled to 16kHz to meet silero-VAD requirements.
   - The original audio stream is sent unaltered to Deepgram to maintain transcription accuracy.

4. Heuristic Processing:
   - The `VADHeuristic` class processes both transcription results from Deepgram and local VAD events.
   - It intelligently combines information from interim results, final results, and VAD events to determine when to finalize transcript segments.
   - The heuristic takes advantage of Deepgram's `speech_final` flag and local VAD end-of-speech detection to make endpointing decisions.
   - This approach allows for more responsive and accurate transcript finalization, especially in cases where the API's endpointing might be delayed or when local VAD can provide earlier end-of-speech detection.
   - The heuristic also manages the current utterance state, handling the transition between interim and final results, and deciding when to start a new utterance based on both API and local VAD inputs.

    5. Output:
   - The script displays real-time transcription results, VAD events, and completed speech segments in the terminal.

## Implementation Notes

- This example is based on using the Deepgram cloud STT API. In a self-hosted environment with the Deepgram STT API, different custom logic might be warranted due to greater control over transcription latency.

- Currently, this example supports only single-channel audio. However, the approach outlined here can be adapted for multichannel audio with additional complexity. If you need to use this approach with multichannel audio, please contact your Deepgram representative for further guidance and best practices.

- This example captures audio at 48 kHz, based on the device microphone sample rate. While suitable for this local reference implementation, such high sample rates are not recommended for production real-time use cases (e.g., conversational AI / voice bots). Human speech primarily occupies frequencies up to 8 kHz, which is fully captured by 16 kHz audio. Higher sample rates, such as common default input sample rates for audio devices (e.g., 44.1 kHz or 48 kHz), are designed for full-range audio applications but add unnecessary bandwidth overhead for voice. 16 kHz is commonly used in Speech-to-Text applications as it efficiently captures all critical frequencies for clear, accurate speech recognition while optimizing bandwidth and processing requirements.



