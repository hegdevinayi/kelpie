#!/bin/bash -l
#SBATCH -J waspy
#SBATCH -N 1
#SBATCH -t 24:00:00
#SBATCH -p regular
#SBATCH -A 2588
#SBATCH -L SCRATCH
#SBATCH -o job.oe
#SBATCH -C knl,quad,cache
#SBATCH --qos=normal

ulimit -s unlimited
export OMP_NUM_THREADS=1

module load vasp/20170629-knl
