编解码测试脚本：
1、支持功能
1>、支持批量进行编码或解码；

2>、支持对编解码器的输出日志进行数据统计（格式输出并导入excel中）；

3>、支持对编解码器进行一致性/正确性验证;

4>、支持对待验证编解码器进行valgrind内存检查；

5>、支持对待验证编解码器进行gprof分析。

6>、支持计算BDBR和绘制率失真曲线图。

7>、支持绘制码率波动图。

2、支持平台
Windows，Linux(ARM)，macOS

3、使用方法
一、Shell脚本
./auto_codec_test.sh ./bin/xvid_decraw ./stream ./out 1 ./bin/xvid_decraw 0 0

二、Python脚本
python auto_codec_test.py ./bin/xvid_decraw ./stream/ ./out/python 1 1 ./bin/xvid_decraw 0

python auto_codec_test.py ./bin/xvid_decraw ./stream/ ./out/python 0 1 ./bin/xvid_decraw 1

python auto_data_collect.py src out 1 //ref

python auto_data_collect.py src out 0 //anchor

python auto_codec_test_vbr.py ~/H264/x264/x264 /home/myshare/TestSequence/CTC/ out_x264_test 0 0 0 0 0 15 // 编解码批处理+数据统计

python auto_codec_test_cqp.py ~/H264/x264/x264 /home/myshare/TestSequence/CTC/ out_x264_test 0 0 0 0 0 10 // 编解码批处理+数据统计

python auto_data_analysis.py result/__result_x264_vbr.csv out result/__result_x265_vbr.csv // 计算BDBR和绘制率失真曲线图

python auto_codec_bitratewaveplot.py ./bin/SvtAv1DecApp ./out_svtav1_vbr ./out_svtav1_vbr 0 0 0 0 0 30 10 // 绘制码率波动图