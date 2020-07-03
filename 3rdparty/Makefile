#指定后缀名和伪目标
.SUFFIXES: .c,.o,.cpp,.S,.s  
.PHONY: all,clean
#设置相关工具
CC = gcc
CXX = g++
AR = ar
LD = ld

#设置相关路径
vpath %.h ./inc
ROOTSRC = ./
INCLUDES = ./inc

#设置工具的相关参数
BIN_TARGET = diffyuv
CFLAGS += -Wall -O3  -g  -I$(INCLUDES)
CXXFLAGS += -Wall -g
LDFLAGS += -Wall -O3 -g
ARFLAGS += -crus

#以下获取OBJS文件的方式适用于含有少量文件的编译
SRCS = $(ROOTSRC)/diffyuv.c			
       	   
OBJS = $(patsubst %.s, %.o, $(patsubst %.cpp,%.o, $(patsubst %.c,%.o,$(SRCS))))

#以下通过通配符和字符串函数获取OBJS的方式适用于较大工程（含有大量文件）的编译
#SRCOBJS := $(patsubst %.cpp, %.o, $(wildcard $(SRCDIR)/*.cpp))
#TESTOBJS := $(patsubst %.cpp, %.o, $(wildcard $(TESTDIR)/*.cpp))
#OBJS := $(SRCOBJS) $(TESTOBJS)

#编译规则
all: $(BIN_TARGET)
$(BIN_TARGET): $(OBJS)
	$(CXX) -o $@ $(OBJS) $(LDFLAGS)
	rm $(OBJS)

%.o: %.c
	$(CC) -c $< $(CFLAGS) -o $@
%.o: %.cpp
	$(CXX) -c $< $(CXXFLAGS) -o $@
	
clean:
	-rm  $(OBJS)
	-rm  $(BIN_TARGET)