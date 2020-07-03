#! /bin/bash
#Functionality： codecs coherence test and performance test
#Filename:  auto_codec_arm_test.sh
#Creator: 	SoaringLee 
#Modify: 1、支持待验证可执行文件单独解码码流；
#		 2、支持测试性能时，解码不写yuv，默认是解码写yuv的；
#		 3、增加在脚本执行中断后从制定序号位置处继续执行的功能；
##===================main========================
##定义全局变量
MaxChar=100
AnchorNdec=0
RefNdec=0

Refdemo="0"
YUVflag="1" #默认写yuv
YUVCompare="./3rdparty/diffyuv" ##YUV比较可执行文件
CoreNum="" ##指定当前可执行文件运行的CPU核心

##输入参数个数检查
if [ $# -lt 3 ] ;then
	echo "Usage: $0 <AnchorDemo StreamDir outFileDir> [YUVflag RefDemo start_idx CoreNum]"
	echo "Notice: This shell script need at lease 3 parameters,<xxx> is necessary, [xxx] is optinal"
	exit 1
fi	
	
##读取命令行参数，增加可读性
AnchorDemo="$1"
StreamsDir="$2"
outFileDir="$3"

#echo ${outFileDir}

##判断输出目录是否存在
if [ ! -d ${outFileDir} ];then
	echo "${outFileDir} doesn't exist, Now create it!"
	mkdir "${outFileDir}"
else
	echo "${outFileDir} already exist!"
fi


if [ $# -ge 4 ];then
	YUVflag="$4"
fi

if [ $# -ge 5 ];then
	RefDemo="$5"
fi

if [ $# -ge 6 ];then
	StartIdx="$6"
fi

if [ $# -ge 7 ];then
	CoreNum="$7"
fi

##统计输出txt
pMatchtxt=${outFileDir}/"__pMatch.txt"       #一致性对比的一致输出txt
pNotMatchtxt=${outFileDir}/"__pNotMatch.txt" #一致性对比的不一致输出txt
pPerformancetxt=${outFileDir}/"__pCollect.txt" #性能对比输出txt
pAnchor_Ndectxt=${outFileDir}/"__Anchor_notdecstream.txt" #待验证可执行文件不能解码的码流
pRef_Ndectxt=${outFileDir}/"__Ref_notdecstream.txt" #参考可执行文件不能解码的码流
##title
title="filename"
spacenum_title=$((${MaxChar}-${#title}))
spacezero=$(seq -s '-' ${spacenum_title} | sed 's/[0-9]//g')
totaltitle="filename ${spacezero}    total frames  | fps"
echo $totaltitle > $pPerformancetxt

processIdx=-1

echo ${StreamsDir}

##[1]. Recursively get svac stream files
allfile=$(find ${StreamsDir} -name "*.mpeg4")
echo ${allfile}

for file in `ls ${allfile}`
do
	#echo ${file}
	# 去除含有QP和ai的码流
	#result=`echo $file | grep -e "QP" -e "ai"`
	#if  [ -n "${result}" ]; then
	#	continue
	#fi
	processIdx=$((${processIdx}+1))
	#if [ $# -ge 6 ]; then
	#  if [ ${processIdx}  -le  ${StartIdx} ]; then
	#	continue
	#  fi
	#fi
	echo "******processIdx*******:" ${processIdx}
	echo "******Current test*******:" $file
	#提取出文件名
	filename=${file##*/} #从字符首部开始，删除最长匹配*/的子串
	filename=${filename%.*} #从字符串尾部开始，删除最短匹配.*的子串
	##格式控制
	spacenum=$((${MaxChar}-${#filename} - 3))
	spaceone=$(seq -s ' ' ${spacenum} | sed 's/[0-9]//g')
	spacetwo=$(seq -s '-' ${spacenum} | sed 's/[0-9]//g')
	spacethr=$(seq -s '-' ${#filename} | sed 's/[0-9]//g')

	##解码yuv和解码输出txt
	outyuvAnchor=${outFileDir}/${filename}"_Anchor.yuv"
	outyuvRef=${outFileDir}/${filename}"_Ref.yuv"
	outtxtAnchor=${outFileDir}/${filename}"_Anchor.txt"
	outtxtRef=${outFileDir}/${filename}"_Ref.txt"

	RawCmd=${AnchorDemo}" -i "${file}
	RefCmd=${RefDemo}" -i "${file}

	#[2].Decoding svac streams using anchor and red decoder
	if [ "${YUVflag}"=="1" ];then
		RefCmd=${RefCmd}" -d "${outyuvRef}
		RawCmd=${RawCmd}" -d "${outyuvAnchor}
		RefCmd=${RefCmd}" -c i420 -f yuv "
		RawCmd=${RawCmd}" -c i420 -f yuv "	
	fi 
	if [ -n "${CoreNum}" ]; then
		RefCmd=${RefCmd}" -c ${CoreNum}"
		RawCmd=${RawCmd}" -c ${CoreNum}"
	fi

	RefCmd=${RefCmd}" > "${outtxtRef}
	RawCmd=${RawCmd}" > "${outtxtAnchor}

	##原始可执行文件解码
	echo ${RawCmd}
	eval ${RawCmd}
	if [ $? -ne 0 ];then
		echo "========Anchor Dec Failure!========="
		echo "${AnchorDemo} cannot dec: $file, ret:$?" >> ${pAnchor_Ndectxt}
		AnchorNdec=1
	 else
		echo "********Anchor Dec Success!*********"
	fi

	## 参考可执行文件解码
	if [ x"RefDemo" != x"0" ];then
		 echo ${RefCmd}
		 eval ${RefCmd}
		 if [ $? -ne 0 ] ;then
			 echo "========Ref Dec Failure!========="
			 echo "${RefDemo} cannot dec: $file, ret:$?" >> ${pRef_Ndectxt}
			 RefNdec=1
		 else
			echo "********Ref Dec Success!*********"
		 fi
	else
		 RefNdec=1
	fi

	##[3]. ref and anchor filecmp for coherence test
	if [[ ${AnchorNdec} -ne 1 && ${RefNdec} -ne 1 && ${YUVflag} -eq 1 ]];then ##两者都解码成功才进行yuv比较
		 cmpCmd=${YUVCompare}" "${outyuvAnchor}" "${outyuvRef}
		 eval ${cmpCmd}
		 if [ $? -eq 0 ];then
			 echo "**********YUV MATCH!***********"
			 echo "[$filename]${spacesone}MATCH!" >>${pMatchtxt}
			 rm -f ${outyuvAnchor}
			 rm -f ${outyuvRef}
		 else
			 echo "=========YUV DISMATCH!========="
			 echo "[$filename]${spacesone}DISMATCH!>>${pNotMatchtxt}"
		 fi
	fi
	##[4]. Performance collect
	if [ ${AnchorNdec} -ne 1 ];then
		 result=`cat $outtxtAnchor | grep -e Avg` #查找文件中含有loop字符串的行
		 echo ${result}
		 framenum=${result##*length(bytes) =} ##delete right side
		 #framenum=${result%%, length*} ##delete right side
		 #framenum=${framenum##*,} ##delete left side
		 #echo ${framenum}
		 fps=${result%%, length*}
		 fps=${fps##*fps =}
		 #echo ${fps}
		 echo "$filename(Anchor) ${spaceone} $framenum  $fps" >> ${pPerformancetxt}
		 #rm -f ${outtxtAnchor}
	fi

	if [ ${RefNdec} -ne 1 ];then
		 #result=`cat $outtxtRef | grep -e loop` #查找文件中含有loop字符串的行
		 #framenum=${result%%frames*} ##delete right side
		 #framenum=${framenum##*,} ##delete left side
		 #fps=${result%%fps*}
		 #fps=${fps##*,}
		 result=`cat $outtxtAnchor | grep -e Avg` #查找文件中含有loop字符串的行
		 echo ${result}
		 framenum=${result##*length(bytes) =} ##delete right side
		 fps=${result%%, length*}
		 fps=${fps##*fps =}
		 echo "${spacesthr}   (Ref   ) ${spaceone} $framenum  $fps" >> ${pPerformancetxt}
		 #rm -f ${outtxtRef}
	fi

	AnchorNdec=0  ##恢复原始不解码标记
	RefNdec=0  ##恢复参考不解码标记
done

echo "This shell script run successfully!"
exit 0
