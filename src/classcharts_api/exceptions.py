class ClassChartsApiError(Exception):
    """Raised when the ClassCharts API returns an error response."""


class ClassChartsAuthError(ClassChartsApiError):
    """Raised when authentication with ClassCharts fails."""
