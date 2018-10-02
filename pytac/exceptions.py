"""Module containing all the exceptions used in pytac."""


class FieldException(Exception):
    """Exception associated with invalid field requests.
    """
    pass


class HandleException(Exception):
    """Exception associated with requests with invalid handles.
    """
    pass


class DeviceException(Exception):
    """Exception associated with Device misconfiguration or invalid requests.
    """
    pass


class UnitsException(Exception):
    """Conversion not understood
    """
    pass


class LatticeException(Exception):
    pass


class TimeoutError(Exception):
    """Manual TimeoutException for python versions > 3.3
    """
    pass
