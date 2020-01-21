#!/bin/bash

# Contributor: Axel Fiedler
# Updated on: 20.01.2020

echo -e "This script will run a Reynolds number study of a flow around Suzanne"

for Re in {1000..8000..1000}
do
	echo -e "Re: $Re"

	echo -e "Remove folders from previous run.\n"
	rm -r processor*
	rm -r 0.* 1* 2* 3* 4* 5* 6* 7* 8* 9*
	rm log*
	rm 0/cellLevel 0/pointLevel
	rm -r postProcessing/forces postProcessing/residuals

	echo -e "\nSet magUInf.\n"
	sed -i "78s/.*/        magUInf     $(python -c "Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; print U;"); /" system/controlDict

	echo -e "Set inlet velocity.\n"
	sed -i "27s/.*/        value           uniform (0 $(python -c "Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; print U;") 0); /" 0/U # Dhyd = 4*A/U; U = Re*nu/Dhyd;

	# Uncomment following sections for k-epsilon or k-Omega calculation and set constant/turbelenceProperties accordingly

	echo -e "Set turbulent kinetic energy at inlet.\n"
	sed -i "19s/.*/internalField   uniform $(python -c "I=0.05; Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; k = 1.5*(U*I)**2; print k;"); /" 0/k # k = 1.5*(U*I_T)^2
	sed -i "26s/.*/        value           uniform $(python -c "I=0.05; Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; k = 1.5*(U*I)**2; print k;"); /" 0/k # k = 1.5*(U*I_T)^2
	sed -i "37s/.*/        value           uniform $(python -c "I=0.05; Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; k = 1.5*(U*I)**2; print k;"); /" 0/k # k = 1.5*(U*I_T)^2

	echo -e "Set turbulent dissipation at inlet.\n"

	sed -i "20s/.*/internalField           uniform $(python -c "I=0.05; Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; k = 1.5*(U*I)**2; epsilon = 0.09**(3/4) * k**(3/2)/(0.07*Dhyd); print epsilon;"); /" 0/epsilon # epsilon = 0.09^(3/4) * k^(3/2)/(0.07*L_char); omega = epsilon/k
	sed -i "27s/.*/        value      		uniform $(python -c "I=0.05; Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; k = 1.5*(U*I)**2; epsilon = 0.09**(3/4) * k**(3/2)/(0.07*Dhyd); print epsilon;"); /" 0/epsilon # epsilon = 0.09^(3/4) * k^(3/2)/(0.07*L_char); omega = epsilon/k
	sed -i "38s/.*/        value      		uniform $(python -c "I=0.05; Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; k = 1.5*(U*I)**2; epsilon = 0.09**(3/4) * k**(3/2)/(0.07*Dhyd); print epsilon;"); /" 0/epsilon # epsilon = 0.09^(3/4) * k^(3/2)/(0.07*L_char); omega = epsilon/k

	echo -e "Set specific turbulent dissipation at inlet.\n"

	sed -i "19s/.*/internalField           uniform $(python -c "I=0.05; Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; k = 1.5*(U*I)**2; epsilon = 0.09**(3/4) * k**(3/2)/(0.07*Dhyd); omega=epsilon/k; print omega;"); /" 0/omega # epsilon = 0.09^(3/4) * k^(3/2)/(0.07*L_char); omega = epsilon/k
	sed -i "26s/.*/        value      		uniform $(python -c "I=0.05; Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; k = 1.5*(U*I)**2; epsilon = 0.09**(3/4) * k**(3/2)/(0.07*Dhyd); omega=epsilon/k; print omega;"); /" 0/omega # epsilon = 0.09^(3/4) * k^(3/2)/(0.07*L_char); omega = epsilon/k
	sed -i "37s/.*/        value      		uniform $(python -c "I=0.05; Re=$Re; nu=0.00001; Dhyd=4*0.02562 / 0.804201; U=Re*nu/Dhyd; k = 1.5*(U*I)**2; epsilon = 0.09**(3/4) * k**(3/2)/(0.07*Dhyd); omega=epsilon/k; print omega;"); /" 0/omega # epsilon = 0.09^(3/4) * k^(3/2)/(0.07*L_char); omega = epsilon/k

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
