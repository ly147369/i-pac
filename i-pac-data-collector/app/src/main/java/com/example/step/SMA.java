package com.example.step;

public class SMA {
    //处理加速度，简单移动平均法（Simple Moving Average）
    private slideQueue queueX;
    private slideQueue queueY;
    private slideQueue queueZ;
    private float maxX;
    private float maxY;
    private float maxZ;
    private int length = 5;

    public SMA() {
        queueX = new slideQueue();
        queueY = new slideQueue();
        queueZ = new slideQueue();
    }


    public boolean ifTrue()//判断是否大于5
    {
        return queueX.full() && queueY.full() && queueZ.full();
    }

    public void smaInit(float x, float y, float z) {
        maxX += x;
        maxY += y;
        maxZ += z;
        queueZ.offer(z);
        queueX.offer(x);
        queueY.offer(y);
    }

    public void smaRun(float x, float y, float z)//满足==5执行
    {
        maxX -= queueX.poll();
        queueX.offer(x);
        maxX += x;

        maxY -= queueY.poll();
        queueY.offer(y);
        maxY += y;

        maxZ -= queueZ.poll();
        queueZ.offer(z);
        maxZ += z;

    }

    public float getX() {
        return maxX / length;
    }

    public float getY() {
        return maxY / length;
    }

    public float getZ() {
        return maxZ / length;
    }
}