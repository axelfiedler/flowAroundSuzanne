#!/bin/bash

# Contributor: Axel Fiedler
# Updated on: 01.07.2018

echo -e "This script will run a Reynolds number study of a flow around Suzanne"

for Re in {100..2000..100}
do
	echo -e "Re: $Re"

	echo -e "Remove folders from previous run.\n"
	rm -r processor*
	rm -r 0.* 1* 2* 3* 4* 5* 6* 7* 8* 9*
	rm log*

	echo -e "\nSet magUInf.\n"
	sed -i "79s/.*/        magUInf     $(python -c "Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; print U;"); /" system/controlDict

	echo -e "Set inlet velocity.\n"
	sed -i "27s/.*/        value           uniform (0 $(python -c "Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; print U;") 0); /" 0/U # Dhyd = 4*A/U; U = Re*nu/Dhyd;

	echo -e "Decompose case.\n"
	decomposePar >> logSimpleFoam

	echo -e "Renumber mesh for speedup.\n"
	mpirun -np 4 renumberMesh -overwrite -parallel >> logSimpleFoam
	renumberMesh >> logSimpleFoam

	echo -e "Run simpleFoam in parallel.\n"
	mpirun -np 4 simpleFoam -parallel >> logSimpleFoam

	echo -e "Reconstruct case.\n"
	reconstructPar >> logSimpleFoam

	echo -e "Copy results into C_D folder.\n"
	cd postProcessing/forces/*/.
	cp forceCoeffs.dat ../../../C_D/
	cd ../../..
	rm -r postProcessing/forces/
	mv "C_D/forceCoeffs.dat" "C_D/Re_${Re}.dat"

	echo -e "Copy residuals into residuals folder.\n"
	cd postProcessing/residuals/*/.
	cp residuals.dat ../../../residuals/
	cd ../../..
	rm -r postProcessing/residuals/
	mv "residuals/residuals.dat" "residuals/Re_${Re}.dat"
	rm -r postProcessing

	echo -e "Calculation done.\n"

done
