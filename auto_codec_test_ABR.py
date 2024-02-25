#_*_ coding=UTF-8_*_  #脚本中有中文注释必须包含这一句

################################################################################################################
##脚本用法： python auto_codec_coherence.py <rawDemo srcStreamDir outFileDir codec scc> [gprofflag outyuvflag refDemo memcheckflag startIdx NosaveBin SSIM]
##参数说明：	 rawDemo	 :	 待验证的可执行文件（编码器/解码器）
##				srcStreamDir:	码流/YUV路径
##				outFileDir	:	结果输出路径
##				codec		:   0: x264, 1: x265, 2:uavs3e, 3: vvenc
##				scc			:   0: CTC 主流, 1: SCC 辅流
##				gprofflag	:	gprof开关(默认为0):如果取0表示不会利用gprof工具进行分析; 取1表示利用gprof进行分析
##				outyuvflag	:	yuv输出开关(默认为0): 如果取0,表示解码不输出yuv,否则相反。
##				refDemo		: 	参考可执行文件（编码器/解码器）
##				memcheckflag:	使用valgrind进行内存泄露检查(默认为0)(针对linux下编译的64位库)
##				startIdx	: 	在批处理过程中,支持从指定序号startIdx的位置处开始执行。
##				saveBin	    : 	是否保存编码码流, 1:不保存  0:保存。
##			    SSIM		:   是否计算SSIM, 1: 计算SSIM 0: 不计算SSIM
##
## Author : Created by lipeng at July 3 2020
## Version: 2.0.4
## Revision History:
## (1) 2020.7.3   tag V1.0    支持批量编解码、一致性验证, 支持Windows平台(Python)
## (2) 2020.7.6   tag V2.0    支持valgrind和gprof分析
## (3) 2020.7.10  tag V2.0.1  支持对编解码数据进行数据统计(格式输出并导入excel中)
## (4) 2020.7.17  tag V2.0.2  支持BDBR统计分析
## (5) 2021.7.21  tag V2.0.3  支持中断处理功能, 区分CBR/VBR配置, 支持x264/x265/uavs3e/libaom/vvenc等开源编码器。
## (6) 2021.7.30  tag V2.0.3  简化脚本
## (7) 2024.l.30  tag V2.0.4  增加是否保存码流和输出log的功能, 支持CTC和SCC不同场景码流文件解析, 支持SSIM
################################################################################################################
import os			#linux命令操作
import re			#字符串匹配操作
import sys			#系统操作
import glob			#搜索
import filecmp		#用于文件比较
import shutil
import subprocess	#子进程，用于创建导出日志的管道
import subprocess as sub
import csv			#逗号值文件
import codecs		#编码方式
from   collections import OrderedDict
import pandas as pd                     #转换excel
import math			# log10

space = ' '
delimiter = '/'

collect = '_pyout_collect'  				#性能对比输出文件夹
cmp_match = '_pyout_match'  				#yuv对比一致
cmp_dismatch = '_pyout_dismatch' 			#yuv对比不一致
Anchor_Ndec = '_pyAnchor_notdecstream'		#待验证的可执行文件不能解码的码流
Reference_Ndec = '_pyRef_notdecstream'		#参考可执行文件不能解码的码流
Anchor_memchecklog = '_pyAnchor_memcheck' 	#对待验证可执行文件进行内存检查后的汇总文件

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
		print(allfiles)
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
		dirs[:] = [d for d in dirs if d not in "ClassF"]  # 排除掉具有ClassF名称的子目录
		dirs[:] = [d for d in dirs if d not in "Class4K"]
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

def del_file_dir(pathDir):
	for root, dirs, files in os.walk(pathDir):
		for f in files:
			if (re.search('bin$', f) or re.search('txt$', f)):
				os.remove(os.path.join(root, f))
	print('[info]: '+ '指定文件删除成功！')

#从x264编码器输出日志文本中提取数据
def get_data_from_txt_x264(filename, txtfile, outdatafile, anchor='1'):
	pFile = open(txtfile, 'r')
	lines = pFile.readlines() #读取文本中所有行
	lineflag = 0
	Data = {}  #dictory
	for i in range(len(lines)):
		if lines[i].find('encoded') != -1:
			word = lines[i].split(',')
			lineflag = 0
			bitrate=word[2].strip().split(' ')[0]
			framenum=word[0].split(' ')[1]
			fps = word[1].strip().split(' ')[0]
			time = float('%.3f' %(float(framenum)/float(fps)))
		if lines[i].find('x264 [info]: PSNR Mean') != -1:
			Mean_PSNR = lines[i].strip().split(' ')
			Y_PSNR    = Mean_PSNR[4].split(':')[1]
			U_PSNR    = Mean_PSNR[5].split(':')[1]
			V_PSNR    = Mean_PSNR[6].split(':')[1]
	pFile.close()
	pFile = open(outdatafile, 'a+')
	if(anchor==1):
		oneline = filename + '(anchor)' + ' '*(30-len(filename)+15) + \
		framenum + 10*' ' + bitrate + 10*' ' + str(Y_PSNR) + 10*' ' +\
		str(U_PSNR) + 10*' ' + str(V_PSNR) + 10*' ' + str(time) + '\n'
	else:
		oneline = filename + '(ref)   ' + ' '*(30-len(filename)+10) + \
		Data['length(bytes) '] + ' '*12 + \
		Data['fps '] + ' '*5 + '\n'
	pFile.write(oneline)
	pFile.close()
	print("[info]: get_data_from_txt_x264 success!")
	
