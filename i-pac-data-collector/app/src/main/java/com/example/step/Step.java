package com.example.step;

public class Step {

    private final int num = 5;//数组大小
    private float[] diffValue = new float[num];//存放波峰波谷差值
    private int diffCount = 0;//实际波峰波谷差值的数量
    private boolean Up = false; //波形上升标志位
    private int UpCount = 0;  //上升次数
    private int upCountBefore = 0;    //上一点的持续上升的次数
    private int downCountBefore = 0;    //上一次的持续下降次数
    private int DownCount = 0;            //下降次数
    private float peak = 0;    //波峰值
    private float valley = 0;    //波谷值
    private long peakTimeNow = 0; //此次波峰的时间
    private long peakTimeBefore = 0;//上次波峰的时间
    private float sensorOld = 0;    //上次传感器的值
    private boolean step = false; //是否走步
    private double stepLength =0.62;  //步长

    //控制参数
    private static final float init_limit_value = (float) 3.5;    //初始阈值
    private static final int PEAK_TIME_DIFF = 400;//满足条件--两个波峰的时间差
    private static final int UP_DOWN_COUNT = 5;//满足条件--上升或者下降连续次数
    private float Auto_limit_value = (float) 4;//动态阈值需要动态的数据，这个值用于这些动态数据的阈值

    private void calStepLength()
    {
        float H = peak-valley;
        long W = peakTimeNow - peakTimeBefore;
        //calStepLength=0.37-0.000155f*W+0.1638*Math.sqrt(H);//原始公式
        stepLength =0.25-0.000155f*W+0.1638*Math.sqrt(H);//修改公式
    }
    public void stepRun(float value) {
        if (sensorOld != 0) {
            if (checkPeak(value, sensorOld)) //检测到波峰
            {
                peakTimeBefore = peakTimeNow;
                long timeOfNow = System.currentTimeMillis();//系统时间毫秒数,当前的时间
                if (timeOfNow - peakTimeBefore >= PEAK_TIME_DIFF && (peak - valley >= Auto_limit_value)) {
                    peakTimeNow = timeOfNow;//将当前时间定为当前波峰时间
                    calStepLength();
                    step = true;
                }
                if (timeOfNow - peakTimeBefore >= PEAK_TIME_DIFF && (peak - valley >= init_limit_value)) {
                    peakTimeNow = timeOfNow;
                    Auto_limit_value = limitValueUpdate(peak - valley);//更新动态阈值
                }
            }
        }
        sensorOld = value;
    }

    private boolean checkPeak(float newValue, float oldValue) {
        boolean stateBefore = Up;//保存上次的状态，上升还是下降
        if (newValue >= oldValue)//上升
        {
            Up = true;
            UpCount++;
            downCountBefore = DownCount;
            DownCount = 0;

        } else//下降
        {
            upCountBefore = UpCount;
            UpCount = 0;

            DownCount++;
            Up = false;
        }

        if (!Up && stateBefore && (upCountBefore >= UP_DOWN_COUNT || oldValue >= 25)) //当前下降之前上升为波峰
        {
            peak = oldValue;
            return true;
        } else if (!stateBefore && Up && downCountBefore >= UP_DOWN_COUNT)//当前上升之前下降为波谷
        {
            valley = oldValue;
            return false;
        } else {
            return false;
        }
    }

    private float limitValueUpdate(float value) //传入波峰与波谷的差值
    {
        float temp = Auto_limit_value;
        if (diffCount < num) {
            diffValue[diffCount] = value;
            diffCount++;
        } else {
            temp = averageValue(diffValue);
            for (int i = 1; i < num; i++) {
                diffValue[i - 1] = diffValue[i];
            }
            diffValue[num - 1] = value;
        }
        return temp;

    }

    private float averageValue(float value[]) {
        float ave = 0;
        for (int i = 0; i < num; i++) {
            ave += value[i];
        }
        ave = ave / num;
        if (ave >= 8)
            ave = (float) 6.5;
        else if (ave >= 7 && ave < 8)
            ave = (float) 5.5;
        else if (ave >= 6 && ave < 7)
            ave = (float) 4.5;
        else {
            ave = (float) 3.5;
        }
        return ave;
    }

    public boolean getStep() {
        return step;
    }

    public void setStep(boolean step) {
        this.step = step;
    }

    public double getStepLength() {
        return stepLength;
    }
}
