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
#import scipy 							#特殊三对角矩阵求解
import numpy as np 						#用于数学计算(曲线拟合、积分等)

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
                print '[info]: ' + path+' Create success!'
                return True
        else:   #如果目录存在则不创建，并提示目录已经存在
                print '[info]: ' + path+' aleady exist!'
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

def shuffle_info(anchor, isAnchor):
    anchordata    = csv.reader(open(anchor), quotechar="'") ## 'r'
    count_num = -1
    index_num =  0

    oriBit_arr   = np.zeros(4)
    testBit_arr  = np.zeros(4)
    oriPSNR_arr  = np.zeros(4)
    testPSNR_arr = np.zeros(4)
    oriTime_arr  = np.zeros(4)
    testTime_arr = np.zeros(4)

    for anchor_line in anchordata:
        count_num = count_num + 1
        if count_num == 0:
            continue
        #print anchor_line
        seq_name=anchor_line[0].split('_br')[0]
        #print seq_name
        bitrate = anchor_line[2]
        #print bitrate
        Y_PSNR  = anchor_line[3]
        U_PSNR  = anchor_line[4]
        V_PSNR  = anchor_line[5]
        time    = anchor_line[-1]
        #print bitrate
        if isAnchor == 1:
            oriBit_arr[index_num]   = bitrate
            oriPSNR_arr[index_num]  = Y_PSNR
            oriTime_arr[index_num]  = time
        else:
            testBit_arr[index_num]   = bitrate
            testPSNR_arr[index_num]  = Y_PSNR
            testTime_arr[index_num]  = time    
        index_num=index_num+1
        if index_num == 4:
            index_num = 0
            if isAnchor == 1:
                #print seq_name, oriBit_arr
                origBit_dict[seq_name]  = oriBit_arr.copy()  #深拷贝
                origPSNR_dict[seq_name] = oriPSNR_arr.copy()
                origTime_dict[seq_name] = oriTime_arr.copy()
                seqName_dict[count_num/4] = seq_name
                #print origBit_dict
                #print origPSNR_dict
                #print origTime_dict
                #print seqName_dict
            else:
                testBit_dict[seq_name]  = testBit_arr.copy()
                testPSNR_dict[seq_name] = testPSNR_arr.copy()
                testTime_dict[seq_name] = testTime_arr.copy()
                #print testBit_dict
                #print testPSNR_dict
                #print testTime_dict
    return (count_num/4)

def pchip_end(h1, h2, del1, del2):
    d = ((2*h1 + h2)*del1 - h1*del2) / (h1 + h2)
    if np.sign(d) != np.sign(del1):
        d = 0
    elif np.sign(del1) != np.sign(del2) and np.abs(d) > np.abs(3*del1):
        d = 3 * del1
    return d

def pchip_slopes(h, delta):
    d = np.zeros(len(h) + 1)
    k = np.argwhere(np.sign(delta[:-1]) * np.sign(delta[1:]) > 0).reshape(-1) + 1
    w1 = 2*h[k] + h[k-1]
    w2 = h[k] + 2*h[k-1]
    d[k] = (w1 + w2) / (w1 / delta[k-1] + w2 / delta[k])
    d[0] = pchip_end(h[0], h[1], delta[0], delta[1])
    d[-1] = pchip_end(h[-1], h[-2], delta[-1], delta[-2])
    return d

def spline_slopes(h, delta):
    a, r = np.zeros([3, len(h)+1]), np.zeros(len(h)+1)
    a[0, 1], a[0, 2:] = h[0] + h[1], h[:-1]
    a[1, 0], a[1, 1:-1], a[1, -1] = h[1], 2*(h[:-1] + h[1:]), h[-2]
    a[2, :-2], a[2, -2] = h[1:], h[-1] + h[-2]

    r[0] = ((h[0] + 2*a[0, 1])*h[1]*delta[0] + h[0]**2*delta[1]) / a[0, 1]
    r[1:-1] = 3*(h[1:] * delta[:-1] + h[:-1] * delta[1:])
    r[-1] = (h[-1]**2*delta[-2] + (2*a[2, -2] + h[-1])*h[-2]*delta[-1]) / a[2, -2]

    d = scipy.linalg.solve_banded((1, 1), a, r)
    return d

