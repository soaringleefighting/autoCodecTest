#_*_ coding=UTF-8_*_  #脚本中有中文注释必须包含这一句

################################################################################################################
##脚本用法： python auto_codec_coherence.py rawDemo srcStreamDir outFileDir [gprofflag outyuvflag refDemo memcheckflag startIdx winsize winstep]
##参数说明：	 rawDemo	 :	 待验证的可执行文件
##				srcStreamDir:	码流路径
##				outFileDir	:	结果输出路径
##				gprofflag	:	gprof开关(默认为0)：如果取0表示不会利用gprof工具进行分析;取1表示利用gprof进行分析
##				outyuvflag	:	yuv输出开关(默认为0)：如果取0，表示解码不输出yuv,否则相反。
##				refDemo		: 	参考可执行文件
##				memcheckflag:	使用valgrind进行内存泄露检查(默认为0)(针对linux下编译的64位库)
##				startIdx	:	在批处理过程中，支持从指定序号startIdx的位置处开始执行。
##				winsize		:	计算瞬时码率的窗口大小
##				winstep		:	计算瞬时码率的滑动窗口步长
##
## Created by lipeng at July 3 2020
## Version 1.0
## Modified:
## (1)2020.7.3 create tag V1.0    支持批量编解码、一致性验证，支持Windows平台(Python)
## (2)2020.7.6 create tag V2.0    支持valgrind和gprof分析
## (3)2020.7.10 create tag V2.0.1 支持对编解码数据进行数据统计(格式输出并导入excel中)
## (4)2021.9.12 create tag V2.2   支持绘制码率波动图，用于分析编码器的码率控制精度。	
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
import numpy as np
import matplotlib.pyplot as plt

reload(sys)
sys.setdefaultencoding('utf-8')


space = ' '
delimiter = '/'

#定义输出文件
bits_summary_file 	= "bitrate_summary.log"
bits_summary_all    = "bitrate_summary_all.log"

collect 			= '_pyout_collect'  	#性能对比输出文件夹
cmp_match			= '_pyout_match'  		#yuv对比一致
cmp_dismatch 		= '_pyout_dismatch' 	# yuv对比不一致
Anchor_Ndec 		= '_pyAnchor_notdecstream'	#待验证的可执行文件不能解码的码流
Reference_Ndec		= '_pyRef_notdecstream'		#参考可执行文件不能解码的码流
Anchor_memchecklog 	= '_pyAnchor_memcheck' 		#对待验证可执行文件进行内存检查后的汇总文件

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
		files = [rawdir+"/"+f for f in allfiles if re.search('bin$',f)]
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

#从序列名字中提取相关信息（序列名/分辨率/目标码率）
def extract_info_from_name(filename):
	key = ["SVT-AV1"]
	target_bit = []
	stream_name = []
	stream_resolution = ''
	##filename=xulie_832x480_br1024.264 or xulie_832x480.yuv
	stream_name.append(filename.split('_')[0])
	stream_resolution = filename.split('_')[1]
	stream_name.append(stream_resolution)
	key.append('_'.join(stream_name))
	target_bit = filename.split('_')[-1].split('br')[-1]
	key.append(str(target_bit))
	#print key
	return key
			
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


##计算一个列表里所有值的总和
def sum_list(list):
    if (list==[]):
        return 0
    return list[0] + sum_list(list[1:])  ##迭代思想

##以滑动窗口跟滑动步长计算一个列表（每个滑动窗求取窗口内的平均值）
def cacl_avg_in_windowsize(list, winsize, winstep):
	len_list = len(list)
	#print len_list
	list_avg = []
	for i in range(0, len_list, winstep):
		if i + winsize > len_list:
			break
		windata_list = list[i:i+winsize]
		windata_avg  = float(sum_list(windata_list)) / winsize
		windata_avg  = windata_avg *30 / 1000  ## bps-->kbps
		list_avg.append(windata_avg)
	list_avg.append(float(sum_list(list_avg)) / len(list_avg))
	list_avg_str = map(lambda x:str(x), list_avg)
	return list_avg_str