#从x265编码器输出日志文本中提取数据
def get_data_from_txt_x265(filename, txtfile, outdatafile, anchor='1'):
	pFile = open(txtfile, 'r')
	lines = pFile.readlines() #读取文本中所有行
	lineflag = 0
	Data = {}  #dictory
	frame_numI = 0
	frame_numP = 0
	frame_numB = 0	# 默认不含B帧

	Y_PSNR_I   = 0
	U_PSNR_I   = 0
	V_PSNR_I   = 0
	Y_PSNR_P   = 0
	U_PSNR_P   = 0
	V_PSNR_P   = 0
	Y_PSNR_B   = 0
	U_PSNR_B   = 0
	V_PSNR_B   = 0
	Y_SSIM_I   = 0
	Y_SSIM_P   = 0
	Y_SSIM_B   = 0
	for i in range(len(lines)):
		if lines[i].find('encoded') != -1:
			word = lines[i].split(',')
			lineflag = 0
			bitrate=word[1].split(' ')[1]
			framenum=word[0].split(' ')[1]
			time = word[0].split(' ')[4].split('s')[0]
			fps  = word[0].split('fps)')[0].split('(')[-1]
		if lines[i].find('x265 [info]: frame I:') != -1: # 老版本中为x265
			Mean_PSNR = lines[i].strip('\n').split('PSNR Mean:')[-1]
			Y_PSNR_I    = Mean_PSNR.split(' ')[1].split('Y:')[1]
			U_PSNR_I    = Mean_PSNR.split(' ')[2].split('U:')[1]
			V_PSNR_I    = Mean_PSNR.split(' ')[3].split('V:')[1] 
			frame_numI  = lines[i].strip('\r').strip('\n').split(',')[-2].split(' ')[-1]      
			Mean_SSIM   = Mean_PSNR.strip(' ').split("SSIM Mean:")[-1].strip(' ').split(' ')[-1].split("dB")
			Y_SSIM_I    = Mean_SSIM[0].split('(')[1]
		if lines[i].find('x265 [info]: frame P:') != -1: # x265
			Mean_PSNR = lines[i].strip('\n').split('PSNR Mean:')[-1]
			Y_PSNR_P    = Mean_PSNR.split(' ')[1].split('Y:')[1]
			U_PSNR_P    = Mean_PSNR.split(' ')[2].split('U:')[1]
			V_PSNR_P    = Mean_PSNR.split(' ')[3].split('V:')[1]
			frame_numP  = lines[i].strip('\r').strip('\n').split(',')[-2].split(' ')[-1]
			Mean_SSIM   = Mean_PSNR.strip(' ').split("SSIM Mean:")[-1].strip(' ').split(' ')[-1].split("dB")
			Y_SSIM_P    = Mean_SSIM[0].split('(')[1]
		if lines[i].find('x265 [info]: frame B:') != -1:
			Mean_PSNR = lines[i].strip('\n').split('PSNR Mean:')[-1]
			Y_PSNR_B    = Mean_PSNR.split(' ')[1].split('Y:')[1]
			U_PSNR_B    = Mean_PSNR.split(' ')[2].split('U:')[1]
			V_PSNR_B    = Mean_PSNR.split(' ')[3].split('V:')[1]
			frame_numB  = lines[i].strip('\r').strip('\n').split(',')[-2].split(' ')[-1]
			Mean_SSIM   = Mean_PSNR.strip(' ').split("SSIM Mean:")[-1].strip(' ').split(' ')[-1].split("dB")
			Y_SSIM_B    = Mean_SSIM[0].split('(')[1]
	frameTotal = int(frame_numI) + int(frame_numP) + int(frame_numB)
	Y_PSNR = float('%.3f' % (((float(Y_PSNR_I) * int(frame_numI)) + (float(Y_PSNR_P)*int(frame_numP)) + (float(Y_PSNR_B)*int(frame_numB)))/ frameTotal))
	U_PSNR = float('%.3f' % (((float(U_PSNR_I) * int(frame_numI)) + (float(U_PSNR_P)*int(frame_numP)) + (float(U_PSNR_B)*int(frame_numB)))/ frameTotal))
	V_PSNR = float('%.3f' % (((float(V_PSNR_I) * int(frame_numI)) + (float(V_PSNR_P)*int(frame_numP)) + (float(V_PSNR_B)*int(frame_numB)))/ frameTotal))
	Y_SSIM = float('%.3f' % (((float(Y_SSIM_I) * int(frame_numI)) + (float(Y_SSIM_P)*int(frame_numP)) + (float(Y_SSIM_B)*int(frame_numB)))/ frameTotal))
	pFile.close()
	pFile = open(outdatafile, 'a+')
	if(anchor==1):
		oneline = filename + '(anchor)' + ' '*(30-len(filename)+20) + \
		framenum + 10*' ' + bitrate + 10*' ' + str(Y_PSNR) + 10*' ' + \
		str(U_PSNR) + 10*' ' + str(V_PSNR) + 10*' ' + str(Y_SSIM) + 10*' ' + str(time) + 10*' ' +  fps + '\n'
	else:
		oneline = filename + '(ref)   ' + ' '*(30-len(filename)+20) + \
		framenum + 10*' ' + bitrate + 10*' ' + str(Y_PSNR) + 10*' ' + \
		str(U_PSNR) + 10*' ' + str(V_PSNR) + 10*' ' + str(Y_SSIM) + 10*' ' + str(time) + 10*' ' +  fps + '\n'
	pFile.write(oneline)
	pFile.close()
	print("[info]: get_data_from_txt_x265 success!")

