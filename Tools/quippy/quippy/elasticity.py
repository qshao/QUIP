# HQ XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# HQ X
# HQ X   quippy: Python interface to QUIP atomistic simulation library
# HQ X
# HQ X   Copyright James Kermode 2010
# HQ X
# HQ X   These portions of the source code are released under the GNU General
# HQ X   Public License, version 2, http://www.gnu.org/copyleft/gpl.html
# HQ X
# HQ X   If you would like to license the source code under different terms,
# HQ X   please contact James Kermode, james.kermode@gmail.com
# HQ X
# HQ X   When using this software, please cite the following reference:
# HQ X
# HQ X   http://www.jrkermode.co.uk/quippy
# HQ X
# HQ XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

from quippy import available_modules
if 'scipy' in available_modules:
    from scipy import stats
from farray import *
from quippy.atoms import Atoms
from quippy import _elasticity
from quippy._elasticity import *
import numpy as np
__all__ = _elasticity.__all__ + ['strain_matrix', 'stress_matrix', 'strain_vector',
                                 'stress_vector', 'generate_strained_configs',
                                 'calc_stress', 'fit_elastic_constants',
                                 'elastic_constants', 'atomic_strain',
                                 'elastic_fields_fortran', 'elastic_fields',
                                 'AtomResolvedStressField',
                                 'transform_elasticity', 'rayleigh_wave_speed']

def strain_matrix(strain_vector):
    """
    Form a 3x3 strain matrix from a 6 component vector in Voigt notation
    """
    e1, e2, e3, e4, e5, e6 = strain_vector
    return farray([[1.0+e1, 0.5*e6, 0.5*e5],
                   [0.5*e6, 1.0+e2, 0.5*e4],
                   [0.5*e5, 0.5*e4, 1.0+e3]])

def stress_matrix(stress_vector):
    """
    Form a 3x3 stress matrix from a 6 component vector in Voigt notation
    """
    s1, s2, s3, s4, s5, s6 = stress_vector
    return farray([[s1, s6, s5],
                   [s6, s2, s4],
                   [s5, s4, s3]])

def strain_vector(strain_matrix):
    """
    Form a 6 component strain vector in Voight notation from a 3x3 matrix
    """

    return farray([strain_matrix[1,1] - 1.0,
                   strain_matrix[2,2] - 1.0,
                   strain_matrix[3,3] - 1.0,
                   2.0*strain_matrix[2,3],
                   2.0*strain_matrix[1,3],
                   2.0*strain_matrix[1,2]])

def stress_vector(stress_matrix):
    """
    Form a 6 component stress vector in Voight notation from a 3x3 matrix
    """
    return farray([stress_matrix[1,1],
                   stress_matrix[2,2],
                   stress_matrix[3,3],
                   stress_matrix[2,3],
                   stress_matrix[1,3],
                   stress_matrix[1,2]])



Cij_symmetry = {
   'cubic':           farray([[1, 7, 7, 0, 0, 0],
                              [7, 1, 7, 0, 0, 0],
                              [7, 7, 1, 0, 0, 0],
                              [0, 0, 0, 4, 0, 0],
                              [0, 0, 0, 0, 4, 0],
                              [0, 0, 0, 0, 0, 4]]),

   'trigonal_high':   farray([[1, 7, 8, 9, 10, 0],
                              [7, 1, 8, 0,-9, 0],
                              [8, 8, 3, 0, 0, 0],
                              [9, -9, 0, 4, 0, 0],
                              [10, 0, 0, 0, 4, 0],
                              [0, 0, 0, 0, 0, 6]]),

   'trigonal_low':    farray([[1,  7,  8,  9,  10,  0 ],
                              [7,  1,  8, -9, -10,  0 ],
                              [8,  8,  3,  0,   0,  0 ],
                              [9, -9,  0,  4,   0, -10],
                              [10,-10, 0,  0,   4,  9 ],
                              [0,  0,  0, -10 , 9,  6 ]]),

   'tetragonal_high': farray([[1, 7, 8, 0, 0, 0],
                              [7, 1, 8, 0, 0, 0],
                              [8, 8, 3, 0, 0, 0],
                              [0, 0, 0, 4, 0, 0],
                              [0, 0, 0, 0, 4, 0],
                              [0, 0, 0, 0, 0, 6]]),

   'tetragonal_low':  farray([[1, 7, 8, 0, 0, 11],
                              [7, 1, 8, 0, 0, -11],
                              [8, 8, 3, 0, 0, 0],
                              [0, 0, 0, 4, 0, 0],
                              [0, 0, 0, 0, 4, 0],
                              [11, -11, 0, 0, 0, 6]]),

   'orthorhombic':    farray([[ 1,  7,  8,  0,  0,  0],
                              [ 7,  2, 12,  0,  0,  0],
                              [ 8, 12,  3,  0,  0,  0],
                              [ 0,  0,  0,  4,  0,  0],
                              [ 0,  0,  0,  0,  5,  0],
                              [ 0,  0,  0,  0,  0,  6]]),

   'monoclinic':      farray([[ 1,  7,  8,  0,  10,  0],
                              [ 7,  2, 12,  0, 14,  0],
                              [ 8, 12,  3,  0, 17,  0],
                              [ 0,  0,  0,  4,  0,  20],
                              [10, 14, 17,  0,  5,  0],
                              [ 0,  0,  0, 20,  0,  6]]),

   'triclinic':       farray([[ 1,  7,  8,  9,  10, 11],
                              [ 7,  2, 12,  13, 14, 15],
                              [ 8, 12,  3,  16, 17, 18],
                              [ 9, 13, 16,  4,  19, 20],
                              [10, 14, 17, 19,  5,  21],
                              [11, 15, 18, 20,  21, 6 ]]),
   }