##从解码输出文件中提取码率    
def extract_bits(outdir, outtxt, keys, winsize, winstep):
	file_out = open(outtxt, 'r+')
	lines = file_out.readlines()
	line_begin = 0
	y_bits = []
	for i in range(len(lines)):
		if lines[i].find('frame_size') != -1:
			line_begin = 1
		if line_begin == 1:
			line_word = lines[i].split(',')[1].strip().split(':')[1]
			y_bits.append(float(line_word)*8)  ## Byte-->bit
			#print y_bits
	y_bits_win_avg = cacl_avg_in_windowsize(y_bits, winsize, winstep)
	#print y_bits_win_avg
	def write_summary_to_file(outdir, summary_file, bits_summary_all, keys, data, check):
		file = open(outdir + delimiter + summary_file, 'w+')
		lines = file.readlines()
		if check == 1:
			anchor_keys = list(keys)
			anchor_keys[0] = 'Anchor'
			anchor_keys.extend(data)
			print anchor_keys
			one_line = space.join(anchor_keys)

			def check_data(one_line, lines):
				ret = 0
				lines_len = len(lines)
				for i in range(0, lines_len):
					test = lines[i].strip()
					if one_line == lines[i].strip():
						ret = 1
				return ret
			ret = check_data(one_line, lines)
			if ret == 0:
				file.write(one_line + '\n')
		else:
			file.write(one_line + '\n')
		file.close()

		file = open(outdir + delimiter + bits_summary_all, 'a+')
		file.write(one_line + '\n')
		file.close()
    
	write_summary_to_file(outdir, bits_summary_file, bits_summary_all, keys, y_bits_win_avg, 1)
	file_out.close()

##从汇总文件中提取编码器的名字、序列名、码率信息
def get_encoder_seqs_bits(summary_file):
	file = open(summary_file,"r")
	lines = file.readlines()
	encodes_list = []
	seqs_list = []
	bits_list = []
	def extract_enc_seq_bit(content):
		items = content.split()
		if not items[0] in encodes_list:
			encodes_list.append(items[0])
		if not items[1] in seqs_list:
			seqs_list.append(items[1])
		if not items[2] in bits_list:
			bits_list.append(items[2])
	map(extract_enc_seq_bit, lines)
	file.close()
	#print encodes_list
	#print seqs_list
	#print bits_list
	return (encodes_list, seqs_list, bits_list)

##排除某编码器之外的数据
def filter_by_enc(enc):
	return (lambda x:True if cmp(x[0], enc) == 0 else False)
	
##排除某序列之外的数据
def filter_by_seq(seq):
	return (lambda x:True if cmp(x[1], seq) == 0 else False)    
	
##排除某码率之外的数据
def filter_by_bit(bit):
	return (lambda x:True if cmp(x[2], bit) == 0 else False)


###执行画波动图
def exec_plot_wave_chart_process(outdir, bit, enclist, seq, plot_table, y_label, winsize):
	x		   = []
	item_count = 0
	data_max   = 0
	data_min   = 0

	for i in range(0, len(enclist)):
		enc 	  		 = enclist[i]
		data_list 		 = plot_table[i]
		data_list 		 = map(lambda x:float(x), data_list) #数字转换为float型
		data_each 		 = data_list[0:-1]
		data_max  		 = max(data_each)
		data_min  		 = min(data_each)
		data_avg  		 = float('%.3f' % data_list[-1])
		data_target 	 = float(bit)
		target_avg_ratio = float('%.3f' %(data_target / data_avg))	
		
		print 'target_bitrate:  ' + str(bit)
		print 'average_bitrate: ' + str(data_avg)
		print 'max_bitrate: '     + str(data_max)
		print 'min_bitrate: '     + str(data_min)

		plt.plot()
		#plt.style.use('ggplot') #使用'ggplot'风格美化显示的图表 ##classic #Solarize_Light2  ##print(plt.style.available)
		plt.title('_'.join([seq, bit])+' (Bitrate interval: '+str(winsize)+' frames)' + '\n'   + \
				  'Average, Maximum bitrate: '+str(data_avg)+' kbps, '+str(data_max) +' kbps\n' + \
				  'Max/Avg: '+	str(target_avg_ratio), fontsize=10 )
		plt.xlabel("Frame Idx")
		plt.ylabel(y_label)
		plt.grid(True)
		
		#码率信息
		x = range(0, len(data_each))
		plt.plot(x, data_each, "-o", label = '_'.join([enc, seq, bit]))
		plt.rcParams["legend.fontsize"] = "x-small"
		plt.legend(shadow=True, loc=0)
		
		#平均码率
		item_count = len(data_each)
		data_avg_list = np.linspace(data_avg, data_avg, item_count)
		plt.plot(x, data_avg_list, "-x", label='_'.join(["average"]))
		plt.legend(shadow=True, loc=0)

		#目标码率
		item_count = len(data_each)
		data_target_list = np.linspace(data_target, data_target, item_count)
		plt.plot(x, data_target_list, "-*", label='_'.join(["target"]))
		plt.legend(shadow=True, loc=0)

		#目标码率*120%
		item_count = len(data_each)
		data_target_list = np.linspace(data_target*1.2, data_target*1.2, item_count)
		plt.plot(x, data_target_list, "-v", label='_'.join(["target*120%"]))
		plt.legend(shadow=True, loc=0)

	plt.savefig('_'.join([outdir+delimiter+"bitrate_waveplot"+delimiter, seq, bit, y_label]) + ".png")
	plt.close()

