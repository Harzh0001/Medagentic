from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App config loaded from .env (Pydantic V2 style)
    model_config = SettingsConfigDict(env_file=".env")

    zen_api_key: str = ""
    zen_base_url: str = "https://api.opencode.ai/v1"
    zen_model: str = "gpt-4o-mini"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Fix legacy incorrect base URL if user has it stuck in Streamlit secrets
        if self.zen_base_url == "https://opencode.ai/api/v1" or self.zen_base_url == "https://opencode.ai/zen/v1":
            self.zen_base_url = "https://api.opencode.ai/v1"

    pubmed_base: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    top_k: int = 6
    max_abstract_chars: int = 1800
    
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8502"


settings = Settings()