strain_patterns = {

   'cubic': [
      # strain pattern e1+e4, yields C11, C21, C31 and C44, then C12 is average of C21 and C31
      [ farray([1,0,0,1,0,0]), [(1,1), (2,1), (3,1), (4,4)]]
   ],

   'trigonal_high': [
      # strain pattern e3 yield C13, C23 and C33
      [ farray([0,0,1,0,0,0]), [(1,3), (2,3), (3,3)]],

      # strain pattern e1+e4 yields C11 C21 C31 and C44
      [ farray([1,0,0,1,0,0]), [(1,1), (2,1), (3,1), (4,4)]],

      # strain pattern e1 yields C11 C21 C31 C41 C51
      [ farray([1,0,0,0,0,0]), [(1,1), (2,1), (3,1), (4,1), (5,1)]],

      # strain pattern e3+e4
      [ farray([0,0,1,1,0,0]), [(3,3), (4,4)]]

   ],

   'trigonal_low': [
     # strain pattern e1, yields C11, C21, C31, C41, C51
     [ farray([1,0,0,0,0,0]), [(1,1), (2,1), (3,1), (4,1), (5,1)]],

     # strain pattern e3 + e4, yields C33, C44
     [ farray([0,0,1,1,0,0]), [(3,3), (4,4)] ],

     [ farray([0,0,0,0,0,1]), [(6,6)] ]
   ],

   'tetragonal': [
     # strain pattern e1+e4
     [ farray([1,0,0,1,0,0]), [(1,1), (2,1), (3,1), (6,1), (4,4)] ],

     # strain pattern e3+e6
     [ farray([0,0,1,0,0,1]), [(3,3), (6,6)] ]
   ],

   'orthorhombic': [
      # strain pattern e1+e4
      [ farray([1,0,0,1,0,0]), [(1,1), (2,1), (3,1), (4,4)] ],

      # strain pattern e2+e5
      [ farray([0,1,0,0,1,0]), [(1,2), (2,2), (3,2), (5,5)] ],

      # strain pattern e3+e6
      [ farray([0,0,1,0,0,1]), [(1,3), (2,3), (3,3), (6,6)] ]
   ],

   'monoclinic': [
      # strain pattern e1+e4
      [ farray([1,0,0,1,0,0]), [(1,1), (2,1), (3,1), (4,4), (5,1), (6,4)] ],

      # strain pattern e3+e6
      [ farray([0,0,1,0,0,1]), [(1,3), (2,3), (3,3), (5,3), (4,6), (6,6)] ],

      # strain pattern e2
      [ farray([0,1,0,0,0,0]), [(1,2), (2,2), (3,2), (5,2)] ],

      # strain pattern e5
      [ farray([0,0,0,0,1,0]), [(1,5), (2,5), (3,5), (5,5)] ]
   ],

   'triclinic': [
      [ farray([1,0,0,0,0,0]), [(1,1), (2,1), (3,1), (4,1), (5,1), (6,1)]],
      [ farray([0,1,0,0,0,0]), [(1,2), (2,2), (3,2), (4,2), (5,2), (6,2)]],
      [ farray([0,0,1,0,0,0]), [(1,3), (2,3), (3,3), (4,3), (5,3), (6,3)]],
      [ farray([0,0,0,1,0,0]), [(1,4), (2,4), (3,4), (4,4), (5,4), (6,4)]],
      [ farray([0,0,0,0,1,0]), [(1,5), (2,5), (3,5), (4,5), (5,5), (6,5)]],
      [ farray([0,0,0,0,0,1]), [(1,6), (2,6), (3,6), (4,6), (5,6), (6,6)]],
   ]

   }

Cij_symmetry['hexagonal'] = Cij_symmetry['trigonal_high']
Cij_symmetry[None] = Cij_symmetry['triclinic']

strain_patterns['hexagonal'] = strain_patterns['trigonal_high']
strain_patterns['tetragonal_high'] = strain_patterns['tetragonal_low'] = strain_patterns['tetragonal']
strain_patterns[None] = strain_patterns['triclinic']


