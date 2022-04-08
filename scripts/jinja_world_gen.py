#!/usr/bin/env python3
"""
Generate Worlds
@author: Benjamin Perseghetti
@email: bperseghetti@rudislabs.com
"""
import jinja2
import argparse
import os
import numpy as np
import datetime
import ast

rel_ignition_path = ".."
rel_world_path ="../worlds"
script_path = os.path.realpath(__file__).replace("jinja_world_gen.py","")
defaultEnvPath = os.path.relpath(os.path.join(script_path, rel_ignition_path))
default_world_path = os.path.relpath(os.path.join(script_path, rel_world_path))
defaultFilename = os.path.relpath(os.path.join(default_world_path, "gen.world.jinja"))
defaultSDFWorldDict = {
    "empty": 1.8,
    "canvas": 1.8,
    "ground_plane": 1.8
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sun', default={'model': "sunUTC", 'dateUTC': "1904/09/20/17:30"}, help="model [sunNoon, sunNight, sunUTC, sunNone] and dateUTC 'YYYY_MM_DD_hh_mm' or 'sunNow' for your current UTC time.")
    parser.add_argument('--skybox', default=0, help="Skybox on [1] or off [0]")
    parser.add_argument('--wind', default="NotSet", help="Dictionary of wind attributes (linear_velocity, more to come).")
    parser.add_argument('--name', default="NotSet", help="Name of world, see defaultSDFWorldDict for options")
    parser.add_argument('--WGS84', default={'degLatitude': 39.8039, 'degLognitude': -84.0606, 'mAltitude': 244, 'useSphericalCoords': 1}, help="{'degLatitude': , 'degLognitude': , 'mAltitude': , 'useSphericalCoords': } for spherical coordinates and sunUTC calculation")
    parser.add_argument('--embeddedModels', default="NotSet", help="Array of models with poses to be embedded in world file")
    parser.add_argument('--outputFile', help="world output file")
    args = parser.parse_args()

    print('Generation script passed world name: "{:s}"'.format(args.name))


    try:
        WGS84 = ast.literal_eval(args.WGS84)
    except:
        print("Failed to read passed WGS84 dictionary using defaults.")
        WGS84 = {'degLatitude': 39.8039, 'degLognitude': -84.0606, 'mAltitude': 244, 'useSphericalCoords': 1}
        pass
    if 'degLatitude' not in WGS84 or 'degLognitude' not in WGS84 or 'mAltitude' not in WGS84 or 'useSphericalCoords' not in WGS84:
        print('Malformed WGS84 dictionary: {:s}\n using default.'.format(str(WGS84)))
        WGS84 = {'degLatitude': 39.8039, 'degLognitude': -84.0606, 'mAltitude': 244, 'useSphericalCoords': 1}

    try:
        sun = ast.literal_eval(args.sun)
    except:
        print("Failed to read passed WGS84 dictionary using defaults.")
        sun = {'model': "sunUTC", 'dateUTC': "1904_09_20_17_30"}
        pass
    if 'model' not in sun or 'dateUTC' not in sun:
        print("Malformed sun dictionary, using default.")
        sun = {'model': "sunUTC", 'dateUTC': "1904_09_20_17_30"}

    print('sun dictionary: {:s}\n'.format(str(sun)))

    if args.embeddedModels != "NotSet":
        try:
            args.embeddedModels = ast.literal_eval(args.embeddedModels)
        except:
            print("Failed to read passed embeddedModels dictionary")
            args.embeddedModels = "NotSet"
            pass

    if args.wind != "NotSet":
        try:
            args.wind = ast.literal_eval(args.wind)
        except:
            print("Failed to read passed wind dictionary")
            args.wind = "NotSet"
            pass

    if args.name not in defaultSDFWorldDict:
        print("\nERROR!!!")
        print('World name: "{:s}" DOES NOT MATCH any entries in defaultSDFWorldDict.\nTry world name:'.format(args.name))
        for worldOption in defaultSDFWorldDict:
            print('\t{:s}'.format(worldOption))
        print("\nEXITING jinja_world_gen.py...\n")
        exit(1)

    
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(defaultEnvPath))
    template = env.get_template(os.path.relpath(defaultFilename, defaultEnvPath))

    if sun["model"] == "sunUTC":
        try:
            import pysolar
        except ImportError:
            print("Failed to import pysolar - try installing with: \n\tsudo apt install python3-pysolar\n")
            sun["model"] = "sunNone"
            pass

    if sun["model"] == "sunUTC":
        dateStringUTC = sun["dateUTC"]
        if dateStringUTC == "sunNow":
            dateUTC = datetime.datetime.now(datetime.timezone.utc)
        else:
            if len(dateStringUTC) != 16:
                dateStringUTC='1904/09/20/17:30'
            YYYY = int(dateStringUTC[:4])
            MM = int(dateStringUTC[5:7])
            DD = int(dateStringUTC[8:10])
            hh = int(dateStringUTC[11:13])
            mm = int(dateStringUTC[14:16])
            dateUTC = datetime.datetime(YYYY, MM, DD, hh, mm, 0, 0, tzinfo=datetime.timezone.utc)
        sunLatitude = float(WGS84["degLatitude"])
        sunLongitude = float(WGS84["degLognitude"])
        sunRise, sunSet = pysolar.util.get_sunrise_sunset(latitude_deg=sunLatitude, longitude_deg=sunLongitude, when=dateUTC)
        solarNoon = sunRise+(sunSet-sunRise)/2
        cmpSunRise = (dateUTC-sunRise).total_seconds()/60
        cmpSunSet = (sunSet-dateUTC).total_seconds()/60
        cmpsolarNoon = abs((solarNoon-dateUTC).total_seconds()/60)
        if cmpSunRise > 0 and cmpSunSet > 0:
            print("Sun at day time.")
            sun["ambientLight"] = 0.4
            sun["backgroundColor"] = 0.7
        if cmpSunRise < -60 or cmpSunSet < -60:
            print("Sun at night time.")
            sun["model"] = "sunNight"
        if abs(cmpSunRise) <= 60:
            print("Sun near sunrise.")
            sun["ambientLight"] = 0.205+(cmpSunRise/60)*0.195
            sun["backgroundColor"] = 0.375+(cmpSunRise/60)*0.325
        if abs(cmpSunSet) <= 60:
            print("Sun near sunset.")
            sun["ambientLight"] = 0.205+(cmpSunSet/60)*0.195
            sun["backgroundColor"] = 0.375+(cmpSunSet/60)*0.325
        if cmpsolarNoon <= 90:
            print("Sun near solar noon.")
            sun["ambientLight"] = 0.6-(cmpsolarNoon/90)*0.2
            sun["backgroundColor"] = 0.9-(cmpsolarNoon/90)*0.2

        sunAzimuth = pysolar.solar.get_azimuth(sunLatitude, sunLongitude, dateUTC)
        sunAltitude = pysolar.solar.get_altitude(sunLatitude, sunLongitude, dateUTC)
        sunRadiation =  pysolar.radiation.get_radiation_direct(dateUTC, sunAltitude)
        if sunRadiation > 1000.0:
            sunRadiation = 1000.0
        if sunRadiation < 0.0:
            sunRadiation = 0.0
        sunRadiationNorm = sunRadiation/1000.0
        specularRatio = 0.3
        sun["diffuse"] = '{:1.3f} {:1.3f} {:1.3f} 1'.format(sunRadiationNorm,sunRadiationNorm,sunRadiationNorm,sunRadiationNorm)
        sun["specular"] = '{:1.3f} {:1.3f} {:1.3f} 1'.format(specularRatio*sunRadiationNorm,specularRatio*sunRadiationNorm,specularRatio*sunRadiationNorm,specularRatio*sunRadiationNorm)
    
        sunAzimuthRad = sunAzimuth*np.pi/180.0
        sunAltitudeRad = sunAltitude*np.pi/180.0
    
        Xenu = -np.cos(sunAltitudeRad)*np.sin(sunAzimuthRad)
        Yenu = -np.cos(sunAltitudeRad)*np.cos(sunAzimuthRad)
        Zenu = -np.sin(sunAltitudeRad)
    
        sun["vector"] = '{:1.3f} {:1.3f} {:1.3f}'.format(Xenu, Yenu, Zenu)
    
        if sunRadiationNorm == 0:
            sun["model"]="sunNight"

    if sun["model"] == "sunNight":
        print("WARNING: WORLD IS SET TO NIGHT TIME MODE!!!")

    d = {'sun': sun, \
         'wind': args.wind, \
         'skybox': args.skybox, \
         'WGS84': WGS84, \
         'name': args.name, \
         'embeddedModels': args.embeddedModels}

        
    
    if (not os.path.isdir('/tmp/fuel/worlds')):
        try: 
            os.makedirs('/tmp/fuel/worlds', exist_ok = True) 
        except OSError as error: 
            print("Directory creation error.")

    result = template.render(d)
    if args.outputFile:
        filenameOut = args.outputFile
    else:
        filenameOut = '{:s}/{:s}.sdf'.format("/tmp/fuel/worlds",args.name)

    with open(filenameOut, 'w') as f_out:
        print(('{:s} -> {:s}'.format(defaultFilename, filenameOut)))
        f_out.write(result)
