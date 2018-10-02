import sys
import pytac
import pytest
from mock import patch, MagicMock
from types import ModuleType
from pytac.load_csv import load
from pytac.exceptions import LatticeException
from constants import DUMMY_VALUE_1, DUMMY_VALUE_2
if float(sys.version[:3]) < 3.3:
    from pytac.exceptions import TimeoutError


@pytest.fixture(scope="session")
def Travis_CI_compatibility():
    # Cothread
    """Travis CI cannot import cothread so we must create a mock of cothread and
        catools (the module that ytac imports from cothread), including the
        functions that pytac explicitly imports (caget and caput).
       First we create a return function that depending on it's input specifies
        what our new caget will return. we also create a set function, to
        replace caset, that raises exceptions in the same manner as the original
        Then we make a MagicMock for the catools class and assign our return
        function to the caget method on our catools. Next we create a blank
        cothread module, and put our catools class into it. Finally, we edit
        sys.modules to ensure our new mocked code is called instead of the
        original.
    """
    def return_func(pvs, timeout, throw):
        if type(pvs) is list:
            for pv in pvs:
                if pv.count('not') is not 0:
                    return [None, None]
            return [DUMMY_VALUE_1, DUMMY_VALUE_2]
        else:
            if pvs.count('not') is 0:
                return DUMMY_VALUE_1
            else:
                return None

    def set_func(pvs, values, timeout, throw):
        if type(pvs) is list:
            for pv in pvs:
                if pv.count('not') is not 0:
                    raise Exception
        else:
            if pvs.count('not') is 0:
                raise Exception

    catools = MagicMock()
    catools.caget = return_func
    catools.caput = set_func
    cothread = ModuleType('cothread')
    cothread.catools = catools
    sys.modules['cothread'] = cothread
    sys.modules['cothread.catools'] = catools
    # Caproto
    """Travis also can't import caproto, but more importantly caproto requires a
        python version of 3.6 or greater. So in order to make sure the tests
        always run correctly we must mock caproto. N.B. this is  more
        complicated than mocking cothread as the process of getting values from
        multiple PVs is significantly more complex in caproto.
       First we create a fixture that returns our response object, with the data
        as an attribute, in the correct manner. Next we create a new mock client
        class with sub-classes Context and Batch, these sub-classes have the
        correct methods and logic to return the right values in the appropriate
        way to emulate caproto as we use it. Then we create the blank modules,
        caproto and caproto.threading, and put our client class inside the
        latter. Finally we edit sys.modules to ensure that our mocked caproto
        code is called instead of the original.
    """
    def r(value):
        class response(object):
            def __init__(self, value):
                self.data = [value]
        res = response(value)
        return res

    class client(object):
        class Context(object):
            def get_pvs(self, *pvs):
                if len(pvs) > 1:
                    pv_obj_1 = MagicMock()
                    pv_obj_2 = MagicMock()
                    if pvs[0].count('not') is 0:
                        pv_obj_1.read.return_value = r(DUMMY_VALUE_1)
                    else:
                        pv_obj_1.read = MagicMock()
                        pv_obj_1.read.side_effect = TimeoutError
                        pv_obj_2.write = MagicMock()
                        pv_obj_2.write.side_effect = TimeoutError
                    if pvs[1].count('not') is 0:
                        pv_obj_2.read.return_value = r(DUMMY_VALUE_2)
                    else:
                        pv_obj_2.read = MagicMock()
                        pv_obj_2.read.side_effect = TimeoutError
                        pv_obj_2.write = MagicMock()
                        pv_obj_2.write.side_effect = TimeoutError
                    return [pv_obj_1, pv_obj_2]
                else:
                    pv_obj = MagicMock()
                    if pvs[0].count('not') is 0:
                        pv_obj.read.return_value = r(DUMMY_VALUE_1)
                    else:
                        pv_obj.read = MagicMock()
                        pv_obj.read.side_effect = TimeoutError
                        pv_obj.write = MagicMock()
                        pv_obj.write.side_effect = TimeoutError
                    return [pv_obj]

        class Batch(object):
            def __enter__(self):
                return self

            def read(self, pv_obj, callback):
                callback(pv_obj.read())

            def write(self, pv_obj, value):
                pv_obj.write()

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

    caproto = ModuleType('caproto')
    caproto.threading = ModuleType('caproto.threading')
    caproto.threading.client = client
    sys.modules['caproto'] = caproto
    sys.modules['caproto.threading'] = caproto.threading
    sys.modules['caproto.threading.client'] = client
    # Pyepics
    """Travis also can't import pyepics, and pyepics requires a glibc version of
        2.14 or greater. So in order to make sure the tests always run correctly
        we must mock pyepics. N.B. this is more complicated than mocking
        cothread as the process of getting values from multiple PVs is
        significantly more complex in pyepics.
       First we mock the ca module, complete with the functions we use. N.B. we
        add a little bit of logic in there to change the behaviour if the PV
        doesn't exist. Next we create a get_function that specifies what caget
        returns. Then we create a blank epics module, and put our ca class as
        well as our caget and caset functions into it. Finally we edit
        sys.modules to ensure that our mocked pyepics code is called instead of
        the original.
    """
    class ca(object):
        def __init__(self):
            self.calls = 0

        def poll(self):
            pass

        def create_channel(self, pv, auto_cb):
            if pv.count('not') is 0:
                return 12345678
            else:
                return 0

        def connect_channel(self, chid, timeout):
            if chid is 0:
                return False
            else:
                return True

        def get(self, chid, wait):
            pass

        def get_complete(self, chid):
            self.calls += 1
            if self.calls % 2:
                return DUMMY_VALUE_1
            else:
                return DUMMY_VALUE_2

    def get_func(pv, timeout):
        if pv.count('not') is 0:
            return DUMMY_VALUE_1
        else:
            return None

    epics = ModuleType('epics')
    epics.ca = ca()
    epics.caget = get_func
    epics.caput = MagicMock()
    sys.modules['epics'] = epics
    sys.modules['epics.ca'] = ca()
    sys.modules['epics.caget'] = get_func
    sys.modules['epics.caput'] = epics.caput


