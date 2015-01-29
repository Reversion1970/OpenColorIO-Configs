#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implements support for *Panasonic* colorspaces conversions and transfer functions.
"""

import array
import os

import PyOpenColorIO as ocio

import aces_ocio.generate_lut as genlut
from aces_ocio.utilities import ColorSpace

__author__ = 'ACES Developers'
__copyright__ = 'Copyright (C) 2014 - 2015 - ACES Developers'
__license__ = ''
__maintainer__ = 'ACES Developers'
__email__ = 'aces@oscars.org'
__status__ = 'Production'

__all__ = ['create_v_log',
           'create_colorspaces']


def create_v_log(gamut,
                 transfer_function,
                 name,
                 lut_directory,
                 lut_resolution_1d,
                 aliases):
    """
    Object description.

    Panasonic V-Log to ACES.

    Parameters
    ----------
    parameter : type
        Parameter description.

    Returns
    -------
    type
         Return value description.
    """

    name = '%s - %s' % (transfer_function, gamut)
    if transfer_function == '':
        name = 'Linear - %s' % gamut
    if gamut == '':
        name = '%s' % transfer_function

    cs = ColorSpace(name)
    cs.description = name
    cs.aliases = aliases
    cs.equality_group = ''
    cs.family = 'Panasonic'
    cs.is_data = False

    # A linear space needs allocation variables
    if transfer_function == '':
        cs.allocation_type = ocio.Constants.ALLOCATION_LG2
        cs.allocation_vars = [-8, 5, 0.00390625]

    def v_log_to_linear(x):
        cutInv = 0.181
        b = 0.00873
        c = 0.241514
        d = 0.598206

        if (x <= cutInv):
            return (x - 0.125) / 5.6
        else:
            return pow(10, (x-d)/c) - b

    cs.to_reference_transforms = []

    if transfer_function == 'V-Log':
        data = array.array('f', '\0' * lut_resolution_1d * 4)
        for c in range(lut_resolution_1d):
            data[c] = v_log_to_linear(float(c) / (lut_resolution_1d - 1))

        lut = '%s_to_linear.spi1d' % transfer_function
        genlut.write_SPI_1d(
            os.path.join(lut_directory, lut),
            0.0,
            1.0,
            data,
            lut_resolution_1d,
            1)

        cs.to_reference_transforms.append({
            'type': 'lutFile',
            'path': lut,
            'interpolation': 'linear',
            'direction': 'forward'})

    if gamut == 'V-Gamut':
        cs.to_reference_transforms.append({
            'type': 'matrix',
            'matrix': [ 0.724382758,  0.166748484,  0.108497411, 0.0,
                        0.021354009,  0.985138372, -0.006319092, 0.0,
                       -0.009234278, -0.00104295,   1.010272625, 0.0,
                        0, 0, 0, 1.0],
            'direction': 'forward'})

    cs.from_reference_transforms = []
    return cs


def create_colorspaces(lut_directory, lut_resolution_1d):
    """
    Generates the colorspace conversions.

    Parameters
    ----------
    parameter : type
        Parameter description.

    Returns
    -------
    type
         Return value description.
    """

    colorspaces = []

    # Full conversion
    v_log_1 = create_v_log(
        'V-Gamut',
        'V-Log',
        'V-Log',
        lut_directory,
        lut_resolution_1d,
        ["vlog_vgamut"])
    colorspaces.append(v_log_1)

    # Linearization Only
    v_log_2 = create_v_log(
        '',
        'V-Log',
        'V-Log',
        lut_directory,
        lut_resolution_1d,
        ["crv_vlog"])
    colorspaces.append(v_log_2)

    # Primaries Only
    v_log_3 = create_v_log(
        'V-Gamut',
        '',
        'V-Log',
        lut_directory,
        lut_resolution_1d,
        ["lin_vgamut"])
    colorspaces.append(v_log_3)

    return colorspaces