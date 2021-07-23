#_*_ coding=utf-8_*_  #脚本中有中文注释必须包含这一句

#######################################################################################
##脚本功能： 本脚本用于将统一规范输出txt（比如HM输出或者其他自定义输出）中的特定数据提取到excel中
##脚本用法： python auto_data_collect.py srcDir outDir 
##参数说明：	srcDir		:	原始数据存放的文件夹
##              outDir          :       数据输出excel
##
## Created by lipeng at July 10 2020
## Version 1.0
## Modified:
## 2020.7.10 create tag V1.0
## 2020.7.16 create tag V2.0 suppport BDBR collect
#######################################################################################
import os
import re
import sys
import glob
import filecmp
import shutil
import subprocess
import subprocess as sub
import csv
import codecs
from   collections import OrderedDict
import collections
import xlrd
import xlwt
from   xlutils.copy import copy


space = ' '
delimiter = '/'

reload(sys)
sys.setdefaultencoding('utf-8')

#比较两个文件是否相同, 相同则返回True, 不同返回False
def	yuv_cmp(file1,file2):
	isNul1 = os.path.getsize(file1)
	isNul2 = os.path.getsize(file2)
	if((not isNul1) or (not isNul2)):
		return False
	if(isNul1 == isNul2):
		return True

#提取文件的名字
def get_file_name(fullfilename):
	tmp = fullfilename.strip()
	name = os.path.split(tmp)[-1]   #提取文件名，不包含路径
	return os.path.splitext(name)[0] #提取文件名，不包含后缀

#创建文件目录
def make_all_dir(path):	
	path = path.strip() #去除首位空格
	path=path.rstrip("\\")  #去除尾部\符号

	isExist = os.path.exists(path) #判断路径是否存在
        if not isExist:        #如果不存在则创建目录
                os.makedirs(path)
                print path+' Create success!'
                return True
        else:   #如果目录存在则不创建，并提示目录已经存在
                print path+' aleady exist!'
                return False

#获取数据文件
def	get_raw_data(rawdir):
	isfile = 0
	if os.path.isdir(rawdir):
		allfiles = os.listdir(rawdir)
		files = [rawdir+"/"+f for f in allfiles if re.search('txt$',f) or  re.search('log$',f)]
	elif os.path.isfile(rawdir):
		isfile = 1
		files = [rawdir]
	else:
		files = []
		print("ERROR: " + sys.argv[1] + "  is not a dir or file!")
	files.sort(key=str.lower)
	return [files,isfile]

#create new excel file
def create_excel(excel_name):
    file = open(excel_name,'wb')
    writer=csv.writer(file)
    file.close()

#从文本中提取数据
#下面示例主要针对SCM输出提取bitrate,Y-PSNR,time    
def get_data_from_txt(filename, txtfile, outdatafile):
	pFile = open(txtfile, 'a+')
	lines = pFile.readlines() #读取文本中所有行
	lineflag = 0
	#Data = {}  #dictionary
	for i in range(len(lines)):
	    if lines[i].find('Bytes written to file') != -1:	    
		word = lines[i].split(':')
		lineflag = 0
		#print word
	        splitvalue = (word[1].strip().split('kbps'))
                bitrate=splitvalue[0].strip().split('(')[1]
            if lines[i].find('Total Time:') != -1:
                 word = lines[i].split(':')
                 #print word[1].strip().split('sec.')[0]
                 time=word[1].strip().split('sec.')[0]
            if lines[i].find('Average: 	       20    a') != -1:
                 word = lines[i].split(':')
                 #print word[1].strip().split('   ')[3]
                 psnr=word[1].strip().split('   ')[3]  
	pFile.close()
	pFile = open(outdatafile, 'w+')

        #oneline = filename + ' '*(30-len(filename)+5) + \
	#			str(bitrate) + ' '*12 + str(psnr)+' '*5+ str(time) + '\n'
	oneline = filename + ' ' + str(bitrate) + ' ' + str(psnr)+' '+ str(time) 
        #print oneline
        pFile.write(oneline)
        pFile.close()

count = 0
#collect data from format text to excel
def collect_data_to_excel(excelname, inputfile):
    pFile = open(inputfile, 'a+')
    lines = pFile.readlines()
    #data = {}  ##默认字典是无序的(hash)
    data = collections.OrderedDict()  ##使用有序字典
    #splitValue = []
    #for i in range(len(lines)):
        #if lines[i].find('Anchor') != -1:
        #    splitValue = ((lines[i].split()).split(':')[3]  ##此处根据具体文本数据格式进行分割提取
        #    data[filename] = [filename, splitValue[0], splitValue[1], splitValue[2], splitValue[3], 0]
    splitValue = lines[0].strip().split(' ')
    #print lines[0].strip().split(' ')
    data[splitValue[0]] = [splitValue[0], splitValue[1], splitValue[2], splitValue[3]]
    pFile = open(excelname, 'a+')
    pFile.write(codecs.BOM_UTF8)
    csv_writer=csv.writer(pFile, dialect='excel')
    #if count[0]==0:
    #    title=['name', 'key1', 'key2', 'key3', 'key4', 'key5']
    #    csv_writer.writerow(title)
    #    count[0]=count[0]+1
    global count
    if count==0:  ##第一次打开文件时才写入
        title=['video sequence', 'bitrate（kbps）', 'Y-PSNR(dB)', 'time(sec)']
        csv_writer.writerow(title)
        count=count+1
    for key, value in data.items():
        csv_writer.writerow(value)
    pFile.close()
    return 0

