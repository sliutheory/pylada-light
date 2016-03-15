###############################
#  This file is part of PyLaDa.
#
#  Copyright (C) 2013 National Renewable Energy Lab
#
#  PyLaDa is a high throughput computational platform for Physics. It aims to make it easier to
#  submit large numbers of jobs on supercomputers. It provides a python interface to physical input,
#  such as crystal structures, as well as to a number of DFT (VASP, CRYSTAL) and atomic potential
#  programs. It is able to organise and launch computational jobs on PBS and SLURM.
#
#  PyLaDa is free software: you can redistribute it and/or modify it under the terms of the GNU
#  General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  PyLaDa is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
#  Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with PyLaDa.  If not, see
#  <http://www.gnu.org/licenses/>.
###############################

# -*- coding: utf-8 -*-
""" Reads and writes structure to and from espresso input """
__docformat__ = "restructuredtext en"
__all__ = ['read_structure', 'write_structure']

from pylada import logger
logger = logger.getChild('espresso')
""" Logger for espresso """


def read_structure(filename):
    """ Reads crystal structure from Espresso input """
    from numpy import dot, array
    from io import StringIO
    from os.path import expanduser, expandvars, abspath
    from ..crystal import Structure
    from .. import error
    from . import Namelist
    from .card import read_cards
    namelists = Namelist()
    namelists.read(filename)
    cards = read_cards(filename)
    if 'atomic_positions' not in set([u.name for u in cards]):
        raise error.RuntimeError("Card ATOMIC_POSITIONS is missing from input")
    positions = [u for u in cards if u.name == 'atomic_positions'][0]
    if 'cell_parameters' not in set([u.name for u in cards]):
        cell_parameters = None
        if namelists.system.ibrav == 0:
            raise RuntimeError("Card CELL_PARAMETERS is missing")
    else:
        cell_parameters = [u for u in cards if u.name == 'cell_parameters'][0]

    cell, scale = read_cell_and_scale(namelists.system, cell_parameters)
    result = Structure()

    result.cell = cell
    result.scale = scale
    for line in positions.value.rstrip().lstrip().split('\n'):
        line = line.split()
        result.add_atom(array(line[1:4], dtype='float64'), line[0])

    if positions.subtitle == 'bohr':
        factor = float(bohr_radius.rescale(result.scale))
        for atom in result:
            atom.pos *= factor
    elif positions.subtitle == 'angstrom':
        factor = float(angstrom.rescale(result.scale))
        for atom in result:
            atom.pos *= factor
    elif positions.subtitle == 'crystal':
        for atom in result:
            atom.pos = dot(result.cell, atom.pos)
    elif positions.subtitle == 'crystal_sg':
        raise RuntimeError("Reading symmetric atomic positions is not implemented")

    return result


def read_cell_and_scale(system, cell_parameters):
    from numpy import identity, array

    if system.ibrav == 0:
        return _read_free(system, cell_parameters)
    elif system.ibrav == 1:
        return identity(3, dtype='float64'), _get_scale(system)
    elif system.ibrav == 2:
        return 0.5 * array([[-1, 0, 1], [0, 1, 1], [-1, 1, 0]], dtype='float64').transpose(),\
            _get_scale(system)
    elif system.ibrav == 3:
        return 0.5 * array([[1, 1, 1], [-1, 1, 1], [-1, -1, 1]], dtype='float64').transpose(),\
            _get_scale(system)
    elif system.ibrav == 4:
        return _read_hexa(system)
    elif system.ibrav == 5:
        logger.warning('ibrav=5 has not been tested')
        return _read_trig(system)
    elif system.ibrav == -5:
        logger.warning('ibrav=-5 has not been tested')
        return _read_mtrig(system)
    else:
        NotImplementedError("Reading from this kind of lattice has not been implemented")


def _get_scale(system):
    from quantities import bohr_radius, angstrom
    celldm = getattr(system, 'celldm', None)
    if celldm == 'A':
        return angstrom
    elif celldm is not None and len(celldm) > 0:
        return celldm[0] * bohr_radius
    elif hasattr(system, 'A'):
        return system.a * angstrom
    return bohr_radius


def _get_params(system):
    """ Returns celldim(2-6), whatever the input may be """
    from numpy import zeros
    from quantities import bohr_radius, angstrom
    result = zeros(5, dtype='float64')
    celldim = getattr(system, 'celldm', None)
    if celldim is not None:
        result[:len(celldim) - 1] = celldim[1:]
        return result
    scale = _get_scale(system)
    result[0] = float((getattr(system, 'b', 0) * angstrom / scale).simplified)
    result[1] = float((getattr(system, 'c', 0) * angstrom / scale).simplified)
    result[2] = getattr(system, 'cosab', 0)
    result[3] = getattr(system, 'cosac', 0)
    result[4] = getattr(system, 'cosbc', 0)
    return result


def _read_free(system, cell_parameters):
    """ Read free cell """
    from numpy import array
    from quantities import bohr_radius, angstrom
    celldm = getattr(system, 'celldm', None)
    scale = _get_scale(system)
    if cell_parameters.subtitle is not None:
        if cell_parameters.subtitle == 'bohr':
            scale = bohr_radius
        elif cell_parameters.subtitle == 'angstrom':
            scale = angstrom
    cell = array([u.split() for u in cell_parameters.value.rstrip().lstrip().split('\n')],
                 dtype='float64').transpose()
    return cell, scale


def _read_hexa(system):
    from quantities import angstrom
    from numpy import sqrt, array
    scale = _get_scale(system)
    c_over_a = _get_params(system)[1]
    cell = array([[1, 0, 0], [-0.5, sqrt(3.) / 2., 0], [0, 0, c_over_a]], dtype='float64')
    return cell.transpose(), scale


def _read_trig(system):
    from quantities import angstrom
    from numpy import sqrt, array
    scale = _get_scale(system)
    c = _get_params(system)[2]
    tx, ty, tz = sqrt((1.-c)/2.), sqrt((1.-c)/6.), sqrt((1+2*c)/3.)
    cell = array([[tx, -ty, tz], [0, 2. * ty, tz], [-tx, -ty, tz]], dtype='float64')
    return cell.transpose(), scale


def _read_mtrig(system):
    from quantities import angstrom
    from numpy import sqrt, array
    scale = _get_scale(system)
    c = _get_params(system)[2]
    tx, ty, tz = sqrt((1.-c)/2.), sqrt((1.-c)/6.), sqrt((1+2*c)/3.)
    u, v = tz - 2*sqrt(2)*ty,  tz + sqrt(2)*ty
    cell = array([[u, v, v], [v, u, v], [v, v, u]], dtype='float64')
    return cell.transpose(), scale / sqrt(3.)


def write_structure(structure, stream):
    pass