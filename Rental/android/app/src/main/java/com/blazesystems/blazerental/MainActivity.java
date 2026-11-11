package com.blazesystems.blazerental;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.view.Gravity;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.content.SharedPreferences;
import org.json.JSONObject;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

/** Read-only standalone preview. Does NOT implement rental phone enforcement. */
public final class MainActivity extends Activity {
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());
    private final AtomicBoolean pending = new AtomicBoolean(false);
    private TextView status, countdown;
    private EditText server, device, secret;
    private long leaseEndMs = 0;
    private boolean confirmed = false;
    private final Runnable ticker = new Runnable() {
        @Override public void run() {
            long left = confirmed ? Math.max(0, leaseEndMs-SystemClock.elapsedRealtime())/1000 : 0;
            if (left == 0) confirmed = false;
            countdown.setText(String.format(Locale.US, "%02d:%02d:%02d", left/3600, (left/60)%60, left%60));
            if (!confirmed) status.setText("Offline or expired — access not verified");
            main.postDelayed(this,1000);
        }
    };
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(28,32,28,24);
        TextView title=new TextView(this);title.setText("BlazeRental");title.setTextSize(27);root.addView(title);
        TextView note=new TextView(this);note.setText("Standalone controller preview • monitoring only");root.addView(note);
        server=field("Server URL (http://router.local)");device=field("Device ID (24 hex)");secret=field("Pairing secret (64 hex)");
        secret.setInputType(129);
        SharedPreferences prefs=getSharedPreferences("rental_pairing_preview",MODE_PRIVATE);
        server.setText(prefs.getString("server",""));device.setText(prefs.getString("id",""));secret.setText(prefs.getString("secret",""));
        root.addView(server);root.addView(device);root.addView(secret);
        Button check=new Button(this);check.setText("Save pairing & check server");root.addView(check);
        status=new TextView(this);status.setText("Unverified");status.setTextSize(16);status.setGravity(Gravity.CENTER);root.addView(status);
        countdown=new TextView(this);countdown.setText("00:00:00");countdown.setTextSize(34);countdown.setGravity(Gravity.CENTER);root.addView(countdown);
        TextView caution=new TextView(this);caution.setText("No kiosk lock, paid credit or remote administration in this preview. Pair only on a trusted LAN.");root.addView(caution);
        setContentView(root);
        check.setOnClickListener(v->sync(prefs));
    }
    private EditText field(String hint){EditText e=new EditText(this);e.setSingleLine(true);e.setHint(hint);return e;}
    private void sync(SharedPreferences prefs) {
        if(!pending.compareAndSet(false,true)) return;
        confirmed=false;
        final String url=server.getText().toString().trim(), id=device.getText().toString().trim(), key=secret.getText().toString().trim();
        if ((!url.startsWith("http://") && !url.startsWith("https://")) || !ProtocolV1.isHex(id,24) || !ProtocolV1.isHex(key,64)) {
            status.setText("Invalid server or pairing credentials");pending.set(false);return;
        }
        prefs.edit().putString("server",url).putString("id",id).putString("secret",key).apply();
        status.setText("Checking server…");
        io.execute(()-> {
            boolean valid=false; long remainingMs=0;String message="Server unavailable / signature invalid";
            try {
                String nonce=ProtocolV1.nonce();String sig=ProtocolV1.requestSignature(id,nonce,key);
                URL endpoint=new URL(url.replaceAll("/+$","")+"/cgi-bin/blazerental?action=status&device_id="+id+"&nonce="+nonce+"&sig="+sig);
                if(endpoint.getUserInfo()!=null || endpoint.getQuery()==null)throw new IllegalArgumentException("Invalid server");
                HttpURLConnection con=(HttpURLConnection)endpoint.openConnection();
                con.setConnectTimeout(3000);con.setReadTimeout(3000);con.setUseCaches(false);
                try {
                    if(con.getResponseCode()!=200)throw new IllegalArgumentException("HTTP error");
                    try(InputStream in=con.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream()) {
                        byte[] chunk=new byte[1024];int n;
                        while((n=in.read(chunk))!=-1){if(out.size()+n>8192)throw new IllegalArgumentException("Oversize response");out.write(chunk,0,n);}
                        JSONObject response=new JSONObject(out.toString("UTF-8"));
                        long now=response.getLong("server_time"),until=response.getLong("lease_until");
                        if(!response.getBoolean("ok") || response.getInt("api_version")!=1 || !id.equals(response.getString("device_id")) || !nonce.equals(response.getString("nonce")) || !ProtocolV1.verifyReply(id,nonce,now,until,key,response.getString("proof")))throw new IllegalArgumentException("Unauthenticated response");
                        remainingMs=Math.max(0,until-now)*1000L;
                        if(remainingMs>2592000000L) throw new IllegalArgumentException("Lease exceeds preview bound");
                        valid=true;message="Server verified";
                    }
                } finally {con.disconnect();}
            } catch(Exception ignored) { }
            final boolean ok=valid;final long duration=remainingMs;final String result=message;
            main.post(()-> {
                pending.set(false);
                if(isFinishing()||isDestroyed()) return;
                if(ok) {leaseEndMs=SystemClock.elapsedRealtime()+duration;confirmed=duration>0;}
                status.setText(result);
            });
        });
    }
    @Override public void onResume(){super.onResume();main.post(ticker);}
    @Override public void onPause(){main.removeCallbacks(ticker);super.onPause();}
    @Override public void onDestroy(){main.removeCallbacks(ticker);io.shutdownNow();super.onDestroy();}
}