def generate_strained_configs(at0, symmetry='triclinic', N_steps=5, delta=1e-2):
    """Generate a sequence of strained configurations"""

    if not symmetry in strain_patterns:
        raise ValueError('Unknown symmetry %s. Valid options are %s' % (symmetry, strain_patterns.keys()))

    for pindex, (pattern, fit_pairs) in fenumerate(strain_patterns[symmetry]):
        for step in frange(N_steps):
            strain = np.where(pattern == 1, delta*(step-(N_steps+1)/2.0), 0.0)
            at = at0.copy()
            T = strain_matrix(strain)
            at.set_lattice(np.dot(T,at.lattice), scale_positions=False)
            at.pos[:] = np.dot(T,at.pos)
            at.params['strain'] = T
            yield at


def calc_stress(configs, pot, relax=False, relax_tol=1e-3, relax_steps=100):
    """Given a sequence of configs, calculate stress on each one"""
    from quippy import GPA
    for at in configs:
        at2 = at.copy()
        at2.set_cutoff(pot.cutoff())
        at2.calc_connect()
        if relax:
            pot.minim(at2, 'cg', relax_tol, relax_steps, do_pos=True, do_lat=False)
        pot.calc(at2, virial=True)
        at2.params['stress'] = -at2.params['virial']*GPA/at2.cell_volume()
        yield at2


# Elastic constant calculation.

# Code adapted from elastics.py script, available from
# http://github.com/djw/elastic-constants
#
# Copyright (c) 2008, Dan Wilson
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the copyright holder nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY DAN WILSON ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL DAN WILSON BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

def fit_elastic_constants(configs, symmetry=None, N_steps=5, verbose=True, graphics=True):
    """Given a sequence of configs with strain and stress parameters, fit elastic constants C_ij"""

    def do_fit(index1, index2, stress, strain, patt):
        if verbose:
            print 'Fitting C_%d%d' % (index1, index2)
            print 'Strain %r' % strain[:,index2]
            print 'Stress %r' % stress[:,index1]

        cijFitted,intercept,r,tt,stderr = stats.linregress(strain[:,index2],stress[:,index1])

        if verbose:
            # print info about the fit
            print     'Cij (gradient)          :    ',cijFitted
            print     'Error in Cij            :    ', stderr
            if abs(r) > 0.9:
                print 'Correlation coefficient :    ',r
            else:
                print 'Correlation coefficient :    ',r, '     <----- WARNING'

        if graphics:
            import pylab
            # position this plot in a 6x6 grid
            sp = pylab.subplot(6,6,6*(index1-1)+index2)
            sp.set_axis_on()

            # change the labels on the axes
            xlabels = sp.get_xticklabels()
            pylab.setp(xlabels,'rotation',90,fontsize=7)
            ylabels = sp.get_yticklabels()
            pylab.setp(ylabels,fontsize=7)

            # colour the plot depending on the strain pattern
            colourDict = {1: '#BAD0EF', 2:'#FFCECE', 3:'#BDF4CB', 4:'#EEF093',5:'#FFA4FF',6:'#75ECFD'}
            sp.set_axis_bgcolor(colourDict[patt])

            # plot the data
            pylab.plot([strain[1,index2],strain[-1,index2]],[cijFitted*strain[1,index2]+intercept,cijFitted*strain[-1,index2]+intercept])
            pylab.plot(list(strain[:,index2]),list(stress[:,index1]),'ro')

        return cijFitted, stderr

    if not symmetry in strain_patterns:
        raise ValueError('Unknown symmetry %s. Valid options are %s' % (symmetry, strain_patterns.keys()))

    # There are 21 independent elastic constants
    Cijs = {}
    Cij_err = {}

    # Construct mapping from (i,j) to index into Cijs in range 1..21
    # (upper triangle only to start with)
    Cij_map = {}
    Cij_map_sym = {}
    for i in frange(6):
        for j in frange(i,6):
            Cij_map[(i,j)] = Cij_symmetry[None][i,j]
            Cij_map_sym[(i,j)] = Cij_symmetry[symmetry][i,j]

    # Reverse mapping, index 1..21 -> tuple (i,j) with i, j in range 1..6
    Cij_rev_map = dict(zip(Cij_map.values(), Cij_map.keys()))

    # Add the lower triangle to Cij_map, e.g. C21 = C12
    for (i1,i2) in Cij_map.keys():
        Cij_map[(i2,i1)] = Cij_map[(i1,i2)]
        Cij_map_sym[(i2,i1)] = Cij_map_sym[(i1,i2)]


    N_pattern = len(strain_patterns[symmetry])
    configs = iter(configs)

    strain = fzeros((N_pattern, N_steps, 6))
    stress = fzeros((N_pattern, N_steps, 6))

    if graphics:
        import pylab
        fig = pylab.figure(num=1, figsize=(9.5,8),facecolor='white')
        fig.clear()
        fig.subplots_adjust(left=0.07,right=0.97,top=0.97,bottom=0.07,wspace=0.5,hspace=0.5)

        for index1 in range(6):
            for index2 in range(6):
                # position this plot in a 6x6 grid
                sp = pylab.subplot(6,6,6*(index1)+index2+1)
                sp.set_axis_off()
                pylab.text(0.4,0.4, "n/a")

    # Fill in strain and stress arrays from config Atoms list
    for pindex, (pattern, fit_pairs) in fenumerate(strain_patterns[symmetry]):
        for step in frange(N_steps):
            at = configs.next()
            strain[pindex, step, :] = strain_vector(at.params['strain'])
            stress[pindex, step, :] = stress_vector(at.params['stress'])

    # Do the linear regression
    for pindex, (pattern, fit_pairs) in fenumerate(strain_patterns[symmetry]):
        for (index1, index2) in fit_pairs:
            fitted, err = do_fit(index1, index2, stress[pindex,:,:], strain[pindex,:,:], pindex)

            index = abs(Cij_map_sym[(index1, index2)])

            if not index in Cijs:
                if verbose:
                    print 'Setting C%d%d (%d) to %f +/- %f' % (index1, index2, index, fitted, err)
                Cijs[index] = [fitted]
                Cij_err[index] = [err]
            else:
                if verbose:
                    print 'Updating C%d%d (%d) with value %f +/- %f' % (index1, index2, index, fitted, err)
                Cijs[index].append(fitted)
                Cij_err[index].append(err)
            if verbose: print '\n'


    C = fzeros((6,6))
    C_err = fzeros((6,6))
    C_labels = fzeros((6,6),dtype='S4')
    C_labels[:] = '    '

    # Convert lists to mean
    for k in Cijs:
        Cijs[k] = np.mean(Cijs[k])

    # Combine statistical errors
    for k, v in Cij_err.iteritems():
        Cij_err[k] = np.sqrt(np.sum(farray(v)**2))/np.sqrt(len(v))

    if symmetry.startswith('trigonal'):
        # Special case for trigonal lattice: C66 = (C11 - C12)/2
        Cijs[Cij_map[(6,6)]] = 0.5*(Cijs[Cij_map[(1,1)]]-Cijs[Cij_map[(1,2)]])
        Cij_err[Cij_map[(6,6)]] = np.sqrt(Cij_err[Cij_map[(1,1)]]**2 + Cij_err[Cij_map[(1,2)]]**2)

    # Generate the 6x6 matrix of elastic constants
    # - negative values signify a symmetry relation
    for i in frange(6):
        for j in frange(6):
            index = Cij_symmetry[symmetry][i,j]
            if index > 0:
                C[i,j] = Cijs[index]
                C_err[i,j] = Cij_err[index]
                C_labels[i,j] = ' C%d%d' % Cij_rev_map[index]
                C_err[i,j] = Cij_err[index]
            elif index < 0:
                C[i,j] = -Cijs[-index]
                C_err[i,j] = Cij_err[-index]
                C_labels[i,j] = '-C%d%d' % Cij_rev_map[-index]

    if verbose:
        print np.array2string(C_labels).replace("'","")
        print '\n = \n'
        print np.array2string(C, suppress_small=True, precision=2)
        print

        # Summarise the independent components of C_ij matrix
        printed = {}
        for i in frange(6):
            for j in frange(6):
                index = Cij_symmetry[symmetry][i,j]
                if index <= 0 or index in printed: continue
                print 'C_%d%d = %-4.2f +/- %-4.2f GPa' % (i, j, C[i,j], C_err[i,j])
                printed[index] = 1

    return C, C_err


