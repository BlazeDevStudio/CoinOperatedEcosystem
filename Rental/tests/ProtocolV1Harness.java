import com.blazesystems.blazerental.ProtocolV1;
public final class ProtocolV1Harness {
    public static void main(String[] args) throws Exception {
        String id="1234567890abcdef12345678", nonce="deadbeef00112233deadbeef00112233";
        String key="00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff";
        String proof=ProtocolV1.hmac(key,"v1|status-reply|"+id+"|"+nonce+"|1800000000|1800000900");
        if(!ProtocolV1.verifyReply(id,nonce,1800000000L,1800000900L,key,proof))throw new AssertionError("Valid proof rejected");
        if(ProtocolV1.verifyReply(id,nonce,1800000000L,1800000901L,key,proof))throw new AssertionError("Changed lease accepted");
        if(!ProtocolV1.isHex(ProtocolV1.requestSignature(id,nonce,key),64))throw new AssertionError("HMAC invalid");
        if(ProtocolV1.isHex(id.toUpperCase(),24))throw new AssertionError("Uppercase ID accepted");
        System.out.println("JAVA_PROTOCOL_PASS");
    }
}
