package com.example.stw;

import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.IBinder;

import com.example.step.SMA;
import com.example.step.Step;

public class PdrService extends Service {

    private SensorManager sensorManager;//传感器
    private SMA sma;//移动平均法
    private Step step;//是否走了一步
    private float[] accValues = new float[3];//SMA之后的加速度
    private float stepDirection = 0;//角度
    private String SerialNumber = android.os.Build.SERIAL;
    private int standtime = 0;

    public PdrService() {
    }

    @Override
    public IBinder onBind(Intent intent) {
        // TODO: Return the communication channel to the service.
        throw new UnsupportedOperationException("Not yet implemented");
    }

    @Override
    public void onCreate() {
        //service创建时调用
        super.onCreate();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        //service启动时调用
        new Thread(new Runnable() {
            @Override
            public void run() {
                step = new Step();
                sma = new SMA();
                beginPdrSensor();
            }
        }).start();

        return super.onStartCommand(intent, flags, startId);
    }

    @Override
    public void onDestroy() {
        //service销毁时调用
        super.onDestroy();
        if (sensorManager != null) {
            sensorManager.unregisterListener(listenerA);
            sensorManager.unregisterListener(listenerM);
        }

    }

    private void beginPdrSensor() {
        Sensor sensorA;//加速度传感器
        Sensor sensorM;//地磁传感器
        Sensor sensorG;//陀螺仪传感器
        sensorManager = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        //开启加速度传感器监听
        sensorA = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        sensorManager.registerListener(listenerA, sensorA, SensorManager.SENSOR_DELAY_GAME);
        //开启地磁传感器监听
        sensorM = sensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD);
        sensorManager.registerListener(listenerM, sensorM, SensorManager.SENSOR_DELAY_GAME);
        //开启陀螺仪传感器监听
        sensorG = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE);
        sensorManager.registerListener(listenerG, sensorG, SensorManager.SENSOR_DELAY_GAME);


    }

    private double adjustStepLength(double roughStepLength) {
        if (roughStepLength <= 0) return 0.42;
        else if (roughStepLength <= 0.53) return 0.53;
        else if (roughStepLength <= 0.76) return roughStepLength;
        else if (roughStepLength <= 1.2) return 0.76;
        else return 0.95;

    }

    private SensorEventListener listenerA = new SensorEventListener() {
        //加速度传感器监听器
        @Override
        public void onSensorChanged(SensorEvent sensorEvent) {
            //获取x、y、z三轴加速度
            float accX = sensorEvent.values[0];
            float accY = sensorEvent.values[1];
            float accZ = sensorEvent.values[2];
            //判断是否走了一步
            if (judgeStep(accX, accY, accZ)) {
                //将（角度dir，步长）上传
                standtime = 0;
                step.setStep(false);
                double stepLength = adjustStepLength(step.getStepLength());
                String PdrData = "PDR " + String.format("%.2f", stepDirection) + " " + String.format("%.2f", stepLength) + " " + SerialNumber;
                MainActivity.socketThread.sendData(PdrData);
            } else {
                standtime++;
                if (standtime == 100) {
                    standtime = 0;
                    String PdrData = "PDR " + "0" + " " + "0" + " " + SerialNumber;
                    MainActivity.socketThread.sendData(PdrData);
                }
            }
        }

        @Override
        public void onAccuracyChanged(Sensor sensor, int i) {

        }
    };

    private boolean judgeStep(float accX, float accY, float accZ) {
        //判断是否走了一步
        if (sma.ifTrue())//加速度处理完成
        {
            sma.smaRun(accX, accY, accZ);
            accValues[0] = sma.getX();
            accValues[1] = sma.getY();
            accValues[2] = sma.getZ();
            float accAll = (float) Math.sqrt(accValues[0] * accValues[0] + accValues[1] * accValues[1] + accValues[2] * accValues[2]);
            step.stepRun(accAll);
        } else {
            sma.smaInit(accX, accY, accZ);
        }
        return step.getStep();
    }

    private SensorEventListener listenerM = new SensorEventListener() {
        @Override
        public void onSensorChanged(SensorEvent sensorEvent) {
            float[] dirValues = new float[3];
            dirValues[0] = sensorEvent.values[0];
            dirValues[1] = sensorEvent.values[1];
            dirValues[2] = sensorEvent.values[2];
            stepDirection = calculateOrientation(dirValues);
        }

        @Override
        public void onAccuracyChanged(Sensor sensor, int i) {

        }
    };

    private float calculateOrientation(float dirValues[]) {
        //根据地磁角度计算世界角度
        float[] values = new float[3];
        float[] R = new float[9];
        SensorManager.getRotationMatrix(R, null, accValues, dirValues);
        SensorManager.getOrientation(R, values);//values[0]即为世界角度（弧度）
        values[0] = (float) Math.toDegrees(values[0]);//转换为角度
        return values[0];
    }

    private SensorEventListener listenerG = new SensorEventListener() {
        @Override
        public void onSensorChanged(SensorEvent sensorEvent) {

        }

        @Override
        public void onAccuracyChanged(Sensor sensor, int i) {

        }
    };
}