def get_data_from_txt_yl265(filename, txtfile, outdatafile, anchor='1', SSIM=0):
	pFile = open(txtfile, 'r')
	lines = pFile.readlines() #读取文本中所有行
	lineflag = 0
	Data = {}  #dictory
	frame_numI = 0
	frame_numP = 0
	frame_numB = 0	# 默认不含B帧

	Y_PSNR_I   = 0
	U_PSNR_I   = 0
	V_PSNR_I   = 0

	Y_PSNR_P   = 0
	U_PSNR_P   = 0
	V_PSNR_P   = 0

	Y_PSNR_B   = 0
	U_PSNR_B   = 0
	V_PSNR_B   = 0

	Y_SSIM_I   = 0
	Y_SSIM_P   = 0
	Y_SSIM_B   = 0
	for i in range(len(lines)):
		if lines[i].find('encoded') != -1:
			word = lines[i].split(',')
			lineflag = 0
			bitrate=word[1].split(' ')[1]
			framenum=word[0].split(' ')[1]
			PSNR = word[3].split(' ')[3].split('\n')[0]
		if lines[i].find('pure encoding time:') != -1:
			word = lines[i].split(',')
			time = float(word[0].split(' ')[-1].split('ms')[0]) / 1000
			fps  = word[1].split('fps:')[-1]
		if lines[i].find('yl265 [info]: frame I  :') != -1: # 老版本中为x265
		#if lines[i].find('yl265 [info]: frame I:') != -1: # 老版本中为x265
			Mean_PSNR = lines[i].strip('\n').split('PSNR Mean:')[-1]
			Y_PSNR_I    = Mean_PSNR.split(' ')[1].split('Y:')[1]
			U_PSNR_I    = Mean_PSNR.split(' ')[2].split('U:')[1]
			V_PSNR_I    = Mean_PSNR.split(' ')[3].split('V:')[1] 
			frame_numI  = lines[i].strip('\r').strip('\n').split(',')[-2].split(' ')[-1]      
			if (SSIM == 1):
				Mean_SSIM   = Mean_PSNR.strip(' ').split("SSIM Mean:")[-1].strip(' ').split(' ')[-1].split("dB")
				Y_SSIM_I    = Mean_SSIM[0].split('(')[1]
		if lines[i].find('yl265 [info]: frame P  :') != -1: # x265
		#if lines[i].find('yl265 [info]: frame P:') != -1: # x265
			Mean_PSNR = lines[i].strip('\n').split('PSNR Mean:')[-1]
			Y_PSNR_P    = Mean_PSNR.split(' ')[1].split('Y:')[1]
			U_PSNR_P    = Mean_PSNR.split(' ')[2].split('U:')[1]
			V_PSNR_P    = Mean_PSNR.split(' ')[3].split('V:')[1]
			frame_numP  = lines[i].strip('\r').strip('\n').split(',')[-2].split(' ')[-1]
			if (SSIM == 1):
				Mean_SSIM   = Mean_PSNR.strip(' ').split("SSIM Mean:")[-1].strip(' ').split(' ')[-1].split("dB")
				Y_SSIM_P    = Mean_SSIM[0].split('(')[1]
		if lines[i].find('yl265 [info]: frame B:') != -1:
			Mean_PSNR = lines[i].strip('\n').split('PSNR Mean:')[-1]
			Y_PSNR_B    = Mean_PSNR.split(' ')[1].split('Y:')[1]
			U_PSNR_B    = Mean_PSNR.split(' ')[2].split('U:')[1]
			V_PSNR_B    = Mean_PSNR.split(' ')[3].split('V:')[1]
			frame_numB  = lines[i].strip('\r').strip('\n').split(',')[-2].split(' ')[-1]
			if (SSIM == 1):
				Mean_SSIM   = Mean_PSNR.strip(' ').split("SSIM Mean:")[-1].strip(' ').split(' ')[-1].split("dB")
				Y_SSIM_B    = Mean_SSIM[0].split('(')[1]
	frameTotal = int(frame_numI) + int(frame_numP) + int(frame_numB)
	Y_PSNR = float('%.3f' % (((float(Y_PSNR_I) * int(frame_numI)) + (float(Y_PSNR_P)*int(frame_numP)) + (float(Y_PSNR_B)*int(frame_numB)))/ frameTotal))
	U_PSNR = float('%.3f' % (((float(U_PSNR_I) * int(frame_numI)) + (float(U_PSNR_P)*int(frame_numP)) + (float(U_PSNR_B)*int(frame_numB)))/ frameTotal))
	V_PSNR = float('%.3f' % (((float(V_PSNR_I) * int(frame_numI)) + (float(V_PSNR_P)*int(frame_numP)) + (float(V_PSNR_B)*int(frame_numB)))/ frameTotal))
	if (SSIM == 1):
		Y_SSIM = float('%.3f' % (((float(Y_SSIM_I) * int(frame_numI)) + (float(Y_SSIM_P)*int(frame_numP)) + (float(Y_SSIM_B)*int(frame_numB)))/ frameTotal))
	pFile.close()
	pFile = open(outdatafile, 'a+')
	if(anchor==1):
		if (SSIM == 1):
			oneline = filename + '(anchor)' + ' '*(30-len(filename)+20) + \
			framenum + 10*' ' + bitrate + 10*' ' + str(Y_PSNR) + 10*' ' + \
			str(U_PSNR) + 10*' ' + str(V_PSNR) + 10*' ' + str(Y_SSIM) + 10*' ' + str(time) + 10*' ' +  fps + '\n'
		else:
			oneline = filename + '(anchor)' + ' '*(30-len(filename)+20) + \
			framenum + 10*' ' + bitrate + 10*' ' + str(Y_PSNR) + 10*' ' + \
			str(U_PSNR) + 10*' ' + str(V_PSNR)   + 10*' ' + str(time) + 10*' ' +  fps + '\n'		
	else:
		if (SSIM == 1):
			oneline = filename + '(ref)   ' + ' '*(30-len(filename)+20) + \
			framenum + 10*' ' + bitrate + 10*' ' + str(Y_PSNR) + 10*' ' + \
			str(U_PSNR) + 10*' ' + str(V_PSNR) + 10*' ' + str(Y_SSIM) + 10*' ' + str(time) + 10*' ' +  fps + '\n'
		else:
			oneline = filename + '(ref)   ' + ' '*(30-len(filename)+20) + \
			framenum + 10*' ' + bitrate + 10*' ' + str(Y_PSNR) + 10*' ' + \
			str(U_PSNR) + 10*' ' + str(V_PSNR)   + 10*' ' + str(time) + 10*' ' +  fps + '\n'			
	pFile.write(oneline)
	pFile.close()
	print("[info]: get_data_from_txt_yl265 success!")

