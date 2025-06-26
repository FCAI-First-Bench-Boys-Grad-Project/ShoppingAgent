import yaml


def load_system_prompt(agent):
    with open("src/nodes/agents/prompts.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data[agent]["system_prompt"]
