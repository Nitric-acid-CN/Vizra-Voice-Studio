# Third-party sources and models

The source package does not bundle model weights, upstream repositories, private
reference voices, generated audio, runtime caches, or virtual environments.

- Qwen3-TTS: https://github.com/QwenLM/Qwen3-TTS (Apache-2.0).
- CosyVoice: https://github.com/QwenAudio/CosyVoice (Apache-2.0).
- Matcha-TTS: https://github.com/shivammehta25/Matcha-TTS (check its upstream license).
- Model weights are obtained from their official ModelScope repositories. Review
  each model card and license before redistribution or commercial use.

Additional official engines:

- Chatterbox: https://github.com/resemble-ai/chatterbox (MIT), source commit
  `5de7a54aa4e5e2baadb0182dde554908b48b85c2`.
- Chatterbox-Turbo weights: https://huggingface.co/ResembleAI/chatterbox-turbo,
  revision `749d1c1a46eb10492095d68fbcf55691ccf137cd` (see official model card).
- Perth: https://github.com/resemble-ai/Perth (MIT), source commit
  `ff1c8ac55a976971245cdd53c18d6131ca00d993`. Official watermarking is retained.
- Kokoro code: https://github.com/hexgrad/kokoro (Apache-2.0), package 0.9.4.
- Kokoro weights: https://huggingface.co/hexgrad/Kokoro-82M (Apache-2.0),
  revision `f3ff3571791e39611d31c381e3a41a3af07b4987`.
- English NLP asset: https://github.com/explosion/spacy-models,
  `en_core_web_sm` 3.8.0 (see asset license).

The workbench's own code is MIT, see LICENSE. No third-party repository or model
weights are bundled in the source archive. Models are downloaded from their
official repositories and keep their original licenses and notices. This does
not relicense upstream models or claim a universal right to redistribute them.

The model adapters retain official architectures and weights. Windows loading
workarounds, environment isolation, job cancellation, file management and UI
integration are documented in this workbench. Chatterbox runs its official
FP32 path because verified stability is preferred to untested half precision;
Qwen/CosyVoice use the tested mixed/half precision paths described in validation.
