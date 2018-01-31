#!/bin/bash -l
#MSUB -l nodes={nodes}:ppn={n_mpi_per_node}
#MSUB -l walltime={walltime}
#MSUB -N {job-name}
#MSUB -A {account}
#MSUB -o {output}
#MSUB -q buyin

ulimit -s unlimited
export OMP_NUM_THREADS=1

{modules}

source activate kelpie
kelpie -m graze -l {run_location} {calculation_params}
