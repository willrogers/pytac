import sys
import pytac
import pytest
from mock import patch
from types import ModuleType
from pytac.load_csv import load
from pytac.exceptions import LatticeException


@pytest.fixture(scope="session")
def Travis_CI_compatibility():
    """Travis CI cannot import cothread so we must create a mock of cothread and
        catools (the module that pytac imports from cothread), including the
        functions that pytac explicitly imports (caget and caput).
    """
    class catools(object):
        def caget():
            pass

        def caput():
            pass

        def ca_nothing():
            pass

    cothread = ModuleType('cothread')
    cothread.catools = catools
    sys.modules['cothread'] = cothread
    sys.modules['cothread.catools'] = catools


@pytest.fixture(scope="session")
def mock_cs_raises_ImportError():
    """We create a mock control system to replace CothreadControlSystem, so that
        we can check that when it raises an ImportError load_csv.load catches it
        and raises a LatticeException instead.
    N.B. Our new CothreadControlSystem is nested inside a fixture so it can be
     patched into pytac.cothread_cs to replace the existing
     CothreadControlSystem class. The new CothreadControlSystem created here is
     a function not a class (like the original) to prevent it from raising the
     ImportError when the code is compiled.
    """
    def CothreadControlSystem():
        raise ImportError
    return CothreadControlSystem


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


def test_elements_loaded(lattice):
    assert len(lattice) == 4
    assert len(lattice.get_elements('drift')) == 2
    assert len(lattice.get_elements('no_family')) == 0
    assert lattice.get_length() == 2.6


def test_element_details_loaded(lattice):
    quad = lattice.get_elements('quad')[0]
    assert quad.cell == 1
    assert quad.s == 1.0
    assert quad.index == 2


def test_devices_loaded(lattice):
    quads = lattice.get_elements('quad')
    assert len(quads) == 1
    assert quads[0].get_pv_name(field='b1', handle='readback') == 'Q1:RB'
    assert quads[0].get_pv_name(field='b1', handle='setpoint') == 'Q1:SP'


def test_families_loaded(lattice):
    assert lattice.get_all_families() == set(['drift', 'sext', 'quad',
                                              'ds', 'qf', 'qs', 'sd'])
    assert lattice.get_elements('quad')[0].families == set(('quad', 'qf', 'qs'))