def calc_ssim2dB(ssim_val):
	inv_ssim = 1 - ssim_val
	if (inv_ssim <= 0.0000000001):
		return 100
	return -10.0 * math.log10(inv_ssim)
#从KSC265编码器输出日志文本中提取数据
def get_data_from_txt_KSC265(filename, txtfile, outdatafile, anchor='1'):
	pFile = open(txtfile, 'r')
	lines = pFile.readlines() #读取文本中所有行
	Data = {}  #dictory
	for i in range(len(lines)):
		if lines[i].find('pure encoding time:') != -1:
			word = lines[i].split(',')
			#print word
			time = word[1].split(' ')[-1].split('ms')[0]
			time = str(float(time) / 1000)
			fps  = word[2].split(' ')[1]
			framenum=word[0].split(' ')[-1]
			#print time, fps, framenum
		if lines[i].find('bitrate, psnr:') != -1:
			#print lines[i] 
			word = lines[i].split(' ')[-1].split('\t')
			bitrate = word[0]
			Y_PSNR  = word[1]
			U_PSNR  = word[2]
			V_PSNR  = word[3].split('\n')[0]
			#print Y_PSNR, U_PSNR, V_PSNR
		if lines[i].find('ssim:') != -1:
			word = lines[i].strip(' ').split(' ')[-1].split('\t')
			Y_SSIM = word[1]
			U_SSIM = word[2]
			V_SSIM = word[3].split('\n')[0]
			Y_SSIM_DB= float('%.4f' %(calc_ssim2dB(float(Y_SSIM))))

	pFile.close()
	pFile = open(outdatafile, 'a+')
	oneline = filename + '(anchor)' + ' '*(30-len(filename)+20) + \
			  framenum + 10*' ' + bitrate + 10*' ' + str(Y_PSNR) + 10*' ' + str(U_PSNR) + 10*' ' + str(V_PSNR) + \
			  10*' ' + str(Y_SSIM_DB)  + 10*' ' + time + 10*' ' +  fps + '\n'
	pFile.write(oneline)
	pFile.close()
	print("[info]: get_data_from_txt_KSC265 success!")

