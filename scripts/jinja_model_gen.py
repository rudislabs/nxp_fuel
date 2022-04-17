#!/usr/bin/env python3
"""
Generate Models
@author: Benjamin Perseghetti
@email: bperseghetti@rudislabs.com
"""
import jinja2
import argparse
import os
import numpy as np
import json
import shlex
import sys
import subprocess
import ast

relativeFuelPath = ".."
relativeModelPath ="../models"
scriptPath = os.path.realpath(__file__).replace("jinja_model_gen.py","")
defaultEnvPath = os.path.relpath(os.path.join(scriptPath, relativeFuelPath))
defaultModelPath = os.path.relpath(os.path.join(scriptPath, relativeModelPath))
baseDict = {
    "El_Mandadero": 1.8,
    "Buggy3": 1.8,

}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default="NotSet", help="Base model jinja file EX: iris")
    parser.add_argument('--controller', default="NotSet", help="Model to be used in jinja files")
    parser.add_argument('--sensors', default="NotSet", help="Model to be used in jinja files")
    parser.add_argument('--attachements', default="NotSet", help="Model to be used in jinja files")

    args = parser.parse_args()

    if args.sensors != "NotSet":
        try:
            sensors = ast.literal_eval(args.sensors)
        except:
            print("Failed to read passed sensors dictionary")
            sensors = "NotSet"
            pass

    if args.attachements != "NotSet":
        try:
            sensors = ast.literal_eval(args.sensors)
        except:
            print("Failed to read passed sensors dictionary")
            sensors = "NotSet"
            pass

    if model['base'] not in baseDict:
        print("\nWARNING!!!")
        print('Base model: "{:s}" DOES NOT MATCH any entries in baseDict.\nTry base model name:'.format(args.base_model))
        for modelOption in baseDict:
            print('\t{:s}'.format(modelOption))
        print("\nEXITING jinja_model_gen.py...\n")
        exit(1)

    if sensors != "NotSet":
        for sensor in sensors:
            if sensors[sensor]["method"] == "include":
    
                generate_sensor_args = ' --sdf_version "{:s}" --namespace "{:s}" --params "{:s}"'.format(
                    str(args.sdf_version), str(args.namespace), str(sensors[sensor]["params"]))
                
                generate_sensor_cmd = 'python3 {:s}/jinja_sensor_gen.py{:s}'.format(
                    scriptPath, generate_sensor_args).replace("\n","").replace("    ","")
                sensor_cmd_popen=shlex.split(generate_sensor_cmd)
                sensor_popen = subprocess.Popen(sensor_cmd_popen, stdout=subprocess.PIPE, text=True)
                while True:
                    output = sensor_popen.stdout.readline()
                    if output == '' and sensor_popen.poll() is not None:
                        break
                    if output:
                        print(output.strip())
                    sensor_popen.wait()
        
    inputFilename = os.path.relpath(os.path.join(defaultModelPath, '{:s}/model.sdf.jinja'.format(args.base_model,args.base_model)))
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(defaultEnvPath))
    templateModel = env.get_template(os.path.relpath(inputFilename, defaultEnvPath))
    

    d = {'model': model, \
         'controller': controller, \
         'attachements': attachements, \
         'sensors': sensors}

    if (not os.path.isdir('/tmp/fuel/models/{:s}'.format(args.model_name))):
        try: 
            os.makedirs('/tmp/fuel/models/{:s}'.format(args.model_name), exist_ok = True) 
        except OSError as error: 
            print("Directory creation error.")

    model_result = templateModel.render(d)
    model_out = '/tmp/fuel/models/{:s}/model.sdf'.format(args.model_name, args.model_name)

    with open(model_out, 'w') as m_out:
        print(('{:s} -> {:s}'.format(inputFilename, model_out)))
        m_out.write(model_result)

    input_config = os.path.relpath(os.path.join(scriptPath, 'model.config.jinja'))
    template_config = env.get_template(os.path.relpath(input_config, defaultEnvPath))
    result_config = template_config.render(d)
    out_config = '/tmp/fuel/models/{:s}/model.config'.format(args.model_name)
    with open(out_config, 'w') as c_out:
        print(('{:s} -> {:s}'.format("scripts/model.config.jinja", out_config)))
        c_out.write(result_config)
