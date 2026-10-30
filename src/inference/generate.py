"""propose: run batch inference and text generation using trained models and prompt templates.
input: artifacts/training/models/, input prompt/test set, sampling parameters.
output: artifacts/evaluation/predictions/ (json/csv completions)."""

from src.inference.ai_config import load_ai_config, require_approved


def apply_prompt_template(system_prompt: str, user_input: str, template_type: str) -> str:
    """formats raw input into the target model's chat/prompt template."""
    return f"{system_prompt}\n{user_input}"


def run_batch_generation(model, tokenized_prompts: list, sampling_params: dict) -> list:
    """executes batch inference loop over input test prompts."""
    require_approved(load_ai_config())
    return []