class PCHIP:
    def __init__(self, x, y, use_spline=False):
        assert len(np.unique(x)) == len(x)
        #将数据按x坐标从小到大排序
        order = np.argsort(x)
        self.xi, self.yi = x[order], y[order]

        #求输入x、y的间隔，按间隔计算delta
        h = np.diff(self.xi)
        delta = np.diff(self.yi) / h

        self.d = spline_slopes(h, delta) if use_spline else pchip_slopes(h, delta)
        self.c = (3*delta - 2*self.d[:-1] - self.d[1:]) / h
        self.b = (self.d[:-1] - 2*delta + self.d[1:]) / h**2

        """
        The piecewise function is like p(x) = y_k + s*d_k + s*s*c_k + s*s*s*b_k
        where s = x - xi_k, k is the interval includeing x.
        So the original function of p(x) is P(x) = s*y_k + 1/2*s*s*d_k + 1/3*s*s*s*c_k + 1/4*s*s*s*s*b_k + C.
        """
        self.interval_int_coeff = []
        self.interval_int = np.zeros(len(x)-1)
        for i in range(len(x)-1):
            self.interval_int_coeff.append(np.polyint([self.b[i], self.c[i], self.d[i], self.yi[i]]))
            self.interval_int[i] = np.polyval(self.interval_int_coeff[-1], h[i]) - np.polyval(self.interval_int_coeff[-1], 0)

    def _integral(self, lower, upper):
        assert lower <= upper
        if lower < np.min(self.xi):
            lower = np.min(self.xi)
            print('Warning: The lower bound is less than the interval and clipped!')
        elif lower > np.max(self.xi):
            print('Warning: The lower bound is greater than the interval!')
            return 0
        if upper > np.max(self.xi):
            upper = np.max(self.xi)
            print('Warning: The upper bound is greater than the interval and clipped!')
        elif upper < np.min(self.xi):
            print('Warning: The lower bound is less than the interval!')
            return 0
        left = np.arange(len(self.xi))[self.xi - lower > -1e-6][0]
        right = np.arange(len(self.xi))[self.xi - upper < 1e-6][-1]

        inte = np.sum(self.interval_int[left:right])
        if self.xi[left] - lower > 1e-6:
            inte += (np.polyval(self.interval_int_coeff[left-1], self.xi[left]-self.xi[left-1]) - np.polyval(self.interval_int_coeff[left-1], lower-self.xi[left-1]))
        if self.xi[right] - upper < -1e-6:
            inte += (np.polyval(self.interval_int_coeff[right], upper-self.xi[right]) - np.polyval(self.interval_int_coeff[right], 0))
        return inte

    def integral(self, lower, upper):
        if lower > upper:
            return -self._integral(upper, lower)
        else:
            return self._integral(lower, upper)

def computeBDRate(testNum, basePSNR, baseBitrate, testPSNR, testBitrate, piecewise=True):
    #码率取对数
    baseLogBitrate = np.log10(baseBitrate)
    testLogBitrate = np.log10(testBitrate)
    #确定共同范围
    minPSNR = np.max((np.min(basePSNR), np.min(testPSNR)))
    maxPSNR = np.min((np.max(basePSNR), np.max(testPSNR)))
    if piecewise == True:
        baseIntegral = PCHIP(basePSNR, baseLogBitrate, use_spline=False).integral(minPSNR, maxPSNR)
        testIntegral = PCHIP(testPSNR, testLogBitrate, use_spline=False).integral(minPSNR, maxPSNR)
    else:
        #拟合曲线
        baseFitting = np.polyfit(basePSNR, baseLogBitrate, testNum-1)
        testFitting = np.polyfit(testPSNR, testLogBitrate, testNum-1)
        #不定积分
        baseIndefiniteInt = np.polyint(baseFitting)
        testIndefiniteInt = np.polyint(testFitting)
        #求积分
        baseIntegral = np.polyval(baseIndefiniteInt, maxPSNR) - np.polyval(baseIndefiniteInt, minPSNR)
        testIntegral = np.polyval(testIndefiniteInt, maxPSNR) - np.polyval(testIndefiniteInt, minPSNR)

    #平均差值
    meanEXPDiff = (testIntegral - baseIntegral) / (maxPSNR - minPSNR)
    meanDiff = (np.power(10, meanEXPDiff) - 1)

    return meanDiff



