# Model development strategy

## Objective

Develop our own specialized transformer adaptation for website/API security investigation, evidence assessment, and remediation guidance.

This repository does not contain trained weights and makes no claim of matching a frontier general-purpose model.

## Development stages

1. Define reproducible tasks and verifiers.
2. Evaluate candidate unchanged open-weight models and optional hosted baselines through the same tools.
3. Collect reviewed traces containing successful checks, safe controls, false alarms, inconclusive attempts, and verified fixes.
4. Train an initial supervised adaptation, potentially using LoRA.
5. Compare against the exact unchanged base model and system configuration.
6. Release an adapter/checkpoint only after capability, regression, data-rights, and redistribution reviews.

Training a foundation model from scratch is a separate future decision requiring a corpus, tokenizer, compute plan, and evidence that adaptation is insufficient.

## Initial specialization

Begin with evidence assessment and fix guidance for a small number of access-control scenarios. Expand to action planning only after reliable policy enforcement and independent verification exist.

Keep current vulnerability knowledge in a versioned retrieval source when appropriate. Fine-tuning alone is not a dependable way to keep advisories current.

## Model selection criteria

- Tool-use and structured-output reliability.
- Ability to interpret multi-account browser/HTTP observations.
- Measured precision, recall, abstention, latency, and cost.
- Deployment hardware and context requirements.
- Terms permitting the intended adaptation, hosting, and distribution.

No specific model is selected yet. Do not label an unchanged provider API as a proprietary trained model.

## Training controls

Use human-reviewed traces. Include benign and fixed cases, not just positive examples. Preserve evaluator-only labels outside model context.

Split by application family, scenario family, and version lineage before generating variations. Do not randomly split nearly identical requests across training and evaluation.

Customer findings, credentials, and personal data are excluded by default. Explicit permission and sanitization are required before any separately reviewed customer-derived training dataset.

## Release evidence

Publish base model identity/revision, adaptation settings, eligible data sources, split construction, benchmark contamination limitations, metrics, failures, and known scope restrictions.

Model weights, adaptation code, hosted service, and underlying datasets are distinct artifacts with potentially different licenses.

## References

- [LoRA concepts and implementation](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)
- [Research on limitations in vulnerability reasoning](https://arxiv.org/abs/2403.17218)

These references inform the plan; neither establishes our model's performance.
