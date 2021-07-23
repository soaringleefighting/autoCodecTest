#_*_ coding=UTF-8_*_  #脚本中有中文注释必须包含这一句

################################################################################################################
##脚本用法： python auto_codec_coherence.py rawDemo srcStreamDir outFileDir [gprofflag outyuvflag refDemo memcheckflag startIdx]
##参数说明：	rawDemo		:	待验证的可执行文件（编码器/解码器）
##				srcStreamDir:	码流/YUV路径
##				outFileDir	:	结果输出路径
##				gprofflag	:	gprof开关(默认为0)：如果取0表示不会利用gprof工具进行分析; 取1表示利用gprof进行分析
##				outyuvflag	:	yuv输出开关(默认为0)：如果取0，表示解码不输出yuv,否则相反。
##				refDemo		: 	参考可执行文件（编码器/解码器）
##				memcheckflag:	使用valgrind进行内存泄露检查(默认为0)(针对linux下编译的64位库)
##				startIdx	: 	在批处理过程中，支持从指定序号startIdx的位置处开始执行。
##
## Author : Created by lipeng at July 3 2020
## Version: 2.0.3
## Revision History:
## (1) 2020.7.3   tag V1.0    支持批量编解码、一致性验证，支持Windows平台(Python)
## (2) 2020.7.6   tag V2.0    支持valgrind和gprof分析
## (3) 2020.7.10  tag V2.0.1  支持对编解码数据进行数据统计(格式输出并导入excel中)
## (4) 2020.7.17  tag V2.0.2  支持BDBR统计分析
## (5) 2021.7.21  tag V2.0.3  支持中断处理功能，区分CBR/VBR配置，支持x264/x265/uavs3e/libaom/vvenc等开源编码器。
################################################################################################################
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

space = ' '
delimiter = '/'

collect = '_pyout_collect'  		#性能对比输出文件夹
cmp_match = '_pyout_match'  		#yuv对比一致
cmp_dismatch = '_pyout_dismatch' 	# yuv对比不一致
Anchor_Ndec = '_pyAnchor_notdecstream'	#待验证的可执行文件不能解码的码流
Reference_Ndec = '_pyRef_notdecstream'	#参考可执行文件不能解码的码流
Anchor_memchecklog = '_pyAnchor_memcheck' #对待验证可执行文件进行内存检查后的汇总文件

#比较两个文件是否相同, 相同则返回True, 不同返回False
def yuv_cmp(file1,file2):
		isNul1 = os.path.getsize(file1)
		isNul2 = os.path.getsize(file2)
		if((not isNul1) or (not isNul2)):
				return False
		if(isNul1 == isNul2):
				return True

#获取码流文件
def get_raw_mpeg4(rawdir):
	isfile = 0
	if os.path.isdir(rawdir):
		allfiles = os.listdir(rawdir)
		print allfiles
		files = [rawdir+"/"+f for f in allfiles if re.search('yuv$',f)]
	elif os.path.isfile(rawdir):
		isfile = 1
		files = [rawdir]
	else:
		files = []
		print("ERROR: " + sys.argv[1] + "  is not a dir or file!")
	files.sort(key=str.lower)
	return [files, isfile]

allfiles = []
def get_raw_data(rawdir):
    for root, dirs, files in os.walk(rawdir):
        for f in files:
            if(re.search('yuv$', f)):
                allfiles.append(os.path.join(root, f))
                #print allfiles
    allfiles.sort(key=str.lower)
    return  allfiles
                              
#提取文件的名字
def get_file_name(fullfilename):
	tmp = fullfilename.strip()
	name = os.path.split(tmp)[-1]   #提取文件名，不包含路径
	return os.path.splitext(name)[0] #提取文件名，不包含后缀

#提取文件的名字(包含后缀)
def get_file_name_ext(fullfilename):
	tmp = fullfilename.strip()
	name = os.path.split(tmp)[-1]   #提取文件名，不包含路径
	return name #提取文件名

