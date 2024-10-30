import os
from dotenv import load_dotenv


class Settings:
    def __init__(self) -> None:
        load_dotenv()
        self.endpoint = os.getenv('OPENAI_ENDPOINT')
        self.key = os.getenv("OPENAI_KEY")
        self.version = os.getenv("OPENAI_VERSION")
        self.chat_model = os.getenv("OPENAI_MODEL")
        self.cluster = os.getenv("KUSTO_CLUSTER")


settings = None


def get_settings_instance() -> Settings:
    global settings
    if not settings:
        settings = Settings()
    return settings
