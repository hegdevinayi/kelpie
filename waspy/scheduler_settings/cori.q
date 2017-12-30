#!/bin/bash -l
#SBATCH -J {job-name}
#SBATCH -N {nodes}
#SBATCH -p {partition}
#SBATCH -t {walltime}
#SBATCH -A {account}
#SBATCH -L {license}
#SBATCH -o {output}
#SBATCH -C {constraint}
#SBATCH --qos={qos}

ulimit -s unlimited
export OMP_NUM_THREADS=1


