#include <cassert>
#include <cstdio>
#include <cstring>
#include "../esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/RemoteCsCodec.h"

int main(){
 uint8_t key[32]={};for(int i=0;i<32;++i)key[i]=(uint8_t)(0x11+i);
 blaze_remote::Message request={};
 memcpy(request.kind,"OPEN",5);request.source=0xB135C001;
 request.destination=0x00AB12CD;request.command=42;
 request.session=0x123456789ABCDEF0ULL;request.event=0;request.value=30;
 char wire[blaze_remote::WIRE_MAX]={};
 const size_t n=blaze_remote::encode(request,key,wire);
 assert(n>130 && n<blaze_remote::WIRE_MAX);
 blaze_remote::Message out={};
 assert(blaze_remote::decode(wire,n,key,request.source,request.destination,out));
 assert(out.command==42 && out.session==request.session && out.value==30);
 assert(!blaze_remote::decode(wire,n,key,request.destination,request.source,out));
 uint8_t otherKey[32]={};memset(otherKey,7,sizeof(otherKey));
 assert(!blaze_remote::decode(wire,n,otherKey,request.source,request.destination,out));
 wire[10]^=1;assert(!blaze_remote::decode(wire,n,key,request.source,request.destination,out));
 wire[10]^=1;assert(blaze_remote::decode(wire,n,key,request.source,request.destination,out));
 assert(!blaze_remote::decode(wire,n-1,key,request.source,request.destination,out));
 // Every event must bind an exact session and pulse amount, never time/price.
 blaze_remote::Message event={};memcpy(event.kind,"EVNT",5);
 event.source=request.destination;event.destination=request.source;
 event.session=request.session;event.event=3;event.value=5;
 const size_t en=blaze_remote::encode(event,key,wire);
 assert(en>0);
 assert(blaze_remote::decode(wire,en,key,event.source,event.destination,out));
 assert(out.session==request.session && out.event==3 && out.value==5);
 // Two-slot record integrity, binding and corruption protection.
 blaze_remote::Record rec={};
 rec.owner=event.source;rec.controller=event.destination;
 for(int i=0;i<16;++i)rec.keyTag[i]=(uint8_t)(i+1);
 rec.generation=1;rec.lastCommand=42;rec.eventCounter=3;
 rec.pendingEvent=3;rec.pendingSession=request.session;rec.pendingPulses=5;
 uint8_t image[blaze_remote::JOURNAL_BYTES]={};
 assert(blaze_remote::encodeRecord(rec,image));
 blaze_remote::Record decoded={};
 assert(blaze_remote::decodeRecord(image,sizeof(image),rec,decoded));
 assert(decoded.generation==1 && decoded.pendingSession==request.session);
 assert(decoded.pendingPulses==5 && decoded.pendingEvent==3);
 auto wrong=rec;wrong.controller^=1;
 assert(!blaze_remote::decodeRecord(image,sizeof(image),wrong,decoded));
 wrong=rec;wrong.keyTag[0]^=1;
 assert(!blaze_remote::decodeRecord(image,sizeof(image),wrong,decoded));
 image[58]^=1;assert(!blaze_remote::decodeRecord(image,sizeof(image),rec,decoded));
 image[58]^=1;assert(blaze_remote::decodeRecord(image,sizeof(image),rec,decoded));
 auto bad=rec;bad.pendingPulses=21;assert(!blaze_remote::encodeRecord(bad,image));
 bad=rec;bad.pendingSession=0;assert(!blaze_remote::encodeRecord(bad,image));
 bad=rec;bad.pendingEvent=0;assert(!blaze_remote::encodeRecord(bad,image));
 bad=rec;bad.generation=0;assert(!blaze_remote::encodeRecord(bad,image));
 // Persistent acknowledged receipt has no pending event, but preserves next id.
 rec.pendingPulses=0;rec.pendingSession=0;rec.pendingEvent=0;rec.generation=2;
 assert(blaze_remote::encodeRecord(rec,image));
 assert(blaze_remote::decodeRecord(image,sizeof(image),rec,decoded));
 assert(decoded.eventCounter==3 && decoded.pendingEvent==0);
 puts("PASS: signed Remote CS OPEN/EVNT, wrong key, corruption, binding and ACK snapshot");
}
