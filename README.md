# autoCodecTest
This is a codecs coherence and performance test script. 

## 1、支持功能

1、支持批量进行编码或解码；

2、支持对编解码的性能进行数据统计；

3、支持对编解码进行一致性验证;

4、支持对待验证编解码器进行valgrind内存检查；

5、支持gprof。 

## 2、支持平台
Windows, Linux(ARM)

## 3、使用方法

### 一、shell脚本
./auto_codec_test.sh ./bin/xvid_decraw ./stream  ./out 1 ./bin/xvid_decraw  0 0


### 二、Python脚本
python auto_codec_test.py  ./bin/xvid_decraw  ./stream/ ./out/python  1 1 ./bin/xvid_decraw  0

python auto_codec_test.py  ./bin/xvid_decraw  ./stream/ ./out/python  0 1 ./bin/xvid_decraw  1

## 4、注意事项

1、valgrind和gpof不能同时使用。

