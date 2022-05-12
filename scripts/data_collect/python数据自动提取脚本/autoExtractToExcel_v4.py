#-*- coding:utf-8 -*-
# Function: get data from multiple txt with certern format to excel

import os
import re
import sys
import glob
import filecmp
import shutil
import commands
import subprocess
import subprocess as sub
import csv
import codecs
from collections import OrderedDict
import collections
import xlrd
import xlwt
from   xlutils.copy import copy

space = ' '
delimiter = '/'
MAX_FILE_NAME = 100

reload(sys)
sys.setdefaultencoding('utf-8')

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
            print splitValue
            data[filename] = [str(splitValue)+'\t', 0, 0, 0, 0, 0, 0]
        if lines[i].find('"imei":') != -1 and i==43:
            splitValue2 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            print splitValue2
            data[filename][2] = str(splitValue2)+'\t'
        if lines[i].find('"imsi":') != -1 and i==44:
            splitValue3 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            print splitValue3
            data[filename][3] = str(splitValue3)+'\t'
        if lines[i].find('"iccid":') != -1 and i==45:
            splitValue1 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            print splitValue1
            data[filename][1] = str(splitValue1)+'\t'
        if lines[i].find('"imei":') != -1 and i==95:
            splitValue4 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            print splitValue4
            data[filename][5] = str(splitValue4)+'\t'
        if lines[i].find('"imsi":') != -1 and i==96:
            splitValue5 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            print splitValue5
            data[filename][6] = str(splitValue5)+'\t'
        if lines[i].find('"iccid":') != -1 and i==97:
            splitValue6 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            print splitValue6
            data[filename][4] = str(splitValue6)+'\t'
    with open(excelname, 'ab+') as f:  #newline=''
        csv_writer = csv.writer(f, dialect='excel') #, dialect='excel'
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


#从文本中提取数据到格式化文本文件中
def get_data_from_txt(txtfile, outdatafile):
    pFile = open(txtfile, 'a+')
    lines = pFile.readlines() #读取文本中所有行
    filename = get_file_name(txtfile)
    data  = OrderedDict()

    for i in range(len(lines)):
        #print lines
        if lines[i].find('"mac":') != -1 and i==8:
            splitValue = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue
            data[filename] = [str(splitValue), 0, 0, 0, 0, 0, 0]
        if lines[i].find('"imei":') != -1 and i==43:
            splitValue2 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue2
            data[filename][2] = str(splitValue2)
        if lines[i].find('"imsi":') != -1 and i==44:
            splitValue3 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue3
            data[filename][3] = str(splitValue3)
        if lines[i].find('"iccid":') != -1 and i==45:
            splitValue1 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue1
            data[filename][1] = str(splitValue1)
        if lines[i].find('"imei":') != -1 and i==95:
            splitValue4 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue4
            data[filename][5] = str(splitValue4)
        if lines[i].find('"imsi":') != -1 and i==96:
            splitValue5 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue5
            data[filename][6] = str(splitValue5)
        if lines[i].find('"iccid":') != -1 and i==97:
            splitValue6 = (lines[i].split())[0].split(",")[0].split("\"")[-2].strip()
            #print splitValue6
            data[filename][4] = str(splitValue6)
	pFile.close()
	pFile = open(outdatafile, 'w+')

    for key, value in data.items():
        oneline = value
	#oneline = filename + ' ' + data[filename]
    #print ','.join(oneline)
    pFile.write(','.join(oneline))
    pFile.close()

#collect data from format text to BDBR excel for ref data
count_row = [3,0]
def collect_data_to_excel_target(exceldata, datawt, inputfile, outexcel):
    pFile = open(inputfile, 'a+')
    lines = pFile.readlines()
    data = collections.OrderedDict()  ##使用有序字典
    splitValue = lines[0].strip().split(',')
    #print splitValue

    #exceldata.sheet_names()
    #print("sheets: " + str(exceldata.sheet_names()))
    table    = exceldata.sheet_by_name('MAC')
    #print format(datawt)
    table_wt = datawt.get_sheet('MAC')
    #print("Total rows: " + str(table.nrows))
    #print("Total columns: " + str(table.ncols))

    ##遍历excel中每一行，存在匹配的字符串则写入对应的data信息
    table_wt.write(count_row[0], 1, splitValue[0]) # MAC
    table_wt.write(count_row[0], 4, splitValue[1]) # ICCID
    table_wt.write(count_row[0], 5, splitValue[2]) # IMEI
    table_wt.write(count_row[0], 6, splitValue[3]) # IMSI
    table_wt.write(count_row[0], 7, splitValue[4]) # ICCID
    table_wt.write(count_row[0], 8, splitValue[5]) # IMEI
    table_wt.write(count_row[0], 9, splitValue[6]) # IMSI
    count_row[0]=count_row[0]+1
    datawt.save(outexcel)
    return 0

########Main Function Entrance##########
if __name__ == '__main__':
    #if(len(sys.argv) < 3):
    #    print("Usage: autoExtractToExcel.py targetDir outResultDir\n")
    #    sys.exit(1)
    collectDataDir = 'data' #sys.argv[1]
    outResultDir   = 'out'  #sys.argv[2]
    
    if(not os.path.exists(outResultDir)):
        make_all_dir(outResultDir)
    #outExcelData   = outResultDir + delimiter + '__result.csv'
    #create_excel(outExcelData)
    outExcelData = collectDataDir + delimiter + 'MAC-1.xls'         ##该文件是BDBR格式文件，不要修改
    outexcel     = outResultDir   + delimiter + 'MAC-1_result.xls'  ##该文件是统计得到的BDBR数据文件
    create_excel(outexcel)
 
    exceldata = xlrd.open_workbook(outExcelData, encoding_override="gbk")
    datawt    = copy(exceldata)  ##完成xlrd对象向xlwt对象转换
    [files, isfile] = get_raw_log(collectDataDir) #获取当前目录中指定格式的文件
  
    #遍历每个指定格式的文件进行数据提取
    for collectdata in files:
        print('[Process]: '+collectdata) 
        filename = get_file_name(collectdata) ## 获取文件名
        #ret = collect_data_to_excel(outExcelData, collectdata)
        outrawtxt = outResultDir + delimiter + filename + '_format_data.txt'  ##格式化文本数据
        get_data_from_txt(collectdata, outrawtxt) ##提取数据信息到格式化文本数据中
        ret = collect_data_to_excel_target(exceldata, datawt, outrawtxt, outexcel) ## 写入目标Excel中
    if(ret!=0):
        print("--------Process finished!--------")
        os._exit(0)
