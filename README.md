# autoCodecTest
This is a codecs coherence and performance test script. 

## 1、支持功能

1>、支持批量进行编码或解码；

2>、支持对编解码的性能进行数据统计（格式输出并导入excel中）；

3>、支持对编解码进行一致性验证;

4>、支持对待验证编解码器进行valgrind内存检查；

5>、支持gprof。 

6>、支持BDBR统计分析。

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

## 4、注意事项

1>、valgrind和gpof不能同时使用。

## 5、Revision History

1> 2020.7.3  create tag V1.0    支持批量编解码、一致性验证，支持Windows平台(Python)

2> 2020.7.6  create tag V2.0    支持valgrind和gprof分析

3> 2020.7.10 create tag V2.0.1  支持对编解码数据进行数据统计(格式输出并导入excel中)

4> 2020.7.17 create tag V2.0.2  auto_data_collect.py支持BDBR统计分析。
