#!/bin/bash

# Contributor: Axel Fiedler
# Updated on: 20.01.2020

echo -e "This script will run a Reynolds number study of a flow around Suzanne\n"

DHYD=$(python -c "print 4*0.02562 / 0.804201") # Dhyd = 4*A/U;

for Re in {100..1000..100}
do
	echo -e "Re: $Re"

	echo -e "Remove folders from previous run.\n"
	rm -r processor*
	rm -r 0.* 1* 2* 3* 4* 5* 6* 7* 8* 9*
	rm log*
	rm 0/cellLevel 0/pointLevel
	rm -r postProcessing

	echo -e "\nSet magUInf.\n"
	sed -i "82s/.*/        magUInf     $(python -c "Re=$Re; nu=0.00001; U=Re*nu/$DHYD; print U;"); /" system/controlDict

	echo -e "Set inlet velocity.\n"
	sed -i "27s/.*/        value           uniform (0 $(python -c "Re=$Re; nu=0.00001; U=Re*nu/$DHYD; print U;") 0); /" 0/U

	echo -e "Decompose case.\n"
	decomposePar >> logPimpleFoam

	echo -e "Renumber mesh for speedup.\n"
	mpirun -np 4 renumberMesh -overwrite -parallel >> logPimpleFoam
	renumberMesh >> logPimpleFoam

	FACENO=$(sed -n 19p constant/polyMesh/faces)
	SIMTYPE=$(sed -n 18p constant/turbulenceProperties)
	if [[ $SIMTYPE == *"RAS"* ]]; then
  	TURB=$(sed -n 22p constant/turbulenceProperties)
		if [[ $TURB == *"kEpsilon"* ]]; then
			TURB="kEpsilon"
		else
			TURB="kOmega"
		fi
	else
		TURB="laminar"
	fi

	echo -e "${TURB} simulation on mesh with ${FACENO} faces.\n"

	echo -e "Run pimpleFoam in parallel.\n"
	mpirun -np 4 pimpleFoam -parallel >> logPimpleFoam

	echo -e "Reconstruct case.\n"
	reconstructPar >> logPimpleFoam

  echo -e "Copy results into forces folder.\n"
	for entry in `ls postProcessing/forces`; do
	  sed -i '1,9d' "postProcessing/forces/${entry}/forceCoeffs.dat"
	  cat "postProcessing/forces/$entry/forceCoeffs.dat" >> forceCoeffs.dat
	done

	mkdir -p "forces_${TURB}_${FACENO}"
	cp "forceCoeffs.dat" "forces_${TURB}_${FACENO}/Re_${Re}.dat"
	rm forceCoeffs.dat

	echo -e "Copy residuals into residuals folder.\n"
	for entry in `ls postProcessing/residuals`; do
	  sed -i '1,2d' "postProcessing/residuals/${entry}/residuals.dat"
	  cat "postProcessing/residuals/$entry/residuals.dat" >> residuals.dat
	done

	mkdir -p "residuals_${TURB}_${FACENO}"
	cp "residuals.dat" "residuals_${TURB}_${FACENO}/Re_${Re}.dat"
	rm residuals.dat

	rm -r postProcessing

	echo -e "Calculation done.\n"

	echo -e "Save contour plot screenshot"

	#pvpython "save_contours.py"

done