###画波动图前预处理
def plot_wave_chart_process(outdir, summary_file, y_label, winsize):
	(encs, seqs, bits) = get_encoder_seqs_bits(outdir+delimiter+summary_file)
	file = open(outdir+delimiter+summary_file, "r")
	lines = file.readlines()
	def collect_enc(idx):
		def collect(x, y):
			x.append(y[idx])
			return x
		return collect
	for seq in seqs:
		plot_tabel= []
		for bit in bits:
			datas = filter(filter_by_seq(seq), (filter(filter_by_bit(bit), map(str.split, lines))))
			#print datas
			encs = reduce(collect_enc(0), datas, list())
			#print encs
			plot_tabel = map(lambda x:(x[3:]), datas)
			#print plot_tabel
			exec_plot_wave_chart_process(outdir, bit, encs, seq, plot_tabel, y_label, winsize)

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
def process_encode_decode(rawDemo, srcBinDir, outFileDir, gprof='0', yuvflag='0', refDemo='0', memcheckflag='0', startIdx=0, winsize=30, winstep=8):
	if (os.path.exists(srcBinDir) == False):
		print('the input file path is not exist')
		return -1
	## 1.创建输出目录
	make_all_dir(outFileDir)
	## 1.1 创建性能分析目录
	if(int(gprof) == 1):
		make_all_dir(outFileDir + '/outgprof') #如果gprof为1,表示需要对代码进行性能分析，需要创建存储性能分析文件的目录
	
	## 1.2 创建码控分析目录
	make_all_dir(outFileDir + delimiter + "bitrate_waveplot")

	outtotal 		= outFileDir + delimiter + collect + '.txt'
	outmatch 		= outFileDir + delimiter + cmp_match + '.txt'
	outdismatch 	= outFileDir + delimiter + cmp_dismatch + '.txt'
	outanchorNdec 	= outFileDir + delimiter + Anchor_Ndec + '.txt'
	outredNdec 		= outFileDir + delimiter + Reference_Ndec + '.txt'
	outMemchecklog 	= outFileDir + delimiter + Anchor_memchecklog + '.log'
	outExcelData 	= outFileDir + delimiter +'__result.csv'  ## excel file

	maxch 			= 70
	spacesymbo 		= "-"

	pFileNotdec = open(outanchorNdec, 'w') #默认创建记录基准demo解码失败的文件
	if refDemo != '0': #如果有参考，则创建记录参考demo解码失败的文件
		pFileRefNdec = open(outredNdec, "w")
		pFileMatch = open(outmatch, "w+")
		pFileDismatch = open(outdismatch, "w+")
	
	[files, isfile] = get_raw_mpeg4(srcBinDir)  ##根据码流后缀名对应修改即可
	processIdx = -1 # 处理顺序的索引

	## 2.遍历每个码流文件进行编码或解码
	for filename in files: #遍历每个码流文件
		#print filename
		processIdx = processIdx+1
		if processIdx < startIdx:
			print('[Info] skip:' + filename)
			continue
					
		print('\n*****processIdx******: ' + str(processIdx))
		print('[Process]:' + filename)
		pFile = open(outtotal, 'w') #创建汇总文件，性能数据
		totaltitle = 'filename' + ' '*(40 - len('#filename')) + 'bitrate' + ' | ' + 'decoding times(ms)'
		pFile.writelines(totaltitle)
		pFile.write('\n')
		pFile.close()

		space_num = maxch - len(filename)
		onlystreamname = get_file_name(filename)
		#print filename
		print onlystreamname

		outrawtxt = outFileDir + delimiter + onlystreamname + '_Anchordec.txt'
		outreftxt = outFileDir + delimiter + onlystreamname + '_Refdec.txt'
		outrawyuv = outFileDir + delimiter + onlystreamname + '_Anchordec.yuv'
		outrefyuv = outFileDir + delimiter + onlystreamname + '_Refdec.yuv'
		outmemcheckanchortxt = outFileDir + delimiter  + '__pyMemcheckAnchor.log'
		outmemcheckreftxt 	 = outFileDir + delimiter  + '__pyMemcheckRef.log'

		pFileAnchorNdec = open(outanchorNdec, 'w')
		pFileRefNdec    = open(outredNdec, 'w')

		# 2.1 原始可执行文件解码
		if yuvflag != '0':
		    cmd_raw = space.join([rawDemo, '-i', filename, '-o', outrawyuv, '>', outrawtxt, '2>&1'])  ##命令行参数需要根据编解码器具体修改
		else:
		    cmd_raw = space.join([rawDemo, '-i', filename, '>', outrawtxt, '2>&1'])
		#print cmd_raw
		ret = subprocess.call(cmd_raw, shell=True)
		if(ret!=0):
		    print(filename + ' rawDemo failed!')
		    pFileAnchorNdec.write(rawDemo+'cannot dec'+filename+' '+' ret: '+ bytes(ret)+'\n')
		    return -1
		else:
		    print(filename + ' rawDemo success!')

		# 2.2 参考可执行文件解码
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
		
        ## 6. 绘制码率波动图
		## 6.1 提取相关信息
		keys = extract_info_from_name(onlystreamname)
		
		## 6.2 统计码率情况
		extract_bits(outFileDir, outrawtxt, keys, winsize, winstep)

		## 6.3 绘制码率波动图
		plot_wave_chart_process(outFileDir, bits_summary_file, "Bitrate(Kbps)", winsize)

		## 7.将性能数据结果输出到格式化文本中 outrawtxt--->outtotal
		#get_data_from_txt(filename, outrawtxt, outtotal, 1)
		#if(refDemo != '0'):
		#    get_data_from_txt(filename, outreftxt, outtotal, 0)
		
        ## 8.将数据结果从格式化文本写入到excel中 outtotal--->outExcelData
		#collect_data_to_excel(outExcelData, outtotal, 1)
		#print("-----collect data to excel success!------")
		
		## 关闭打开的文件
		pFileAnchorNdec.close()
		if refDemo != '0':
		    pFileMatch.close()
		    pFileDismatch.close()
		    pFileRefNdec.close()

