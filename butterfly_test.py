#import ipost as ip
import butterfly as bf
import shutil
from pathlib import Path

new_folder_name = 'suzanne_generated'

generated_folder = Path(new_folder_name)
if generated_folder.exists() and generated_folder.is_dir():
    shutil.rmtree(generated_folder)

case_dir = 'suzanne_simple_case'
solver = 'simpleFoam'
n_proc = 4

# Load case as butterfly from folder
suzanne_case = bf.Case.from_folder(case_dir,new_folder_name)

suzanne_case.working_dir = '.'

# Set maximum simulation time to 2000s
suzanne_case.controlDict.endTime = 4000

# Set solver to simpleFoam
suzanne_case.controlDict.application = solver

# Set turbulence to laminar
#suzanne_case.turbulenceProperties.laminar()

suzanne_case.save(overwrite=True, minimum=False)