def elastic_constants(pot, at, sym='cubic', relax=True, verbose=True, graphics=True):
    """Convenience function which returns the 6x6 matrix :math:`C_{ij}` of configuration `at`
    with Potential `pot` assumming symmetry `sym` (default "cubic")."""

    strained_configs = generate_strained_configs(at, sym)
    stressed_configs = calc_stress(strained_configs, pot, relax=relax)
    C, C_err = fit_elastic_constants(stressed_configs, sym, verbose=verbose, graphics=graphics)

    return C


def atomic_strain(at, r0, crystal_factor=1.0):
    """Atomic strain as defined by JA Zimmerman in `Continuum and Atomistic Modeling of
    Dislocation Nucleation at Crystal Surface Ledges`, PhD Thesis, Stanford University (1999)."""

    strain = fzeros((3,3,at.n))

    for l in frange(at.n):
        for n in at.neighbours[l]:
            for i in frange(3):
                for j in frange(3):
                    strain[i,j,l] += n.diff[i]*n.diff[j]/r0**2.0

    return strain/crystal_factor


elastic_fields_fortran = elastic_fields # Fortran elastic fields routine

def elastic_fields(at, a=None,  bond_length=None, c=None, c_vector=None, cij=None,
                   save_reference=False, use_reference=False, mask=None, interpolate=False,
                   cutoff_factor=1.2, system='tetrahedric'):
    """
    Compute atomistic strain field and linear elastic stress response.

    Stress and strain are stored in compressed Voigt notation::

       at.strain[:,i] = [e_xx,e_yy,e_zz,e_yz,e_xz,e_xy]
       at.stress[:,i] = [sig_xx, sig_yy, sig_zz, sig_yz, sig_xz, sig_xy]

    so that sig = dot(C, strain) in the appropriate reference frame.

    Four-fold coordinate atoms within `at` are used to define
    tetrahedra. The deformation of each tetrahedra is determined
    relative to the ideal structure, using `a` as the cubic lattice
    constant (related to bond length by a factor :math:`sqrt{3}/4`).
    This deformation is then split into a strain and a rotation
    using a Polar decomposition.

    If `save_reference` or `use_reference` are True then `at` must have
    a `primitive_index` integer property which is different for each
    atom in the primitive unit cell. `save_reference` causes the
    local strain and rotation for one atom of each primitive type
    to be saved as entries `at.params`. Conversely, `use_reference` uses
    this information and to undo the local strain and rotation.

    The strain is then transformed into the crystal reference frame
    (i.e. x=100, y=010, z=001) to calculate the stress using the `cij`
    matrix of elastic constants. Finally the resulting stress is
    transformed back into the sample frame.

    The stress and strain tensor fields are interpolated to give
    values for atoms which are not four-fold coordinated (for example
    oxygen atoms in silica).

    Eigenvalues and eigenvectors of the stress are stored in the
    properties `stress_evals`,`stress_evec1`, `stress_evec2` and
    `stress_evec3`, ordered decreasingly by eigenvalue so that the
    principal eigenvalue and eigenvector are `stress_evals[1,:]` and
    `stress_evec1[:,i]` respectively.

    """

    def compute_stress_eig(i):
        D, SigEvecs = np.linalg.eig(stress_matrix(at.stress[:,i]))

        # Order by descending size of eigenvalues
        sorted_evals, order = zip(*sorted(zip(D, [1,2,3]),reverse=True))

        at.stress_eval[:,i]  = sorted_evals
        at.stress_evec1[:,i] = SigEvecs[:,order[0]]
        at.stress_evec2[:,i] = SigEvecs[:,order[1]]
        at.stress_evec3[:,i] = SigEvecs[:,order[2]]

    if sum([a is None, bond_length is None]) != 1:
        raise ValueError('One of lattice constant or bond length must be given')

    if a is None:
        a = bond_length*4/np.sqrt(3.)

    # We want nearest neighbour connectivity only
    save_cutoff, save_use_uniform_cutoff = at.cutoff, at.use_uniform_cutoff
    at.set_cutoff_factor(cutoff_factor)
    at.calc_connect()

    if (save_reference or use_reference) and not at.has_property('primitive_index'):
        raise ValueError('Property "primitive_index" missing from Atoms object')

    # Add various properties to store results
    at.add_property('strain', 0.0, n_cols=6)
    if cij is not None:
        at.add_property('stress', 0.0, n_cols=6)
        at.add_property('stress_eval', 0.0, n_cols=3)
        at.add_property('stress_evec1', 0.0, n_cols=3)
        at.add_property('stress_evec2', 0.0, n_cols=3)
        at.add_property('stress_evec3', 0.0, n_cols=3)
        at.add_property('strain_energy_density', 0.0)

    rotXYZ = fzeros((3,3))
    rotXYZ[1,2] = 1.0
    rotXYZ[2,3] = 1.0
    rotXYZ[3,1] = 1.0
    E = fidentity(3)

    n_at=0

    # Consider first atoms with four neighbours
    for i in frange(at.n):
        if mask is not None and not mask[i]: continue

        neighb = at.neighbours[i]

        if (system == 'anatase' and at.z[i] == 22):
           print i, len(neighb)

        if (system == 'tetrahedric' and len(neighb) == 4) or (system == 'anatase' and len(neighb) == 6):

            if (system == 'tetrahedric' and len(neighb) == 4):

                #print '\nProcessing atom', i

                # Consider neighbours in order of their index within the primitive cell
                if hasattr(at, 'primitive_index'):
                    (j1,i1), (j2,i2), (j3,i3), (j4,i4) = sorted((at.primitive_index[n.j],i) for i,n in fenumerate(neighb))
                else:
                    (j1,i1), (j2,i2), (j3,i3), (j4,i4) = list((n.j,i) for i,n in fenumerate(neighb))

                # Find cubic axes from neighbours
                n1 = neighb[i2].diff - neighb[i1].diff
                n2 = neighb[i3].diff - neighb[i1].diff
                n3 = neighb[i4].diff - neighb[i1].diff
                #print 'n1', n1.norm(), n1
                #print 'n2', n2.norm(), n2
                #print 'n3', n3.norm(), n3

                E[:,1] = (n1 + n2 - n3)/a
                E[:,2] = (n2 + n3 - n1)/a
                E[:,3] = (n3 + n1 - n2)/a

                if all(E[:,1] == 0) or all(E[:,2] == 0) or all(E[:,3]) == 0:
                    continue

            elif (system == 'anatase' and len(neighb) == 6):
                #c_vector indicates the direction of the longest O-O bond (among the ones with Ti as a center of symmetry).
                #It is necessary to identify the crystal orientation. 

                n_at = n_at + 1

                if(c_vector==None):
                    c_vector = fzeros(3)
                    c_vector[:] = [0, 0, 1]

                c_local = fzeros(3)
                for j in frange(3):
                    c_local[j] = c_vector[j] * (c/2)

                # Consider neighbours in order of their index within the primitive cell
                if hasattr(at, 'primitive_index'):
                    (j1,i1), (j2,i2), (j3,i3), (j4,i4), (j5,i5), (j6,i6) = sorted((at.primitive_index[n.j],i) for i,n in fenumerate(neighb))
                else:
                    (j1,i1), (j2,i2), (j3,i3), (j4,i4), (j5,i5), (j6,i6) = list((n.j,i) for i,n in fenumerate(neighb))

                dd = fzeros(6)
                dd[1] = np.linalg.norm(c_local - neighb[i1].diff)
                dd[2] = np.linalg.norm(c_local - neighb[i2].diff)
                dd[3] = np.linalg.norm(c_local - neighb[i3].diff)
                dd[4] = np.linalg.norm(c_local - neighb[i4].diff)
                dd[5] = np.linalg.norm(c_local - neighb[i5].diff)
                dd[6] = np.linalg.norm(c_local - neighb[i6].diff)
                #print dd[5], c_local - neighb[i5].diff
                ind =  np.argsort(dd)
               
                dd2 = fzeros(3)
                dd2[1] = at.distance_min_image( neighb[ind[2]].j , neighb[ind[3]].j )
                dd2[2] = at.distance_min_image( neighb[ind[2]].j , neighb[ind[4]].j )
                dd2[3] = at.distance_min_image( neighb[ind[2]].j , neighb[ind[5]].j )
                ind2 = np.argsort(dd2) 
                if  ind2[3] == 2:
                     a1 = ind[4] 
                     a2 = ind[3] 
                     ind[4] = a2 
                     ind[3] = a1
                elif ind2[3] == 3:
                     a1 = ind[5] 
                     a2 = ind[3] 
                     ind[5] = a2 
                     ind[3] = a1

                n1 = neighb[ind[1]].diff - neighb[ind[6]].diff
                n2 = neighb[ind[2]].diff - neighb[ind[3]].diff
                n3 = neighb[ind[4]].diff - neighb[ind[5]].diff

                E[:,1] = n3/a
                E[:,2] = n2/a
                E[:,3] = n1/c

            #print 'E', E

            # Kill near zero elements
            E[abs(E) < 1e-6] = 0.0

            if (E < 0.0).all(): E = -E

            # Find polar decomposition: E = S*R where S is symmetric,
            # and R is a rotation
            #
            #  EEt = E*E', EEt = VDV' D diagonal, S = V D^1/2 V', R = S^-1*E
            EEt = np.dot(E, E.T)

            D, V = np.linalg.eig(EEt)

            S = farray(np.dot(np.dot(V, np.diag(np.sqrt(D))), V.T))
            R = farray(np.dot(np.dot(np.dot(V, np.diag(D**-0.5)), V.T), E))

            #print 'S:', S
            #print 'R:', R

            if save_reference:
                key = 'strain_inv_%d' % at.primitive_index[i]
                if key not in at.params:
                    at.params[key] = np.linalg.inv(S)

            if use_reference:
                S = np.dot(S, at.params['strain_inv_%d' % at.primitive_index[i]])

            #print 'S after apply S0_inv:', S

            # Strain in rotated coordinate system
            at.strain[:,i] = strain_vector(S)

            # Test for permutations - check which way x points
            RtE = np.dot(R.T, E)
            if RtE[2,1] > RtE[1,1] and RtE[2,1] > RtE[3,1]:
                R = np.dot(rotXYZ, R)
            elif RtE[3,1] > RtE[1,1] and RtE[3,1] > RtE[2,1]:
                R = np.dot(rotXYZ.T, R)

            if save_reference:
                key = 'rotation_inv_%d' % at.primitive_index[i]
                if key not in at.params:
                    at.params[key] = R.T

            if use_reference:
                R = np.dot(R, at.params['rotation_inv_%d' % at.primitive_index[i]])

            #print 'R after apply R0t:', R

            # Rotate to crystal coordinate system to apply Cij matrix
            RtSR = np.dot(np.dot(R.T, S), R)
            #print 'RtSR:', RtSR

            if cij is not None:
                sig = stress_matrix(np.dot(cij, strain_vector(RtSR)))

                # Rotate back to local coordinate system
                RsigRt = np.dot(np.dot(R, sig), R.T)

                # Symmetrise stress tensor
                RsigRt = (RsigRt + RsigRt.T)/2.0
                at.stress[:,i] = stress_vector(RsigRt)

                at.strain_energy_density[i] = 0.5*np.dot(at.strain[:,i], at.stress[:,i])
                #print at.strain[:, i]

                compute_stress_eig(i)

    # For atoms without 4 neighbours, interpolate stress and strain fields
    if interpolate:
        for i in frange(at.n):
            if mask is not None and not mask[i]: continue

            neighb = at.neighbours[i]
            if at.z[i] != 8 or  len(neighb) == 0 : continue

            at.strain[:,i] = at.strain[:,[n.j for n in neighb]].mean(axis=2)
            if cij is not None:
                at.stress[:,i] = at.stress[:,[n.j for n in neighb]].mean(axis=2)
                compute_stress_eig(i)

            at.strain_energy_density[i] = 0.5*np.dot(at.strain[:,i], at.stress[:,i])

    if (system == 'anatase'):
        print 'Ti atoms computed', n_at

    # Restore original neighbour cutoff
    at.cutoff, at.use_uniform_cutoff = save_cutoff, save_use_uniform_cutoff


