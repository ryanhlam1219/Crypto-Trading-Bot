class DataFetchException(Exception):
    """Exception raised for errors while fetching data from an API."""

    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.error_code = error_code