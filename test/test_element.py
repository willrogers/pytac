import pytac.element
import pytac.device
import pytac.model
from pytac.units import PolyUnitConv
import pytest
import mock
import pytac
from constants import PREFIX, RB_PV, SP_PV


DUMMY_VALUE_1 = 40.0
DUMMY_VALUE_2 = 4.7
DUMMY_VALUE_3 = -6

mock_uc = PolyUnitConv([2, 0])


@pytest.fixture
def test_element(uc=mock_uc):
    mock_cs = mock.MagicMock()
    mock_cs.get.return_value = DUMMY_VALUE_1

    element = pytac.element.Element('dummy', 1.0, 'Quad')
    device1 = pytac.device.Device(PREFIX, mock_cs, True, RB_PV, SP_PV)
    device2 = pytac.device.Device(PREFIX, mock_cs, True, SP_PV, RB_PV)

    device_model = pytac.model.DeviceModel()
    element.set_model(device_model, pytac.LIVE)
    element.add_device('x', device1, uc)
    element.add_device('y', device2, uc)

    mock_model = mock.MagicMock()
    mock_model.get_value.return_value = DUMMY_VALUE_2
    mock_model.units = pytac.PHYS
    element.set_model(mock_model, pytac.SIM)

    return element


def test_create_element():
    e = pytac.element.Element('bpm1', 6.0, 'bpm')
    e.add_to_family('BPM')
    assert 'BPM' in e.families
    assert e.length == 6.0


def test_add_element_to_family():
    e = pytac.element.Element('dummy', 6.0, 'Quad')
    e.add_to_family('fam')
    assert 'fam' in e.families


def test_get_device_raises_KeyError_if_device_not_present(test_element):
    with pytest.raises(KeyError):
        test_element.get_device('not-a-device')


def test_get_unitconv_returns_unitconv_object():
    dummy_uc = mock.MagicMock()
    element = test_element(dummy_uc)
    assert element.get_unitconv('x') == dummy_uc
    assert element.get_unitconv('y') == dummy_uc


def test_get_unitconv_raises_KeyError_if_device_not_present(test_element):
    with pytest.raises(KeyError):
        test_element.get_unitconv('not-a-device')


def test_get_value_uses_cs_if_model_live(test_element):
    test_element.get_value('x', handle=pytac.SP, model=pytac.LIVE)
    test_element.get_device('x')._cs.get.assert_called_with(SP_PV)
    test_element.get_value('x', handle=pytac.RB, model=pytac.LIVE)
    test_element.get_device('x')._cs.get.assert_called_with(RB_PV)


def test_get_value_uses_uc_if_necessary_for_cs_call(test_element):
    assert test_element.get_value('x', handle=pytac.SP, units=pytac.PHYS,
                                  model=pytac.LIVE) == (DUMMY_VALUE_1 * 2)
    test_element.get_device('x')._cs.get.assert_called_with(SP_PV)


def test_get_value_uses_uc_if_necessary_for_model_call(test_element):
    print(test_element._models)
    assert test_element.get_value('x', handle=pytac.SP, units=pytac.ENG,
                                  model=pytac.SIM) == (DUMMY_VALUE_2 / 2)
    test_element._models[pytac.SIM].get_value.assert_called_with('x', pytac.SP)


@pytest.mark.parametrize('pv_type', ['readback', 'setpoint'])
def test_get_pv_name(pv_type, test_element):
    assert isinstance(test_element.get_pv_name('x', pv_type), str)
    assert isinstance(test_element.get_pv_name('y', pv_type), str)


def test_set_value_eng(test_element):
    test_element.set_value('x', DUMMY_VALUE_2)
    # No conversion needed
    test_element.get_device('x')._cs.put.assert_called_with(SP_PV,
                                                            DUMMY_VALUE_2)


def test_set_value_phys(test_element):
    test_element.set_value('x', DUMMY_VALUE_2, units=pytac.PHYS)
    # Conversion fron physics to engineering units
    test_element.get_device('x')._cs.put.assert_called_with(SP_PV,
                                                            (DUMMY_VALUE_2 / 2))


def test_set_value_incorrect_field(test_element):
    with pytest.raises(pytac.device.DeviceException):
        test_element.set_value('non_existent', 40.0)


def test_get_pv_exceptions(test_element):
    with pytest.raises(pytac.device.DeviceException):
        test_element.get_value('setpoint', 'unknown_field')
    with pytest.raises(pytac.device.DeviceException):
        test_element.get_value('unknown_handle', 'y')


def test_identity_conversion():
    uc_id = PolyUnitConv([1, 0])
    element = test_element(uc=uc_id)
    value_physics = element.get_value('x', 'setpoint', pytac.PHYS)
    value_machine = element.get_value('x', 'setpoint', pytac.ENG)
    assert value_machine == DUMMY_VALUE_1
    assert value_physics == 40.0


def test_get_fields(test_element):
    assert set(test_element.get_fields()) == set(['y', 'x'])


def test_element_representation(test_element):
    s = str(test_element)
    assert test_element.name in s
    assert str(test_element.length) in s
    for f in test_element.families:
        assert f in s
