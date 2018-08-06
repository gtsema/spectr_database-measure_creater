# -*- coding: utf-8 -*-
'''
Created on 16.02.2018.

@author: Greg
'''
import scipy.integrate as integrate
import scipy.interpolate as interpolate
import pandas as pd
import os, sys, collections, random
#-------------------------------------------------------------------------------------------------------
def obj_dataset(path, filename):
    with open(path + '\\' + filename) as file:
        data = file.readlines()
        
    dataset = pd.DataFrame(columns=('wavelength', 'reflectance', 'deviation'))
    WavelengthFactorFlag = False
    
    for i in range(16, len(data)):
        datastring = data[i].strip().split('      ')
        
        if float(datastring[0]) < 0:
            continue
            
        if not WavelengthFactorFlag:
            WavelengthFactor = 1000 if(int(datastring[0][0]) == 0) else 100
            WavelengthFactorFlag = True
                    
        if ((float(datastring[0]) * WavelengthFactor) >= 361 and ((float(datastring[0]) * WavelengthFactor) <= 890) and float(datastring[1]) > 0):
            
            dataset = dataset.append(pd.DataFrame([[int(float(datastring[0]) * WavelengthFactor),
                                                    float(datastring[1]),
                                                    float(datastring[2])]],
                                                    columns=('wavelength', 'reflectance', 'deviation')),
                                                    ignore_index=True)
        else:
            continue
    return {data[14].strip() : dataset}
#-------------------------------------------------------------------------------------------------------
def measure_dataset(path, filename, n):
    with open(path + '\\' + filename) as file:
        data = file.readlines()
    
    result = {}
    WavelengthFactorFlag = False
    
    for j in range(1, n + 1):
        dataset = pd.DataFrame(columns=('wavelength', 'reflectance'))
        for i in range(16, len(data)):
            datastring = data[i].strip().split('      ')
        
            if float(datastring[0]) < 0:
                continue
            
            if not WavelengthFactorFlag:
                WavelengthFactor = 1000 if(int(datastring[0][0]) == 0) else 100
                WavelengthFactorFlag = True
                    
            if ((float(datastring[0]) * WavelengthFactor) >= 361 and ((float(datastring[0]) * WavelengthFactor) <= 890)
                                                                 and float(datastring[1]) > 0 
                                                                 and float(datastring[2]) > 0):
            
                dataset = dataset.append(pd.DataFrame([[int(float(datastring[0]) * WavelengthFactor),
                                                        random.normalvariate(float(datastring[1]), float(datastring[2]))]],
                                                        columns=('wavelength', 'reflectance')),
                                                        ignore_index=True)
            elif((float(datastring[0]) * WavelengthFactor) >= 361 and ((float(datastring[0]) * WavelengthFactor) <= 890)
                                                                  and float(datastring[1]) > 0 
                                                                  and float(datastring[2]) <= 0):
                dataset = dataset.append(pd.DataFrame([[int(float(datastring[0]) * WavelengthFactor), 0]], 
                                                        columns=('wavelength', 'reflectance')), ignore_index=True)
            else:
                continue
            
        result.update({str(data[14].strip()) + '_' + str(j) : dataset})
    return result
#-------------------------------------------------------------------------------------------------------
def filter_database(path):
    fltDataBase = collections.OrderedDict()
    files = sorted([file for file in os.listdir(path) if file.lower().endswith('.xlsx')], key=len)
    for file in files:
        get_fil = pd.read_excel(path + '\\' + file)
        filx = get_fil['Wavelength (nm)']
        fily = get_fil['% Transmission']
        dataset = pd.concat([filx, fily], axis=1, ignore_index=True)
        dataset.columns = ['wavelength', 'transmission']
        fltDataBase.update({file.split('.')[0] : dataset})
    return fltDataBase
#-------------------------------------------------------------------------------------------------------
def get_integral_value(flt, obj):

    fltFunction = interpolate.interp1d(flt.wavelength, flt.transmission)

    fltDataMin = min(flt.wavelength)
    fltDataMax = max(flt.wavelength)

    cropObj_data = obj[(obj.wavelength >= fltDataMin) & (obj.wavelength <= fltDataMax)].reset_index(drop=True)
    
    newxFltData = cropObj_data.wavelength.reset_index(drop=True)
    newxFltData = pd.to_numeric(newxFltData)
    
    newyFltData = fltFunction(newxFltData)
    
    newFlt_data = pd.DataFrame({'wavelength' : newxFltData, 'transmission' : newyFltData})
  
    prodFltObj = pd.DataFrame({'wavelength' : newFlt_data.wavelength, 'reflectance' : newFlt_data.transmission * cropObj_data['reflectance']})
    
    result = integrate.trapz(prodFltObj.reflectance, x = prodFltObj.wavelength)
    
    return result
#-------------------------------------------------------------------------------------------------------
def main(*args):
    PATH = os.getcwd()
    FLT_PATH = PATH + '\\' + 'filters'
    OBJ_PATH = PATH + '\\' + 'objects_test'
    
    filters = filter_database(FLT_PATH)
    
    ObjDataBase = pd.DataFrame() # result
    objFiles = sorted([file for file in os.listdir(OBJ_PATH) if file.lower().endswith('.asc')], key=len)
    
    for file in objFiles:
        
        os.system('cls')
        print('Выполнено %d' % (objFiles.index(file)*100/len(objFiles)) + '%')
        
        if(len(args) == 0):
            objDict = obj_dataset(OBJ_PATH, file)
        else:
            objDict = measure_dataset(OBJ_PATH, file, int(args[0]))
        
        for key in objDict:
            objName = key
            objData = objDict.get(key)
            ObjIntegralValue = []
            
            for flt in filters:
                ObjIntegralValue.append("{0:.3f}".format(get_integral_value(filters.get(flt), objData)))
                
            ObjDataBase = ObjDataBase.append(pd.DataFrame([ObjIntegralValue], columns = ['Filter_1(400)', 'Filter_2(450)', 'Filter_3(500)', 'Filter_4(550)', 'Filter_5(600)', 
                                                                                         'Filter_6(650)', 'Filter_7(700)', 'Filter_8(750)', 'Filter_9(800)', 'Filter_10(850)'],
                                                                                         index=[objName]))
    os.system('cls')
    print('Выполнено 100%')
    ObjDataBase.to_csv(OBJ_PATH + '\\data.csv')
#-------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
 
    sys.argv.pop(0)
    if(len(sys.argv) == 0):
        print(u'нужно указать ключ')
    elif(len(sys.argv) == 1 and sys.argv[0] == '-d'):
        main()
    elif(len(sys.argv) == 2 and sys.argv[0] == '-m' and sys.argv[1].isdigit()):
        main(int(sys.argv[1]))
    else: print('error')
