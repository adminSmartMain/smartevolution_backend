class BillyError(Exception):
    """Error base para la integración con Billy."""


class BillyTimeoutError(BillyError):
    """Billy no respondió dentro del timeout configurado."""


class BillyConnectionError(BillyError):
    """No fue posible conectarse con Billy."""


class BillyAuthenticationError(BillyError):
    """El token de Billy es inválido o expiró."""


class BillyRateLimitError(BillyError):
    """Billy rechazó la petición por rate limiting."""

    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


class BillyNotFoundError(BillyError):
    """Billy no encontró el recurso solicitado."""


class BillyAPIError(BillyError):
    """Billy respondió con un error HTTP no contemplado."""

    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data
        
class BillyLocalRateLimitError(BillyError):
    """SmartEvolution alcanzó su límite interno de llamadas a Billy."""

    def __init__(
        self,
        message,
        retry_after=None,
        count=None,
        limit=None,
    ):
        super().__init__(message)

        self.retry_after = retry_after
        self.count = count
        self.limit = limit
        
class BillyLocalRateLimitError(BillyError):
    """SmartEvolution alcanzó su límite interno de llamadas a Billy."""

    def __init__(
        self,
        message,
        retry_after=None,
        count=None,
        limit=None,
    ):
        super().__init__(message)

        self.retry_after = retry_after
        self.count = count
        self.limit = limit