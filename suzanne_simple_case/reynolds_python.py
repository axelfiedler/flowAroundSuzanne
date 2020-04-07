import os
import re
import subprocess
import numpy as np
import pandas as pd
import shutil
import glob
import PyFoam
from PyFoam.RunDictionary.SolutionDirectory import SolutionDirectory
from PyFoam.RunDictionary.SolutionFile import SolutionFile
from PyFoam.Applications.Decomposer import Decomposer


def bash_command(cmd):
    p = subprocess.Popen(cmd, shell=True, executable='/bin/bash')
    p.communicate()

def make_folder(path):
    try:
        os.mkdir(path)
    except OSError:
        print ("Creation of the directory %s failed" % path)

def rm_folder(glob_exp):
    for folder_path in glob.glob(glob_exp):
        try:
            shutil.rmtree(folder_path,ignore_errors=True)
        except OSError as e:
            print("Error: %s : %s" % (folder_path, e.strerror))

def copy_files(glob_exp,dest_dir,n_header):
    files = glob.glob(glob_exp, recursive=True)
    if len(files)==1:
        shutil.copy(files,dest_dir)
    else:
        text_out
        for file in files:
            with open(file,'r') as f:
                content = f.readlines()
            f.close()
            text_out.append(content[n_header:])
        f = open(dest_dir+'/'+files[0], 'w+')
        f.writelines(text_out)
        f.close()


def rm_file(glob_exp):
    for file_path in glob.glob(glob_exp):
        try:
            os.remove(file_path)
        except OSError as e:
            print("Error: %s : %s" % (file_path, e.strerror))

def change_line(file_path,prop_name,new_string):
    with open(file_path,'r') as f:
        content = f.readlines()
    f.close()

    line_index = [x for x in range(len(content)) if re.search("^.*"+prop_name+"[^a-zA-Z].*$",content[x])]
    content[line_index[0]] = new_string+'\n'
    f = open(file_path, 'w')
    f.writelines(content)
    f.close()

def delete_line(file_path,prop_name):
    with open(file_path, "r") as f:
        lines = f.readlines()
    with open(file_path, "w") as f:
        for line in lines:
            if not re.search("^.*"+prop_name+".*$",line):
                f.write(line)

def set_turbulence_mode(case_dir,simulation_type,RAS_model):
    change_line(case_dir +'/constant/turbulenceProperties','simulationType','simulationType '+simulation_type+';')
    change_line(case_dir +'/constant/turbulenceProperties','RASModel','    RASModel        '+RAS_model+';')
    if simulation_type == 'RAS':
        change_line(case_dir +'/constant/turbulenceProperties','turbulence','    turbulence      on;')
    elif simulation_type == 'laminar':
        change_line(case_dir +'/constant/turbulenceProperties','turbulence','    turbulence      off;')
    else:
        print('Currently only laminar and RAS are available')

def set_decomposition(case_dir,n_proc,decompose_method,decompose_coeffs):
    change_line(case_dir +'/system/decomposeParDict','numberOfSubdomains','numberOfSubdomains '+str(n_proc)+';')
    change_line(case_dir +'/system/decomposeParDict','method','method          '+decompose_method+';')
    change_line(case_dir +'/system/decomposeParDict','\(','    n               '+decompose_coeffs+';')

def set_turbulence_boundary(case_dir,prop_name,boundaries,prop_value):
    dir = SolutionDirectory(case_dir)
    turb_file=SolutionFile(dir.initialDir(),prop_name)
    for boundary in boundaries:
        turb_file.replaceBoundary(boundary,str(prop_value))
    delete_line(case_dir +'/0/'+prop_name,'PyFoamRemoved')
    change_line(case_dir +'/0/'+prop_name,'internalField','internalField   uniform '+str(prop_value)+'; ')

def main():
    solver = 'simpleFoam'
    case_dir = '.';
    n_proc = 4;
    decompose_method = 'simple'
    decompose_coeffs = '(2 2 1)'
    log_file = 'logSimpleFoam'
    mesh_points = 333329
    turb_type = 'laminar';
    turb_model = 'no'

    set_turbulence_mode(case_dir,turb_type,turb_model) #'laminar' or 'RAS', 'none' or 'kEpsilon' or 'kOmega'
    d_hyd = 4*0.02562 / 0.804201
    nu=0.00001 # SET IN FILE
    I = 0.05
    Re_range = range(100,200,100)

    glob_folders = [case_dir + '/' + s for s in ['processor*','0/cellLevel','0/pointLevel']]
    glob_files = [case_dir + '/' + s for s in ['log*','PyFoam*']]

    for Re in Re_range:
        print("Re: {}".format(Re))
        print("Remove folders from previous run.")
        dir = SolutionDirectory(case_dir)
        dir.clearResults()
        for glob_exp in glob_folders:
            rm_folder(glob_exp)
        for glob_exp in glob_files:
            rm_file(glob_exp)

        print("Set inlet velocity.")
        U_value = Re*nu/d_hyd

        U_file=SolutionFile(dir.initialDir(),"U")
        U_file.replaceBoundary("inlet","(0 %f 0)" %(U_value))
        delete_line(case_dir+'/0/U','PyFoamRemoved')

        print("Set magUInf.")
        change_line(case_dir+'/system/controlDict','magUInf','        magUInf     '+str(U_value)+'; ')

        print("Set turbulent kinetic energy at inlet.")
        k_value = 1.5*(U_value*I)**2
        set_turbulence_boundary(case_dir,'k',["inlet","monkey"],k_value)

        print("Set turbulent dissipation at inlet.")
        epsilon_value = 0.09**(3/4) * k_value**(3/2)/(0.07*d_hyd)
        set_turbulence_boundary(case_dir,'epsilon',["inlet","monkey"],epsilon_value)

        print("Set specific turbulent dissipation at inlet.")
        omega_value = epsilon_value/k_value;
        set_turbulence_boundary(case_dir,'omega',["inlet","monkey"],omega_value)

        print("Decompose case.")
        set_decomposition(case_dir,n_proc,decompose_method,decompose_coeffs)
        bash_command('cd '+case_dir+' && decomposePar -force >> '+case_dir+'/'+log_file)

        print("Renumber mesh for speedup.")
        bash_command('cd '+case_dir+' && mpirun -np '+str(n_proc)+' renumberMesh -overwrite -parallel >> '+case_dir+'/'+log_file)

        print(turb_type+" simulation using "+turb_model+" turbulence model on mesh with "+str(mesh_points)+" mesh points.")
        print("Run "+solver+" in parallel.")
        bash_command('cd '+case_dir+' && mpirun -np '+str(n_proc)+' '+solver+' -parallel >> '+case_dir+'/'+log_file)

        print("Reconstruct case.")
        bash_command('cd '+case_dir+' && reconstructPar >> '+case_dir+'/'+log_file)

        print("Copy results into results folder.")
        make_folder(case_dir+'/Results')
        result_string = turb_type+'_'+turb_model+'_turbmodel_'+str(mesh_points)+'_meshpoints'
        make_folder(case_dir+'/Results/forces_'+result_string)
        make_folder(case_dir+'/Results/residuals_'+result_string)

        copy_files(case_dir+'/postProcessing/forces/**/*.dat',case_dir+'/Results/forces_'+result_string+'/Re_'+Re+'.dat',9)
        copy_files(case_dir+'/postProcessing/residuals/**/*.dat',case_dir+'/Results/residuals_'+result_string+'/Re_'+Re+'.dat',2)
        #rm_folder(case_dir+'/postProcessing')

if __name__ == "__main__":
    main()
