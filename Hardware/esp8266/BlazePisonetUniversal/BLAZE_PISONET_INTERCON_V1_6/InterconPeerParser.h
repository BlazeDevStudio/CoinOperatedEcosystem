#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>

// Read-only discovery packet parser, intentionally independent of ESP8266 and
// Arduino. Discovery NEVER authorizes a paid credit or a hardware command.
// V1 format: BLAZE1|HELLO|XXXXXXXX|id|role|name
namespace blaze_intercon {
struct Hello {
  uint32_t chipId;
  uint16_t nodeId;
  uint8_t role;
  char name[25];
};

inline bool parseUnsigned(const char *begin, const char *end, unsigned long maxValue, unsigned long &out) {
  if (!begin || !end || begin >= end || end-begin > 10) return false;
  unsigned long n = 0;
  for (const char *p=begin;p<end;p++) {
    if (*p<'0'||*p>'9')return false;
    unsigned long v=(unsigned long)(*p-'0');
    if (v>maxValue || n>(maxValue-v)/10) return false;
    n=n*10+v;
  }
  out=n; return true;
}

inline bool parseHello(const char *data, size_t size, Hello &out) {
  if (!data || size < 27 || size > 79 || memchr(data, '\0', size)) return false;
  static const char prefix[]="BLAZE1|HELLO|";
  const size_t pre=sizeof(prefix)-1;
  if (size<=pre+8 || memcmp(data,prefix,pre)!=0) return false;
  const char *p=data+pre;
  uint32_t chip=0;
  for(unsigned i=0;i<8;i++) {
    char ch=p[i]; int v=(ch>='0'&&ch<='9')?ch-'0':(ch>='A'&&ch<='F')?ch-'A'+10:-1;
    if(v<0) return false;
    chip=(chip<<4)|(uint32_t)v;
  }
  if(p[8]!='|')return false;
  const char *id=p+9, *idEnd=(const char*)memchr(id,'|',(data+size)-id);
  if(!idEnd)return false;
  unsigned long node=0;
  if(!parseUnsigned(id,idEnd,65535UL,node) || node==0)return false;
  const char *role=idEnd+1, *roleEnd=(const char*)memchr(role,'|',(data+size)-role);
  if(!roleEnd)return false;
  unsigned long mode=0;
  if(!parseUnsigned(role,roleEnd,2UL,mode))return false;
  const char *name=roleEnd+1;
  size_t nlen=(size_t)((data+size)-name);
  if(nlen<1 || nlen>24)return false;
  for(size_t i=0;i<nlen;i++) {
    char ch=name[i];
    if(!((ch>='A'&&ch<='Z')||(ch>='a'&&ch<='z')||(ch>='0'&&ch<='9')||ch=='-'||ch=='_'))return false;
  }
  out.chipId=chip;out.nodeId=(uint16_t)node;out.role=(uint8_t)mode;
  memcpy(out.name,name,nlen);out.name[nlen]='\0';return true;
}
}
