#_*_ coding=UTF-8_*_  #脚本中有中文注释必须包含这一句

################################################################################################################
##脚本用法： python auto_codec_coherence.py rawDemo srcStreamDir outFileDir [gprofflag outyuvflag refDemo memcheckflag]
##参数说明：	rawDemo		:	待验证的可执行文件
##				srcStreamDir:	码流路径
##				outFileDir	:	结果输出路径
##				gprofflag	:	gprof开关(默认为0)：如果取0表示不会利用gprof工具进行分析;取1表示利用gprof进行分析
##				outyuvflag	:	yuv输出开关(默认为0)：如果取0，表示解码不输出yuv,否则相反。
##				refDemo		: 	参考可执行文件
##				memcheckflag:	使用valgrind进行内存泄露检查(默认为0)(针对linux下编译的64位库)
##
## Created by lipeng at July 3 2020
## Version 1.0
## Modified:
## (1)2020.7.3 create tag V1.0    支持批量编解码、一致性验证，支持Windows平台(Python)
## (2)2020.7.6 create tag V2.0    支持valgrind和gprof分析
## (3)2020.7.10 create tag V2.0.1 支持对编解码数据进行数据统计(格式输出并导入excel中)
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
		files = [rawdir+"/"+f for f in allfiles if re.search('mpeg4$',f)]
	elif os.path.isfile(rawdir):
		isfile = 1
		files = [rawdir]
	else:
		files = []
		print("ERROR: " + sys.argv[1] + "  is not a dir or file!")
	files.sort(key=str.lower)
	return [files,isfile]

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
		print(path+'创建成功！')
		return True
	else:   #如果目录存在则不创建，并提示目录已经存在
		print(path+'目录已存在！')
		return False

#从文本中提取数据
def get_data_from_txt(filename, txtfile, outdatafile, anchor='1'):
	pFile = open(txtfile, 'a+')
	lines = pFile.readlines() #读取文本中所有行
	lineflag = 0
	Data = {}  #dictory
	for i in range(len(lines)):
		if lines[i].find('Avg: dectime(ms)') != -1:
			lineflag = 1
		if lineflag == 1:
			word = lines[i].split(',')
			lineflag = 0
			print(word)
			for i in range(len(word)):
				splitvalue = (word[i].strip().split('='))
				#print splitvalue[0]
				#print splitvalue[-1]
				Data[splitvalue[0]] = splitvalue[-1]
		#print Data
	pFile.close()
	pFile = open(outdatafile, 'a+')
	if(anchor==1):
		oneline = filename + '(anchor)' + ' '*(30-len(filename)+5) + \
				Data['length(bytes) '] + ' '*12 + \
				Data['fps '] + ' '*5 + '\n'
	else:
		oneline = filename + '(ref)   ' + ' '*(30-len(filename)+5) + \
				Data['length(bytes) '] + ' '*12 + \
				Data['fps '] + ' '*5 + '\n'
	pFile.write(oneline)
	pFile.close()


