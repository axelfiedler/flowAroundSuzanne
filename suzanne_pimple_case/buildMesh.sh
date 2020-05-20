#!/bin/bash

# Contributor: Axel Fiedler
# Updated on: 01.07.2018

echo -e "This script will generate a mesh for the monkey Suzanne using snappyHexMesh"

rm log*
rm -r 0.* 1* 2* 3* 4* 5* 6* 7* 8* 9*
rm -r processor*
rm -r constant/polyMesh
blockMesh >> logBlockMesh
snappyHexMesh -overwrite >> logSnappyHexMesh
#decomposePar >> logSnappyHexMesh
#mpirun -np 4 snappyHexMesh -overwrite -parallel >> logSnappyHexMesh
#reconstructParMesh