@pytest.fixture(scope="session")
def mock_cs_raises_ImportError():
    """We create a mock control system to replace CothreadControlSystem, so that
        we can check that when it raises an ImportError load_csv.load catches it
        and raises a LatticeException instead.
       N.B. Our new CothreadControlSystem is nested inside a fixture so it can
        be patched into pytac.cothread_cs to replace the existing
        CothreadControlSystem class. The new CothreadControlSystem created here
        is a function not a class (like the original) to prevent it from raising
        the ImportError when the code is compiled.
    """
    def CothreadControlSystem():
        raise ImportError
    return CothreadControlSystem


def make_control_system(cs):
    """This function depending upon it's input creates either a cothread or
        caproto control system and returns it. This is used to enable the use of
        parametrization in tests that are not control system specific.
    """
    if cs == 'cothread':
        from pytac import cothread_cs
        return cothread_cs.CothreadControlSystem()
    elif cs == 'caproto':
        from pytac import caproto_cs
        return caproto_cs.CaprotoControlSystem()
    elif cs == 'pyepics':
        from pytac import pyepics_cs
        return pyepics_cs.PyepicsControlSystem()


def test_import_caproto_cs(Travis_CI_compatibility):
    """Test that the caproto control system sucessfully loads.
    """
    cs = make_control_system('caproto')
    assert bool(load('VMX', cs))


def test_import_pyepics_cs(Travis_CI_compatibility):
    """Test that the pyepics control system sucessfully loads.
    """
    cs = make_control_system('pyepics')
    assert bool(load('VMX', cs))


