// Portable arm-marker identity, CRC, role and reboot semantics contract.
// Actual LittleFS power-cut and physical coin accounting remain unverified.
#include <cassert>
#include <cstdio>
#include <cstring>
#include "../esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/InterconArmGuardCodec.h"
int main(){
  blaze_journal::Binding b={};
  b.owner=0x00AB1234U;b.peer=0x00FE5678U;
  b.role=blaze_journal::ROLE_MASTER;
  for(unsigned i=0;i<16;++i)b.keyTag[i]=(uint8_t)(0xA0U+i);
  uint8_t image[blaze_arm::IMAGE_BYTES]={};
  assert(blaze_arm::encode(b,image));
  assert(blaze_arm::matches(image,sizeof(image),b));
  assert(!blaze_arm::matches(image,sizeof(image)-1,b));
  blaze_journal::Binding wrong=b;
  wrong.owner^=1U;assert(!blaze_arm::matches(image,sizeof(image),wrong));
  wrong=b;wrong.peer^=1U;assert(!blaze_arm::matches(image,sizeof(image),wrong));
  wrong=b;wrong.keyTag[0]^=1U;
  assert(!blaze_arm::matches(image,sizeof(image),wrong));
  wrong=b;wrong.role=blaze_journal::ROLE_SLAVE;
  assert(!blaze_arm::matches(image,sizeof(image),wrong));
  image[6]^=1U;assert(!blaze_arm::matches(image,sizeof(image),b));
  image[6]^=1U;assert(blaze_arm::matches(image,sizeof(image),b));
  b.role=blaze_journal::ROLE_SLAVE;
  assert(!blaze_arm::encode(b,image));
  puts("PASS: durable Master arming marker codec, CRC, identity and role binding");
}
