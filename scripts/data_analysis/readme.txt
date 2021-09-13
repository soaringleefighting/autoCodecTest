一、auto_data_analysis.py

作用：计算得到BDBR和率失真曲线，时间差和PSNR差异。

使用方法：
1、输入auto_codec_test.py脚本或者auto_data_collect.py脚本输出的指定格式的__result.csv统计数据（比如__result_x265_vbr.csv）；
2、运行auto_codec_analysis.py脚本，输出对应的BDBR和率失真曲线。

示例：
python auto_data_analysis.py result/__result_x264_vbr.csv out result/__result_x265_vbr.csv


二、auto_codec_bitratewaveplot.py

作用：编码或解码后，绘制码率波动图，用于分析编码器的码率控制情况（精度）。

注意事项：
（1）解码输出格式需要根据编解码器对应修改。
（2）图像的标题包含了测试序列名称（码率统计间隔）,平均码率，最大码率信息，及最大码率/平均码率的比值。图像中采用直线表明了平均码率、目标码率和目标码率的120%。

示例：
python auto_codec_bitratewaveplot.py ./bin/SvtAv1DecApp  ./out_svtav1_vbr  ./out_svtav1_vbr  0 0 0 0 0 30 10
