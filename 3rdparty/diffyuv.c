#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int compareFile(FILE* file_compared, FILE* file_checked);

int main(int argc, char **argv)
{
	int ret;
	FILE *file1=fopen(argv[1],"rb");
	FILE *file2=fopen(argv[2],"rb");
	if(NULL==file1 || NULL==file2)
		printf("file1 or file2 open error!\n");
	ret = compareFile(file1,file2);
	if(ret)
		printf("Different!\n");
	else
		printf("Same!\n");
	return ret;
}

int compareFile(FILE* file_compared, FILE* file_checked)
{
	int diff=0;
	int N=30;
	char* b1 = (char*) calloc(1,N+1);
	char* b2 = (char*) calloc(1,N+1);
	size_t s1,s2;
	do{
		s1 = fread(b1,1,N,file_compared);
		s2 = fread(b2,1,N,file_checked);
		if(s1 != s2 || memcmp(b1,b2,s1))
		{
			diff = 1;
			break;
		}	
	}while(!feof(file_compared)||!feof(file_checked));
	free(b1);
	free(b2);
	if(diff)   return 1;
	else       return 0;
}
