#! /bin/sh
# /etc/init.d/octopanel.sh

case "$1" in
  start)
    echo "Starting OctoPanel"
    cd /home/pi/OctoPanel
    sudo -u pi /usr/bin/python /home/pi/OctoPanel/OctoPanel.py &
  ;;
  stop)
    echo "Stopping OctoPanel"
#    killall python
    ;;
  *)
    echo "Usage: /etc/init.d/octopanel.sh {start|stop}"
    exit 1
    ;;
esac

exit 0