class AtomResolvedStressField(object):
    """
    Calculator interface to :func:`elastic_fields_fortran` and :func:`elastic_fields`

    Computes local stresses from atom resolved strain tensor and linear elasticity.

    Parameters
    ----------
    bulk: Atoms object, optional
       If present, set `a` and ``cij`` from ``bulk.cell[0,0]`` and
       ``bulk.get_calculator().get_elastic_constants(bulk)``. This means
       `bulk` should be a relaxed cubic unit cell.
    a : float, optional
       Lattice constant
    cij : array_like, optional
       6 x 6 matrix of elastic constants :math:`C_{ij}`.
       Can be obtained with :meth:`.Potential.get_elastic_constants'.
    method : str
       Which routine to use: one of "fortran" or "python".
    **extra_args : dict
       Extra arguments to be passed along to python :func:`elastic_fields`, e.g.
       for non-cubic cells.
    """

    def __init__(self,  bulk=None, a=None, cij=None, method='fortran', **extra_args):
        if method not in ['fortran', 'python']:
            raise ValueError('method should be one of "fortran" or "python"')
        self.method = method
        self.a = a
        self.cij = farray(cij)
        self.extra_args = extra_args
        if bulk is not None:
            self.a = bulk.cell[0,0]
            calc = bulk.get_calculator()
            if calc is None:
                raise RuntimeError('bulk Atoms passed to AtomResolvedStressField has no calculator!')
            self.cij = farray(calc.get_elastic_constants(bulk))
        

    def get_stresses(self, atoms):
        """
        Returns local stresses on `atoms` as a ``(len(atoms), 3, 3)`` array
        """
        if not isinstance(atoms, Atoms):
            atoms = Atoms(atoms)
        
        sigma = np.zeros((len(atoms), 3, 3))
        if self.method == 'fortran':
            elastic_fields_fortran(atoms, a=self.a, cij=self.cij)
            
            sigma[:,0,0], sigma[:,1,1], sigma[:,2,2], sigma[:,1,2], sigma[:,0,2], sigma[:,0,1] = \
               atoms.sig_xx, atoms.sig_yy, atoms.sig_zz, atoms.sig_yz, atoms.sig_xz, atoms.sig_xy
        else:
            elastic_fields(atoms, a=self.a, cij=self.cij, **self.extra_args)

            sigma[:,0,0], sigma[:,1,1], sigma[:,2,2], sigma[:,1,2], sigma[:,0,2], sigma[0,1] = atoms.stress

        # Fill in symmetric components
        sigma[:,1,0] = sigma[:,0,1]
        sigma[:,2,1] = sigma[:,1,2]
        sigma[:,2,0] = sigma[:,0,2]

        return sigma


    def get_stress(self, atoms):
        """
        Returns total stress on `atoms`, as a 6-element array
        """
        stresses = self.get_stresses(atoms)
        return stresses.sum(axis=0)
        

