LOG_PATH="/home/pi/logs/network.log"
now=$(date +"%m-%d %r")

# Which Interface do you want to check
wlan='wlan0'

# Which address do you want to ping to see if you can connect
pingip='google.com'

if [ "$1" = "" ]; then
    echo "Please provide network interface (wlan0 or ppp0)"
fi

if [ "$1" = "ppp0" ]; then
    echo "$now [EnviroSCALE] Attempting to connect to 3G network." >> $LOG_PATH
    sudo ifdown wlan0
    sleep 2
    sudo bash /home/pi/msarwaru/sakis3g  connect --console APN='CUSTOM_APN' USBINTERFACE='0' USBDRIVER='sierra' OTHER='USBMODEM' USBMODEM="12d1:1417" CUSTOM_APN='blweb' APN_USER='blank' APN_PASS='blank'

    if [ "$(ping -c2 -w1 -q 192.168.1.1 |grep -wc "1 packets")" -ne 1 ]; then
        echo "$now [EnviroSCALE] 3G -> ping to 192.168.1.1 failed." >> $LOG_PATH
        sudo bash /home/pi/msarwaru/sakis3g disconnect
        echo "$now [EnviroSCALE] 3G Network connection attempt failed." >> $LOG_PATH
        sudo bash /home/pi/msarwaru/sakis3g  connect --console APN='CUSTOM_APN' USB$
	#sudo /sbin/ifdown wlan0
        #sleep 5
        #sudo /sbin/ifup --force wlan0
    fi

fi


if [ "$1" = "wlan0" ]; then
    # Perform the network check and reset if necessary
    sudo /bin/ping -c 2 -I $wlan $pingip > /dev/null 2> /dev/null
    if [ $? -ge 1 ] ; then
        echo "$now [EnviroSCALE] WiFi Network is DOWN. Performing a reset" >> $LOG_PATH
        sudo /sbin/ifdown $wlan
        sleep 5
        sudo /sbin/ifup --force $wlan
    else
        :
        #echo "$now [EnviroSCALE] WiFi Network is UP. Just do nothing." >> $LOG_PATH
    fi
fi






