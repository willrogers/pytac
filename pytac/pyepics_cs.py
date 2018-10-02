from pytac.cs import ControlSystem
from epics import ca, caget, caput
from collections import OrderedDict


class PyepicsControlSystem(ControlSystem):
    """A control system using pyepics to communicate with EPICS. N.B. this is
        currently entirely theoretical and has not yet been tested.

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
            return float(caget(pv, timeout=1.0))
        except TypeError:
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
        pv_data = OrderedDict()  # values in format: [channel_status, channel_id, pv_value]
        results = []
        for pv in pvs:  # create channel
            pv_data[pv] = [False, ca.create_channel(pv, auto_cb=False), None]
        ca.poll()  # wait
        for pv, data in pv_data.items():  # connect to channel
            data[0] = ca.connect_channel(data[1], timeout=1.0)
            if data[0]:  # if connected, send get request
                ca.get(data[1], wait=False)
            else:
                print('cannot connect to {}'.format(pv))
        ca.poll()  # wait
        for pv, data in pv_data.items():
            if data[0]:  # if connected, read get request
                data[2] = float(ca.get_complete(data[1]))
            else:
                data[2] = None
        for pv in pvs:  # support for repeated PVs
            results.append(pv_data[pv][2])
        return results

    def set_single(self, pv, value):
        """Set the value of a given PV.

        Args:
            pv (string): The PV to set the value of. It must be a setpoint PV.
            value (Number): The value to set the PV to.
        """
        caput(pv, value, wait=True, timeout=1.0)

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
        for pv, value in zip(pvs, values):
            caput(pv, value, wait=False, timeout=1.0)