def elasticity_matrix_to_tensor(C):
    """Given a 6x6 elastic matrix in compressed Voigt notation, return
    the full 3x3x3x3 elastic constant tensor C_ijkl"""

    c = zeros((3,3,3,3),'d')
    for p in frange(6):
        for q in frange(6):
            i, j = voigt_map[p]
            k, l = voigt_map[q]
            c[i,j,k,l] = c[j,i,k,l] = c[i,j,l,k] = c[j,i,l,k] = c[k,l,i,j] = C[p,q]

    return c

def elasticity_tensor_to_matrix(c):
    """Given full tensor c_ijkl, return compressed Voigt form C_ij.
    First checks that c_ijkl obeys required symmetries."""

    tol = 1e-10
    for i in frange(3):
        for j in frange(3):
            for k in frange(3):
                for l in frange(3):
                    assert(c[i,j,k,l] - c[j,i,k,l] < tol)
                    assert(c[i,j,k,l] - c[i,j,l,k] < tol)
                    assert(c[i,j,k,l] - c[j,i,l,k] < tol)
                    assert(c[i,j,k,l] - c[k,l,i,j] < tol)

    C = zeros((6,6),'d')
    for p in frange(6):
        for q in frange(6):
            i, j = voigt_map[p]
            k, l = voigt_map[q]
            C[p,q] = c[i,j,k,l]

    return C

