目录说明：
.
├── codecs_batch	：auto_codec_test.py	批处理脚本：   支持批处理运行编解码器，支持一致性验证，valgrind检查和gprof分析。
├── data_collect	：auto_data_collect.py	数据统计脚本：支持对编解码运行日志进行数据统计（格式输出并写入excel中），支持简单的BDBR统计分析。
├── data_analysis：	:  auto_data_analysis.py	数据分析脚本：支持基于auto_data_collect.py的数据统计结果，计算BDBR和绘制率失真曲线图。
└── readme.txt	：本说明文件

通常使用方法：
1、先运行批处理脚本auto_codec_test.py；
2、再运行auto_data_analysis.py获取数据分析结果（BD-rate/PSNR/Time和率失真曲线图）。

注意事项：
1、auto_codec_test.py脚本中包含了auto_data_collect.py脚本的数据统计功能。