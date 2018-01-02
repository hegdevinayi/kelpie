#!/bin/bash -l
#SBATCH -J {job-name}
#SBATCH -N {nodes}
#SBATCH -t {walltime}
#SBATCH -A {account}
#SBATCH -L {license}
#SBATCH -o {output}
#SBATCH --qos={qos}

ulimit -s unlimited
export OMP_NUM_THREADS=2