####################################main 函数入口####################################################
if __name__ == '__main__':
	if(len(sys.argv) < 4):
		print('Usage: ' + '<rawDemo srcStreamDir outFileDir> [gprof yuvflag refDemo memcheckflag startIdx winsize winstep] ' + '\n')
		print('Notice: <> is necessary, [] is optional')
		exit()

	def clear_file(filename):
		file = open(filename, "w+")
		file.truncate()
		file.close()

	## 1.命令行参数解析		
	rawDemo 	 = sys.argv[1]
	srcStreamDir = sys.argv[2]
	outFileDir   = sys.argv[3]

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
	if len(sys.argv) >= 10:
		winsize = int(sys.argv[9])
	else:
		winsize = 30
	if len(sys.argv) >= 11:
		winstep = int(sys.argv[10])
	else:
		winstep = 8
	
	## 2.清空文件
	if (os.path.exists(outFileDir+delimiter+bits_summary_file) == True):
		clear_file(outFileDir+delimiter+bits_summary_file)

	## 3.执行批处理编解码和绘制码率波动图
	ret = process_encode_decode(rawDemo, srcStreamDir, outFileDir, gprof, yuvflag, refDemo, memcheckflag, startIdx, winsize, winstep)

	if (ret!=0):
		print("---------Process finished!---------")
	exit()