#创建文件目录
def make_all_dir(path):
	path = path.strip() #去除首位空格
	path=path.rstrip("\\")  #去除尾部\符号
	isExist = os.path.exists(path) #判断路径是否存在
	if not isExist:        #如果不存在则创建目录
		os.makedirs(path)
		print('[info]: '+ path+'创建成功！')
		return True
	else:   #如果目录存在则不创建，并提示目录已经存在
		print('[info]: '+ path+'目录已存在！')
		return False

#从文本中提取数据
def get_data_from_txt_x265(filename, txtfile, outdatafile, anchor='1'):
	pFile = open(txtfile, 'r')
	lines = pFile.readlines() #读取文本中所有行
	lineflag = 0
	Data = {}  #dictory
	for i in range(len(lines)):
            if lines[i].find('encoded') != -1:
                #print lines[i]
	        word = lines[i].split(',')
	        lineflag = 0
	        bitrate=word[1].split(' ')[1]
	        framenum=word[0].split(' ')[1]
	        PSNR = word[3].split(' ')[3].split('\n')[0]
                time = word[0].split(' ')[4].split('s')[0]
            if lines[i].find('x265 [info]: frame I:') != -1:
                Mean_PSNR = lines[i].strip('\n').split('PSNR Mean:')[-1]
                Y_PSNR_I    = Mean_PSNR.split(' ')[1].split('Y:')[1]
                U_PSNR_I    = Mean_PSNR.split(' ')[2].split('U:')[1]
                V_PSNR_I    = Mean_PSNR.split(' ')[3].split('V:')[1] 
	        frame_numI  = lines[i].strip('\r').strip('\n').split(',')[-2].split(' ')[-1]
	        #print frame_numI        
            if lines[i].find('x265 [info]: frame P:') != -1:
                Mean_PSNR = lines[i].strip('\n').split('PSNR Mean:')[-1]
                Y_PSNR_P    = Mean_PSNR.split(' ')[1].split('Y:')[1]
                U_PSNR_P    = Mean_PSNR.split(' ')[2].split('U:')[1]
                V_PSNR_P    = Mean_PSNR.split(' ')[3].split('V:')[1]
	        frame_numP  = lines[i].strip('\r').strip('\n').split(',')[-2].split(' ')[-1]
	        #print frame_numP
	        frameTotal = int(frame_numI) + int(frame_numP)
	        #print frameTotal
                Y_PSNR = ((float(Y_PSNR_I) * int(frame_numI)) + (float(Y_PSNR_P)*int(frame_numP)))/ frameTotal
                U_PSNR = ((float(U_PSNR_I) * int(frame_numI)) + (float(U_PSNR_P)*int(frame_numP)))/ frameTotal
                V_PSNR = ((float(V_PSNR_I) * int(frame_numI)) + (float(V_PSNR_P)*int(frame_numP)))/ frameTotal 

	pFile.close()
	pFile = open(outdatafile, 'a+')
	if(anchor==1):
            oneline = filename + '(anchor)' + ' '*(30-len(filename)+15) + \
		    framenum + 10*' ' + bitrate + 10*' ' + str(Y_PSNR) + 10*' ' +\
		    str(U_PSNR) + 10*' ' + str(V_PSNR) + 10*' ' + time + '\n'
	else:
            oneline = filename + '(ref)   ' + ' '*(30-len(filename)+10) + \
		    Data['length(bytes) '] + ' '*12 + \
		    Data['fps '] + ' '*5 + '\n'
	pFile.write(oneline)
	pFile.close()
	print("[info]: get_data_from_txt_x265 success!")

