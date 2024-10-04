# Deepgram Custom Speech Endpointing Reference Implementations

This repository contains reference implementations for robust end-of-speech detection using a combination of Deepgram's real-time transcription API features and custom heuristics. The goal is to demonstrate how low-latency, real-time solutions can be created using the Deepgram API, open-source Voice Activity Detection (VAD), and tailored heuristics.

## Overview

The project showcases how to combine various Deepgram API features with local processing to achieve accurate and low-latency speech endpointing. It utilizes:

- Deepgram API features:
  - Endpointing
  - Utterance End
  - Word-level timestamps
- Local Voice Activity Detection (VAD) using [`silero-vad`](https://github.com/snakers4/silero-vad)
- Custom heuristics for speech detection and endpointing

The system is designed to be modular, allowing for easy addition and modification of different event handlers and heuristics.

## Project Structure

The repository is organized as follows:
```
project_root/
│
├── base_heuristic.py
├── vad.py
├── examples
│ └── vad_implementation
│  ├── heuristic.py
│  ├── terminal_renderer.py
│  ├── main.py
│  └── README.md
├── requirements.txt
└── README.md
```

- `base_heuristic.py`: Contains the base `Heuristic` class for implementing custom logic.
- `vad.py`: Implements Voice Activity Detection using silero-vad.
- `examples/`: Contains different implementation examples.
  - `vad_implementation/`: An example implementation using VAD and custom heuristics.

## Getting Started

To use any of the reference implementations:

1. Navigate to the specific example folder (e.g., `examples/vad_implementation/`).
2. Follow the README instructions in that folder for setup and execution.

Each example folder contains its own `requirements.txt` file and specific instructions for running the implementation.

## Examples

### VAD Implementation

The VAD implementation demonstrates how to combine Deepgram's real-time transcription with local Voice Activity Detection for advanced end-of-speech detection. It showcases the use of `silero-vad` alongside Deepgram's API features.

For more details, see the README in the `examples/vad_implementation/` folder.

## Future Examples

While the current VAD implementation represents our recommended approach for robust, low-latency speech detection, we plan to add the following examples:

- A web app implementation demonstrating the VAD approach with a simple web frontend
- Examples showing heuristic approaches to end-of-speech detection without using a local VAD, relying solely on analysis of transcript results

It's important to note that for the most reliable and low-latency performance, we recommend using a local VAD (such as `silero-VAD`) as close as possible to where audio enters the application. This forms the cornerstone of a robust heuristic approach. Other examples are provided to demonstrate alternative methods and use cases, but may not achieve the same level of performance as the VAD-based approach.

## Dependencies

The main dependencies for this project are:

- [Deepgram Python SDK](https://github.com/deepgram/deepgram-python): For interfacing with the Deepgram API
- [silero-vad](https://github.com/snakers4/silero-vad): For local Voice Activity Detection

Specific dependencies for each implementation are listed in the respective `requirements.txt` files.

## Note

This is a reference implementation intended for demonstration purposes. It showcases how to leverage Deepgram's API features alongside custom processing for advanced speech endpointing scenarios.