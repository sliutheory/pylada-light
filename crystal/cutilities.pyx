import numpy as np
cimport numpy as np

cdef extern from "crystal/types.h" namespace "pylada::types":
    ctypedef int t_int
    ctypedef double t_real

cdef extern from "crystal/cutilities.h" namespace "pylada":
    void snf "pylada::smith_normal_form" (t_int *_S, t_int *_L, t_int *_R) except +
    void c_gruber "pylada::gruber"(t_real *out, t_real *_in, size_t itermax, t_real _tol) except +

def smith_normal_form(np.ndarray cell not None):
    """ Computes smith normal form on input matrix """
    from numpy.linalg import det
    from numpy import asarray, transpose
    if cell.ndim == 2 and cell.shape[0] != 3 and cell.shape[1] != 3:
        raise ValueError("Can only compute Smith normal form of 3x3 matrix")
    if det(cell) == 0:
        raise ValueError("Input cell is singular")

    left = np.identity(3, dtype='intc')
    right = np.identity(3, dtype='intc')

    S = asarray(cell, dtype='intc', order='F')

    cdef:
        long L_data = left.ctypes.data
        long S_data = S.ctypes.data
        long R_data = right.ctypes.data


    snf(<t_int*>S_data, <t_int*>L_data, <t_int*>R_data)
    return S, transpose(left), transpose(right)

def gruber(np.ndarray cell not None, size_t itermax = 0, double tolerance = 1e-12):
    """ Determines Gruber cell of an input cell

        The Gruber cell is an optimal parameterization of a lattice, eg shortest
        cell-vectors and angles closest to 90 degrees.

        :param cell:
            The input lattice cell-vectors.
        :type cell:
            numpy 3x3 array
        :param int itermax:
            Maximum number of iterations. Defaults to 0, ie infinit number of iterations.
        :param float tolerance:
            Tolerance parameter when comparing real numbers. Defaults to Pylada internals.
        :returns: An equivalent standardized cell.
        :raises ValueError: If the input matrix is singular.
        :raises RuntimeError: If the maximum number of iterations is reached.
    """
    from numpy.linalg import det
    from numpy import require, zeros, abs, transpose

    if cell.ndim == 2 and cell.shape[0] != 3 and cell.shape[1] != 3:
        raise ValueError("Can only compute Smith normal form of 3x3 matrix")
    if abs(det(cell)) < 1e-12:
        raise ValueError("Input cell is singular");

    cell = require(cell, dtype='float64', requirements=['F_CONTIGUOUS'])

    result = zeros((3, 3), dtype='float64')
    cdef:
        long c_result = result.ctypes.data
        long c_cell = cell.ctypes.data

    c_gruber(<t_real*>c_result, <t_real*>c_cell, itermax, tolerance)
    return transpose(result)

