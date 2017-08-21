#include <stdio.h>
#include <cs50.h>
#include <string.h>
#include <ctype.h>
#define _XOPEN_SOURCE
#include <unistd.h>
#include <crypt.h>

int main(int argc,char *argv[])
{
      if(argc != 2)
   {
       printf("Invalid Command Line Arguments");
       return 1;
   }
   
   string x = argv[1];
   
    char salt[2];
    salt[0] = x[0];
    salt[1] = x[1];
    
    int len = strlen(x);
    string ans;
    int flag = 1;
    for(int i=1; i<=4 && flag ; i++)
    {
        char pass[i];
        for(int j=0; j<52 && flag; j++)
        {   
            if(j < 26)
                pass[0] = (char)('a'+j);
            else
                pass[0] = (char)('A'+(j-26));
            
            for(int k=0; k<52 && flag; k++)
            {
                if(i < 2) {
                    string out = crypt(pass,salt);
                    int ii=0;
                    for(ii=0; ii<len; ii++)
                        if(out[ii] != x[ii])
                            break;
                    if(ii == len){ ans = pass; printf("%s\n",pass); flag = 0; }
                    break;
                }
                if(k < 26)
                     pass[1] = (char)('a'+k);
                else
                     pass[1] = (char)('A'+(k-26));
               
                for(int m=0; m<52 && flag; m++)
                {
                     if(i < 3) {
                      
                     string out = crypt(pass,salt);
                    int ii=0;
                    for(ii=0; ii<len; ii++)
                        if(out[ii] != x[ii])
                            break;
                    if(ii == len) { ans = pass; printf("%s\n",pass); flag = 0; }
                  
                    break;
                     }
                     if(m < 26)
                         pass[2] = (char)('a'+m);
                     else
                         pass[2] = (char)('A'+(m-26));
                   
                    for(int n=0; n<52 && flag; n++)
                    {
                        if(i < 4) {
                        string out = crypt(pass,salt);
                    int ii=0;
                    for(ii=0; ii<len; ii++)
                        if(out[ii] != x[ii])
                            break;
                    if(ii == len) { ans = pass; printf("%s\n",pass); flag = 0; }
                           break; 
                        }
                         if(n < 26)
                              pass[3] = (char)('a'+n);
                          else
                               pass[3] = (char)('A'+(n-26));
                               
                    string out = crypt(pass,salt);
                    int ii=0;
                    for(ii=0; ii<len; ii++)
                        if(out[ii] != x[ii])
                            break;
                    if(ii == len) { ans = pass; printf("%s\n",pass); flag = 0; }
                   
                    }
                }
            }
        }
    }
    return 0;
   
}