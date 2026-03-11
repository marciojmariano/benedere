"""
Configurações centrais via pydantic-settings.
Combina boas práticas:
- Variáveis de DB separadas (legibilidade e flexibilidade)
- @lru_cache para singleton e facilidade nos testes
- Método is_swagger_enabled() expressivo
- Suporte a múltiplos ambientes
- Campos lista declarados como str e convertidos via @computed_field
  (solução definitiva para o bug de parsing do pydantic-settings)
"""
from functools import lru_cache

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Aplicação ─────────────────────────────────────────────────────────
    APP_NAME: str = "Benedere"
    AMBIENTE: str = "desenvolvimento"   # desenvolvimento | homologacao | producao
    LOG_LEVEL: str = "INFO"

    # ── Banco de Dados ────────────────────────────────────────────────────
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "benedere"
    DB_PASSWORD: str = "benedere123"
    DB_NAME: str = "benedere_dev"

    # ── Auth0 ─────────────────────────────────────────────────────────────
    AUTH0_DOMAIN: str = "your-domain.us.auth0.com"
    AUTH0_AUDIENCE: str = "https://api.benedere.com.br"

    # Declarados como str para evitar bug de parsing do pydantic-settings
    # O .env aceita: RS256  ou  RS256,HS256
    AUTH0_ALGORITHMS: str = "RS256"

    # O .env aceita: http://localhost:3000  ou  http://localhost:3000,http://localhost:5173
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # ── Propriedades computadas ───────────────────────────────────────────

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Monta a URL de conexão a partir das variáveis separadas."""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @computed_field
    @property
    def auth0_algorithms_list(self) -> list[str]:
        """Converte AUTH0_ALGORITHMS string -> list para uso no código."""
        return [a.strip() for a in self.AUTH0_ALGORITHMS.split(",") if a.strip()]

    @computed_field
    @property
    def allowed_origins_list(self) -> list[str]:
        """Converte ALLOWED_ORIGINS string -> list para uso no código."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # ── Métodos de controle ───────────────────────────────────────────────

    def is_swagger_enabled(self) -> bool:
        """Swagger visível em todos os ambientes, exceto produção."""
        return self.AMBIENTE.lower() != "producao"

    def is_debug(self) -> bool:
        """Ativo apenas em desenvolvimento."""
        return self.AMBIENTE.lower() == "desenvolvimento"

    def is_production(self) -> bool:
        return self.AMBIENTE.lower() == "producao"

    # ── Validators ────────────────────────────────────────────────────────

    @field_validator("AMBIENTE")
    @classmethod
    def validate_ambiente(cls, v: str) -> str:
        allowed = {"desenvolvimento", "homologacao", "producao"}
        if v.lower() not in allowed:
            raise ValueError(f"AMBIENTE deve ser um de: {allowed}")
        return v.lower()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Retorna instância única (singleton) das configurações.
    O @lru_cache permite sobrescrever nos testes sem efeitos colaterais.
    """
    return Settings()


settings = get_settings()
