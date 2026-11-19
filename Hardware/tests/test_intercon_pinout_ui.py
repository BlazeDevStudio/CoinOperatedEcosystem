#!/usr/bin/env python3
"""Validate actual embedded INTERCON Settings JS, GPIO vectors and source gates.

Node syntax/host checks do not replace ESP8266 compile or hardware acceptance.
"""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
sketch=(ROOT/"esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/BlazePisonetIntercon.ino").read_text(encoding="utf-8")
assert sketch.count("<script>")==1 and sketch.count("</script>")==1, "unexpected inline script count"
js=sketch.split("<script>",1)[1].split("</script>",1)[0]
subprocess.run(["node","--check"],input=js,text=True,check=True)
start=js.index("const pinmapFunctions=")
end=js.index("function pinmapReadForm(){",start)
code=js[start:end] + """
const assert=require('node:assert/strict');
const normal={coinPin:0,relayPin:16,relay2Pin:12,displayClk:5,displayDio:4,buzzerPin:14,csPin:13};
assert.deepEqual(pinmapValidate(normal),[], 'V1.5 NodeMCU wiring must pass');
for(const [k,v] of [['coinPin',16],['coinPin',2],['relayPin',0],['relayPin',15],['displayClk',16],['displayDio',2],['displayDio',6],['relay2Pin',13],['relayPin',14],['coinPin',3],['displayClk',5.1],['relay2Pin',-1]]){
 const bad={...normal,[k]:v};
 assert.ok(pinmapValidate(bad).length>0, k+'='+v+' should be rejected');
}
assert.ok(pinmapValidate({...normal,relayPin:12}).length>0,'duplicate relay conflict');
assert.ok(pinmapValidate({...normal,buzzerPin:12}).length>0,'buzzer fixed D5');
assert.ok(pinmapValidate({...normal,csPin:5}).length>0,'CS fixed D7');
console.log('PASS: embedded live GPIO map rules match preserved firmware wiring');
"""
subprocess.run(["node","-"],input=code,text=True,check=True)
required=[
 'id="pinmap-left"', 'id="pinmap-right"', 'id="pinValidation"',
 'function updatePinout()', "function pinmapValidate(map)",
 "function updateRolePolicy()", 'roleSwitchLocked', 'liveCoinEdges=',
 'parseGpio("coinPin",nc)', 'wiringChanged &&',
 'interconRecovered.snapshot.master.pendingSequence',
 'pinSetIsUnique(nc,nr1,nr2,FIXED_BUZZER_PIN,nclk,ndio)',
]
for needle in required:
    assert needle in sketch, "missing server/UI contract: "+needle
assert 'constrain(server.arg("coinPin").toInt(),0,16)' not in sketch, "silent pin clamp reintroduced"
print("PASS: live pinout, strict GPIO request parsing, role and coin interlocks")