def test_import_cothread_cs(Travis_CI_compatibility):
    """Test that the cothread control system sucessfully loads.
    """
    cs = make_control_system('cothread')
    assert bool(load('VMX', cs))


def test_default_control_system_import(Travis_CI_compatibility):
    """In this test we:
        - assert that the lattice is indeed loaded if no execeptions are raised.
        - assert that the default control system is indeed cothread and that it
           is loaded onto the lattice correctly.
    """
    assert bool(load('VMX'))
    assert isinstance(load('VMX')._cs, pytac.cothread_cs.CothreadControlSystem)


def test_import_fail_raises_LatticeException(Travis_CI_compatibility,
                                             mock_cs_raises_ImportError):
    """In this test we:
        - check that load corectly fails if cothread cannot be imported.
        - check that when the import of the CothreadControlSystem fails the
           ImportError raised is replaced with a LatticeException.
    """
    with patch('pytac.cothread_cs.CothreadControlSystem',
               mock_cs_raises_ImportError):
        with pytest.raises(LatticeException):
            load('VMX')


def test_cothread_nonexistent_pv(Travis_CI_compatibility):
    """Use the logic we built into our mock cothread control system to test that
        the control system acts correctly if the PV does not exist.
    """
    cs = make_control_system('cothread')
    assert cs.get_single('not_a_PV') is None
    assert cs.get_multiple(['not_a_PV_1', 'not_a_PV_2']) == [None, None]
    cs.set_single('not_a_PV', 0)
    cs.set_multiple(['not_a_PV_1', 'not_a_PV_2'], [0, 0])


def test_caproto_nonexistent_pv(Travis_CI_compatibility):
    cs = make_control_system('caproto')
    assert cs.get_single('not_a_PV') is None
    assert cs.get_multiple(['not_a_PV_1', 'not_a_PV_2']) == [None, None]
    cs.set_single('not_a_PV', 0)
    cs.set_multiple(['not_a_PV_1', 'not_a_PV_2'], [0, 0])


def test_pyepics_failed_connect(Travis_CI_compatibility):
    """Use the logic we built into our mock pyepics control system to test that
        the control system acts correctly if the PV does not exist.
    """
    cs = make_control_system('pyepics')
    assert cs.get_single('not_a_PV') is None
    assert cs.get_multiple(['not_a_PV_1', 'not_a_PV_2']) == [None, None]
    cs.set_single('not_a_PV', 0)
    cs.set_multiple(['not_a_PV_1', 'not_a_PV_2'], [0, 0])


@pytest.mark.parametrize('cs', ['cothread', 'caproto', 'pyepics'])
def test_control_system_raises_ValueError(Travis_CI_compatibility, cs):
    """Test that all the control systems raise errors correctly.
    """
    control_system = make_control_system(cs)
    with pytest.raises(ValueError):
        control_system.get_multiple('not_a_list')
    with pytest.raises(ValueError):
        control_system.set_multiple('not_a_list', [DUMMY_VALUE_1])
    with pytest.raises(ValueError):
        control_system.set_multiple(['PV_1'], [])
    with pytest.raises(ValueError):
        control_system.set_multiple(['PV_1'], [DUMMY_VALUE_1, DUMMY_VALUE_2])


@pytest.mark.parametrize('cs', ['cothread', 'caproto', 'pyepics'])
def test_all_control_system_methods(Travis_CI_compatibility, cs):
    """Test that all control systems call all of their methods correctly.
    """
    control_system = make_control_system(cs)
    assert control_system.get_single('PV_1') == DUMMY_VALUE_1
    assert control_system.get_multiple(['PV_1', 'PV_2']) == [DUMMY_VALUE_1,
                                                             DUMMY_VALUE_2]
    control_system.set_single('PV_1', DUMMY_VALUE_1)
    control_system.set_multiple(['PV_1', 'PV_2'], [DUMMY_VALUE_1,
                                                   DUMMY_VALUE_2])
