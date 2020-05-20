#!/bin/bash
echo -e "Copy results into forces folder.\n"
mkdir -p "forces_${TURB}_${FACENO}"
cp forceCoeffs.dat "/forces_${TURB}_${FACENO}/"
rm -r postProcessing/forces/
mv "forces_${TURB}_${FACENO}/forceCoeffs.dat" "forces_${TURB}_${FACENO}/Re_${Re}.dat"
