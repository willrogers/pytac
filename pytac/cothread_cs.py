from pytac.cs import ControlSystem
from cothread.catools import caget, caput


class CothreadControlSystem(ControlSystem):
    """A control system using cothread to communicate with EPICS. N.B. this is
        the default control system.

    It is used to communicate over channel access with the hardware
    in the ring.

    **Methods:**
    """
    def __init__(self):
        pass

    def get_single(self, pv):
        """Get the value of a given PV.

        Args:
            pv (string): The process variable given as a string. It can be a
                         readback or a setpoint PV.

        Returns:
            float: Represents the current value of the given PV.
        """
        try:
            return float(caget(pv, timeout=1.0, throw=False))
        except TypeError:
            print('cannot connect to {}'.format(pv))
            return None

    def get_multiple(self, pvs):
        """Get the value for given PVs.

        Args:
            pvs (list): A list of process variables, given as a strings. They
                         can be a readback or setpoint PVs.

        Returns:
            list: of floats, representing the current values of the PVs.

        Raises:
            ValueError: if the PVs are not passed in as a list.
        """
        if not isinstance(pvs, list):
            raise ValueError('Please enter PVs as a list.')
        results = caget(pvs, timeout=1.0, throw=False)
        for i in range(len(results)):
            try:
                results[i] = float(results[i])
            except TypeError:
                print('cannot connect to {}'.format(pvs[i]))
                results[i] = None
        return results

    def set_single(self, pv, value):
        """Set the value of a given PV.

        Args:
            pv (string): The PV to set the value of. It must be a setpoint PV.
            value (Number): The value to set the PV to.
        """
        try:
            caput(pv, value, timeout=1.0, throw=True)
        except Exception:
            print('cannot connect to {}'.format(pv))

    def set_multiple(self, pvs, values):
        """Set the values for given PVs.

        Args:
            pvs (list): A list of PVs to set the values of. It must be a
                         setpoint PV.
            values (list): A list of the numbers to set no the PVs.

        Raises:
            ValueError: if the PVs or values are not passed in as a list, or if
                         the lists of values and PVs are diffent lengths.
        """
        if not isinstance(pvs, list) or not isinstance(values, list):
            raise ValueError('Please enter PVs and values as a list.')
        elif len(pvs) != len(values):
            raise ValueError('Please enter the same number of values as PVs.')
        try:
            caput(pvs, values, timeout=1.0, throw=True)
        except Exception:
            print('cannot connect to one or more PV(s).')
