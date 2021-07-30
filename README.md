# autoCodecTest
This is a codecs coherence and performance test script. 

## 1、支持功能

1>、支持批量进行编码或解码；

2>、支持对编解码的性能进行数据统计（格式输出并导入excel中）；

3>、支持对编解码进行一致性验证;

4>、支持对待验证编解码器进行valgrind内存检查；

5>、支持待验证编解码器gprof分析。 

6>、支持计算BDBR和绘制率失真曲线图。

## 2、支持平台
Windows, Linux(ARM)

## 3、使用方法

### 一、Shell脚本
./auto_codec_test.sh ./bin/xvid_decraw ./stream  ./out 1 ./bin/xvid_decraw  0 0


### 二、Python脚本
python auto_codec_test.py  ./bin/xvid_decraw  ./stream/ ./out/python  1 1 ./bin/xvid_decraw  0

python auto_codec_test.py  ./bin/xvid_decraw  ./stream/ ./out/python  0 1 ./bin/xvid_decraw  1

python auto_data_collect.py  src  out 1   //ref

python auto_data_collect.py  src  out 0   //anchor

python auto_codec_test_vbr.py ~/H264/x264/x264 /home/myshare/TestSequence/CTC/ out_x264_test 0  0 0 0 0 15

python auto_codec_test_cqp.py ~/H264/x264/x264 /home/myshare/TestSequence/CTC/ out_x264_test 0 0 0 0 0 10

python auto_data_analysis.py result/__result_x264_vbr.csv out result/__result_x265_vbr.csv

## 4、注意事项

1>、valgrind和gpof不能同时使用。

## 5、Revision History

-  2020.7.3   tag V1.0      支持批量编解码、一致性验证，支持Windows平台(Python)

-  2020.7.6   tag V2.0      支持valgrind和gprof分析

-  2020.7.10  tag V2.0.1  支持对编解码数据进行数据统计(格式输出并导入excel中)

-  2020.7.17  tag V2.0.2  支持简单的BDBR统计分析。

-  2021.7.30  tag V2.1     支持计算BDBR和绘制率失真曲线图。
