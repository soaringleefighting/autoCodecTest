#-*- coding:utf-8 -*-
# Function: get data from multiple txt with certern format to excel

import os
import re
import sys
import glob
import shutil
import commands
import subprocess
import subprocess as sub
import csv
import codecs
from collections import OrderedDict

space = ' '
delimiter = '/'
MAX_FILE_NAME = 100

#new excel file
def create_excel(excel_name):
    file = open(excel_name,'wb')
    writer=csv.writer(file)
    file.close()

#extract file name
def get_file_name(fullfilename):
    tmp = fullfilename.strip()
    name = os.path.split(tmp)[-1]  #提取出文件名，不包含路径
    return os.path.splitext(name)[0] 

#获取目录以及子目录下的所有文件
allfiles = []
def get_all_files(rawdir):
    allfilelist = os.listdir(rawdir)
    for f in allfilelist:
        filepath = os.path.join(rawdir, f)
        if os.path.isdir(filepath):
            get_all_files(filepath)
        allfiles.append(filepath)
    return allfiles

def make_all_dir(path):
    path = path.strip()
    isExist = os.path.exists(path)
    if (not isExist):
        os.makedirs(path)
        print(path+' Successful Create!')
        return True

#获取特定类型的文件
def get_raw_log(rawdir):
    isfile = 0
    if os.path.isdir(rawdir):
        get_all_files(rawdir)
        files = [f for f in allfiles if re.search('txt$',f)]
    elif os.path.isfile(rawdir):
        iffile = 1
        files = [rawdir]
    else:
        files = []
        print("Error: " + sys.argv[1] + " is not a dir or file!")
    files.sort(key=str.lower)
    return [files, isfile]


count = [0,0]
# collect data
def collect_data_to_excel(excelname, inputfile):
    pFile = open(inputfile, 'a+')
    lines = pFile.readlines()
    data = OrderedDict()
    splitValue = []
    filename = get_file_name(inputfile)
    for i in range(len(lines)):
        #print lines
        if lines[i].find('"mac":') != -1 and i==8:
            splitValue = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue
            data[filename] = [str(splitValue)+'\t', 0, 0, 0, 0, 0, 0]
        if lines[i].find('"imei":') != -1 and i==43:
            splitValue2 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue2
            data[filename][2] = str(splitValue2)+'\t'
        if lines[i].find('"imsi":') != -1 and i==44:
            splitValue3 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue3
            data[filename][3] = str(splitValue3)+'\t'
        if lines[i].find('"iccid":') != -1 and i==45:
            splitValue1 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue1
            data[filename][1] = str(splitValue1)+'\t'
        if lines[i].find('"imei":') != -1 and i==95:
            splitValue4 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue4
            data[filename][5] = str(splitValue4)+'\t'
        if lines[i].find('"imsi":') != -1 and i==96:
            splitValue5 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue5
            data[filename][6] = str(splitValue5)+'\t'
        if lines[i].find('"iccid":') != -1 and i==97:
            splitValue6 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue6
            data[filename][4] = str(splitValue6)+'\t'
    with open(excelname, 'a+') as f:  #newline=''
        csv_writer = csv.writer(f, dialect='excel', lineterminator='\n') #, dialect='excel' 
        if count[0]==0: 
            title=['MAC', 'ICCID', 'IMEI', 'IMSI', 'ICCID', 'IMEI', 'IMSI']
            csv_writer.writerow(title)
            count[0]=count[0]+1
        for key, value in data.items():
            csv_writer.writerow(value)    

    #pFile = open(excelname, 'ab+')  # newline=''
    #csv_writer = csv.writer(pFile, dialect='excel')
    #if count[0]==0: 
    #    title=['MAC', 'ICCID', 'IMEI', 'IMSI', 'ICCID', 'IMEI', 'IMSI']
    #    csv_writer.writerow(title)
    #    count[0]=count[0]+1
    #for key, value in data.items():
    #    csv_writer.writerow(value)
    pFile.close()


########main Function Entry##########
if __name__ == '__main__':
    #if(len(sys.argv) < 3):
    #    print("Usage: autoExtractToExcel.py targetDir outResultDir\n")
    #    sys.exit(1)
    collectDataDir = 'data' #sys.argv[1]
    outResultDir   = 'out'  #sys.argv[2]
    
    if(not os.path.exists(outResultDir)):
        make_all_dir(outResultDir)
    outExcelData   = outResultDir + delimiter + '__result.csv'
    create_excel(outExcelData)
    [files,isfile] = get_raw_log(collectDataDir) #获取当前目录中指定格式的文件
  
    #遍历每个指定格式的文件进行数据提取
    for collectData in files:
        print('[Process]: '+collectData)
        ret = collect_data_to_excel(outExcelData,collectData)
    if(ret!=0):
        print("--------Process finished!--------")
        os._exit(0)
