#!/bin/bash

######functions ######
count_job_success_devices(){
    temp=$(aws iot describe-job --job-id TestJob5566unitx | awk -F " " '{print $8}' | tr "\n" " ")
    success_devices_count=$(echo $temp | awk -F " " '{print $2}')
    echo $success_devices_count
    return "$success_devices_count"
}

####### build you firmware #######
echo "Building Firmware"
sleep 5s
####### flash it firmware to your SOC #######
echo "Flashing your device"
sleep 5s
####### Test Starts here!! #######
echo "Stress Starts"
echo "your agent should be listening to the Jobs from IoT Core"

#### parameter initicalization #####
jobid=$2
TestRound=$3
JobFile=$4
JobStreamFile=$5
JobStreamID=$6
Targets=$7
counter=0
fail_counter=0
HardLimitWaitCount=200

####parse thing lists
file="${PWD}/${1}"
device_counter=0
ThingARN=""
while IFS= read line
do
    if  [ $device_counter -gt 0 ]
    then
        ThingARN="$line $ThingARN"
    else
        ThingARN=$line
    fi
    device_counter=$((device_counter+1))
done <"$file"

if [ 0 -eq $device_counter ]
then
    ThingARN=$(cat $file)
    if [ -z $ThingARN ]
    then
        echo "error device_counter can not be 0"
        exit
    else
        device_counter=$((device_counter+1))
    fi
fi



echo "final ThingARN, total $device_counter things"
ThingARN="$ThingARN"
echo "$ThingARN"
Targets=$ThingARN


### Start to Deploy Jobs
aws iot cancel-job --job-id ${jobid}
sleep 10s
aws iot delete-job --job-id ${jobid}
sleep 10s
aws iot delete-stream --stream-id ${JobStreamID}
sleep 10s

while  [ $counter -lt $TestRound ]
do 
    aws iot create-stream --cli-input-json ${JobStreamFile}
    aws iot create-job --job-id ${jobid} --targets ${Targets} --document ${JobFile} --description "example job test" --target-selection SNAPSHOT
    sleep 3s
    WaitCount=0
    while true
    do
        result_p=$(aws iot describe-job --job-id ${jobid}  | grep IN_PROGRESS)
        if [ -z "$result_p" ]
        then
            result_c=$(aws iot describe-job --job-id ${jobid}  | grep COMPLETED)
            if [ -z "$result_c" ]
            then
                if [ $WaitCount -gt $HardLimitWaitCount ]
                then
                    echo "OTA job failed"
                    echo "print the JOB status"
                    counter=0
                    aws iot describe-job --job-id ${jobid}
                    #aws iot cancel-job --job-id ${jobid}
                    #aws iot delete-job --job-id ${jobid}
                    #aws iot delete-stream --stream-id ${JobStreamID}
                    sleep 30s
                    exit
                else
                    aws iot describe-job --job-id ${jobid}
                    sleep 30s
                fi
            else
                success_devices_count=$( count_job_success_devices )
                if [ $success_devices_count -eq $device_counter ]
                then
                    counter=$((counter+1))
                    aws iot describe-job --job-id ${jobid}
                    echo "OTA job success and completed devices $success_devices_count, device_counter: $device_counter count=$counter, canceling the job and creating a new one"
                    aws iot delete-job --job-id ${jobid}
                    aws iot delete-stream --stream-id ${JobStreamID}
                    sleep 30s
                    break
                else
                    echo "success device count and completed device count mis match "
                    echo "OTA job failed"
                    echo "print the JOB status"
                    counter=0
                    fail_counter=$((fail_counter+1))
                    aws iot describe-job --job-id ${jobid}
                    #aws iot cancel-job --job-id ${jobid}
                    #aws iot delete-job --job-id ${jobid}
                    #aws iot delete-stream --stream-id ${JobStreamID}
                    sleep 30s
                    exit
                fi

            fi
        else
            echo "OTA JOB IN PROGRESS..."
            aws iot describe-job --job-id ${jobid}
            sleep 10s
            WaitCount=$((WaitCount+1))
        fi
    done
done

# results
echo "total,$counter" > results.csv
echo "fail,$fail_counter" >> results.csv
echo "succeed,$((counter - fail_counter))" >> results.csv