def get_data_from_txt_uave3e(filename, txtfile, outdatafile, anchor='1'):
	pFile = open(txtfile, 'a+')
	lines = pFile.readlines() #读取文本中所有行
	Data = {}  #dictory
	for i in range(len(lines)):
            if lines[i].find('bitrate') != -1:
                bitrate = lines[i].split(':')[1].strip('\n')
            if lines[i].find('Encoded frame count')!= -1:
                framenum = lines[i].split('=')[1].strip('\n')
            if lines[i].find('Total encoding time') != -1:
                time = lines[i].split(' ')[-2].strip('\n')
            ###TODO: 增加Y_PSNR, U_PSNR, V_PSNR的解析
            if lines[i].find('PSNR Y(dB)') != -1:
                Y_PSNR = lines[i].split(':')[-1].strip('\n')
            if lines[i].find('PSNR U(dB)') != -1:
                U_PSNR = lines[i].split(':')[-1].strip('\n')
            if lines[i].find('PSNR V(dB)') != -1:
                V_PSNR = lines[i].split(':')[-1].strip('\n')
            
	pFile.close()
	pFile = open(outdatafile, 'a+')
	if(anchor==1):
            oneline = filename + '(anchor)' + ' '*(30-len(filename)+15) + \
		    framenum + 10*' ' + str(bitrate) + 10*' ' + Y_PSNR + 10*' ' + \
		    U_PSNR + 10*' ' + V_PSNR + 10*' ' + str(time) + '\n'
	else:
            oneline = filename + '(ref)   ' + ' '*(30-len(filename)+10) + \
		    Data['length(bytes) '] + ' '*12 + \
		    Data['fps '] + ' '*5 + '\n'
	pFile.write(oneline)
	pFile.close()
        print("[info]: get_data_from_txt_uavs3e success!")

def get_data_from_txt_libaom(filename, txtfile, outdatafile, anchor='1'):
	pFile = open(txtfile, 'a+')
	lines = pFile.readlines() #读取文本中所有行
	lineflag = 0
	Data = {}  #dictory
	for i in range(len(lines)):
            if lines[i].find('Stream 0 PSNR (Overall/Avg/Y/U/V)') != -1:
                #print lines[i]
	        lineflag = 1
	    if lineflag == 1:
	        word = lines[i].split('(Overall/Avg/Y/U/V)')[1].split('bps')[0]
	        word = word.strip(' ').split(' ')
	        print word
	        lineflag = 0
	        bitrate=float('%.3f' % (int(word[-1]) / 1024.0))  # bps-->kbps
	        Y_PSNR = word[2]
	        U_PSNR = word[3]
	        V_PSNR = word[4]
	        print bitrate
	        print Y_PSNR
	        print U_PSNR
	        print V_PSNR
	        time_framenum=lines[i].split('bps')[1].strip(' ')
                time = int(time_framenum.split(' ')[0]) /1000.0  # ms-->sec
                #print time
                framenum=time_framenum.split(' ')[-2]
                #print framenum

	pFile.close()
	pFile = open(outdatafile, 'a+')
	if(anchor==1):
            oneline = filename + '(anchor)' + ' '*(30-len(filename)+15) + \
		    framenum + 10*' ' + str(bitrate) + 10*' ' + Y_PSNR + 10*' ' +\
		    U_PSNR + 10*' ' + V_PSNR + 10*' ' + str(time) + '\n'
	else:
            oneline = filename + '(ref)   ' + ' '*(30-len(filename)+10) + \
		    Data['length(bytes) '] + ' '*12 + \
		    Data['fps '] + ' '*5 + '\n'
	pFile.write(oneline)
	pFile.close()
	print("[info]: get_data_from_txt_libaom success!")
	
#collect data from formated text to excel
count = 0
def collect_data_to_excel(excelname, inputfile, anchor='1', processIdx=0):
	pFile = open(inputfile, 'a+')
	lines = pFile.readlines()
	#data = {}  ##默认字典是无序的(hash)
	data = OrderedDict()  ##使用有序字典
	#splitValue = []

	for i in range(len(lines)):
		if lines[i].find('anchor') != -1 or lines[i].find('ref') != -1:
			#print lines[i]
			splitValue = lines[i].split()  ##此处根据具体文本数据格式进行分割提取
			print(splitValue)
			filename = get_file_name_ext(splitValue[0])
			#print filename
			data[filename] = [filename, splitValue[1], splitValue[2], splitValue[3], splitValue[4], splitValue[5], splitValue[6]]
			
	pFile = open(excelname, 'a+')
	pFile.write(codecs.BOM_UTF8)
	csv_writer=csv.writer(pFile, dialect='excel')
	global count
	if count==0 and processIdx==0:  ##第一次打开文件时才写入
		title=['video sequence', 'total frames', 'bitrate(kbps)', 'Y-PSNR(dB)', 'U-PSNR(dB)', 'V-PSNR(dB)', 'time(s)']
		csv_writer.writerow(title)
		count=count+1
	for key, value in data.items():
		csv_writer.writerow(value)
	pFile.close()

