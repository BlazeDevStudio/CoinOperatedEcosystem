package com.blazesystems.blazerental;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Locale;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/** Pure Java wire contract; this class has no BlazePwifi or Android dependency. */
public final class ProtocolV1 {
    private static final SecureRandom RANDOM = new SecureRandom();
    private ProtocolV1() {}

    public static String nonce() {
        byte[] n = new byte[16];
        RANDOM.nextBytes(n);
        return hex(n);
    }

    public static String hmac(String secretHex, String canonical) throws Exception {
        if (!isHex(secretHex, 64)) throw new IllegalArgumentException("Invalid pairing key");
        byte[] key = fromHex(secretHex);
        Mac m = Mac.getInstance("HmacSHA256");
        m.init(new SecretKeySpec(key, "HmacSHA256"));
        return hex(m.doFinal(canonical.getBytes(StandardCharsets.UTF_8)));
    }

    public static String requestSignature(String id, String nonce, String secret) throws Exception {
        return hmac(secret, "v1|status|" + id + "|" + nonce);
    }

    public static boolean verifyReply(String id, String nonce, long now, long until, String secret, String proof) throws Exception {
        if (!isHex(proof, 64) || !isHex(id, 24) || !isHex(nonce, 32) || now < 1700000000L || until < 0) return false;
        String expected = hmac(secret, "v1|status-reply|" + id + "|" + nonce + "|" + now + "|" + until);
        return MessageDigest.isEqual(fromHex(proof), fromHex(expected));
    }

    public static boolean isHex(String s, int n) {
        if (s == null || s.length() != n) return false;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (!(c >= '0' && c <= '9') && !(c >= 'a' && c <= 'f')) return false;
        }
        return true;
    }

    private static byte[] fromHex(String s) {
        byte[] b = new byte[s.length()/2];
        for (int i=0;i<b.length;i++) b[i]=(byte)((Character.digit(s.charAt(i*2),16)<<4)|Character.digit(s.charAt(i*2+1),16));
        return b;
    }
    private static String hex(byte[] b) {
        char[] chars = "0123456789abcdef".toCharArray();
        char[] s = new char[b.length*2];
        for(int i=0;i<b.length;i++) { int x=b[i]&255; s[2*i]=chars[x>>>4]; s[2*i+1]=chars[x&15]; }
        return new String(s);
    }
}
