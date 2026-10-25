"""Domain-specific errors. Unexpected programming errors are not wrapped here."""


class OrbitalGuardError(Exception):
    """Base class for expected application failures."""


class DataSourceError(OrbitalGuardError):
    pass


class RateLimitedError(DataSourceError):
    pass


class CatalogEmptyError(DataSourceError):
    pass


class ObjectNotFoundError(DataSourceError):
    pass


class InvalidOrbitalRecordError(OrbitalGuardError):
    pass


class TLEChecksumError(InvalidOrbitalRecordError):
    pass


class PropagationError(OrbitalGuardError):
    pass


class ScreeningError(OrbitalGuardError):
    pass


class InvalidConfigurationError(OrbitalGuardError):
    pass


class CoordinateError(OrbitalGuardError):
    pass


class ReportError(OrbitalGuardError):
    pass


class InsufficientMLDataError(OrbitalGuardError):
    pass


class ModelUnavailableError(OrbitalGuardError):
    pass


class IncompatibleModelError(OrbitalGuardError):
    pass