# Voigt notation: 1 = 11 (xx), 2 = 22 (yy), 3 = 33 (zz), 4 = 23 (yz), 5 = 31 (zx), 6 = 12 (xy
voigt_map = dict( ((1,(1,1)),  # xx
                   (2,(2,2)),  # yy
                   (3,(3,3)),  # zz
                   (4,(2,3)),  # yz
                   (5,(3,1)),  # zx
                   (6,(1,2)))) # xy

def elasticity_matrix_to_tensor(C):
    """Given a 6x6 elastic matrix in compressed Voigt notation, return
    the full 3x3x3x3 elastic constant tensor C_ijkl"""

    c = fzeros((3,3,3,3),'d')
    for p in frange(6):
        for q in frange(6):
            i, j = voigt_map[p]
            k, l = voigt_map[q]
            c[i,j,k,l] = c[j,i,k,l] = c[i,j,l,k] = c[j,i,l,k] = c[k,l,i,j] = C[p,q]

    return c

def elasticity_tensor_to_matrix(c):
    """Given full tensor c_ijkl, return compressed Voigt form C_ij.
    
    First checks that c_ijkl obeys required symmetries."""

    tol = 1e-10
    for i in frange(3):
        for j in frange(3):
            for k in frange(3):
                for l in frange(3):
                    assert(c[i,j,k,l] - c[j,i,k,l] < tol)
                    assert(c[i,j,k,l] - c[i,j,l,k] < tol)
                    assert(c[i,j,k,l] - c[j,i,l,k] < tol)
                    assert(c[i,j,k,l] - c[k,l,i,j] < tol)

    C = fzeros((6,6),'d')
    for p in frange(6):
        for q in frange(6):
            i, j = voigt_map[p]
            k, l = voigt_map[q]
            C[p,q] = c[i,j,k,l]

    return C

