# -*- coding: utf-8 -*-
# Copyright 2021 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""
Author: NoEvaa
Date: 2022-03-14 15:28:57
LastEditTime: 2022-05-12 02:01:36
Description: Generate a uccsd quantum circuit 
             based on a molecular data 
             generated by HiQfermion or openfermion.
FilePath: /src/uccsd_generator.py
"""
import numpy as np
from collections import OrderedDict as ordict
import itertools

from mindquantum.core.circuit import Circuit
from mindquantum import gates as G
from mindquantum.core.parameterresolver import ParameterResolver as PR
from openfermion.chem import MolecularData
from mindquantum.core.operators import FermionOperator
from mindquantum.core.operators.utils import down_index, up_index, get_fermion_operator
from mindquantum.algorithm.nisq.chem.transform import Transform
from mindquantum.third_party.interaction_operator import InteractionOperator


class Circuit_Generator:
    r"""
    Transform a pauli ansatz to parameterized quantum circuit.

    Args:
        pauli_ansatz (): .
        n_qubits (int): .
    """
    def __init__(self, pauli_ansatz, n_qubits):
        self.pauli_ansatz = pauli_ansatz
        self.n_qubits = n_qubits
        self.ops_retention = [None for i in range(n_qubits)]

    @property
    def circuit(self):
        """
        Returns:
            Circuit, a quantum circuit.
        """
        circuit = Circuit()
        for k, v in self.pauli_ansatz.items():
            circuit += self.decompose_single_term_HE(k, v)
        circuit += Circuit(self._HE_eliminating(()))
        return circuit

    def decompose_single_term_HE(self, term, para): #Happy Eliminating Ver.
        """
        # Modified from mindquantum.core.circuit.utils.decompose_single_term_time_evolution
        Decompose a time evolution gate into basic quantum gates.

        This function only work for the hamiltonian with only single pauli word.
        For example, exp(-i * t * ham), ham can only be a single pauli word, such
        as ham = X0 x Y1 x Z2, and at this time, term will be
        ((0, 'X'), (1, 'Y'), (2, 'Z')). When the evolution time is expressd as
        t = a*x + b*y, para would be {'x':a, 'y':b}.

        Args:
            term (tuple, QubitOperator): the hamiltonian term of just the
                evolution qubit operator.
            para (Union[dict, numbers.Number]): the parameters of evolution operator.

        Returns:
            Circuit, a quantum circuit.

        Raises:
            ValueError: If term has more than one pauli string.
            TypeError: If term is not map.
        """
        if not isinstance(term, tuple):
            try:
                if len(term.terms) != 1:
                    raise ValueError("Only work for single term time \
                        evolution operator, but get {}".format(len(term)))
                term = list(term.terms.keys())[0]
            except TypeError:
                raise TypeError("Not supported type:{}".format(type(term)))

        out = []
        term = sorted(term)
        if len(term) == 1:  # single pauli operator
            out += self._HE_eliminating(())
            if term[0][1] == 'X':
                out.append(G.RX(para * 2).on(term[0][0]))
            elif term[0][1] == 'Y':
                out.append(G.RY(para * 2).on(term[0][0]))
            else:
                out.append(G.RZ(para * 2).on(term[0][0]))
        else:
            out += self._HE_eliminating(term)
            
            out.append(G.BarrierGate(False))
            for i in range(len(term) - 1):
                out.append(G.X.on(term[i + 1][0], term[i][0]))
            out.append(G.BarrierGate(False))

            if isinstance(para, (dict, PR)):
                out.append(G.RZ({i: 2 * j for i, j in para.items()}).on(term[-1][0]))
            else:
                out.append(G.RZ(2 * para).on(term[-1][0]))

            out.append(G.BarrierGate(False))
            for i in range(len(term) - 2, -1, -1):
                out.append(G.X.on(term[i + 1][0], term[i][0]))
            out.append(G.BarrierGate(False))

        return Circuit(out)

    def _HE_eliminating(self, term):
        ops_update = [None for i in range(self.n_qubits)]
        out = []
        for index, action in term:
            ops_update[index] = action
        for i in range(self.n_qubits):
            if self.ops_retention[i] != ops_update[i]:
                if self.ops_retention[i] == 'X':
                    out.append(G.H.on(i))
                elif self.ops_retention[i] == 'Y':
                    out.append(G.RX(np.pi * 1.5).on(i))
                if ops_update[i] == 'X':
                    out.append(G.H.on(i))
                elif ops_update[i] == 'Y':
                    out.append(G.RX(np.pi / 2).on(i))
        self.ops_retention = ops_update
        return out

class Uccsd_Generator:
    r"""
    # Modified from mindquantum.algorithm.nisq.chem.uccsd.generate_uccsd.
    Generate a uccsd quantum circuit based on a molecular data generated by HiQfermion or openfermion.

    Args:
        molecular (Union[str, MolecularData]): the name of the molecular data file,
            or openfermion MolecularData.
        th (int): the threshold to filt the uccsd amplitude. When th < 0, we
            will keep all amplitudes. When th == 0, we will keep all amplitude
            that are positive. Default: 0.
        mode (str): the mode to transform a fermion ansatz. JW | Parity | BK . Default: JW.
    """
    def __init__(self, molecular, th=0, mode='JW'):
        if isinstance(molecular, str):
            self.mol = MolecularData(filename=molecular)
            self.mol.load()
        else:
            self.mol = molecular
        print("ccsd:{}.".format(self.mol.ccsd_energy))
        print("fci:{}.".format(self.mol.fci_energy))
        self.th = th
        self.mode = mode if mode in ['JW', 'Parity', 'BK'] else 'JW'

    @property
    def generate_uccsd(self):
        """
        Returns:
            - **uccsd_circuit** (Circuit), the ansatz circuit generated by uccsd method.
            - **initial_amplitudes** (numpy.ndarray), the initial parameter values of uccsd circuit.
            - **parameters_name** (list[str]), the name of initial parameters.
            - **qubit_hamiltonian** (QubitOperator), the hamiltonian of the molecule.
            - **n_qubits** (int), the number of qubits in simulation.
            - **n_electrons**, the number of electrons of the molecule.
        """
        fermion_ansatz, parameters = self._para_uccsd_singlet_generator(self.mol, self.th)
        pauli_ansatz = self._transform2pauli(fermion_ansatz)

        uccsd_circuit = Circuit_Generator(pauli_ansatz, self.mol.n_qubits).circuit

        ham_of = self.mol.get_molecular_hamiltonian()
        inter_ops = InteractionOperator(*ham_of.n_body_tensors.values())
        ham_hiq = get_fermion_operator(inter_ops)
        qubit_hamiltonian = Transform(ham_hiq).jordan_wigner()
        qubit_hamiltonian.compress()

        parameters_name = list(parameters.keys())
        initial_amplitudes = [parameters[i] for i in parameters_name]

        return uccsd_circuit, \
            initial_amplitudes, \
            parameters_name, \
            qubit_hamiltonian, \
            self.mol.n_qubits, \
            self.mol.n_electrons

    def _para_uccsd_singlet_generator(self, mol, th=0):
        """
        # Modified from mindquantum.algorithm.nisq.chem.uccsd._para_uccsd_singlet_generator
        Generate a uccsd quantum circuit.

        Args:
            mol (molecular): A hdf5 molecular file generated by HiQ Fermion.
            th (int, optional): A threadhold of parameters. If a parameter is
                lower than the threadhold, than we will not update it in VQE
                algorithm. Default: 0.
        """
        n_qubits = mol.n_qubits
        n_electrons = mol.n_electrons
        params = {}
        if n_qubits % 2 != 0:
            raise ValueError('The total number of spin-orbitals should be even.')
        out = []
        out_tmp = []
        n_spatial_orbitals = n_qubits // 2
        n_occupied = int(np.ceil(n_electrons / 2))
        n_virtual = n_spatial_orbitals - n_occupied

        # Unpack amplitudes
        n_single_amplitudes = n_occupied * n_virtual
        # Generate excitations
        spin_index_functions = [up_index, down_index]
        # Generate all spin-conserving single and double excitations derived
        # from one spatial occupied-virtual pair
        for i, (p, q) in enumerate(
                itertools.product(range(n_virtual), range(n_occupied))):

            # Get indices of spatial orbitals
            virtual_spatial = n_occupied + p
            occupied_spatial = q
            virtual_up = virtual_spatial * 2
            occupied_up = occupied_spatial * 2
            virtual_down = virtual_spatial * 2 + 1
            occupied_down = occupied_spatial * 2 + 1
            single_amps = mol.ccsd_single_amps[virtual_up, occupied_up]
            double1_amps = mol.ccsd_double_amps[virtual_up, occupied_up,
                                                virtual_down, occupied_down]
            single_amps_name = 'p' + str(i)
            double1_amps_name = 'p' + str(i + n_single_amplitudes)

            for spin in range(2):
                # Get the functions which map a spatial orbital index to a
                # spin orbital index
                this_index = spin_index_functions[spin]
                other_index = spin_index_functions[1 - spin]

                # Get indices of spin orbitals
                virtual_this = this_index(virtual_spatial)
                virtual_other = other_index(virtual_spatial)
                occupied_this = this_index(occupied_spatial)
                occupied_other = other_index(occupied_spatial)

                # Generate single excitations
                if abs(single_amps) > th:
                    params[single_amps_name] = single_amps
                    fermion_ops1 = FermionOperator(
                        ((occupied_this, 1), (virtual_this, 0)), 1)
                    fermion_ops2 = FermionOperator(
                        ((virtual_this, 1), (occupied_this, 0)), 1)
                    out.append([fermion_ops1 - fermion_ops2, single_amps_name])

            # Generate double excitation
            if abs(double1_amps) > th:
                params[double1_amps_name] = - double1_amps * 2
                fermion_ops1 = FermionOperator(
                    ((virtual_this, 1), (occupied_this, 0), (virtual_other, 1),
                     (occupied_other, 0)), 1)
                fermion_ops2 = FermionOperator(
                    ((occupied_other, 1), (virtual_other, 0),
                     (occupied_this, 1), (virtual_this, 0)), 1)
                out.append([fermion_ops1 - fermion_ops2, double1_amps_name])
        out.extend(out_tmp)
        out_tmp = []
        # Generate all spin-conserving double excitations derived
        # from two spatial occupied-virtual pairs
        for i, ((p, q), (r, s)) in enumerate(
                itertools.combinations(
                    itertools.product(range(n_virtual), range(n_occupied)), 2)):

            # Get indices of spatial orbitals
            virtual_spatial_1 = n_occupied + p
            occupied_spatial_1 = q
            virtual_spatial_2 = n_occupied + r
            occupied_spatial_2 = s

            virtual_1_up = virtual_spatial_1 * 2
            occupied_1_up = occupied_spatial_1 * 2
            virtual_2_up = virtual_spatial_2 * 2 + 1
            occupied_2_up = occupied_spatial_2 * 2 + 1

            double2_amps = mol.ccsd_double_amps[virtual_1_up, occupied_1_up,
                                                virtual_2_up, occupied_2_up]
            double2_amps_name = 'p' + str(i + 2 * n_single_amplitudes)

            # Generate double excitations
            for (spin_a, spin_b) in itertools.product(range(2), repeat=2):
                # Get the functions which map a spatial orbital index to a
                # spin orbital index
                index_a = spin_index_functions[spin_a]
                index_b = spin_index_functions[spin_b]

                # Get indices of spin orbitals
                virtual_1_a = index_a(virtual_spatial_1)
                occupied_1_a = index_a(occupied_spatial_1)
                virtual_2_b = index_b(virtual_spatial_2)
                occupied_2_b = index_b(occupied_spatial_2)
                if abs(double2_amps) > th:
                    params[double2_amps_name] = - double2_amps
                    fermion_ops1 = FermionOperator(
                        ((virtual_1_a, 1), (occupied_1_a, 0), (virtual_2_b, 1),
                         (occupied_2_b, 0)), 1)
                    fermion_ops2 = FermionOperator(
                        ((occupied_2_b, 1), (virtual_2_b, 0), (occupied_1_a, 1),
                         (virtual_1_a, 0)), 1)
                    out.append([fermion_ops1 - fermion_ops2, double2_amps_name])
        return out, params

    def _transform2pauli(self, fermion_ansatz):
        """
        # Modified from mindquantum.algorithm.nisq.chem.uccsd._transform2pauli
        Transform a fermion ansatz to pauli ansatz based on (mode) transformation.
        """
        out = ordict()
        for i in fermion_ansatz:
            if self.mode == 'JW':
                qubit_generator = Transform(i[0]).jordan_wigner()
            elif self.mode == 'BK':
                qubit_generator = Transform(i[0]).bravyi_kitaev()
            else:
                qubit_generator = Transform(i[0]).parity()
            if qubit_generator.terms != {}:
                for key, term in qubit_generator.terms.items():
                    if key not in out:
                        out[key] = ordict({i[1]: float(term.imag)})
                    else:
                        if i[1] in out[key]:
                            out[key][i[1]] += float(term.imag)
                        else:
                            out[key][i[1]] = float(term.imag)
        return out
