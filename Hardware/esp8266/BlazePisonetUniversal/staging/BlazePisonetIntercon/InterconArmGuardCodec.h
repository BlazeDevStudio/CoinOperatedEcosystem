#pragma once
// INTERCON Stage 4.1: portable, bound, versioned Master arm marker.
// A marker means a previous boot intentionally allowed coin acceptance.
// It is NOT a coin counter or proof that every physical coin was recorded.
#include "InterconJournalCodec.h"

namespace blaze_arm {
static const size_t IMAGE_BYTES=32;
static const uint32_t MAGIC=0x314D5241UL; // ARM1 in little-endian
inline bool encode(const blaze_journal::Binding& b,uint8_t out[IMAGE_BYTES]){
  if(b.role!=blaze_journal::ROLE_MASTER || !b.owner || !b.peer ||
     b.owner==b.peer)return false;
  uint8_t nonzero=0;
  for(uint8_t i=0;i<16;i++)nonzero|=b.keyTag[i];
  if(!nonzero)return false;
  memset(out,0,IMAGE_BYTES);
  blaze_journal::w32(out,MAGIC);
  blaze_journal::w32(out+4,b.owner);
  blaze_journal::w32(out+8,b.peer);
  memcpy(out+12,b.keyTag,16);
  blaze_journal::w32(out+28,blaze_journal::crc32(out,28));
  return true;
}
inline bool matches(const uint8_t* image,size_t n,
                    const blaze_journal::Binding& expected){
  if(!image || n!=IMAGE_BYTES ||
     blaze_journal::r32(image+28)!=blaze_journal::crc32(image,28))
    return false;
  uint8_t canonical[IMAGE_BYTES]={};
  return encode(expected,canonical) &&
         memcmp(canonical,image,IMAGE_BYTES)==0;
}
} // namespace blaze_arm
