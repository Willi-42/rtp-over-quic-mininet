set -x

for i in {0..8} ;
do 
	for j in {1..20} ;
	do
		if [ -d "data/$i-$j/" ]
		then
			./plot.py --capacity data/$i-$j/capacity.log --rtp-received data/$i-$j/receiver_rtp.log --rtp-sent data/$i-$j/sender_rtp.log --cc data/$i-$j/cc.log --rtcp-received data/$i-$j/sender_rtcp.log --rtcp-sent data/$i-$j/receiver_rtcp.log --config data/$i-$j/config.json -o $i-$j\_rates.png &
			./plot.py --qdelay data/$i-$j/cc.log -o $i-$j\_qdelay.png &
			./plot.py --loss data/$i-$j/sender_rtp.log data/$i-$j/receiver_rtp.log --config data/$i-$j/config.json -o $i-$j\_loss.png &
			./plot.py --latency data/$i-$j/sender_rtp.log data/$i-$j/receiver_rtp.log --config data/$i-$j/config.json -o $i-$j\_latency.png &
		fi
	done
done

wait

#for i in {0..5} ; do ./plot.py --rtp-received data/$i/receiver_rtp.log --rtp-sent data/$i/sender_rtp.log --cc data/$i/cc.log -o $i\_rates.png; done

