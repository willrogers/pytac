""" This file tests the entire loading of the DLS machine from the CSV
    files in the data directory. These are more like integration tests,
    and allows us to check that the pytac setup is working correctly.
"""
import pytac
import pytest
import re
import mock
import numpy


EPS = 1e-8


def get_lattice(ring_mode):
    """ Load the entire lattice from the data directory. """
    lattice = pytac.load_csv.load(ring_mode, mock.MagicMock())
    return lattice


def test_load_lattice_using_default_dir():
    lat = pytac.load_csv.load('VMX', mock.MagicMock())
    assert len(lat) == 2143


@pytest.mark.parametrize(
    'ring_mode,n_elements,length', [
        ('VMX', 2143, 561.571),
        ('DIAD', 2145, 561.571)
    ])
def test_load_lattice(ring_mode, n_elements, length):
    lattice = get_lattice(ring_mode)
    assert len(lattice) == n_elements
    assert lattice.name == ring_mode
    assert (lattice.get_length() - length) < EPS


@pytest.mark.parametrize(
    'ring_mode,n_bpms', [
        ('VMX', 173),
        ('DIAD', 173)
    ])
def test_get_pv_names(ring_mode, n_bpms):
    lattice = get_lattice(ring_mode)
    bpm_x_pvs = lattice.get_pv_names('BPM', 'x', handle='readback')
    assert len(bpm_x_pvs) == n_bpms
    for pv in bpm_x_pvs:
        assert re.match('SR.*BPM.*X', pv)
    x_sofb_enabled_pvs = lattice.get_pv_names('BPM', 'x_sofb_disabled', handle='readback')
    assert len(bpm_x_pvs) == n_bpms
    for pv in x_sofb_enabled_pvs:
        assert re.match('SR.*HBPM.*SLOW:DISABLED', pv)


@pytest.mark.parametrize(
    'ring_mode,n_bpms', [
        ('VMX', 173),
        ('DIAD', 173)
    ])
def test_load_bpms(ring_mode, n_bpms):
    lattice = get_lattice(ring_mode)
    bpms = lattice.get_elements('BPM')
    bpm_fields = {
        'x', 'y', 'enabled', 'x_fofb_disabled', 'x_sofb_disabled',
        'y_fofb_disabled', 'y_sofb_disabled'
    }
    for bpm in bpms:
        assert set(bpm.get_fields()) == bpm_fields
        assert re.match('SR.*BPM.*X', bpm.get_pv_name('x', pytac.RB))
        with pytest.raises(pytac.device.HandleException):
            bpm.get_pv_name('x', pytac.SP)
    assert len(bpms) == n_bpms
    assert bpms[0].cell == 1
    assert bpms[-1].cell == 24


@pytest.mark.parametrize(
    'ring_mode,n_drifts', [
        ('VMX', 1308),
        ('DIAD', 1311)
    ])
def test_load_drift_elements(ring_mode, n_drifts):
    lattice = get_lattice(ring_mode)
    drifts = lattice.get_elements('DRIFT')
    assert len(drifts) == n_drifts


@pytest.mark.parametrize(
    'ring_mode,n_quads', [
        ('VMX', 248),
        ('DIAD', 248)
    ])
def test_load_quadrupoles(ring_mode, n_quads):
    lattice = get_lattice(ring_mode)
    quads = lattice.get_elements('QUAD')
    assert len(quads) == n_quads
    for quad in quads:
        assert set(quad.get_fields()) == set(('b1',))
        device = quad.get_device('b1')
        assert re.match('SR.*Q.*:I', device.rb_pv)
        assert re.match('SR.*Q.*:SETI', device.sp_pv)


@pytest.mark.parametrize(
    'ring_mode,n_q1b,n_q1d', [
        ('VMX', 34, 12),
        ('DIAD', 34, 12)
    ])
def test_load_quad_family(ring_mode, n_q1b, n_q1d):
    lattice = get_lattice(ring_mode)
    q1b = lattice.get_elements('Q1B')
    assert len(q1b) == n_q1b
    q1d = lattice.get_elements('Q1D')
    assert len(q1d) == n_q1d


@pytest.mark.parametrize(
    'ring_mode,n_correctors', [
        ('VMX', 173),
        ('DIAD', 172)
    ])
def test_load_correctors(ring_mode, n_correctors):
    lattice = get_lattice(ring_mode)
    hcm = lattice.get_elements('HSTR')
    vcm = lattice.get_elements('VSTR')
    assert len(hcm) == n_correctors
    assert len(vcm) == n_correctors
    for element in hcm:
        # each one has b0, h_fofb_disabled and h_sofb_disabled fields.
        assert {'b0', 'h_sofb_disabled', 'h_fofb_disabled'}.issubset(element.get_fields())
    for element in vcm:
        # each one has a0, v_fofb_disabled and v_sofb_disabled fields.
        assert {'a0', 'v_sofb_disabled', 'v_fofb_disabled'}.issubset(element.get_fields())


@pytest.mark.parametrize(
    'ring_mode,n_squads', [
        ('VMX', 98),
        ('DIAD', 98)
    ])
def test_load_squads(ring_mode, n_squads):
    lattice = get_lattice(ring_mode)
    squads = lattice.get_elements('SQUAD')
    assert len(squads) == n_squads
    for squad in squads:
        assert 'a1' in squad.get_fields()
        device = squad.get_device('a1')
        assert re.match('SR.*SQ.*:I', device.rb_pv)
        assert re.match('SR.*SQ.*:SETI', device.sp_pv)


@pytest.mark.parametrize(
    'ring_mode', ('VMX', 'DIAD')
)
def test_cell(ring_mode):
    lattice = get_lattice(ring_mode)
    # there are squads in every cell
    sq = lattice.get_elements('SQUAD')
    assert sq[0].cell == 1
    assert sq[-1].cell == 24


@pytest.mark.parametrize('ring_mode', ('VMX', 'DIAD'))
@pytest.mark.parametrize('field', ('x', 'y'))
def test_bpm_unitconv(ring_mode, field):
    lattice = get_lattice(ring_mode)
    bpm = lattice.get_elements('BPM')[0]
    uc = bpm._uc[field]

    assert uc.eng_to_phys(1) == 0.001
    assert uc.phys_to_eng(2) == 2000


def test_quad_unitconv():
    # From MML: hw2physics('Q1D', 'Monitor', 70, [1])
    lattice = get_lattice('VMX')
    q1d = lattice.get_elements('Q1D')
    lattice._energy = 3000
    for q in q1d:
        uc = q._uc['b1']
        numpy.testing.assert_allclose(uc.eng_to_phys(70), -0.691334652255027)
        numpy.testing.assert_allclose(uc.phys_to_eng(-0.691334652255027), 70)


def test_quad_unitconv_raise_exception():
    uc = pytac.units.PchipUnitConv([50.0, 100.0, 180.0], [-4.95, -9.85, -17.56])
    with pytest.raises(pytac.units.UnitsException):
        uc.phys_to_eng(-0.7)


def test_quad_unitconv_known_failing_test():
    LAT_ENERGY = 3000

    uc = pytac.units.PchipUnitConv([50.0, 100.0, 180.0], [-4.95, -9.85, -17.56])
    uc._post_eng_to_phys = pytac.load_csv.get_div_rigidity(LAT_ENERGY)
    uc._pre_phys_to_eng = pytac.load_csv.get_mult_rigidity(LAT_ENERGY)
    numpy.testing.assert_allclose(uc.eng_to_phys(70), -0.69133465)
    numpy.testing.assert_allclose(uc.phys_to_eng(-0.7), 70.8834284954)
