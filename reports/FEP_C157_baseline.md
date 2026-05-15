# FEP Detector Baseline Report - Cycle 157

## Overview
The `FEPDetector` was tested against a synthetic activation dataset to validate the spike-and-decay logic used for Surprise feature detection.

## Test Results
| Sample ID | Tokens | Detected Features | Peak Confidence | Outcome |
|-----------|--------|-------------------|-----------------|---------|
| `test_spike_decay` | ...is an error... | #101 | 2.45 | ✅ Correctly identified decay pattern. |
| `test_no_decay` | ...remains high... | #201 | 0.22 | ⚠️ Low confidence; identifies as non-surprising (Correct). |
| `test_late_spike` | ...suddenly BOOM | None | N/A | ✅ No decay window available at end of sequence; correctly ignored. |

## Technical Observations
- **Slope sensitivity**: The linear regression on the decay window effectively separates transient spikes from sustained activations.
- **Confidence metric**: Calculated as `(peak * abs(slope)) / (1 + abs(slope))`. This penalizes "flat" signals and rewards sharp resets, aligning with the information gain hypothesis.

## Conclusion
The tool is mechanically sound for detecting FEP events in provided JSONL data. Next step: apply to actual SAE tensors or simulated tensor samples based on real model weights if accessible.
