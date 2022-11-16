package com.example.step;

public class slideQueue {
    //滑动队列,配合sma使用
    private float[] data;// 队列
    private int front;// 队列头，允许删除
    private int rear;// 队列尾，允许插入
    private int LENGTH = 5;
    private boolean full = false;
    private int t = 0;

    public slideQueue() {
        data = new float[LENGTH];
        front = rear = 0;
    }

    // 入队
    public void offer(float date) {
        if (rear < LENGTH) {
            data[rear++] = date;
        } else {
            rear = 0;
        }

        if (t++ >= 5)
            full = true;
    }

    // 出队
    public float poll() {

        if (front < LENGTH) {
            float value = data[front];// 保留队列的front端的元素的值

            front++;
            return value;

        } else {
            front = 0;
            float value = data[front];
            return value;
        }

    }

    public boolean full() {
        return full;
    }
}