def transform_elasticity(c, R):
    """Transform c as a rank-4 tensor by the rotation matrix R.

    Returns the new representation c'. If c is a 6x6 matrix it is first
    converted to 3x3x3x3 form, and then converted back after the
    transformation."""

    made_tensor = False
    if c.shape == (6,6):
        made_tensor = True
        c = elasticity_matrix_to_tensor(c)
    elif c.shape == (3,3,3,3):
        pass
    else:
        raise ValueError('Tensor should either be 3x3x3x3 or 6x6 matrix')

    cp = fzeros((3,3,3,3),'d')
    for i in frange(3):
        for j in frange(3):
            for k in frange(3):
                for l in frange(3):
                    for p in frange(3):
                        for q in frange(3):
                            for r in frange(3):
                                for s in frange(3):
                                    cp[i,j,k,l] += R[i,p]*R[j,q]*R[k,r]*R[l,s]*c[p,q,r,s]

    if made_tensor:
        return elasticity_tensor_to_matrix(cp)
    else:
        return cp


def rayleigh_wave_speed(C, rho, a=4000., b=6000., isotropic=False):
    """
    Rayleigh wave speed in a crystal.

    Returns triplet ``(vs, vp, c_R)`` in m/s, where `vs` is the transverse
    wave speed, `vp` the longitudinal wave speed and `c_R` the Rayleigh
    shear wave speed. 

    For the anisotropic case (default), formula is Darinskii,
    A. (1997).  On the theory of leaky waves in crystals.  `Wave
    Motion, 25(1),
    35-49. <http://dx.doi.org/10.1016/S0165-2125(96)00031-5>`_. If
    `isostropic` is True, formula is from `this page
    <http://sepwww.stanford.edu/data/media/public/docs/sep124/jim1/paper_html/node5.html>`_

    `C` is the 6x6 matrix of elastic contstant, rotated to reference
    the frame of sample, and should be given in units of GPa.  The
    Rayleight speed returned is along the first (x) axis.

    `rho` is the density in g/cm^3.
    """

    if 'scipy' not in available_modules:
        raise RuntimeError('scipy is needed for rayleigh_wave_speed()')

    from scipy.optimize import bisect

    C = C.copy()
    C *= 1e9 # convert GPa -> Pa
    rho *= 1e3 # convert g/cm^3 -> kg/m^3

    if isotropic:
        vp = np.sqrt(C[1,1]/rho)
        vs = np.sqrt(C[4,4]/rho)
        f = lambda v: (np.sqrt(1 - (v/vs)**2)*np.sqrt(1 - (v/vp)**2) -
                       (np.sqrt(1 - v**2/(2*vs**2)))**4)
    else:
        vp = np.sqrt(C[3,3]/rho)
        vs = np.sqrt(C[4,4]/rho)
        f = lambda x: ((x/vp)**4*( (C[3,3]/C[2,2])*(1-(x/vp)**2)) -
                       ((1-( (C[3,2]**2)/(C[2,2]*C[3,3]) ) -
                       (x/vp)**2)**2)*(1-(x/vs)**2))
    c_R = bisect(f, vs/2., vs)
    return vs, vp, c_R

