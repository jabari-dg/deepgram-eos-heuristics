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

```
======================================================================================================================================================
Completed Utterances:
======================================================================================================================================================
[2.80 - 3.30 (540 ms - vad_interim)]  Okay.
[3.80 - 5.66 (176 ms - speech_final)]  I was at the grocery store yesterday,
[11.13 - 11.63 (120 ms - speech_final)]  and you know how sometimes you go in for just one thing, but then you end up wandering around?
[12.36 - 15.90 (123 ms - speech_final)]  Well, I was looking for pasta sauce, which should have been super simple.
[16.82 - 18.84 (169 ms - speech_final)]  But they'd rearranged the whole aisle.

======================================================================================================================================================

Current utterance ( - ): 
Current interim utterance ( - ): 
Real-time Events Log:
------------------------------------------------------------------------------------------------------------------------------------------------------
                               Spot Interim Latency: 95 ms | Spot Endpoint Latency: 169 ms | VAD Speech detected: False                               
------------------------------------------------------------------------------------------------------------------------------------------------------
 Audio Cursor  | Transcript Cursor  | Event Type                    |      Latency       |  Words Start  |   Words End   | Content                                                     
------------------------------------------------------------------------------------------------------------------------------------------------------
     1.15      |        1.06        | interim_transcript            |         95         |       -       |       -       |                                                             
     2.30      |        2.11        | interim_transcript            |        192         |       -       |       -       |                                                             
     2.88      |         -          | vad_event_start               |         80         |      2.8      |       -       | [Speech Started at 2.80s]                                   
     3.26      |        3.17        | interim_transcript            |         96         |     2.72      |     3.17      | Okay.                                                       
     3.74      |         -          | vad_event_end                 |        344         |       -       |      3.4      | [Speech Ended at 3.40s]                                     
     3.84      |        3.84        | vad_interim                   |      0 (540)       |     2.80      |     3.30      | Okay.                                                       
     3.84      |        3.84        | interim_transcript            |         0          |     2.80      |     3.30      | Okay.                                                       
     3.94      |         -          | vad_event_start               |        136         |      3.8      |       -       | [Speech Started at 3.80s]                                   
     4.99      |        4.90        | interim_transcript            |         96         |     2.80      |     4.90      | Okay. I was at the grocery                                  
     5.18      |        3.56        | final_transcript              |         -          |     2.80      |     3.30      | Okay.                                                       
     5.18      |        5.09        | interim_transcript            |         96         |     3.80      |     5.09      | I was at the grocery store                                  
     6.14      |         -          | vad_event_end                 |        244         |       -       |      5.9      | [Speech Ended at 5.90s]                                     
     6.34      |        6.16        | speech_final_transcript       |     176 (676)      |     3.80      |     5.66      | I was at the grocery store yesterday,                       
     6.62      |         -          | vad_event_start               |         24         |      6.6      |       -       | [Speech Started at 6.60s]                                   
     7.39      |         -          | vad_event_end                 |        392         |       -       |      7.0      | [Speech Ended at 7.00s]                                     
     7.39      |         -          | vad_event_start               |         92         |      7.3      |       -       | [Speech Started at 7.30s]                                   
     7.39      |        7.30        | interim_transcript            |         95         |     6.88      |     7.30      | and                                                         
     7.39      |         -          | utterance_end                 |        1732        |       -       |     5.66      | Utterance end for word at 5.66 s                            
     8.45      |        8.35        | interim_transcript            |         95         |     7.04      |     8.34      | and you know how sometimes                                  
     9.50      |        9.41        | interim_transcript            |         95         |     6.96      |     9.41      | and you know how sometimes you go in for just one           
     10.37     |       10.18        | interim_transcript            |        192         |     7.04      |     10.18     | and you know how sometimes you go in for just one thing, but
     11.52     |       10.89        | final_transcript              |         -          |     7.04      |     10.89     | and you know how sometimes you go in for just one thing, but then you end up
     11.90     |         -          | vad_event_end                 |        304         |       -       |     11.6      | [Speech Ended at 11.60s]                                    
     12.00     |       11.88        | speech_final_transcript       |     120 (370)      |     11.13     |     11.63     | wandering around?                                                     
     12.67     |         -          | vad_event_start               |         72         |     12.6      |       -       | [Speech Started at 12.60s]                                  
     12.96     |       12.96        | interim_transcript            |         0          |     12.28     |     12.78     | Well,                                                       
     14.11     |       14.02        | interim_transcript            |         96         |     12.44     |     13.98     | Well, I was looking for pasta                               
     15.17     |       15.07        | interim_transcript            |         96         |     12.36     |     15.07     | Well, I was looking for pasta sauce, which should have been 
     16.13     |         -          | vad_event_end                 |        328         |       -       |     15.8      | [Speech Ended at 15.80s]                                    
     16.22     |       16.10        | speech_final_transcript       |     123 (324)      |     12.36     |     15.90     | Well, I was looking for pasta sauce, which should have been super simple.
     16.51     |         -          | vad_event_start               |         12         |     16.5      |       -       | [Speech Started at 16.50s]                                  
     17.28     |       17.18        | interim_transcript            |         96         |     16.64     |     17.14     | But                                                         
     18.34     |       18.24        | interim_transcript            |         96         |     16.82     |     18.24     | But they'd rearranged the whole                             
     19.01     |         -          | vad_event_end                 |        308         |       -       |     18.7      | [Speech Ended at 18.70s]                                    
     19.20     |       19.03        | speech_final_transcript       |     169 (360)      |     16.82     |     18.84     | But they'd rearranged the whole aisle.                       
     20.26     |       20.06        | interim_transcript            |        192         |       -       |       -       |                                                             
     20.26     |         -          | utterance_end                 |        1416        |       -       |     18.84     | Utterance end for word at 18.84 s                           
     20.83     |       20.83        | interim_transcript            |         0          |       -       |       -       |                                                             
     21.22     |       21.12        | interim_transcript            |         95         |       -       |       -       |                                                             
     21.50     |       21.39        | speech_final_transcript       |        114         |       -       |       -       |                                                             
     22.18     |       22.18        | speech_final_transcript       |         0          |       -       |       -       |                                                             
```

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