#collect data from format text to excel
count = 0
def collect_data_to_excel(excelname, inputfile, anchor='1'):
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
			data[filename] = [filename, splitValue[1], splitValue[2]]

	pFile = open(excelname, 'a+')
	pFile.write(codecs.BOM_UTF8)
	csv_writer=csv.writer(pFile, dialect='excel')
	global count
	if count==0:  ##第一次打开文件时才写入
		title=['video sequence', 'total frames', 'time(ms)']
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
def process_encode_decode(rawDemo, srcBinDir, outFileDir, gprof='0', yuvflag='0', refDemo='0', memcheckflag='0'):
	if (os.path.exists(srcBinDir) == False):
		print('the input file path is not exist')
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
	[files, isfile] = get_raw_mpeg4(srcBinDir)
	## 2.遍历每个码流文件进行编码或解码
	for filename in files: #遍历每个码流文件
		print('[Process]:' + filename)
		pFile = open(outtotal, 'w') #创建汇总文件，性能数据
		totaltitle = 'filename' + ' '*(40 - len('#filename')) + 'total_frames' + ' | ' + 'decoding times(ms)'
		pFile.writelines(totaltitle)
		pFile.write('\n')
		pFile.close()

		space_num = maxch - len(filename)
		onlystreamname = get_file_name(filename)
		#print filename
		#print onlystreamname

		outrawtxt = outFileDir + delimiter + onlystreamname + '_Anchordec.txt'
		outreftxt = outFileDir + delimiter + onlystreamname + '_Refdec.txt'
		outrawyuv = outFileDir + delimiter + onlystreamname + '_Anchordec.yuv'
		outrefyuv = outFileDir + delimiter + onlystreamname + '_Refdec.yuv'
		outmemcheckanchortxt = outFileDir + delimiter  + '__pyMemcheckAnchor.log'
		outmemcheckreftxt = outFileDir + delimiter  + '__pyMemcheckRef.log'

		pFileAnchorNdec = open(outanchorNdec, 'w')
		pFileRefNdec = open(outredNdec, 'w')

		# 原始可执行文件解码
		if yuvflag != '0':
		    cmd_raw = space.join([rawDemo, '-i', filename, '-c', 'i420', '-f', 'yuv', '-d', outrawyuv, '>', outrawtxt])
		else:
		    cmd_raw = space.join([rawDemo, '-i', filename, '-c', 'i420', '-f', 'yuv', '>', outrawtxt])
		ret = subprocess.call(cmd_raw, shell=True)
		if(ret!=0):
		    print(filename + ' rawDemo failed!')
		    pFileAnchorNdec.write(rawDemo+'cannot dec'+filename+' '+' ret: '+ bytes(ret)+'\n')
		    return -1
		else:
		    print(filename + ' rawDemo success!')

		# 参考可执行文件解码
		if refDemo != '0':
		    if yuvflag != '0':
		        cmd_ref = space.join([refDemo, '-i', filename, '-c', 'i420', '-f', 'yuv', '-d', outrefyuv, '>', outreftxt])
		    else:
		        cmd_ref = space.join([refDemo, '-i', filename, '-c', 'i420', '-f', 'yuv', '>', outreftxt])

		    ret = subprocess.call(cmd_ref, shell=True)
		    if(ret==0):
		        print(filename + ' refDemo success!')
		    else:
		        print(filename + ' refDemo failed!')
		        pFileRefNdec.write(refDemo+'cannot dec'+filename+' '+' ret: '+ bytes(ret)+'\n')
		        return -1

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
		        print('MATCH!')
		        coherence= '[' + filename + ']:' + space + 'MATCH!'
		        pFileMatch.write(coherence)
		        pFileMatch.write('\n')
		        os.remove(outrawyuv)
		        os.remove(outrefyuv)
		    else:
		        print('DISMATCH!')
		        coherence= '[' + filename + ']:' + space + 'DISMATCH!'
		        pFileDismatch.write(coherence)
		        pFileDismatch.write('\n')

	        ## 6.将性能数据结果输出到格式化文本中 outrawtxt--->outtotal
		get_data_from_txt(filename, outrawtxt, outtotal, 1)
		if(refDemo != '0'):
		    get_data_from_txt(filename, outreftxt, outtotal, 0)
	       ## 7.将数据结果从格式化文本写入到excel中 outtotal--->outExcelData
		collect_data_to_excel(outExcelData, outtotal, 1)
		print("-----collect data to excel success!------")
	      ## 关闭打开的文件
		pFileAnchorNdec.close()
		if refDemo !=0:
		    pFileMatch.close()
		    pFileDismatch.close()
		    pFileRefNdec.close()


####################################main 函数入口####################################################
if __name__ == '__main__':
	if(len(sys.argv) < 4):
		print('Usage: ' + '<rawDemo srcStreamDir outFileDir> [gprof yuvflag refDemo memcheckflag] ' + '\n')
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
	ret = process_encode_decode(rawDemo, srcStreamDir, outFileDir, gprof, yuvflag, refDemo, memcheckflag)
	if (ret!=0):
		print("---------Process finished!---------")
	exit()
