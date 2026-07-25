class RotaHubError(Exception):
    """Erro base da aplicação."""

    status_code = 500
    default_message = "Erro interno inesperado."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(RotaHubError):
    status_code = 404
    default_message = "Registro não encontrado."


class ConflictError(RotaHubError):
    status_code = 409
    default_message = "Registro já existente."


class ValidationError(RotaHubError):
    status_code = 422
    default_message = "Dados inválidos."


class UnauthorizedError(RotaHubError):
    status_code = 401
    default_message = "Não autenticado."


class ForbiddenError(RotaHubError):
    status_code = 403
    default_message = "Acesso negado."
