auto_data_analysis.py

作用：计算得到BDBR和率失真曲线，时间差和PSNR差异。

使用方法：
1、输入auto_codec_test.py脚本或者auto_data_collect.py脚本输出的指定格式的__result.csv统计数据（比如__result_x265_vbr.csv）；
2、运行auto_codec_analysis.py脚本，输出对应的BDBR和率失真曲线。

示例：
python auto_data_analysis.py result/__result_x264_vbr.csv out result/__result_x265_vbr.csv