#collect data from format text to BDBR excel for ref data
def collect_data_to_BDBRexcel(exceldata, datawt, inputfile, outexcel):
    pFile = open(inputfile, 'a+')
    lines = pFile.readlines()
    data = collections.OrderedDict()  ##使用有序字典
    splitValue = lines[0].strip().split(' ')
    data[splitValue[0]] = [splitValue[0], splitValue[1], splitValue[2], splitValue[3]]
    #print data
    sequence_name_plus_qp = splitValue[0]
    sequence_name = splitValue[0].split('_qp')[0]
    #print sequence_name
    sequence_qp = splitValue[0].split('_qp')[1]
    #print sequence_qp

    #exceldata.sheet_names()
    #print("sheets: " + str(exceldata.sheet_names()))
    table = exceldata.sheet_by_name('AI-Main')
    table_wt = datawt.get_sheet('AI-Main')
    #print("Total rows: " + str(table.nrows))
    #print("Total columns: " + str(table.ncols))

    ##遍历excel中每一行，存在匹配的字符串则写入对应的bitrate,Y-PSNR和EncT
    nrows = table.nrows
    for i in range(nrows):
        if type(table.col_values(2)[i]) == float:  ##将float类型转换成int类型
            qp = int(table.col_values(2)[i])
        #print str(table.col_values(1)[i])
        if str(table.col_values(1)[i]) == sequence_name and str(qp) == sequence_qp:
            #print i
            table_wt.write(i, 11, splitValue[1]) #write bitrate
            table_wt.write(i, 12, splitValue[2]) #write Y-PSNR
            table_wt.write(i, 15, splitValue[3]) #write EncT(s)
    datawt.save(outexcel)
    return 0


# collect data from format text to BDBR excel for anchor data
def collect_data_to_BDBRexcel_vs(exceldata, datawt, inputfile, outexcel):
    pFile = open(inputfile, 'a+')
    lines = pFile.readlines()
    data = collections.OrderedDict()  ##使用有序字典
    splitValue = lines[0].strip().split(' ')
    data[splitValue[0]] = [splitValue[0], splitValue[1], splitValue[2], splitValue[3]]
    #print data
    sequence_name_plus_qp = splitValue[0]
    sequence_name = splitValue[0].split('_qp')[0]
    #print sequence_name
    sequence_qp = splitValue[0].split('_qp')[1]
    #print sequence_qp

    #exceldata.sheet_names()
    #print("sheets: " + str(exceldata.sheet_names()))
    table = exceldata.sheet_by_name('AI-Main')
    table_wt = datawt.get_sheet('AI-Main')
    #print("Total rows: " + str(table.nrows))
    #print("Total columns: " + str(table.ncols))

    ##遍历excel中每一行，存在匹配的字符串则写入对应的bitrate,Y-PSNR和EncT
    nrows = table.nrows
    for i in range(nrows):
        if type(table.col_values(2)[i]) == float:  ##将float类型转换成int类型
            qp = int(table.col_values(2)[i])
        #print str(table.col_values(1)[i])
        if str(table.col_values(1)[i]) == sequence_name and str(qp) == sequence_qp:
            #print i
            table_wt.write(i, 3, splitValue[1]) #write bitrate
            table_wt.write(i, 4, splitValue[2]) #write Y-PSNR
            table_wt.write(i, 7, splitValue[3]) #write EncT(s)
            ## 计算编码节省时间
    datawt.save(outexcel)
    return 0


####################################main 函数入口####################################################
if __name__ == '__main__':
    if(len(sys.argv) < 3):
        print('Usage: auto_data_collect.py ' + '<srcDir outDir>' + ' [ref]' '\n')
        print("For example: auto_data_collect.py ./refdata ./out 1")
        print('Notice: <> is necessary, [] is optional')
        exit()
    srcDir = sys.argv[1]
    outDir = sys.argv[2]
    ref    = sys.argv[3]

    make_all_dir(srcDir)
    make_all_dir(outDir)

    #outExcelData = outDir + delimiter +'__result.csv'
    outExcelData = './' + 'BDBR_calculation.xls'   ##该文件是BDBR格式文件，不要修改
    outexcel = outDir + delimiter + 'BDBR_result.xls'           ##该文件是统计得到的BDBR数据文件

    exceldata = xlrd.open_workbook(outExcelData, encoding_override="gbk")
    datawt = copy(exceldata)  ##完成xlrd对象向xlwt对象转换

    #create_excel(outExcelData)
    [files, isfile]=get_raw_data(srcDir)
    for collectdata in files:
        print('[Process]'+collectdata)
        filename = get_file_name(collectdata)
        outrawtxt = outDir + delimiter + filename + '_format_data.txt'
          # 1.先将数据从文本中提取到有格式文本中 collectdata--->outrawtxt
        get_data_from_txt(filename, collectdata, outrawtxt)  
          # 2.从有格式文本提取数据到excel中 outrawtxt---->outExcelData
        #ret = collect_data_to_excel(outExcelData, outrawtxt)
          # 3.支持从格式文本中提取数据到BDBR excel中
        if ref == '1':
            ret = collect_data_to_BDBRexcel(exceldata, datawt, outrawtxt, outexcel)
        else:
            ret = collect_data_to_BDBRexcel_vs(exceldata, datawt, outrawtxt, outexcel)
    if(ret != -1):
        print("---------Process finished!---------")
        os._exit(0)