#linux下内存泄漏检查valgrind
def perform_valgrind_data(outFileDir, Anchordeccmd='0', onlystreamname='0', Refdeccmd='0', reserve='0'):
	outmemcheckanchortxt = outFileDir + delimiter  + '__pyMemcheckAnchor.log'
	outmemcheckreftxt = outFileDir + delimiter  + '__pyMemcheckRef.log'
	if Anchordeccmd != '0':
		redirectcmd = Anchordeccmd
		cmd = ' '.join(['valgrind',
						'--log-file='+outmemcheckanchortxt,
						'--leak-check=yes --show-reachable=yes --track-origins=yes',
						redirectcmd])
		print(cmd)
		ret = subprocess.call(cmd, shell=True)
	if Refdeccmd != '0':
		redirectcmd = Refdeccmd
		cmd = ' '.join(['valgrind',
				'--log-file='+outmemcheckreftxt,
				'--leak-check=yes --show-reachable=yes --track-origins=yes',
				redirectcmd])
		print(cmd)
		ret = subprocess.call(cmd, shell=True)
		return ret

#从valgrind输出日志中获取数据
def get_data_from_log(filename, logfile, outdatafile):
	pFile = open(logfile, 'a+')
	lines = pFile.readlines()
	lineflag = 0
	for i in range(len(lines)):
		if lines[i].find('total heap usage') != -1:
			infoline = lines[i]
			print(infoline)
	pFile.close()
	#打开汇总文件filename
	pFile = open(outdatafile, 'a+')
	oneline = '[ ' + filename + ' ]: ' + infoline + '\n'
	pFile.writelines(oneline)
	pFile.close()
	return