#从uAVS3e实时编码器输出日志文本中提取数据
def get_data_from_txt_uavs3e(filename, txtfile, outdatafile, anchor='1'):
	pFile = open(txtfile, 'a+')
	lines = pFile.readlines() #读取文本中所有行
	Data = {}  #dictory
	for i in range(len(lines)):
		if lines[i].find('Bit rate (kbit/s)') != -1:
			bitrate = lines[i].split(':')[1].strip('\n').split(' ')[-1]
		if lines[i].find('FramesToBeEncoded')!= -1:
			framenum = lines[i].split('=')[1].split(' ')[-2]
		if lines[i].find('Total encoding time for the seq.') != -1:
			time = lines[i].split(':')[-1].split(' ')[1]
		###增加Y_PSNR, U_PSNR, V_PSNR的解析
		if lines[i].find('SNR Y(dB)') != -1:
			Y_PSNR = lines[i].split(':')[-1].strip(' ').strip('\n')
		if lines[i].find('SNR U(dB)') != -1:
			U_PSNR = lines[i].split(':')[-1].strip(' ').strip('\n')
		if lines[i].find('SNR V(dB)') != -1:
			V_PSNR = lines[i].split(':')[-1].strip(' ').strip('\n')    
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

#从vvenc编码器输出日志文本中提取数据	
def get_data_from_txt_vvenc(filename, txtfile, outdatafile, anchor='1'):
	pFile = open(txtfile, 'a+')
	lines = pFile.readlines() #读取文本中所有行
	Data = {}  #dictory
	for i in range(len(lines)):
		if lines[i].find('SUMMARY') != -1:
			summary = (lines[i+2].strip().split())  #','.join(i.split())
			framenum = summary[0]
			bitrate = summary[2]
			Y_PSNR = summary[3]
			U_PSNR = summary[4]
			V_PSNR = summary[5]
		if lines[i].find('Total Time:') != -1:
			time = lines[i].split('sec')[0].strip('\n').split(':')[-1].strip(' ')       
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
	print("[info]: get_data_from_txt_vvenc success!")

#collect data from formated text to excel
count = 0
def collect_data_to_excel(excelname, inputfile, anchor='1', processIdx=0, SSIM=0):
	pFile = open(inputfile, 'r')
	lines = pFile.readlines()
	#data = {}  ##默认字典是无序的(hash)
	data = OrderedDict()  ##使用有序字典
	for i in range(len(lines)):
		if lines[i].find('anchor') != -1 or lines[i].find('ref') != -1:
			splitValue = lines[i].split()  ##此处根据具体文本数据格式进行分割提取
			#print(splitValue)
			filename = get_file_name_ext(splitValue[0])
			if (SSIM == 1):
				data[filename] = [filename, splitValue[1], splitValue[2], splitValue[3], splitValue[4], splitValue[5], splitValue[6], splitValue[7]]
			else:
				data[filename] = [filename, splitValue[1], splitValue[2], splitValue[3], splitValue[4], splitValue[5], splitValue[6]]		
			print(data[filename])
	pFile = open(excelname, 'a+')
	pFile.write(codecs.BOM_UTF8)
	csv_writer=csv.writer(pFile, dialect='excel')
	global count
	if count==0 and processIdx==0:  ##第一次打开文件时才写入
		if (SSIM == 1):
			title=['video sequence', 'total frames', 'bitrate(kbps)', 'Y-PSNR(dB)', 'U-PSNR(dB)', 'V-PSNR(dB)', 'Y-SSIM(dB)','time(s)']
		else:
			title=['video sequence', 'total frames', 'bitrate(kbps)', 'Y-PSNR(dB)', 'U-PSNR(dB)', 'V-PSNR(dB)', 'time(s)']		
		csv_writer.writerow(title)
		count=count+1
	for key, value in data.items():
		csv_writer.writerow(value)
	pFile.close()

