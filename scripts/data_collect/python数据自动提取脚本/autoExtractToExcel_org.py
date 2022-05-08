import os
import sys
import re
import xlwt
import xlrd

allfiles = []
def get_all_file(rawdir):
      for root,dirs,files in os.walk(rawdir):
            for f in files:
                #print f
                if(re.search('test.txt',f)):
                    print(f)
                    allfiles.append(os.path.join(root,f))
            for dirname in dirs:
                get_all_file(os.path.join(root,dirname))
      allfiles.sort(key=str.lower)
      return allfiles

def make_all_dir(path):
      path = path.strip()
      isExist = os.path.exists(path)
      if (not isExist):
            os.makedirs(path)
            print(path+' Successful Create!')
            return True
      
def autoExtract(file ,excel_file):

    txt = open(file,'r')
    excel = xlwt.Workbook(encoding='utf-8', style_compression=0)
    sheet = excel.add_sheet('statistics')

    lines = txt.readlines()
    i=0
    for line in lines:
        line.rstrip(' ')
        out = re.split('[,]',line)       
        print(out)
        sheet.write(i,0,out[0])
        sheet.write(i,1,out[1])
        sheet.write(i,2,out[2])
        i = i+1
    excel.save(excel_file)
    return 0

if __name__ == '__main__':
    if(len(sys.argv) < 3):
        print("Usage: autoExtractToExcel.py targetDir outResult\n")
        sys.exit(1)
    targetDir = sys.argv[1]
    outResultDir = sys.argv[2]
    if(not os.path.exists(outResultDir)):
          make_all_dir(outResultDir)
    excel_file = outResultDir + "/"+"_result.xls"
    allfiles = get_all_file(targetDir)
    for file in allfiles:
        autoExtract(file,excel_file)

    sys.exit(0)
