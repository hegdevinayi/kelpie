#!/bin/bash -l
#MSUB -l nodes={nodes}:ppn={n_mpi_per_node}
#MSUB -l walltime={walltime}
#MSUB -N {job-name}
#MSUB -A {account}
#MSUB -o {output}

ulimit -s unlimited
export OMP_NUM_THREADS=1
