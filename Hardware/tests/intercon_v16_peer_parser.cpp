#include "../esp8266/BlazePisonetUniversal/BLAZE_PISONET_INTERCON_V1_6/InterconPeerParser.h"
#include <cassert>
#include <cstring>
#include <iostream>
using namespace blaze_intercon;
static bool accepts(const char *s){ Hello h{};return parseHello(s,strlen(s),h); }
int main(){
  Hello h{};
  const char* valid="BLAZE1|HELLO|0123ABCD|65535|2|Pisonet_01";
  assert(parseHello(valid,strlen(valid),h));
  assert(h.chipId==0x0123ABCD && h.nodeId==65535 && h.role==2);
  assert(strcmp(h.name,"Pisonet_01")==0);
  assert(accepts("BLAZE1|HELLO|00000001|1|0|PC-1"));
  const char* bad[]={"BLAZE1|CREDIT|0123ABCD|1|1|PC-01", "BLAZE1|HELLO|0123ABCD|0|0|PC01",
   "BLAZE1|HELLO|0123ABCD|65536|0|PC01", "BLAZE1|HELLO|0123ABCD|1|3|PC01",
   "BLAZE1|HELLO|0123ABCG|1|0|PC01", "BLAZE1|HELLO|0123ABCD|1|0|PC 01",
   "BLAZE1|HELLO|0123ABCD|1|0|PC01|EXTRA", "BLAZE1|HELLO|0123ABCD|1|0|",
   "BLAZE1|HELLO|0123ABCD|-1|0|PC01", "BLAZE1|HELLO|0123ABCD|1|0|PC01\n",
   "BLAZE1|HELLO|0123ABCD|01|x|PC01"};
  for(const char* b:bad)assert(!accepts(b));
  char embeddedNul[]={'B','L','A','Z','E','1','|','H','E','L','L','O','|',0};
  assert(!parseHello(embeddedNul,sizeof(embeddedNul),h));
  char huge[130];memset(huge,'A',sizeof(huge));
  assert(!parseHello(huge,sizeof(huge),h));
  std::cout<<"intercon peer parser: 15 cases PASS\n";
}
