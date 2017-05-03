stt=1
## sleep in bash for loop ##
# create onem2m
for i in {1..5}
do
  kubectl create -f openhab.deploy/openhab_configmap_v02_$i.yaml --namespace kube-system
  #sleep 1h
done

# create sensor
# kubectl create -f sensor.deploy/ --namespace kube-system


