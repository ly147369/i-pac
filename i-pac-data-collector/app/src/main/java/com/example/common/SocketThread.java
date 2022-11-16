package com.example.common;


public class SocketThread extends Thread {
    ConnManager connManager = ConnManager.getInstance();
    private boolean quit = false;
    private boolean conn = false;
    private int num = 0;
    StringBuffer data = new StringBuffer();

    public void sendData(String data) {
        this.data.append(data);
        num++;
    }

    public void connect() {
        conn = true;
    }

    public void disconnect() {
        quit = true;
    }

    public void run() {

        while (true) {
            if (conn) {
                connManager.connect();
                conn = false;
            }
            if (quit) {
                connManager.sendMessage(data.toString());
                connManager.disConnect();
                data.setLength(0);
                num = 0;
                quit = false;
            }
            if (num == 1) {
                connManager.sendMessage(data.toString());
                num = 0;
                data.setLength(0);
            }
        }
    }
}
