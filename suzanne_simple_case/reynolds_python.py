#import numpy as np
#import pandas as pd
import ipost as ip
import PyFoam
from PyFoam.RunDictionary.SolutionDirectory import SolutionDirectory
from PyFoam.RunDictionary.SolutionFile import SolutionFile
from PyFoam.Applications.Decomposer import Decomposer

def main():
    solver = 'simpleFoam'
    case_dir = '.';
    n_proc = 4;
    decompose_method = 'simple'
    decompose_coeffs = '(2 2 1)'
    log_file = 'log_'+solver
    mesh_points = 333329
    turb_type = 'laminar';
    turb_model = 'no'

    ip.set_turbulence_mode(case_dir,turb_type,turb_model) #'laminar' or 'RAS', 'none' or 'kEpsilon' or 'kOmega'
    d_hyd = 4*0.02562 / 0.804201
    nu=0.00001 # SET IN FILE
    I = 0.05
    Re_range = range(100,1100,100)

    glob_folders = [case_dir + '/' + s for s in ['processor*','0/cellLevel','0/pointLevel']]
    glob_files = [case_dir + '/' + s for s in ['log*','PyFoam*']]

    for Re in Re_range:
        print("Re: {}".format(Re))
        print("Remove folders from previous run.")
        dir = SolutionDirectory(case_dir)
        dir.clearResults()
        for glob_exp in glob_folders:
            ip.rm_folder(glob_exp)
        for glob_exp in glob_files:
            ip.rm_file(glob_exp)

        ip.rm_folder(case_dir+'/postProcessing')

        print("Set inlet velocity.")
        U_value = Re*nu/d_hyd

        U_file=SolutionFile(dir.initialDir(),"U")
        U_file.replaceBoundary("inlet","(0 %f 0)" %(U_value))
        ip.delete_line(case_dir+'/0/U','PyFoamRemoved')

        print("Set magUInf.")
        ip.change_line(case_dir+'/system/controlDict','magUInf','        magUInf     '+str(U_value)+'; ')

        print("Set turbulent kinetic energy at inlet.")
        k_value = 1.5*(U_value*I)**2
        ip.set_turbulence_boundary(case_dir,'k',["inlet","monkey"],k_value)

        print("Set turbulent dissipation at inlet.")
        epsilon_value = 0.09**(3/4) * k_value**(3/2)/(0.07*d_hyd)
        ip.set_turbulence_boundary(case_dir,'epsilon',["inlet","monkey"],epsilon_value)

        print("Set specific turbulent dissipation at inlet.")
        omega_value = epsilon_value/k_value;
        ip.set_turbulence_boundary(case_dir,'omega',["inlet","monkey"],omega_value)

        print("Decompose case.")
        ip.set_decomposition(case_dir,n_proc,decompose_method,decompose_coeffs)
        ip.bash_command('cd '+case_dir+' && decomposePar -force >> '+case_dir+'/'+log_file)

        print("Renumber mesh for speedup.")
        ip.bash_command('cd '+case_dir+' && mpirun -np '+str(n_proc)+' renumberMesh -overwrite -parallel >> '+case_dir+'/'+log_file)

        print(turb_type+" simulation using "+turb_model+" turbulence model on mesh with "+str(mesh_points)+" mesh points.")
        print("Run "+solver+" in parallel.")
        ip.bash_command('cd '+case_dir+' && mpirun -np '+str(n_proc)+' '+solver+' -parallel >> '+case_dir+'/'+log_file)

        print("Reconstruct case.")
        ip.bash_command('cd '+case_dir+' && reconstructPar >> '+case_dir+'/'+log_file)

        print("Copy results into results folder.")
        ip.make_folder(case_dir+'/Results')
        result_string = turb_type+'_'+turb_model+'_turbmodel_'+str(mesh_points)+'_meshpoints'
        ip.make_folder(case_dir+'/Results/forces_'+result_string)
        ip.make_folder(case_dir+'/Results/residuals_'+result_string)

        ip.copy_files(case_dir+'/postProcessing/forces/**/*.dat',case_dir+'/Results/forces_'+result_string+'/Re_'+str(Re)+'.dat',9)
        ip.copy_files(case_dir+'/postProcessing/residuals/**/*.dat',case_dir+'/Results/residuals_'+result_string+'/Re_'+str(Re)+'.dat',2)

if __name__ == "__main__":
    main()
