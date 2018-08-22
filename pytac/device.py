"""The device class used to represent a particular function of an accelerator
element.

A physical element in an accelerator may have multiple devices: an example at
DLS is a sextupole magnet that contains also horizontal and vertical corrector
magnets and a skew quadrupole.
"""
import pytac


class HandleException(Exception):
    """Exception associated with requests with invalid handles.
    """
    pass


class DeviceException(Exception):
    """Exception associated with Device misconfiguration or invalid requests.
    """
    pass


class Device(object):
    """A device attached to an element.

    Contains a control system, readback and setpoint PVs. A readback
    or setpoint PV is required when creating a device otherwise a
    DeviceException is raised. The device is enabled by default.

    **Attributes:**

    Attributes:
        name (str): The prefix of EPICS PVs for this device.
        rb_pv (str): The EPICS readback PV.
        sp_pv (str): The EPICS setpoint PV.

    .. Private Attributes:
           _cs (ControlSystem): The control system object used to get and set
                                 the value of a PV.
           _enabled (bool-like): Whether the device is enabled. May be a
                                  PvEnabler object.
    """
    def __init__(self, name, cs, enabled=True, rb_pv=None, sp_pv=None):
        """.. The constructor method for the class, called whenever a 'Device'
               object is constructed.

        Args:
            name (str): The prefix of EPICS PV for this device.
            cs (ControlSystem): The control system object used to get and set
                                 the value of a PV.
            enabled (bool-like): Whether the device is enabled. May be a
                                  PvEnabler object.
            rb_pv (str): The EPICS readback PV.
            sp_pv (str): The EPICS setpoint PV.

        **Methods:**
        """
        self.name = name
        self._cs = cs
        self.rb_pv = rb_pv
        self.sp_pv = sp_pv
        self._enabled = enabled

    def is_enabled(self):
        """Whether the device is enabled.

        Returns:
            bool: whether the device is enabled.
        """
        return bool(self._enabled)

    def set_value(self, value):
        """Set the device value.

        Args:
            value (float): The value to set on the PV.

        Raises:
            HandleException: if no setpoint PV exists.
        """
        if self.sp_pv is None:
            raise HandleException(
                "Device {0} has no setpoint PV.".format(self.name)
            )
        self._cs.put(self.sp_pv, value)

    def get_value(self, handle):
        """Read the value of a readback or setpoint PV.

        Args:
            handle (str): The handle used to get the value off a readback or
                           setpoint PV.

        Returns:
            float: The value of the PV.

        Raises:
            HandleException: if the requested PV doesn't exist.
        """
        print('getting {}'.format('handle'))
        if handle == pytac.RB and self.rb_pv:
            return self._cs.get(self.rb_pv)
        elif handle == pytac.SP and self.sp_pv:
            return self._cs.get(self.sp_pv)

        raise HandleException(
            "Device {0} has no {1} PV.".format(self.name, handle)
        )

    def get_pv_name(self, handle):
        """Get a PV name on a specified handle.

        Args:
            handle (str): The readback or setpoint handle to be returned.

        Returns:
            str: A readback or setpoint PV.

        Raises:
            HandleException: if the PV doesn't exist.
        """
        if handle == pytac.RB and self.rb_pv:
            return self.rb_pv
        elif handle == pytac.SP and self.sp_pv:
            return self.sp_pv

        raise HandleException(
            "Device {0} has no {1} PV.".format(self.name, handle)
        )

    def get_cs(self):
        """The control system object used to get and set the value of a PV.

        Returns:
            ControlSystem: The control system object used to get and set the
            value of a PV.
        """
        return self._cs


class PvEnabler(object):
    """A PvEnabler class to check whether a device is enabled.

    The class will behave like True if the PV value equals enabled_value,
    and False otherwise.

    .. Private Attributes:
           _pv (str): The PV name.
           _enabled_value (str): The value for PV for which the device should
                                  be considered enabled.
           _cs (ControlSystem): The control system object.
    """
    def __init__(self, pv, enabled_value, cs):
        """.. The constructor method for the class, called whenever a
               'PvEnabler' object is constructed.

        Args:
            pv (str): The PV name.
            enabled_value (str): The value for PV for which the device should
                                  be considered enabled.
            cs (ControlSystem): The control system object.
        """
        self._pv = pv
        self._enabled_value = str(int(float(enabled_value)))
        self._cs = cs

    def __nonzero__(self):
        """Used to override the 'if object' clause.

        Support for Python 2.7.

        Returns:
            bool: True if the device should be considered enabled.
        """
        pv_value = self._cs.get(self._pv)
        return self._enabled_value == str(int(float(pv_value)))

    def __bool__(self):
        """Used to override the 'if object' clause.

        Support for Python 3.x.

        Returns:
            bool: True if the device should be considered enabled.
        """
        return self.__nonzero__()
