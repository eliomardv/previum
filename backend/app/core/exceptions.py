class BusinessError(Exception):
    """Expected business rule failure, independent of HTTP."""


class CompanyNotFound(BusinessError):
    pass


class WorkerNotFound(BusinessError):
    pass