####################################main 函数入口####################################################
if __name__ == '__main__':
    if(len(sys.argv) < 4):
        print('Usage: auto_data_analysis.py ' + '<anchor outDir refer> '  + '\n')
        print("For example: auto_data_collect.py anchor_result ./out refer_result ")
        print('Notice: <> is necessary, [] is optional')
        exit()
    anchor = sys.argv[1]
    outDir = sys.argv[2]
    refer1 = sys.argv[3]
    #if (len(sys.argv) > 4):
    #    refer2 = sys.argv[4]

    make_all_dir(outDir)

    outExcelData = outDir + delimiter +'__result_BDBR.csv'
    create_excel(outExcelData)

    pFile = open(outExcelData, 'w') #创建汇总文件，性能数据
    #totaltitle = 'filename' + ' '*(42 - len('#filename') + 15) + 'total_frames'+ 10*' ' + 'bitrate'  + 10*' ' + 'PSNR' + 10*' ' + 'time(s)'
    totaltitle = 'filename' + ' '*(42 - len('#filename') + 15) + 'BD-rate(PieceWise curve)(%)'  + 10*' ' + 'BD-rate(curve)(%)'  + 10*' ' \
    + 'Delta_Y-PSNR(dB)' + 10*' ' + 'Delta_U-PSNR(dB)' + 10*' ' + 'Delta_V-PSNR(dB)' + 10*' ' + 'Delta_time(s)'
    pFile.writelines(totaltitle)
    pFile.write('\n')
    pFile.close()
      
    origBit_dict  = collections.OrderedDict()  ## key: seq_name value: bitrate
    origPSNR_dict = collections.OrderedDict()
    testBit_dict  = collections.OrderedDict()
    testPSNR_dict = collections.OrderedDict()
    origTime_dict = collections.OrderedDict()
    testTime_dict = collections.OrderedDict()
    seqName_dict  = collections.OrderedDict()  ## key: index_num  value: seq_name

    ## 1.读取anchor数据并提取bitrate,PSNR和time信息
    shuffle_info(anchor, 1)
    ## 2.读取ref数据并提取bitrate,PSNR和time信息
    seq_num = shuffle_info(refer1, 0)
    #print seq_num

    #for key in origBit_dict:
        #print seqName_dict[2]
        #print (key + ':' + str(origBit_dict[key]))
    BDBRP_avg  = 0
    BDBR_avg   = 0
    Delta_time = 0.0
    ## 3. 计算BD-rate(Piecewise curve)和BD-rate(curve)
    for index_num in range(1, seq_num + 1): 
        #print filename, origBit_dict[filename]
        filename = seqName_dict[index_num]
        BDBR_P = computeBDRate(index_num, origPSNR_dict[filename], origBit_dict[filename], \
                         testPSNR_dict[filename], testBit_dict[filename], True)
        BDBR_P = float('%.3f' %(BDBR_P * 100))
        BDBRP_avg += BDBR_P
        print index_num, filename, str(float('%.3f'  %((BDBR_P)))) + '%'
        
        BDBR = computeBDRate(index_num, origPSNR_dict[filename], origBit_dict[filename], \
                         testPSNR_dict[filename], testBit_dict[filename], False)
        BDBR = float('%.3f' %(BDBR * 100))
        BDBR_avg += BDBR
        print index_num, filename, str(float('%.3f'  %((BDBR)))) + '%'
        
        #print origPSNR_dict[filename]
        #print testPSNR_dict[filename]
        Delta_YUVPSNR = origPSNR_dict[filename] - testPSNR_dict[filename]
        Delta_YUVPSNR[0] = float('%.3f' %Delta_YUVPSNR[0])
        Delta_YUVPSNR[1] = float('%.3f' %Delta_YUVPSNR[1])
        Delta_YUVPSNR[2] = float('%.3f' %Delta_YUVPSNR[2])
        #print Delta_Y_PSNR[0]

        Delta_time_list   =  ((testTime_dict[filename] - origTime_dict[filename])/ \
            origTime_dict[filename]) *100
        for i in Delta_time_list:
            #print type(Delta_time)
            Delta_time = Delta_time + i
        Delta_time = float(Delta_time / len(Delta_time_list))
        Delta_time = float('%.3f' %(Delta_time))
        print str(Delta_time) + '%'

        pFile = open(outExcelData, 'a+')
        oneline = filename + ' '*(30-len(filename)+15)  \
	        + str(BDBR_P) + 10*' ' + str(BDBR) + 10*' ' + str(Delta_YUVPSNR[0]) + 10*' ' \
            + str(Delta_YUVPSNR[1]) + 10*' ' + str(Delta_YUVPSNR[2]) + 10*' ' + str(Delta_time) + '\n'
        pFile.write(oneline)
        pFile.close()

    BDBRP_avg = BDBRP_avg/seq_num
    BDBR_avg  = BDBR_avg / seq_num

    pFile = open(outExcelData, 'w') #创建汇总文件，性能数据
    #totaltitle = 'filename' + ' '*(42 - len('#filename') + 15) + 'total_frames'+ 10*' ' + 'bitrate'  + 10*' ' + 'PSNR' + 10*' ' + 'time(s)'
    totaltitle = 'Average' + ' '*(42 - len('#filename') + 15) + 'BD-rate(PieceWise curve)(%)'  + 10*' ' + 'BD-rate(curve)(%)'  + 10*' ' \
    + 'Delta_Y-PSNR(dB)' + 10*' ' + 'Delta_U-PSNR(dB)' + 10*' ' + 'Delta_V-PSNR(dB)' + 10*' ' + 'Delta_time(s)'
    pFile.writelines(totaltitle)
    pFile.write('\n')
    pFile.close()

    ## 4.绘制率失真曲线图

    ret = 0
    if(ret != -1):
        print("---------Process finished!---------")
        os._exit(0)