#linux下内存泄漏检查valgrind
def perform_valgrind_data(outFileDir, Anchordeccmd='0', onlystreamname='0', Refdeccmd='0', reserve='0'):
	outmemcheckanchortxt = outFileDir + delimiter  + '__pyMemcheckAnchor.log'
	outmemcheckreftxt    = outFileDir + delimiter  + '__pyMemcheckRef.log'
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
def process_encode_decode(rawDemo, srcBinDir, outFileDir, codec='0', scc='0', gprof='0', yuvflag='0', refDemo='0', memcheckflag='0', startIdx=0, saveBin=0, SSIM=0):
	if (os.path.exists(srcBinDir) == False):
		print('[error]: the input file path is not exist')
		return -1
	## 1.创建输出目录
	make_all_dir(outFileDir)
	if(int(gprof) == 1):
		make_all_dir(outFileDir + '/outgprof') #如果gprof为1,表示需要对代码进行性能分析，需要创建存储性能分析文件的目录
	
	codec_str = 'x264'
	## 2.输出结果文件
	if   codec == '0':
		codec_str = 'x264'
	elif codec == '1':
		codec_str = 'x265'
	elif codec == '2':
		codec_str = 'uavs3e'
	elif codec == '3':
		codec_str = 'vvenc'
	elif codec == '4':
		codec_str = 'ksc265'
	elif codec == '5':
		codec_str = 'yl265'
	
	outtotal       = outFileDir + delimiter + collect + '.txt'
	outmatch       = outFileDir + delimiter + cmp_match + '.txt'
	outdismatch    = outFileDir + delimiter + cmp_dismatch + '.txt'
	outanchorNdec  = outFileDir + delimiter + Anchor_Ndec + '.txt'
	outredNdec     = outFileDir + delimiter + Reference_Ndec + '.txt'
	outMemchecklog = outFileDir + delimiter + Anchor_memchecklog + '.log'
	outExcelData   = outFileDir + delimiter +'__result_'+ codec_str + '_abr.csv'  ## excel file

	maxch = 70
	spacesymbo = "-"

	pFileNotdec = open(outanchorNdec, 'w') #默认创建记录基准demo解码失败的文件
	if refDemo != '0': #如果有参考，则创建记录参考demo解码失败的文件
		pFileRefNdec = open(outredNdec, "w")
		pFileMatch = open(outmatch, "w+")
		pFileDismatch = open(outdismatch, "w+")
	files = get_raw_data(srcBinDir)
	processIdx = -1 # 处理顺序的索引

	ABR_excel = "__result_yl265_ABR_CTC.csv"
	if scc != '0':
		ABR_excel = "__result_yl265_ABR_SCC.csv"

	csv_file1 = pd.read_csv(ABR_excel, encoding='utf-8') #__result_yl265_ABR.csv
	bitrate   = csv_file1.loc[:,'bitrate(kbps)']
	br_list   = list(bitrate)
	print(br_list)

	loop = -4
	## 3.遍历每个码流文件进行编码或解码
	for filename in files: #遍历每个码流文件
	 	#print filename
		processIdx = processIdx+1
		if processIdx < startIdx:
			loop = loop + 4
			print('[Info] skip:' + filename)
			continue            
		print('\n*****processIdx******: ' + str(processIdx))
		print('[Info] Process: ' + filename)

		pFile = open(outtotal, 'w') #创建汇总文件，性能数据
		if (SSIM == 1):
			totaltitle = 'filename' + ' '*(42 - len('#filename') + 15) + 'total_frames'+ 10*' ' + 'bitrate(Kbps)'  + 10*' ' + 'Y-PSNR(dB)' + 10*' ' +\
							'U-PSNR(dB)' + 10*' ' + 'V-PSNR(dB)' + 10*' ' + 'SSIM(dB)' + 10*' ' + 'time(s)' + 10*' ' + 'fps'
		else:
			totaltitle = 'filename' + ' '*(42 - len('#filename') + 15) + 'total_frames'+ 10*' ' + 'bitrate(Kbps)'  + 10*' ' + 'Y-PSNR(dB)' + 10*' ' +\
				'U-PSNR(dB)' + 10*' ' + 'V-PSNR(dB)' + 10*' ' + 'time(s)' + 10*' ' + 'fps'
		pFile.writelines(totaltitle)
		pFile.write('\n')
		pFile.close()

		space_num = maxch - len(filename)
		onlystreamname = get_file_name(filename)
		#print filename
		#print onlystreamname
		if scc == '0': # CTC
			input_res   = onlystreamname.split('_')[1] 
			stream_name = onlystreamname.split('_')[0] 
		else: # SCC
			input_res   = onlystreamname.split('_')[-4]
			stream_name = onlystreamname.split('_')[-5]		

		width  = input_res.split('x')[0]
		height = input_res.split('x')[1]
		stream_name_res=stream_name + '_' + input_res
		framenum = onlystreamname.split('_')[-1]

		# 循环固定br编码
		#for br in br_values:
		loop = loop + 4
		for br in br_list[loop:loop+4]:
			br = str(int(br))
			outrawtxt = outFileDir + delimiter + onlystreamname + '_Anchor_br' + br + '.txt' 
			outreftxt = outFileDir + delimiter + onlystreamname + '_Ref_br'    + br + '.txt'    
			outrawstr = outFileDir + delimiter + onlystreamname + '_Anchor_br' + br + '.bin' 
			outrefstr = outFileDir + delimiter + onlystreamname + '_Ref_br'    + br + '.bin'    
			outmemcheckanchortxt = outFileDir + delimiter  + '__pyMemcheckAnchor_br' + br + '.log'
			outmemcheckreftxt    = outFileDir + delimiter  + '__pyMemcheckRef_br'    + br + '.log'

			pFileAnchorNdec = open(outanchorNdec, 'w')
			pFileRefNdec 	= open(outredNdec, 'w')
			outrawyuv = 'encoded_recon.yuv'
			outrefyuv = 'decoded_' + onlystreamname + '_br_' + br + '.yuv'

			# 1.原始可执行文件编码
			if yuvflag != '0':  ##注：输出重建YUV文件(当前没有加入命令行，按需修改)
				# cmd for YL265
				cmd_raw = space.join([rawDemo, width, height, framenum, '0', br, '32', filename, outrawstr, '>', outrawtxt, '2>&1'])
			else:
				# cmd for x264
				if codec == '0':
					cmd_raw = space.join([rawDemo, '--preset', 'veryfast', '--tune', 'psnr', 
										'--psnr', '-o', outrawstr,  filename, '--input-res', input_res,
										'--fps 30 --keyint 10000 --br', br, '--threads 1  --bframes 3', '>', outrawtxt, '2>&1']) 								  
				# cmd for x265
				elif codec == '1':
					 cmd_raw = space.join([rawDemo, '--input', filename, '--preset', 'veryfast', '-t', 'zerolatency', 
					 		'--psnr --ssim', '-o', outrawstr, '--input-res', input_res, '--bitrate', br, '-f ', framenum,
					 		'--fps 30 --keyint 10000 --aq-mode 0 --no-psy-rd -b 0 --no-wpp -F 1', '>', outrawtxt, '2>&1']) #--no-wpp -F 1
				# cmd for uavs3e RealTime
				elif codec == '2':
					cmd_raw = space.join([rawDemo, '-f /home/lpeng/AVS/uavs3e/bin/encoder_ra.cfg -p InputFile=', filename, '-p OutputFile=', outrawstr,
										'-p SourceWidth=', width, '-p SourceHeight=', height, '-p FramesToBeEncoded=', framenum,
										'-p SpeedLevel=6 -p IntraPeriod=100  -p RateControl=0 -p br=', br , '>', outrawtxt, '2>&1']) 
				# cmd for vvenc
				elif codec == '3':
					cmd_raw = space.join([rawDemo, '-i', filename, '-s', input_res, '-c yuv420 -r 30 -ip 96 --preset faster',
										'--threads 1 -v 6 -b 0 --br', br, '-o', outrawstr, '>', outrawtxt, '2>&1'])	
				# cmd for KSC265
				elif codec == '4':
					cmd_raw = space.join([rawDemo, '-tune default -preset veryfast -latency zerolatency --psnr 1 --ssim 1', '-i', filename, ' -fr 30 -iper 10000',  '-frms', framenum, #-iper 300 -imin 300
							 '-b', outrawstr, '-wdt', width, '-hgt', height, '-rc 2 -threads 1 -wpp 0 -fpp 0 -bframes  0  -ref0 1 -ref 1 -scenecut 0 -icut 0 -gadapt 0', '-br', br, '>', outrawtxt, '2>&1'])	 # -sao 0 -df 0	 -threads 1 -wpp 0		
				# cmd for YL265
				elif codec == '5':
					cmd_raw = space.join([rawDemo, width, height, framenum, scc, br, '32', filename, outrawstr, '>', outrawtxt, '2>&1']) # 0: 主流 1: 辅流
			print(cmd_raw)
			ret=subprocess.call(cmd_raw, shell=True)
			if(ret!=0):
				print('[error]: ' + filename + ' rawDemo failed!')
				pFileAnchorNdec.write(rawDemo+'cannot dec'+filename+' '+' ret: '+ bytes(ret)+'\n')
				return -1
			else:
				print('[info]: ' + filename + ' rawDemo success!')

			# 2.参考可执行文件编码（解码）
			if refDemo != '0':
				if yuvflag != '0':
					#cmd_ref = space.join([refDemo, '-i', filename, '-c', 'i420', '-f', 'yuv', '-d', outrefstr, '>', outreftxt])
					#cmd_ref = space.join([refDemo, '-b', outrawstr, '-o', outrefyuv, '>', outreftxt])
					cmd_ref = space.join([refDemo, '-i', outrawstr, outrefyuv, '>', outreftxt])  # ffmpeg
				else:
					#cmd_ref = space.join([refDemo, '-i', filename, '-c', 'i420', '-f', 'yuv', '>', outreftxt])
					cmd_ref = space.join([refDemo, '--input', filename, '--preset medium', '-t psnr', 
									'--psnr', '-o', outrefstr, '--input-res', input_res,
									'--fps 30 --no-wpp -F 1 -I 0 -b 0 -f 20 --br', br, '>', outreftxt, '2>&1'])
				print(cmd_ref)
				ret=subprocess.call(cmd_ref, shell=True)
				if(ret==0):
					print('[info]: ' + filename + ' refDemo success!')
				else:
					print('[error]: ' + filename + ' refDemo failed!')
					pFileRefNdec.write(refDemo+'cannot dec'+filename+' '+' ret: '+ bytes(ret)+'\n')
					return -1
	
			## 3.将性能数据结果输出到格式化文本中 outrawtxt--->outtotal
			if codec == '0':
				get_data_from_txt_x264(onlystreamname+'_br'+br, outrawtxt, outtotal, 1)
				if(refDemo != '0'):
					get_data_from_txt_x264(stream_name_res, outreftxt, outtotal, 0)
			elif codec == '1':
				get_data_from_txt_x265(stream_name_res+'_br'+br, outrawtxt, outtotal, 1)
				#if(refDemo != '0'):
				#	get_data_from_txt_x265(onlystreamname+'_br'+br, outreftxt, outtotal, 0)
			elif codec == '2':
				get_data_from_txt_uavs3e(stream_name_res+'_br'+br, outrawtxt, outtotal, 1)
				if(refDemo != '0'):
					get_data_from_txt_uavs3e(stream_name_res, outreftxt, outtotal, 0)					              
			elif codec == '3':
				get_data_from_txt_vvenc(stream_name_res+'_br'+br, outrawtxt, outtotal, 1)
				if(refDemo != '0'):
					get_data_from_txt_vvenc(stream_name_res, outreftxt, outtotal, 0)					              
			elif codec == '4':
				get_data_from_txt_KSC265(stream_name_res+'_br'+br, outrawtxt, outtotal, 1)
			elif codec == '5':
				get_data_from_txt_yl265(stream_name_res+'_br'+br, outrawtxt, outtotal, 1, SSIM)

			## 4. gprof性能分析
			if(int(gprof)==1): #默认为0，表示不使用性能分析工具gprof
				cmd = space.join(['gprof', rawDemo, 'gmon.out', '>', outFileDir+'/outgprof/'+onlystreamname+'_gprof_anchor.txt'])
				print(cmd)
				subprocess.call(cmd, shell=True)

			## 5.valgrind内存检查
			if(memcheckflag != '0'):
				#print cmd_ref
				#exit()
				ret = perform_valgrind_data(outFileDir, cmd_raw, filename, cmd_ref)
				get_data_from_log(filename, outmemcheckanchortxt, outMemchecklog)

			## 6. 一致性比较
			if(refDemo != '0' and int(yuvflag) != 0):
				#ret = yuv_cmp(outrawyuv, outrefyuv)
				ret = filecmp.cmp(outrawyuv, outrefyuv)
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

		## 7.将数据结果从格式化文本写入到excel中 outtotal--->outExcelData
		collect_data_to_excel(outExcelData, outtotal, 1, processIdx, SSIM)
		print("[info]: -----collect data to excel success!------")

	if (saveBin != 0):
		del_file_dir(outFileDir)
	## 关闭打开的文件
	pFileAnchorNdec.close()
	if refDemo != '0':
		pFileMatch.close()
		pFileDismatch.close()
		pFileRefNdec.close()


