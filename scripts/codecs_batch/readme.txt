使用命令：
1、CQP配置：
python auto_codec_test_cqp.py ~/H264/x264/x264 /home/myshare/TestSequence/CTC/ out_x264_test 0 0 0 0 0 10
python auto_codec_test_cqp.py  ~/H265/x265/build/linux/x265 /home/myshare/TestSequence/CTC/ out_x265_test  1  0 0 0 0 10
python auto_codec_test_cqp.py ~/AVS/uavs3e/uAVS3  /home/myshare/TestSequence/CTC/ out_uavs3e_test  2 0 0 0 0 10
python auto_codec_test_cqp.py ~/H266/vvenc/source/App/vvencapp/vvencapp /home/myshare/TestSequence/CTC/ out_vvenc_test 3 0 0 0 0 15

2、VBR配置：
python auto_codec_test_vbr.py ~/H264/x264/x264 /home/myshare/TestSequence/CTC/ out_x264_test 0  0 0 0 0 15
python auto_codec_test_vbr.py  ~/H265/x265/build/linux/x265 /home/myshare/TestSequence/CTC/ out_x265_test 1 0 0 0 0 15
python auto_codec_test_vbr.py ~/AVS/uavs3e/uAVS3  /home/myshare/TestSequence/CTC/ out_uavs3e_test 2  0 0 0 0 15
python auto_codec_test_vbr.py ~/AV1/libaom_av1/aom_build/aomenc /home/myshare/TestSequence/CTC/  out_libaom_LDP_VBR 3 0  0 0 0 15