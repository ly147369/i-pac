package com.example.stw;

import android.content.Intent;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;

import com.example.common.SocketThread;

public class MainActivity extends AppCompatActivity {
    Intent intentPDR;
    EditText ipText;
    Button posBtn;
    private boolean isBegin = false;
    public static String SERVER_IP = "";
    public static SocketThread socketThread = new SocketThread();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        ipText = findViewById(R.id.ipText);
        posBtn = findViewById(R.id.posBtn);
        intentPDR = new Intent(MainActivity.this, PdrService.class);
        socketThread.start();
    }

    public void posBtn(View v) {
        if (!isBegin) {
            SERVER_IP = ipText.getText().toString();
            socketThread.connect();
            startService(intentPDR);
            socketThread.sendData("startPOS");
            posBtn.setText("stopPOS");
            isBegin = true;
        } else {
            stopService(intentPDR);
            socketThread.sendData("stopPOS");
            socketThread.disconnect();
            posBtn.setText("startPOS");
            isBegin = false;
        }
    }
}