####################################main 函数入口####################################################
if __name__ == '__main__':
	if(len(sys.argv) < 6):
		print('Usage: ' + '<rawDemo srcStreamDir outFileDir codec scc> [gprof yuvflag refDemo memcheckflag startIdx NosaveBin SSIM] ')
		print('Notice: <> is necessary, [] is optional')
		print('Notice: codec: 0: x264, 1: x265, 2: uavs3e, 3: vvenc, 4: ksc265, 5: yl265'+ '\n')
		exit()
	rawDemo 	 = sys.argv[1]
	srcStreamDir = sys.argv[2]
	outFileDir   = sys.argv[3]
	codec	   	 = sys.argv[4] 
	scc	   	     = sys.argv[5]

	if len(sys.argv) >= 7:
		gprof = sys.argv[6]
	else:
		gprof = 0
	if len(sys.argv) >= 8:
		yuvflag = sys.argv[7]
	else:
		yuvflag = 0
	if len(sys.argv) >= 9:
		refDemo = sys.argv[8]
	else:
		refDemo = 0
	if len(sys.argv) >= 10:
		memcheckflag = sys.argv[9]
	else:
		memcheckflag = 0
	if len(sys.argv) >= 11:
		startIdx = int(sys.argv[10])
	else:
		startIdx = 0
	if len(sys.argv) >= 12:
		saveBin = int(sys.argv[11])
	else:
		saveBin = 0	
	if len(sys.argv) >= 13:
		SSIM = int(sys.argv[12])
	else:
		SSIM = 0	
	## 编解码处理和数据统计
	ret = process_encode_decode(rawDemo, srcStreamDir, outFileDir, codec, scc, gprof, yuvflag, refDemo, memcheckflag, startIdx, saveBin, SSIM)
	if (ret!=0):
		print("[info]: ---------Process finished!---------")
	exit()
