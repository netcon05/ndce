# NDCE
### Network Device Configuration Editor

This application is used to make changes to network device configuration remotely using **TELNET** or **SSH** protocols.

The information about network devices is gathered using **SNMP** protocol.

The application does its job asynchronously.

**On linux systems in order to make icmp pings use the hack below.**

1. Open sysctl.conf in your text editor
    
    ```sudo nano /etc/sysctl.conf```

2. Add code below to the end of the config file

    `net.ipv4.ping_group_range = 0 1000`

3. Save the file.

4. Apply changes.

    `sudo sysctl -p`

> 0 1000 is a range of user ids who has permission to make icmp pings.