#编码或解码处理
def process_encode_decode(rawDemo, srcBinDir, outFileDir, gprof='0', yuvflag='0', refDemo='0', memcheckflag='0', startIdx=0):
	if (os.path.exists(srcBinDir) == False):
		print('[error]: the input file path is not exist')
		return -1
       ## 1.创建输出目录
	make_all_dir(outFileDir)
	if(int(gprof) == 1):
		make_all_dir(outFileDir + '/outgprof') #如果gprof为1,表示需要对代码进行性能分析，需要创建存储性能分析文件的目录
	outtotal = outFileDir + delimiter + collect + '.txt'
	outmatch = outFileDir + delimiter + cmp_match + '.txt'
	outdismatch = outFileDir + delimiter + cmp_dismatch + '.txt'
	outanchorNdec = outFileDir + delimiter + Anchor_Ndec + '.txt'
	outredNdec = outFileDir + delimiter + Reference_Ndec + '.txt'
	outMemchecklog = outFileDir + delimiter + Anchor_memchecklog + '.log'
	outExcelData = outFileDir + delimiter +'__result.csv'  ## excel file

	maxch = 70
	spacesymbo = "-"

	pFileNotdec = open(outanchorNdec, 'w') #默认创建记录基准demo解码失败的文件
	if refDemo != '0': #如果有参考，则创建记录参考demo解码失败的文件
	    pFileRefNdec = open(outredNdec, "w")
	    pFileMatch = open(outmatch, "w+")
	    pFileDismatch = open(outdismatch, "w+")
	pFileAnchorNdec = open(outanchorNdec, 'w')
        pFileRefNdec = open(outredNdec, 'w')
        
        # 采用字典实现4个码率点的列表
        vbr_bitrate= {} # 字典
        vbr_bitrate.setdefault('Traffic', []).append('31000')
        vbr_bitrate.setdefault('Traffic', []).append('20800')
        vbr_bitrate.setdefault('Traffic', []).append('10700')
        vbr_bitrate.setdefault('Traffic', []).append('5800')
        vbr_bitrate.setdefault('PeopleOnStreet', []).append('10100')
        vbr_bitrate.setdefault('PeopleOnStreet', []).append('8500')
        vbr_bitrate.setdefault('PeopleOnStreet', []).append('4300')
        vbr_bitrate.setdefault('PeopleOnStreet', []).append('2400')
        vbr_bitrate.setdefault('Kimono1', []).append('5000')
        vbr_bitrate.setdefault('Kimono1', []).append('3300')
        vbr_bitrate.setdefault('Kimono1', []).append('1600')
        vbr_bitrate.setdefault('Kimono1', []).append('800')
        vbr_bitrate.setdefault('ParkScene', []).append('7500')
        vbr_bitrate.setdefault('ParkScene', []).append('4400')
        vbr_bitrate.setdefault('ParkScene', []).append('1800')
        vbr_bitrate.setdefault('ParkScene', []).append('700')
        vbr_bitrate.setdefault('Cactus', []).append('7600')
        vbr_bitrate.setdefault('Cactus', []).append('4300')
        vbr_bitrate.setdefault('Cactus', []).append('1900')
        vbr_bitrate.setdefault('Cactus', []).append('900')
        vbr_bitrate.setdefault('BQTerrace', []).append('14000')
        vbr_bitrate.setdefault('BQTerrace', []).append('5100')
        vbr_bitrate.setdefault('BQTerrace', []).append('1300')
        vbr_bitrate.setdefault('BQTerrace', []).append('500')
        vbr_bitrate.setdefault('BasketballDrive', []).append('8300')
        vbr_bitrate.setdefault('BasketballDrive', []).append('5000')
        vbr_bitrate.setdefault('BasketballDrive', []).append('2300')
        vbr_bitrate.setdefault('BasketballDrive', []).append('1100')
        vbr_bitrate.setdefault('RaceHorses', []).append('4400')
        vbr_bitrate.setdefault('RaceHorses', []).append('2800')
        vbr_bitrate.setdefault('RaceHorses', []).append('1200')
        vbr_bitrate.setdefault('RaceHorses', []).append('500')
        vbr_bitrate.setdefault('BQMall', []).append('1800')
        vbr_bitrate.setdefault('BQMall', []).append('1100')
        vbr_bitrate.setdefault('BQMall', []).append('500')
        vbr_bitrate.setdefault('BQMall', []).append('200')
        vbr_bitrate.setdefault('PartyScene', []).append('4700')
        vbr_bitrate.setdefault('PartyScene', []).append('2800')
        vbr_bitrate.setdefault('PartyScene', []).append('1100')
        vbr_bitrate.setdefault('PartyScene', []).append('400')
        vbr_bitrate.setdefault('BasketballDrill', []).append('2000')
        vbr_bitrate.setdefault('BasketballDrill', []).append('1300')
        vbr_bitrate.setdefault('BasketballDrill', []).append('600')
        vbr_bitrate.setdefault('BasketballDrill', []).append('300')
        vbr_bitrate.setdefault('RaceHorses', []).append('1100')
        vbr_bitrate.setdefault('RaceHorses', []).append('800')
        vbr_bitrate.setdefault('RaceHorses', []).append('300')
        vbr_bitrate.setdefault('RaceHorses', []).append('100')
        vbr_bitrate.setdefault('BQSquare', []).append('1100')
        vbr_bitrate.setdefault('BQSquare', []).append('600')
        vbr_bitrate.setdefault('BQSquare', []).append('200')
        vbr_bitrate.setdefault('BQSquare', []).append('70')
        vbr_bitrate.setdefault('BlowingBubbles', []).append('1000')
        vbr_bitrate.setdefault('BlowingBubbles', []).append('600')
        vbr_bitrate.setdefault('BlowingBubbles', []).append('200')
        vbr_bitrate.setdefault('BlowingBubbles', []).append('100')
        vbr_bitrate.setdefault('BasketballPass', []).append('900')
        vbr_bitrate.setdefault('BasketballPass', []).append('600')
        vbr_bitrate.setdefault('BasketballPass', []).append('300')
        vbr_bitrate.setdefault('BasketballPass', []).append('100')
        vbr_bitrate.setdefault('FourPeople', []).append('800')
        vbr_bitrate.setdefault('FourPeople', []).append('500')
        vbr_bitrate.setdefault('FourPeople', []).append('200')
        vbr_bitrate.setdefault('FourPeople', []).append('100')
        vbr_bitrate.setdefault('Johnny', []).append('500')
        vbr_bitrate.setdefault('Johnny', []).append('250')
        vbr_bitrate.setdefault('Johnny', []).append('100')
        vbr_bitrate.setdefault('Johnny', []).append('60')
        vbr_bitrate.setdefault('KristenAndSara', []).append('700')
        vbr_bitrate.setdefault('KristenAndSara', []).append('400')
        vbr_bitrate.setdefault('KristenAndSara', []).append('200')
        vbr_bitrate.setdefault('KristenAndSara', []).append('100')
        vbr_bitrate.setdefault('BasketballDrillText', []).append('2200')
        vbr_bitrate.setdefault('BasketballDrillText', []).append('1500')
        vbr_bitrate.setdefault('BasketballDrillText', []).append('700')
        vbr_bitrate.setdefault('BasketballDrillText', []).append('300')
        vbr_bitrate.setdefault('ChinaSpeed', []).append('5400')
        vbr_bitrate.setdefault('ChinaSpeed', []).append('3700')
        vbr_bitrate.setdefault('ChinaSpeed', []).append('1700')
        vbr_bitrate.setdefault('ChinaSpeed', []).append('700')
        vbr_bitrate.setdefault('SlideEditing', []).append('700')
        vbr_bitrate.setdefault('SlideEditing', []).append('500')
        vbr_bitrate.setdefault('SlideEditing', []).append('400')
        vbr_bitrate.setdefault('SlideEditing', []).append('200')
        vbr_bitrate.setdefault('SlideShow', []).append('1200')
        vbr_bitrate.setdefault('SlideShow', []).append('900')
        vbr_bitrate.setdefault('SlideShow', []).append('500')
        vbr_bitrate.setdefault('SlideShow', []).append('300')
        vbr_bitrate.setdefault('Chimei-inn', []).append('7600')
        vbr_bitrate.setdefault('Chimei-inn', []).append('4800')
        vbr_bitrate.setdefault('Chimei-inn', []).append('2300')
        vbr_bitrate.setdefault('Chimei-inn', []).append('1200')
        vbr_bitrate.setdefault('Girlhood', []).append('17700')
        vbr_bitrate.setdefault('Girlhood', []).append('12000')
        vbr_bitrate.setdefault('Girlhood', []).append('6000')
        vbr_bitrate.setdefault('Girlhood', []).append('3200')
        vbr_bitrate.setdefault('Beauty', []).append('58000')
        vbr_bitrate.setdefault('Beauty', []).append('14700')
        vbr_bitrate.setdefault('Beauty', []).append('2000')
        vbr_bitrate.setdefault('Beauty', []).append('1000')
        vbr_bitrate.setdefault('RaceNight', []).append('14800')
        vbr_bitrate.setdefault('RaceNight', []).append('8500')
        vbr_bitrate.setdefault('RaceNight', []).append('4300')
        vbr_bitrate.setdefault('RaceNight', []).append('2400')

	files = get_raw_data(srcBinDir)
	processIdx = -1 # 处理顺序的索引
	
	## 2.遍历每个码流文件进行编码或解码
	for filename in files: #遍历每个码流文件
                #print filename
                processIdx = processIdx+1
                if processIdx < startIdx:
                    print('[Info] skip:' + filename)
                    continue
                          
                print('\n*****processIdx******: ' + str(processIdx))
		print('[Info] Process: ' + filename)
		#if processIdx == 0: #只有在刚开始时才写入头数据
                pFile = open(outtotal, 'w') #创建汇总文件，性能数据
                #totaltitle = 'filename' + ' '*(42 - len('#filename') + 15) + 'total_frames'+ 10*' ' + 'bitrate'  + 10*' ' + 'PSNR' + 10*' ' + 'time(s)'
                totaltitle = 'filename' + ' '*(42 - len('#filename') + 15) + 'total_frames'+ 10*' ' + 'bitrate'  + 10*' ' + 'Y-PSNR' + 10*' ' +\
                             'U-PSNR' + 10*' ' + 'V-PSNR' + 10*' ' + 'time(s)'
                pFile.writelines(totaltitle)
                pFile.write('\n')
                pFile.close()

		space_num = maxch - len(filename)
		onlystreamname = get_file_name(filename)
		#print filename
		#print onlystreamname
		input_res = onlystreamname.split('_')[1]
		#print input_res
		width  = input_res.split('x')[0]
		height = input_res.split('x')[1]
		stream_name = onlystreamname.split('_')[0]
		#print stream_name
		#print width
		#print height

		bitrate = vbr_bitrate[stream_name]
		#print bitrate

                # VBR循环四个码率点编码
		for br in bitrate:
                          outrawtxt = outFileDir + delimiter + onlystreamname + '_Anchor_br' + br + '.txt' 
                          outreftxt = outFileDir + delimiter + onlystreamname + '_Ref_br'    + br + '.txt'    
                          outrawstr = outFileDir + delimiter + onlystreamname + '_Anchor_br' + br + '.bin' 
                          outrefstr = outFileDir + delimiter + onlystreamname + '_Ref_br'    + br + '.bin'    
                          outmemcheckanchortxt = outFileDir + delimiter  + '__pyMemcheckAnchor_br' + br + '.log'
                          outmemcheckreftxt    = outFileDir + delimiter  + '__pyMemcheckRef_br'    + br + '.log'
                          print br

                          # 原始可执行文件编码
                          if yuvflag != '0':
                              cmd_raw = space.join([rawDemo, '--input', filename, '--preset', 'veryfast', '-t', 'zerolatency', 
                                           '--psnr', '-o', outrawstr, '--input-res', input_res,
                                           '--fps 30 --keyint 100 --bitrate', br, '--no-wpp -F 1 -b 0', '>', outrawtxt, '2>&1'])
                              print cmd_raw
                          else:
                              # cmd for x265
                              cmd_raw = space.join([rawDemo, '--input', filename, '--preset', 'veryfast', '-t', 'zerolatency', 
                                           '--psnr', '-o', outrawstr, '--input-res', input_res,
                                           '--fps 30 --keyint 100 --bitrate', br, '--no-wpp -F 1 -b 0', '>', outrawtxt, '2>&1'])
                              # cmd for uavs3e
                              #cmd_raw = space.join([rawDemo, '-i', filename, '--speed_level 3 --fps_num 30 --fps_den 1', 
                              #             '-o', outrawstr, '-w', width, '-h', height, '--input_bit_depth 8 --internal_bit_depth 8',
                              #             '--frm_threads 1 --wpp_threads 1 --rc_type 0 -p 100 -g 0 -v 2 --qp', qp, '>', outrawtxt, '2>&1'])
                              # cmd for libaom
                              #cmd_raw = space.join([rawDemo, filename, '--fps=30/1 --kf-max-dist=100  --kf-min-dist=100',
                              #              '--cpu-used=6  -u 1  --threads=1 --tune=psnr  --psnr=1 --passes=1 -v  --tile-columns=0', 
                              #              '-o', outrawstr, '-w', width, '-h', height, '--end-usage=vbr --mode-cost-upd-freq=2',
                              #              '--undershoot-pct=50 --overshoot-pct=50 --buf-sz=1000 --buf-initial-sz=500 --buf-optimal-sz=600',
                              #              '--max-intra-rate=300 --deltaq-mode=0 --enable-tpl-model=0 --enable-obmc=0 --enable-warped-motion=0',
                              #              '--coeff-cost-upd-freq=2 --enable-ref-frame-mvs=0 --mv-cost-upd-freq=2', '>', outrawtxt, '2>&1'])
                              #cmd_raw_br=''.join(['--target-bitrate=', br])
                              #cmd_raw = space.join([cmd_raw, cmd_raw_br])
                              
                              print cmd_raw
                          ret = subprocess.call(cmd_raw, shell=True)
                          if(ret!=0):
                              print('[error]: ' + filename + ' rawDemo failed!')
                              pFileAnchorNdec.write(rawDemo+'cannot dec'+filename+' '+' ret: '+ bytes(ret)+'\n')
                              return -1
                          else:
                              print('[info]: ' + filename + ' rawDemo success!')

                          # 参考可执行文件编码
                          if refDemo != '0':
                              if yuvflag != '0':
                                  cmd_ref = space.join([refDemo, '-i', filename, '-c', 'i420', '-f', 'yuv', '-d', outrefstr, '>', outreftxt])
                              else:
                                  cmd_ref = space.join([refDemo, '-i', filename, '-c', 'i420', '-f', 'yuv', '>', outreftxt])

                              ret = subprocess.call(cmd_ref, shell=True)
                              if(ret==0):
                                  print('[info]: ' + filename + ' refDemo success!')
                              else:
                                  print('[error]: ' + filename + ' refDemo failed!')
                                  pFileRefNdec.write(refDemo+'cannot dec'+filename+' '+' ret: '+ bytes(ret)+'\n')
                                  return -1
		          ## 将性能数据结果输出到格式化文本中 outrawtxt--->outtotal
                          get_data_from_txt_x265(onlystreamname+'_br'+br, outrawtxt, outtotal, 1)
                          if(refDemo != '0'):
                              get_data_from_txt(filename, outreftxt, outtotal, 0)
                              
                ## 3. gprof性能分析
                if(int(gprof)==1): #默认为0，表示不使用性能分析工具gprof
                    cmd = space.join(['gprof', rawDemo, 'gmon.out', '>', outFileDir+'/outgprof/'+onlystreamname+'_gprof_anchor.txt'])
                    print(cmd)
                    subprocess.call(cmd, shell=True)

                ## 4.valgrind内存检查
                if(memcheckflag != '0'):
                    #print cmd_ref
                    #exit()
                    ret = perform_valgrind_data(outFileDir, cmd_raw, filename, cmd_ref)
                    get_data_from_log(filename, outmemcheckanchortxt, outMemchecklog)

                ## 5. 一致性比较
                if(refDemo != '0' and int(yuvflag) != 0):
                    ret = yuv_cmp(outrawyuv, outrefyuv)
                    if(ret!=0):
                        print('[info]: MATCH!')
                        coherence= '[' + filename + ']:' + space + 'MATCH!'
                        pFileMatch.write(coherence)
                        pFileMatch.write('\n')
                        os.remove(outrawyuv)
                        os.remove(outrefyuv)
                    else:
                        print('[info]: DISMATCH!')
                        coherence= '[' + filename + ']:' + space + 'DISMATCH!'
                        pFileDismatch.write(coherence)
                        pFileDismatch.write('\n')

                ## 6.将数据结果从格式化文本写入到excel中 outtotal--->outExcelData
                collect_data_to_excel(outExcelData, outtotal, 1, processIdx)
                print("[info]: -----collect data to excel success!------")
        ## 关闭打开的文件
	pFileAnchorNdec.close()
        if refDemo != '0':
            pFileMatch.close()
            pFileDismatch.close()
            pFileRefNdec.close()


####################################main 函数入口####################################################
if __name__ == '__main__':
	if(len(sys.argv) < 4):
		print('Usage: ' + '<rawDemo srcStreamDir outFileDir> [gprof yuvflag refDemo memcheckflag startIdx] ' + '\n')
                print('Notice: <> is necessary, [] is optional')
                exit()
	rawDemo = sys.argv[1]
	srcStreamDir = sys.argv[2]
	outFileDir = sys.argv[3]

	if len(sys.argv) >= 5:
		gprof = sys.argv[4]
	else:
		gprof = 0
	if len(sys.argv) >= 6:
		yuvflag = sys.argv[5]
	else:
		yuvflag = 0
	if len(sys.argv) >= 7:
		refDemo = sys.argv[6]
	else:
		refDemo = 0
	if len(sys.argv) >= 8:
		memcheckflag = sys.argv[7]
	else:
		memcheckflag = 0
        if len(sys.argv) >= 9:
                startIdx = int(sys.argv[8])
        else:
                startIdx = 0
                
        #print startIdx
	ret = process_encode_decode(rawDemo, srcStreamDir, outFileDir, gprof, yuvflag, refDemo, memcheckflag, startIdx)
	if (ret!=0):
		print("[info]: ---------Process finished!---------")
	exit()
