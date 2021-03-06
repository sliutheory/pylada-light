###############################
#  This file is part of PyLaDa.
#
#  Copyright (C) 2013 National Renewable Energy Lab
#
#  PyLaDa is a high throughput computational platform for Physics. It aims to
#  make it easier to submit large numbers of jobs on supercomputers. It
#  provides a python interface to physical input, such as crystal structures,
#  as well as to a number of DFT (VASP, CRYSTAL) and atomic potential programs.
#  It is able to organise and launch computational jobs on PBS and SLURM.
#
#  PyLaDa is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  PyLaDa is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#  FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
#  details.
#
#  You should have received a copy of the GNU General Public License along with
#  PyLaDa.  If not, see <http://www.gnu.org/licenses/>.
###############################

add_cython_target(defects_cython _defects.pyx CXX ${PYVER})
add_library(_defects MODULE ${defects_cython} third_order.cc)
python_extension_module(_defects)
target_link_libraries(_defects Eigen3::Eigen)
target_include_directories(
    _defects PRIVATE
    "${PY_HEADER_DIR}" "${NumPy_INCLUDE_DIRS}" "${PYTHON_INCLUDE_DIR}"
)
install(TARGETS _defects LIBRARY DESTINATION ${PY_ROOT_DIR}/crystal/defects)
