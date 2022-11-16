package com.example.common;

import android.util.Log;

import com.example.stw.MainActivity;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Socket;
import java.net.UnknownHostException;

public class ConnManager {

    private static int postPort = 21567;
    private static Socket socket;

    private static ConnManager instance;

    private ConnManager() {
    }

    public static ConnManager getInstance() {
        if (instance == null) {
            synchronized (ConnManager.class) {
                if (instance == null) {
                    instance = new ConnManager();
                }
            }
        }
        return instance;
    }

    public void connect() {
        if (socket == null || socket.isClosed()) {

            try {
                socket = new Socket(MainActivity.SERVER_IP, postPort);
            } catch (UnknownHostException e) {
                e.printStackTrace();
            } catch (IOException e) {
                //throw new RuntimeException("连接失败： " + e.getMessage());
            }

        }

    }

    OutputStream os;

    public void sendMessage(final String content) {

        os = null;
        Log.d("send: ", content);
        try {
            if (socket != null) {
                os = socket.getOutputStream();
                os.write(content.getBytes());
                os.flush();
            }
        } catch (IOException e) {
            //throw new RuntimeException("发送失败"+ e.getMessage());
        }

    }


    public void disConnect() {
        if (socket != null && !socket.isClosed()) {
            try {
                socket.close();
            } catch (IOException e) {
                //throw new RuntimeException("关闭失败" + e.getMessage());
            }
            socket = null;
        }


    }

    public boolean isReady() {
        if (socket != null && !socket.isClosed())
            return true;
        return false;
    }

    public String reciveMessage() {

        InputStream is;
        try {
            is = socket.getInputStream();
            byte[] buffer = new byte[1024];
            int len = -1;
            if ((len = is.read(buffer)) != -1) {
                is.close();
                return new String(buffer, 0, len);
            }
        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }

        return "";
    }

    public interface ConnectionListener {
        void pushData(String str);
    }

    private ConnectionListener mListener;

    public void setConnectionListener(ConnectionListener listener) {
        this.mListener = listener;
    }

}
